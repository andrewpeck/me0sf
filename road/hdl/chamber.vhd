----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--   Segment finding for a single ME0 chamber
----------------------------------------------------------------------------------

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber is
  generic (
    EN_NON_POINTING : boolean := false;

    FINAL_BITONIC  : boolean := true;
    NUM_PARTITIONS : integer := 8;
    NUM_SEGMENTS   : integer := 4;
    S0_WIDTH       : natural := 16;
    S1_REUSE       : natural := 4;      -- 1, 2, or 4

    SELECTOR_LATENCY : natural := 4;

    PATLIST : patdef_array_t := patdef_array;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY2_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY3_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY4_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY5_SPAN : natural := get_max_span(patdef_array)  -- TODO: variably size the other layers instead of using the max
    );
  port(
    clock      : in  std_logic;         -- MUST BE 320MHZ
    clock40    : in  std_logic;         -- FIXME: have an optional output latch
                                        -- at 40MHz and an optional input dav extraction
    thresh     : in  std_logic_vector (2 downto 0);
    dav_i      : in  std_logic;
    dav_o      : out std_logic;
    sbits_i    : in  chamber_t;
    segments_o : out segment_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber;

architecture behavioral of chamber is

  --------------------------------------------------------------------------------
  -- Constants
  --------------------------------------------------------------------------------

  -- Number of segments output from each partition, e.g. 24
  constant NUM_SEGS_PER_PRT : natural := PRT_WIDTH/S0_WIDTH;

  -- number of di-partition segment selectors in the firmware
  -- at the most basic level, it is 1 for each 2 partitions
  -- but we can have a time-multiplexing re-use factor that reduces it further
  --
  -- include a +1 offset so the 15 case divides to 8, while 8 divides to 4
  --
  -- | N_PRT | S1_REUSE | N_SELECTORS |
  -- |-------+----------+-------------|
  -- |     8 |        1 |           4 |
  -- |     8 |        2 |           2 |
  -- |     8 |        4 |           1 |
  -- |    15 |        1 |           8 |
  -- |    15 |        2 |           4 |
  -- |    15 |        4 |           2 |
  --
  constant NUM_SELECTORS_S0 : natural := ((NUM_PARTITIONS+1)/2) / S1_REUSE;

  constant NUM_SEGMENT_SELECTOR_INPUTS : natural := (NUM_PARTITIONS+1)/S1_REUSE*NUM_SEGMENTS*2;

  --------------------------------------------------------------------------------
  -- Segments
  --------------------------------------------------------------------------------

  type segs_t is array
    (integer range 0 to NUM_PARTITIONS-1) of
    segment_list_t (NUM_SEGS_PER_PRT-1 downto 0);

  type segs_s1_demux_t is array
    (integer range 0 to NUM_PARTITIONS/2-1) of
    segment_list_t (NUM_SEGMENTS-1 downto 0);

  signal segs_s1_flat : segment_list_t
    ((NUM_PARTITIONS+1)/2*NUM_SEGMENTS-1 downto 0);

  signal all_segs      : segs_t;
  signal segs_s1_demux : segs_s1_demux_t;

  --------------------------------------------------------------------------------
  -- Data valids
  --------------------------------------------------------------------------------

  signal segs_dav   : std_logic_vector (NUM_PARTITIONS-1 downto 0);
  signal muxout_dav : std_logic := '0';
  signal muxin_phase, muxout_phase : natural range 0 to S1_REUSE-1;

begin

  assert
    (NUM_PARTITIONS = 8 and S1_REUSE = 1 and NUM_SELECTORS_S0 = 4) or
    (NUM_PARTITIONS = 8 and S1_REUSE = 2 and NUM_SELECTORS_S0 = 2) or
    (NUM_PARTITIONS = 8 and S1_REUSE = 4 and NUM_SELECTORS_S0 = 1) or
    (NUM_PARTITIONS = 15 and S1_REUSE = 1 and NUM_SELECTORS_S0 = 8) or
    (NUM_PARTITIONS = 15 and S1_REUSE = 2 and NUM_SELECTORS_S0 = 4) or
    (NUM_PARTITIONS = 15 and S1_REUSE = 4 and NUM_SELECTORS_S0 = 2)
    report "Error in NUM_SELECTORS_S0 calculation" severity error;

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
    signal partition_or : partition_t;
  begin

    single_partitions : if (NUM_PARTITIONS <= 8) generate
      partition_or <= sbits_i(I);
    end generate;

    half_partitions : if (NUM_PARTITIONS > 8) generate

      even_gen : if (I mod 2 = 0) generate
        partition_or <= sbits_i(I/2);
      end generate;

      -- look for only straight and pointing segments
      -- (for cms)
      pointing : if (not EN_NON_POINTING) generate
        odd_gen : if (I mod 2 = 1) generate
          partition_or(5) <= sbits_i((I-1)/2)(5);
          partition_or(4) <= sbits_i((I-1)/2)(4);
          partition_or(3) <= sbits_i((I-1)/2)(3);
          gt_1to15 : if (I > 1) generate
            partition_or(2) <= sbits_i((I-1)/2)(2) or sbits_i((I-1)/2-1)(2);
            partition_or(1) <= sbits_i((I-1)/2)(1) or sbits_i((I-1)/2-1)(1);
            partition_or(0) <= sbits_i((I-1)/2)(0) or sbits_i((I-1)/2-1)(0);
          end generate;
          gt0 : if (I = 1) generate
            partition_or(2) <= sbits_i((I-1)/2)(2);
            partition_or(1) <= sbits_i((I-1)/2)(1);
            partition_or(0) <= sbits_i((I-1)/2)(0);
          end generate;
        end generate;
      end generate;

      -- look for both x-partition segments toward the IP and away
      -- (for cosmic test stand)
      non_pointing : if (EN_NON_POINTING) generate
      begin
        partition_or(5) <= sbits_i((I-1)/2)(5);
        partition_or(4) <= sbits_i((I-1)/2)(4);
        partition_or(3) <= sbits_i((I-1)/2)(3);
        partition_or(2) <= sbits_i((I-1)/2)(2) or sbits_i((I-1)/2-1)(2) or sbits_i((I-1)/2+1)(2);
        partition_or(1) <= sbits_i((I-1)/2)(1) or sbits_i((I-1)/2-1)(1) or sbits_i((I-1)/2+1)(1);
        partition_or(0) <= sbits_i((I-1)/2)(0) or sbits_i((I-1)/2-1)(0) or sbits_i((I-1)/2+1)(0);
      end generate;

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

        thresh => thresh,

        -- primary layer
        partition_i => partition_or,

        -- output patterns
        dav_o      => segs_dav(I),
        segments_o => all_segs(I)

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

  dav_o <= dav_i;

  dav_to_phase_muxin_inst : entity work.dav_to_phase
    generic map (MAX => 8, DIV => 8/S1_REUSE)
    port map (clock  => clock, dav => segs_dav(0), phase_o => muxin_phase);

  dav_to_phase_muxout_inst : entity work.dav_to_phase
    generic map (MAX => 8, DIV => 8/S1_REUSE)
    port map (clock  => clock, dav => muxout_dav, phase_o => muxout_phase);  -- FIXME: this input is wrong

  dav_delay : entity work.fixed_delay_sf
    generic map (
      DELAY => SELECTOR_LATENCY,
      WIDTH => 1
      )
    port map (
      clock     => clock,
      data_i(0) => segs_dav(0),
      data_o(0) => muxout_dav
      );

  --------------------------------------------------------------------------------
  -- MUX
  --
  -- concat together two partitions worth of data and choose
  -- the best N out of N*2 segments
  --------------------------------------------------------------------------------

  sort_gen_s1 : for I in 0 to NUM_SELECTORS_S0 - 1 generate
    signal all_segs_muxin  : segment_list_t (2*NUM_SEGS_PER_PRT-1 downto 0);
    signal all_segs_muxout : segment_list_t (NUM_SEGMENTS-1 downto 0);
  begin

    i_lt_7 : if (I < 7) generate
    begin
      process (clock) is
      begin
        if (rising_edge(clock)) then
          all_segs_muxin <= all_segs ((S1_REUSE*I+muxin_phase)*2+1) &
                            all_segs ((S1_REUSE*I+muxin_phase)*2);
        end if;
      end process;
    end generate;

    i_eq_7 : if (I = 7) generate
      signal nullsegs : segment_list_t(NUM_SEGS_PER_PRT-1 downto 0);
    begin

      nullsegs <= zero(nullsegs);

      process (clock) is
      begin
        if (rising_edge(clock)) then
          all_segs_muxin <= nullsegs & all_segs ((S1_REUSE*I+muxin_phase)*2);
        end if;
      end process;
    end generate;

    --------------------------------------------------------------------------------
    -- Sort from (X segments / partition) to (NUM_SEGMENTS / two partitions)
    --------------------------------------------------------------------------------

    segment_selector_neighbor : entity work.segment_selector

      generic map (
        MODE        => "BITONIC",
        NUM_INPUTS  => NUM_SEGS_PER_PRT*2,  -- put in two partitions worth...
        NUM_OUTPUTS => NUM_SEGMENTS,        -- put out half that number
        SORTB       => PATTERN_SORTB
        )

      port map (
        -- take partition I and partition I+1 and choose the best patterns
        clock  => clock,
        segs_i => all_segs_muxin,
        segs_o => all_segs_muxout);

    PH : for SEL in 0 to S1_REUSE-1 generate  -- number of phases
    begin
      process (clock) is
      begin
        if (rising_edge(clock)) then
          if (muxout_phase = SEL) then
            segs_s1_demux (I*S1_REUSE+SEL) <= all_segs_muxout;
          end if;
        end if;
      end process;
    end generate;

  end generate;

  --------------------------------------------------------------------------------
  -- Final candidate sorting
  --
  -- sort from (NUM_PARTITIONS/2)*NUM_SEGMENTS patterns down to NUM_SEGMENTS
  --------------------------------------------------------------------------------

  -- TODO?: replace with priority encoder... ? the # of outputs is very small...

  single_partitions_flatten : if (NUM_PARTITIONS <= 8) generate
    segs_s1_flat <= segs_s1_demux(3) & segs_s1_demux(2) & segs_s1_demux(1) & segs_s1_demux(0);
  end generate;

  half_partitions_flatten : if (NUM_PARTITIONS > 8) generate
    segs_s1_flat <= segs_s1_demux(7) & segs_s1_demux(6) & segs_s1_demux(5) & segs_s1_demux(4) &
                    segs_s1_demux(3) & segs_s1_demux(2) & segs_s1_demux(1) & segs_s1_demux(0);
  end generate;

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => NUM_SEGMENT_SELECTOR_INPUTS,
      SORTB       => PATTERN_SORTB
      )
    port map (
      clock  => clock,
      segs_i => segs_s1_flat,
      segs_o => segments_o
      );

end behavioral;
