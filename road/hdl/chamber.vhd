----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--   Segment finding for a single ME0 chamber
--
-- Notes:
--
-- + Only apply threshold at the end.. there is no reason to have a choke point
-- anywhere in early in segment finding if we need to do a full sort anyway..
-- might as well just output the raw segments and for the final N outputs apply
-- the layer etc thresholds-- or rather, we can have two different thresholds:
--
--      pretrigger threshold would be applied at the segment creation level and
--      would determine whether a segment forms at all. This could be a lower
--      threshold which would be used for the pretrigger. the full trigger
--      threshold would be applied at the end and can be higher
--
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
    X_PRT_EN        : boolean := true;   -- true to enable x-prt segment finding
    EN_NON_POINTING : boolean := false;  -- true to enable x-prt segment finding on non-pointing muons
    NUM_SEGMENTS    : integer := 4;      -- number of output segments
    S0_WIDTH        : natural := 16;     -- chunk each partition into groups this size and choose only 1 segment from each group
    S1_REUSE        : natural := 4;      -- reuse sorters
    REG_OUTPUTS     : boolean := false;  -- true to  register outputs on the 40MHz clock

    PATLIST : patdef_array_t := patdef_array;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY2_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY3_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY4_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY5_SPAN : natural := get_max_span(patdef_array)   -- TODO: variably size the other layers instead of using the max
    );
  port(
    clock             : in  std_logic;                     -- MUST BE 320MHZ
    clock40           : in  std_logic;                     -- MUST BE  40MHZ

    ly_thresh         : in  std_logic_vector (2 downto 0); -- Layer threshold, 0 to 6
    hit_thresh        : in  std_logic_vector (5 downto 0); -- Hit threshold

    dav_i             : in  std_logic;
    dav_o             : out std_logic;
    -- synthesis translate_off
    dav_i_phase       : out natural range 0 to 7;
    dav_o_phase       : out natural range 0 to 7;
    -- synthesis translate_on

    sbits_i           : in  chamber_t;
    vfat_pretrigger_o : out std_logic_vector (23 downto 0);
    pretrigger_o      : out std_logic;
    segments_o        : out segment_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber;

architecture behavioral of chamber is

  --------------------------------------------------------------------------------
  -- Constants
  --------------------------------------------------------------------------------

  constant NUM_PARTITIONS : integer := 8;

  -- Number of segments output from each partition, e.g. 24
  constant NUM_SEGS_PER_PRT : natural := PRT_WIDTH/S0_WIDTH;

  -- number of di-partition segment selectors in the firmware
  -- at the most basic level, it is 1 for each 2 partitions
  -- but we can have a time-multiplexing re-use factor that reduces it further
  --
  -- include a +1 offset so the 15 case divides to 8, while 8 divides to 4
  --
  -- | X_PRT | S1_REUSE | N_SELECTORS |
  -- |-------+----------+-------------|
  -- |     f |        1 |           4 |
  -- |     f |        2 |           2 |
  -- |     f |        4 |           1 |
  -- |     t |        1 |           8 |
  -- |     t |        2 |           4 |
  -- |     t |        4 |           2 |

  constant NUM_FINDERS : integer := if_then_else (X_PRT_EN, 15, 8);

  constant NUM_SELECTORS_S0 : natural := ((NUM_FINDERS+1)/2) / S1_REUSE;
  constant NUM_SEGMENT_SELECTOR_INPUTS : natural := (NUM_FINDERS+1)/S1_REUSE*NUM_SEGMENTS*2;

  --------------------------------------------------------------------------------
  -- Segments
  --------------------------------------------------------------------------------

  signal segs_to_selector : segment_list_t
    ((NUM_PARTITIONS+1)/2*NUM_SEGMENTS-1 downto 0);

  signal all_segs            : segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0);
  signal one_prt_sorted_segs : segment_list_t (NUM_FINDERS * NUM_SEGMENTS - 1 downto 0);
  signal two_prt_sorted_segs : segment_list_t (NUM_FINDERS * NUM_SEGMENTS/2 - 1 downto 0);
  signal final_segs          : segment_list_t (NUM_SEGMENTS - 1 downto 0);

  signal vfat_pretrigger : std_logic_vector (3*NUM_PARTITIONS-1 downto 0);

  --------------------------------------------------------------------------------
  -- Data valids
  --------------------------------------------------------------------------------

  signal all_segs_dav : std_logic_vector (NUM_FINDERS - 1 downto 0) := (others => '0');

  signal one_prt_sorted_dav : std_logic_vector (NUM_FINDERS-1 downto 0)   := (others => '0');
  signal two_prt_sorted_dav : std_logic_vector (NUM_FINDERS/2-1 downto 0) := (others => '0');
  signal final_segs_dav     : std_logic;

  signal muxout_dav : std_logic := '0';

  signal outclk : std_logic := '0';

