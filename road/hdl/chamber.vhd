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

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity chamber is
  generic (
    DISABLE_PEAKING : boolean := false;  -- true to disable peaking logic; useful for simulation until the tb is updated
    X_PRT_EN        : boolean := true;   -- true to enable x-prt segment finding
    EN_NON_POINTING : boolean := false;  -- true to enable x-prt segment finding on non-pointing muons
    NUM_SEGMENTS    : integer := 4;      -- number of output segments
    S0_WIDTH        : natural := 16;     -- chunk each partition into groups this size and choose only 1 segment from each group
    S1_REUSE        : natural := 4;      -- reuse sorters
    REG_OUTPUTS     : boolean := false;  -- true to  register outputs on the 40MHz clock
    PULSE_EXTEND    : integer := 2;      -- how long pulses should be extended by
    DEADTIME        : natural := 3;      -- deadtime in bx

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

    dav_i             : in  std_logic;
    dav_o             : out std_logic;
    -- synthesis translate_off
    dav_i_phase       : out natural range 0 to 7;
    dav_o_phase       : out natural range 0 to 7;
    -- synthesis translate_on

    sbits_i           : in  chamber_t;
    vfat_pretrigger_o : out std_logic_vector (23 downto 0);
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

  -- use a CEIL here so that 15/2 -> 8 instead of 7..
  -- otherwise the highest partition is dropped
  constant NUM_FINDERS_DIV2 : integer := integer(ceil(real(NUM_FINDERS)/2.0));

  --------------------------------------------------------------------------------
  -- Extension
  --------------------------------------------------------------------------------

  signal sbits_extend : chamber_t;
  signal dav_extend   : std_logic := '0';

  --------------------------------------------------------------------------------
  -- Segments
  --------------------------------------------------------------------------------

  signal all_segs            : segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0)    := (others => null_pattern);  -- get all segments from each partition
  signal two_prt_sorted_segs : segment_list_t (NUM_FINDERS_DIV2 * NUM_SEGMENTS - 1 downto 0)   := (others => null_pattern);  -- sort down to number of output segments for each 2 partitions
  signal one_prt_sorted_segs : segment_list_t (NUM_FINDERS_DIV2*2 * NUM_SEGMENTS - 1 downto 0) := (others => null_pattern);  -- sort down to the number of output segments for each partition
  signal final_segs          : segment_list_t (NUM_SEGMENTS - 1 downto 0)                      := (others => null_pattern);

  --------------------------------------------------------------------------------
  -- Pretriggers
  --------------------------------------------------------------------------------

  type strip_triggers_array_t is array (NUM_FINDERS-1 downto 0) of
    std_logic_vector(PRT_WIDTH-1 downto 0);

  type partition_pretrigger_t is array (integer range <>) of
    std_logic_vector(2 downto 0);

  signal strip_triggers       : strip_triggers_array_t;
  signal vfat_pretrigger_xprt : vfat_pretrigger_t(NUM_FINDERS-1 downto 0);
  signal vfat_pretrigger      : vfat_pretrigger_t(7 downto 0);

  --------------------------------------------------------------------------------
  -- Data valids
  --------------------------------------------------------------------------------

  signal all_segs_dav : std_logic_vector (NUM_FINDERS - 1 downto 0) := (others => '0');

  signal one_prt_sorted_dav : std_logic_vector (NUM_FINDERS-1 downto 0)      := (others => '0');
  signal two_prt_sorted_dav : std_logic_vector (NUM_FINDERS_DIV2-1 downto 0) := (others => '0');
  signal final_segs_dav     : std_logic;

  signal outclk : std_logic := '0';

