-------------------------------------------------------------------------------
-- Title      : Chamber
-------------------------------------------------------------------------------
-- File       : chamber.vhd
-- Last update: 2021-04-14
-- Standard   : VHDL'2008
-------------------------------------------------------------------------------
-- Description:
--
--   Segment finding for a single ME0 chamber
--
-------------------------------------------------------------------------------

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber is
  generic (
    FINAL_BITONIC  : boolean := true;
    NUM_PARTITIONS : integer := 8;
    NUM_SEGMENTS   : integer := 4;
    MUX_FACTOR     : integer := FREQ/40;
    S0_WIDTH       : natural := 8;
    S1_WIDTH       : natural := 2
    );
  port(
    clock   : in  std_logic;
    dav_i   : in  std_logic;
    dav_o   : out std_logic;
    sbits_i : in  chamber_t;
    segs_o  : out pat_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber;

architecture behavioral of chamber is

  constant CHAMBER_WIDTH_S0 : natural := PRT_WIDTH/S0_WIDTH;
  constant CHAMBER_WIDTH_S1 : natural := PRT_WIDTH/S0_WIDTH/2;

  type pats_s0_array_t is array
    (integer range 0 to NUM_PARTITIONS-1) of pat_list_t (CHAMBER_WIDTH_S0-1 downto 0);

  type pats_s1_array_t is array
    (integer range 0 to NUM_PARTITIONS/2-1) of pat_list_t (CHAMBER_WIDTH_S0-1 downto 0);

  signal pats_s0 : pats_s0_array_t;
  signal pats_s1 : pats_s1_array_t;

  -- signal pats_mux : pat_list_t (PRT_WIDTH/S0_REGION_SIZE-1 downto 0);

  -- signal pre_gcl_pats     : pat_list_t (PRT_WIDTH-1 downto 0);
  -- type pre_gcl_array_t is array (integer range 0 to 7) of pat_list_t (PRT_WIDTH-1 downto 0);
  -- signal pre_gcl_pats_o   : pre_gcl_array_t;
  -- signal pre_gcl_pats_i_p : pre_gcl_array_t;
  -- signal pre_gcl_pats_i_n : pre_gcl_array_t;

  -- signal selector_s1_o : pat_list_t (NUM_SEGMENTS-1 downto 0);
  -- signal selector_s2_o : pat_list_t (NUM_SEGMENTS-1 downto 0);

  signal phase_pattern_mux : natural;
  signal phase_selector      : natural;

begin

  dav_to_phase_mux_inst : entity work.dav_to_phase
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_pattern_mux);

  dav_to_phase_selector_inst : entity work.dav_to_phase
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_selector);

  --------------------------------------------------------------------------------
  -- Get pattern unit patterns for each partition, one for each strip
  --------------------------------------------------------------------------------

  -- pre_gcl_pats_i_n (0) <= (others => null_pattern);
  -- pre_gcl_pats_i_n (1) <= pre_gcl_pats_o (0);
  -- pre_gcl_pats_i_n (2) <= pre_gcl_pats_o (1);
  -- pre_gcl_pats_i_n (3) <= pre_gcl_pats_o (2);
  -- pre_gcl_pats_i_n (4) <= pre_gcl_pats_o (3);
  -- pre_gcl_pats_i_n (5) <= pre_gcl_pats_o (4);
  -- pre_gcl_pats_i_n (6) <= pre_gcl_pats_o (5);
  -- pre_gcl_pats_i_n (7) <= pre_gcl_pats_o (6);

  -- pre_gcl_pats_i_p (0) <= pre_gcl_pats_o (1);
  -- pre_gcl_pats_i_p (1) <= pre_gcl_pats_o (2);
  -- pre_gcl_pats_i_p (2) <= pre_gcl_pats_o (3);
  -- pre_gcl_pats_i_p (3) <= pre_gcl_pats_o (4);
  -- pre_gcl_pats_i_p (4) <= pre_gcl_pats_o (5);
  -- pre_gcl_pats_i_p (5) <= pre_gcl_pats_o (6);
  -- pre_gcl_pats_i_p (6) <= pre_gcl_pats_o (7);
  -- pre_gcl_pats_i_n (7) <= (others => null_pattern);

  partition_gen : for I in 0 to NUM_PARTITIONS-1 generate
    signal neighbor : partition_t := (others => (others => '0'));
  begin

    p0 : if (I > 0) generate
      neighbor <= sbits_i(I-1);
    end generate;

    partition_inst : entity work.partition
      generic map (
        NUM_SEGMENTS  => NUM_SEGMENTS,
        PARTITION_NUM => I,
        S0_WIDTH      => S0_WIDTH
        )
      port map (

        clock => clock,
        dav_i => dav_i,
        dav_o => dav_o,

        -- primary layer
        partition_i => sbits_i(I),

        -- neighbor layer
        neighbor_i => neighbor,

        -- output patterns
        pats_o => pats_s0(I)

        -- x-partition ghost cancellation
        -- pre_gcl_pats_o   => pre_gcl_pats_o(I),
        -- pre_gcl_pats_i_p => pre_gcl_pats_i_p(I),
        -- pre_gcl_pats_i_n => pre_gcl_pats_i_n(I),

        );
  end generate;

  --------------------------------------------------------------------------------
  -- Sort neighbors together
  --
  -- sort from 12*8 patterns down to 12*4
  --------------------------------------------------------------------------------

  -- FIXME: append the partition number before sorting

  s1_sort : for I in 0 to NUM_PARTITIONS/2-1 generate
  begin

    segment_selector_neighbor : entity work.segment_selector
      generic map (
        MODE        => "BITONIC",
        NUM_INPUTS  => CHAMBER_WIDTH_S0*2,  -- put in two partitions worth...
        NUM_OUTPUTS => CHAMBER_WIDTH_S0     -- put out half that number
        )
      port map (
        clock  => clock,
        -- take partition I and partition I+1 and choose the best patterns
        pats_i => pats_s0 (I*2+1) & pats_s0 (I*2),
        pats_o => pats_s1 (I),
        sump   => open
        );

  end generate;

  --------------------------------------------------------------------------------
  -- Final canidate sorting
  --
  -- sort from 12*4 patterns down to NUM_SEGMENTS
  --------------------------------------------------------------------------------

  -- FIXME: replace with priority encoder... the # of outputs is so darn small...
  -- keep it under 8 and it only takes 1 clock and 1 encoder

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => NUM_PARTITIONS*CHAMBER_WIDTH_S1
      )
    port map (
      clock  => clock,
      pats_i => pats_s1 (3) & pats_s1 (2) & pats_s1 (1) & pats_s1 (0),
      pats_o => segs_o,
      sump   => open
      );


end behavioral;