begin

  assert
    (X_PRT_EN = false and S1_REUSE = 1 and NUM_SELECTORS_S0 = 4) or
    (X_PRT_EN = false and S1_REUSE = 2 and NUM_SELECTORS_S0 = 2) or
    (X_PRT_EN = false and S1_REUSE = 4 and NUM_SELECTORS_S0 = 1) or
    (X_PRT_EN = true  and S1_REUSE = 1 and NUM_SELECTORS_S0 = 8) or
    (X_PRT_EN = true  and S1_REUSE = 2 and NUM_SELECTORS_S0 = 4) or
    (X_PRT_EN = true  and S1_REUSE = 4 and NUM_SELECTORS_S0 = 2)
    report "Error in NUM_SELECTORS_S0 calculation" severity error;

  assert S1_REUSE = 1 or S1_REUSE = 2 or S1_REUSE = 4
    report "Only allowed values for s1 reuse are 1,2, and 4"
    severity error;

  -- synthesis translate_off
  dav_to_phase_i_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_i, phase_o => dav_i_phase);
  dav_to_phase_o_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_o, phase_o => dav_o_phase);
  -- synthesis translate_on

  --------------------------------------------------------------------------------
  -- Input signal assignment
  --------------------------------------------------------------------------------

  partition_gen : for I in 0 to NUM_FINDERS-1 generate
    signal partition_or     : partition_t;
    signal partition_or_reg : partition_t;
    signal dav_or           : std_logic := '0';
  begin

    single_partitions : if (NUM_FINDERS <= 8) generate
      partition_or <= sbits_i(I);
    end generate;

    half_partitions : if (NUM_FINDERS > 8) generate

      -- for even finders, just take the partition as it is
      even_gen : if (I mod 2 = 0) generate
        partition_or <= sbits_i(I/2);
      end generate;

      -- for odd finders, or adjacent partitions
      odd_gen : if (I mod 2 = 1) generate

        -- look for only straight and pointing segments (for cms)
        pointing : if (not EN_NON_POINTING) generate
          partition_or(0) <=                        sbits_i(I/2)(0);
          partition_or(1) <=                        sbits_i(I/2)(1);
          partition_or(2) <= sbits_i(I/2 + 1)(2) or sbits_i(I/2)(2);
          partition_or(3) <= sbits_i(I/2 + 1)(3) or sbits_i(I/2)(3);
          partition_or(4) <= sbits_i(I/2 + 1)(4);
          partition_or(5) <= sbits_i(I/2 + 1)(5);
        end generate;

        -- look for both x-partition segments toward the IP and away
        -- (for cosmic test stand)
        non_pointing : if (EN_NON_POINTING) generate
        begin
          assert false report "NON_POINTING not supported yet" severity error;
        end generate;

      end generate;

    end generate;

    process (clock) is
    begin
      if (rising_edge(clock)) then
        dav_or           <= dav_i;
        partition_or_reg <= partition_or;
      end if;
    end process;

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
        dav_i => dav_or,

        ly_thresh  => ly_thresh,
        hit_thresh => hit_thresh,

        -- primary layer
        partition_i => partition_or_reg,

        -- output patterns
        dav_o      => all_segs_dav(I),
        segments_o => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT)

        );

  end generate;

  --------------------------------------------------------------------------------
  -- Pretrigger
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then

      -- FIXME: this needs to work with X_PRT pattern finding
      for iprt in 0 to NUM_PARTITIONS-1 loop
        for ivfat in 0 to 2 loop

          vfat_pretrigger(iprt*3+ivfat) <= '0';

          for iseg in 0 to NUM_SEGS_PER_PRT/3-1 loop
            if (all_segs(iprt*NUM_SEGS_PER_PRT +
                         ivfat * NUM_SEGS_PER_PRT/3 +
                         iseg).lc /= 0) then
              vfat_pretrigger(iprt*3+ivfat) <= '1';
            end if;
          end loop;
        end loop;
      end loop;

    end if;
  end process;

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

  partition_sorter : for I in 0 to NUM_FINDERS-1 generate
  begin
    segment_selector_inst : entity work.segment_selector
      generic map (
        MODE        => "BITONIC",
        NUM_OUTPUTS => NUM_SEGMENTS,
        NUM_INPUTS  => NUM_SEGS_PER_PRT,
        SORTB       => PATTERN_SORTB,
        IGNOREB     => PARTITION_BITS)
      port map (
        clock  => clock,
        dav_i  => all_segs_dav(I),
        dav_o  => one_prt_sorted_dav(I),
        segs_i => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT),
        segs_o => one_prt_sorted_segs((I+1)*NUM_SEGMENTS-1 downto I*NUM_SEGMENTS)
        );
  end generate;

  dipartition_sorter : for I in 0 to NUM_FINDERS/2-1 generate
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

  clk40gen : if (REG_OUTPUTS) generate
    outclk <= clock40;
  end generate;
  clk320 : if (not REG_OUTPUTS) generate
    outclk <= clock;
  end generate;

  process (outclk) is
  begin
    if (rising_edge(outclk)) then
      dav_o             <= final_segs_dav;
      segments_o        <= final_segs;
      vfat_pretrigger_o <= vfat_pretrigger;
      pretrigger_o      <= or_reduce(vfat_pretrigger);
    end if;
  end process;


end behavioral;