begin

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
  -- Pulse Extension
  --------------------------------------------------------------------------------

  chamber_pulse_extension_inst : entity work.chamber_pulse_extension
    generic map (LENGTH => PULSE_EXTEND)
    port map (
      clock   => clock40,
      sbits_i => sbits_i,
      sbits_o => sbits_extend);

  dav_extend <= dav_i;

  --------------------------------------------------------------------------------
  -- Input signal assignment
  --------------------------------------------------------------------------------

  partition_gen : for I in 0 to NUM_FINDERS-1 generate
    signal partition_or     : partition_t;
    signal partition_or_reg : partition_t;
    signal dav_or           : std_logic := '0';
  begin

    single_partitions : if (NUM_FINDERS <= 8) generate
      partition_or <= sbits_extend(I);
    end generate;

    half_partitions : if (NUM_FINDERS > 8) generate

      -- for even finders, just take the partition as it is
      even_gen : if (I mod 2 = 0) generate
        partition_or <= sbits_extend(I/2);
      end generate;

      -- for odd finders, or adjacent partitions
      odd_gen : if (I mod 2 = 1) generate

        -- look for only straight and pointing segments (for cms)
        pointing : if (not EN_NON_POINTING) generate
          partition_or(0) <=                         sbits_extend(I/2 + 1)(0);
          partition_or(1) <=                         sbits_extend(I/2 + 1)(1);
          partition_or(2) <= sbits_extend(I/2)(2) or sbits_extend(I/2 + 1)(2);
          partition_or(3) <= sbits_extend(I/2)(3) or sbits_extend(I/2 + 1)(3);
          partition_or(4) <= sbits_extend(I/2)(4);
          partition_or(5) <= sbits_extend(I/2)(5);
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
        dav_or           <= dav_extend;
        partition_or_reg <= partition_or;
      end if;
    end process;

    --------------------------------------------------------------------------------
    -- Per Partition Pattern Finders
    --------------------------------------------------------------------------------

    partition_inst : entity work.partition
      generic map (
        DISABLE_PEAKING => DISABLE_PEAKING,
        NUM_SEGMENTS    => NUM_SEGMENTS,
        S0_WIDTH        => S0_WIDTH,
        DEADTIME        => DEADTIME
        )
      port map (

        clock => clock,
        dav_i => dav_or,

        partition_num => I,

        ly_thresh  => ly_thresh,

        -- primary layer
        partition_i => partition_or_reg,

        -- output patterns
        dav_o      => all_segs_dav(I),
        segments_o => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT),
        trigger_o  => strip_triggers(I)
        );

  end generate;

  --------------------------------------------------------------------------------
  -- Pretrigger
  --------------------------------------------------------------------------------

  pretrig_gen : for iprt in 0 to NUM_PARTITIONS-1 generate

    constant ifinder : integer := if_then_else (X_PRT_EN, iprt*2, iprt);

    signal active_m1 : std_logic_vector (2 downto 0) := (others => '0');
    signal active_p1 : std_logic_vector (2 downto 0) := (others => '0');

  begin

    -- do a reduce_or to get 1 bit per vfat for both the real and cross
    -- partitions
    process (clock) is
    begin
      if (rising_edge(clock)) then
        for ivfat in 0 to 2 loop
          vfat_pretrigger_xprt(iprt)(ivfat) <=
            or_reduce(strip_triggers(iprt)((ivfat+1) * 64 - 1 downto 64*ivfat));
        end loop;
      end if;
    end process;

    -- get the negative and positive active flags
    --
    m_1 : if (X_PRT_EN and ifinder > 0) generate
      active_m1 <= vfat_pretrigger_xprt(iprt-1);
    end generate;

    p_1 : if (X_PRT_EN and ifinder < NUM_FINDERS-1 ) generate
      active_p1 <= vfat_pretrigger_xprt(iprt+1);
    end generate;


        -- -- or together the real and virtual partitions to get an active VFAT flag
    vfat_pretrigger(iprt) <= active_m1 or active_p1 or
                                  vfat_pretrigger_xprt(iprt+1);

  end generate;

  process (clock) is
  begin
    if (rising_edge(clock)) then

      vfat_pretrigger_o(0) <= vfat_pretrigger(0)(0);
      vfat_pretrigger_o(1) <= vfat_pretrigger(1)(0);
      vfat_pretrigger_o(2) <= vfat_pretrigger(2)(0);
      vfat_pretrigger_o(3) <= vfat_pretrigger(3)(0);
      vfat_pretrigger_o(4) <= vfat_pretrigger(4)(0);
      vfat_pretrigger_o(5) <= vfat_pretrigger(5)(0);
      vfat_pretrigger_o(6) <= vfat_pretrigger(6)(0);
      vfat_pretrigger_o(7) <= vfat_pretrigger(7)(0);

      vfat_pretrigger_o(8)  <= vfat_pretrigger(0)(1);
      vfat_pretrigger_o(9)  <= vfat_pretrigger(1)(1);
      vfat_pretrigger_o(10) <= vfat_pretrigger(2)(1);
      vfat_pretrigger_o(11) <= vfat_pretrigger(3)(1);
      vfat_pretrigger_o(12) <= vfat_pretrigger(4)(1);
      vfat_pretrigger_o(13) <= vfat_pretrigger(5)(1);
      vfat_pretrigger_o(14) <= vfat_pretrigger(6)(1);
      vfat_pretrigger_o(15) <= vfat_pretrigger(7)(1);

      vfat_pretrigger_o(16) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(17) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(18) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(19) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(20) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(21) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(22) <= vfat_pretrigger(7)(3);
      vfat_pretrigger_o(23) <= vfat_pretrigger(7)(3);

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
        SORTB       => segment_t'w,
        IGNOREB     => PARTITION_BITS   -- can ignore prt since this is intra-partition
        )
      port map (
        clock  => clock,
        dav_i  => all_segs_dav(I),
        dav_o  => one_prt_sorted_dav(I),
        segs_i => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT),
        segs_o => one_prt_sorted_segs((I+1)*NUM_SEGMENTS-1 downto I*NUM_SEGMENTS)
        );
  end generate;

  dipartition_sorter : for I in 0 to NUM_FINDERS_DIV2-1 generate
  begin
    segment_selector_inst : entity work.segment_selector
      generic map (
        MODE        => "BITONIC",
        NUM_INPUTS  => NUM_SEGMENTS*2,
        NUM_OUTPUTS => NUM_SEGMENTS,
        SORTB       => segment_t'w
        )
      port map (
        clock  => clock,
        dav_i  => one_prt_sorted_dav(I*2),
        dav_o  => two_prt_sorted_dav(I),
        segs_i => one_prt_sorted_segs((I+1)*2*NUM_SEGMENTS-1 downto I*2*NUM_SEGMENTS),
        segs_o => two_prt_sorted_segs((I+1)*NUM_SEGMENTS-1 downto I*NUM_SEGMENTS)
        );
  end generate;

  --------------------------------------------------------------------------------
  -- Final candidate sorting
  --
  -- sort from down to NUM_SEGMENTS
  --------------------------------------------------------------------------------

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => two_prt_sorted_segs'length,
      SORTB       => segment_t'w
      )
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
    end if;
  end process;


end behavioral;
