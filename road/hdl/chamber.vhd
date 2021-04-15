-------------------------------------------------------------------------------
-- Title      : Chamber
-------------------------------------------------------------------------------
-- File       : chamber.vhd
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
    S0_WIDTH       : natural := 16;
    S1_REUSE       : natural := 4       -- 1, 2, or 4
    );
  port(
    clock   : in  std_logic;            -- MUST BE 320MHZ
    dav_i   : in  std_logic;
    dav_o   : out std_logic;
    sbits_i : in  chamber_t;
    segs_o  : out segment_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber;

architecture behavioral of chamber is

  constant CHAMBER_WIDTH_S0 : natural := PRT_WIDTH/S0_WIDTH;
  constant CHAMBER_WIDTH_S1 : natural := PRT_WIDTH/S0_WIDTH/2;

  constant NUM_SELECTORS_S0 : natural := NUM_PARTITIONS/S1_REUSE/2;

  type segs_t is array
    (integer range 0 to NUM_PARTITIONS-1) of
    segment_list_t (CHAMBER_WIDTH_S0-1 downto 0);

  type segs_muxin_t is array
    (integer range 0 to NUM_PARTITIONS/2-1) of
    segment_list_t (2*CHAMBER_WIDTH_S0-1 downto 0);

  type segs_muxout_t is array
    (integer range 0 to NUM_PARTITIONS/2/S1_REUSE-1) of
    segment_list_t (CHAMBER_WIDTH_S0-1 downto 0);

  type segs_demux_t is array
    (integer range 0 to NUM_PARTITIONS/2-1) of
    segment_list_t (CHAMBER_WIDTH_S0-1 downto 0);

  signal segs        : segs_t;
  signal segs_muxin  : segs_muxin_t;
  signal segs_muxout : segs_muxout_t;
  signal segs_demux  : segs_demux_t;

  signal segs_dav, segs_mux_dav    : std_logic := '0';
  signal muxin_phase, muxout_phase : natural range 0 to S1_REUSE-1;

  signal segs_s1_flat : segment_list_t
    (NUM_PARTITIONS/2*CHAMBER_WIDTH_S0-1 downto 0);

  -- signal pre_gcl_pats     : pat_list_t (PRT_WIDTH-1 downto 0);
  -- type pre_gcl_array_t is array (integer range 0 to 7) of
  --    pat_list_t (PRT_WIDTH-1 downto 0);
  -- signal pre_gcl_pats_o   : pre_gcl_array_t;
  -- signal pre_gcl_pats_i_p : pre_gcl_array_t;
  -- signal pre_gcl_pats_i_n : pre_gcl_array_t;

begin

  assert S1_REUSE = 1 or S1_REUSE = 2 or S1_REUSE = 4
    report "Only allowed values for s1 reuse are 1,2, and 4"
    severity error;

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

        -- primary layer
        partition_i => sbits_i(I),

        -- neighbor layer
        neighbor_i => neighbor,

        -- output patterns
        dav_o      => segs_dav,
        segments_o => segs(I)

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
  --
  -- Multiplex together different partition pairs into a single register
  --
  --------------------------------------------------------------------------------

  dav_to_phase_muxin_inst : entity work.dav_to_phase
    generic map (MAX => 8, DIV => 8/S1_REUSE)
    port map (clock  => clock, dav => segs_dav, phase_o => muxin_phase);
  dav_to_phase_muxout_inst : entity work.dav_to_phase
    generic map (MAX => 8, DIV => 8/S1_REUSE)
    port map (clock  => clock, dav => segs_dav, phase_o => muxout_phase);  -- FIXME: this input is wrong

  s1_sort : for I in 0 to NUM_SELECTORS_S0 - 1 generate
  begin

    --------------------------------------------------------------------------------
    -- MUX
    --------------------------------------------------------------------------------

    process (clock) is
    begin
      if (rising_edge(clock)) then
        segs_mux_dav  <= segs_dav;
        segs_muxin(I) <= segs ((S1_REUSE*I+muxin_phase)*2+1)
                         & segs ((S1_REUSE*I+muxin_phase)*2);
      end if;
    end process;

    --------------------------------------------------------------------------------
    -- Sort
    --------------------------------------------------------------------------------

    -- segs (2*S1_REUSE * I + 2*muxin_phase + 1) &
    -- segs (2*S1_REUSE * I + 2*muxin_phase);
    segment_selector_neighbor : entity work.segment_selector
      generic map (
        MODE       => "BITONIC",
        NUM_INPUTS => CHAMBER_WIDTH_S0*2,  -- put in two partitions worth...

        -- FIXME: !!! only need to put out a max of NUM_SEGMENTS...
        -- any more are useless
        NUM_OUTPUTS => CHAMBER_WIDTH_S0  -- put out half that number
        )
      port map (
        clock  => clock,
        -- take partition I and partition I+1 and choose the best patterns
        segs_i => segs_muxin(I),

        -- FIXME: !!! this phase needs to be segment_selector dav_o
        segs_o => segs_muxout(I)
        );

    PH : for SEL in 0 to S1_REUSE-1 generate  -- number of phases
    begin
      process (clock) is
      begin
        if (rising_edge(clock)) then
          if (muxout_phase = SEL) then
            segs_demux (I*S1_REUSE+SEL) <= segs_muxout(I);
          end if;
        end if;
      end process;
    end generate;

  end generate;


  --------------------------------------------------------------------------------
  -- Demux
  --------------------------------------------------------------------------------

  -- segs_demux (I*S1_REUSE+segs_s0_phase) <= segs_s1_muxout;

  -- process (clock) is
  -- begin
  --   if (rising_edge(clock)) then
  --     if (muxout_phase = 0) then
  --       segs_demux (0) <= segs_muxout(0);
  --       segs_demux (2) <= segs_muxout(1);
  --       -- segs_demux (2) <= segs_muxout(1);
  --       -- segs_demux (4) <= segs_muxout(2);
  --       -- segs_demux (6) <= segs_muxout(3);
  --     else
  --       segs_demux (1) <= segs_muxout(0);
  --       segs_demux (3) <= segs_muxout(1);
  --       -- segs_demux (3) <= segs_muxout(1);
  --       -- segs_demux (5) <= segs_muxout(2);
  --       -- segs_demux (7) <= segs_muxout(3);
  --   end if;
  --   end if;
  -- end process;


  --------------------------------------------------------------------------------
  -- Final canidate sorting
  --
  -- sort from 12*4 patterns down to NUM_SEGMENTS
  --------------------------------------------------------------------------------

  -- FIXME: replace with priority encoder... ? the # of outputs is very small...

  segs_s1_flat <= segs_demux(3) & segs_demux(2) & segs_demux(1) & segs_demux(0);

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => NUM_PARTITIONS*CHAMBER_WIDTH_S1
      )
    port map (
      clock  => clock,
      segs_i => segs_s1_flat,
      segs_o => segs_o
      );

end behavioral;
