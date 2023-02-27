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

  signal segs_to_selector : segment_list_t
    ((NUM_PARTITIONS+1)/2*NUM_SEGMENTS-1 downto 0);

  signal all_segs            : segment_list_t (NUM_PARTITIONS * NUM_SEGS_PER_PRT - 1 downto 0);
  signal one_prt_sorted_segs : segment_list_t (NUM_PARTITIONS * NUM_SEGMENTS - 1 downto 0);
  signal two_prt_sorted_segs : segment_list_t (NUM_PARTITIONS * NUM_SEGMENTS/2 - 1 downto 0);
  signal final_segs          : segment_list_t (NUM_SEGMENTS - 1 downto 0);

  --------------------------------------------------------------------------------
  -- Data valids
  --------------------------------------------------------------------------------

  signal all_segs_dav : std_logic_vector (NUM_PARTITIONS - 1 downto 0) := (others => '0');

  signal one_prt_sorted_dav : std_logic_vector (NUM_PARTITIONS-1 downto 0)   := (others => '0');
  signal two_prt_sorted_dav : std_logic_vector (NUM_PARTITIONS/2-1 downto 0) := (others => '0');
  signal final_segs_dav     : std_logic;

  signal dav_sr : std_logic_vector(9 downto 0);

  signal muxout_dav : std_logic := '0';

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
  -- Input signal assignment
  --------------------------------------------------------------------------------

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

    --------------------------------------------------------------------------------
    -- Per Partition Pattern Finders
    --------------------------------------------------------------------------------

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
        dav_o      => all_segs_dav(I),
        segments_o => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT)

        );
  end generate;

  --------------------------------------------------------------------------------
  -- Partition Sorting
  --
  -- Reduce the # of segments / partition from e.g. 24 to NUM_SEGMENTS by doing
  -- a sort within the partition to choose the NUM_SEGMENTS best outputs
  --
  -- Then do a reduction by looking at neighboring partitions and reducing from
  -- NUM_SEGMENTS*2 -> NUM_SEGMENTS for each 2 partitions
  --
  -- after all this,
  --
  -- for a 16 partition chamber we would be reduced to
  -- 8*4 = 32 segments that go into the final sorter
  --
  -- for a 8 partition chamber we would be reduced to
  -- 4*4 = 16 segments that go into the final sorter
  --
  --------------------------------------------------------------------------------

  partition_sorter : for I in 0 to NUM_PARTITIONS-1 generate
  begin
    segment_selector_inst : entity work.segment_selector
      generic map (
        MODE        => "BITONIC",
        NUM_OUTPUTS => NUM_SEGMENTS,
        NUM_INPUTS  => NUM_SEGS_PER_PRT,
        SORTB       => PATTERN_SORTB)
      port map (
        clock  => clock,
        dav_i  => all_segs_dav(I),
        dav_o  => one_prt_sorted_dav(I),
        segs_i => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT),
        segs_o => one_prt_sorted_segs((I+1)*NUM_SEGMENTS-1 downto I*NUM_SEGMENTS)
        );
  end generate;

  dipartition_sorter : for I in 0 to NUM_PARTITIONS/2-1 generate
  begin
    segment_selector_inst : entity work.segment_selector
      generic map (
        MODE        => "BITONIC",
        NUM_INPUTS  => NUM_SEGMENTS*2,
        NUM_OUTPUTS => NUM_SEGMENTS,
        SORTB       => PATTERN_SORTB)
      port map (
        clock  => clock,
        dav_i  => one_prt_sorted_dav(I),
        dav_o  => two_prt_sorted_dav(I),
        segs_i => one_prt_sorted_segs((I+1)*2*NUM_SEGMENTS-1 downto I*2*NUM_SEGMENTS),
        segs_o => two_prt_sorted_segs((I+1)*NUM_SEGMENTS-1 downto I*NUM_SEGMENTS)
        );
  end generate;

  --------------------------------------------------------------------------------
  -- Final candidate sorting
  --
  -- sort from down to NUM_SEGMENTS
  --
  -- TODO?: replace with priority encoder... ? the # of outputs is very small...
  --------------------------------------------------------------------------------

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => two_prt_sorted_segs'length,
      SORTB       => PATTERN_SORTB)
    port map (
      clock  => clock,
      dav_i  => two_prt_sorted_dav(0),
      dav_o  => final_segs_dav,
      segs_i => two_prt_sorted_segs,
      segs_o => final_segs
      );

  --------------------------------------------------------------------------------
  -- Fitting
  --------------------------------------------------------------------------------

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      dav_o      <= final_segs_dav;
      segments_o <= final_segs;
    end if;
  end process;


end behavioral;
