----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity partition is
  generic(

    LATENCY : integer := PARTITION_LATENCY;

    NUM_SEGMENTS   : integer := 4;
    PARTITION_NUM  : integer := 0;          -- just assign a number (e.g. 0-7) to each partition so we can look it up later
    PRT_WIDTH      : natural := PRT_WIDTH;  -- width of the partition (192)
    S0_WIDTH       : natural := 8;          -- width of the pre-sorting regions
    PAT_UNIT_REUSE : natural := 8;          --


    DEGHOST_PRE  : boolean := true;      -- perform intra-partition ghost cancellation BEFORE sorting
    DEGHOST_POST : boolean := false;     -- perform intra-partition ghost cancellation AFTER sorting

    PATLIST : patdef_array_t := patdef_array;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY2_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY3_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY4_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY5_SPAN : natural := get_max_span(patdef_array)   -- TODO: variably size the other layers instead of using the max
    );
  port(

    --------------------------------------------------------------------------------
    -- Control
    --------------------------------------------------------------------------------

    clock : in  std_logic;

    dav_i : in  std_logic;
    dav_o : out std_logic := '0';

    -- synthesis translate_off
    dav_i_phase : out natural range 0 to 7 := 0;
    dav_o_phase : out natural range 0 to 7 := 0;
    -- synthesis translate_on

    ly_thresh  : in std_logic_vector (2 downto 0);
    hit_thresh : in std_logic_vector (5 downto 0);

    --------------------------------------------------------------------------------
    -- Inputs
    --------------------------------------------------------------------------------

    partition_i : in partition_t;

    --------------------------------------------------------------------------------
    -- outputs
    --------------------------------------------------------------------------------

    segments_o : out segment_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0)

    );
end partition;

architecture behavioral of partition is

  signal segments             : segment_list_t (PRT_WIDTH-1 downto 0);
  signal segments_deghost     : segment_list_t (PRT_WIDTH-1 downto 0);
  signal segments_dav         : std_logic := '0';
  signal segments_dav_deghost : std_logic := '0';
  signal segments_s0          : segment_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);

  signal dav_priority : std_logic_vector (PRT_WIDTH/S0_WIDTH-1 downto 0) := (others => '0');

begin

  --------------------------------------------------------------------------------
  -- DAV Monitor (for sim)
  --------------------------------------------------------------------------------

  -- synthesis translate_off
  dav_to_phase_i_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_i, phase_o => dav_i_phase);
  dav_to_phase_o_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_o, phase_o => dav_o_phase);
  -- synthesis translate_on

  --------------------------------------------------------------------------------
  -- Pattern Unit Mux
  --
  -- Find 0 or 1 patterns per strip.
  --
  -- To reduce resources, a mux is wrapped around the pattern unit. Each pattern
  -- can be reused N times per clock cycle
  --------------------------------------------------------------------------------

  pat_unit_mux_inst : entity work.pat_unit_mux
    generic map (
      WIDTH         => PRT_WIDTH,
      MUX_FACTOR    => PAT_UNIT_REUSE,
      PARTITION_NUM => PARTITION_NUM
      )
    port map (
      clock => clock,

      ly_thresh  => ly_thresh,
      hit_thresh => hit_thresh,

      dav_i => dav_i,
      ly0   => partition_i(0),
      ly1   => partition_i(1),
      ly2   => partition_i(2),
      ly3   => partition_i(3),
      ly4   => partition_i(4),
      ly5   => partition_i(5),

      dav_o      => segments_dav,
      segments_o => segments
      );

  --------------------------------------------------------------------------------
  -- Deghost
  --------------------------------------------------------------------------------

  pre_filter_deghost_gen : if (DEGHOST_PRE) generate
    deghost_pre : entity work.deghost
      generic map (
        WIDTH       => segments'length,
        EDGE_DIST   => 2,
        GROUP_WIDTH => S0_WIDTH
        )
      port map (
        clock      => clock,
        dav_i      => segments_dav,
        dav_o      => segments_dav_deghost,
        segments_i => segments,
        segments_o => segments_deghost
        );
  end generate;

  not_pre_filter_deghost_gen : if (not DEGHOST_PRE) generate
    segments_dav_deghost <= segments_dav;
    segments_deghost     <= segments;
  end generate;

  -------------------------------------------------------------------------------
  -- Pre-filter the patterns to limit to 1 segment in every N strips using a
  -- priority encoded sorting tree...
  --
  -- this will make ghosts at the sorting boundaries... need to add in
  -- some ghost cancellation (also need to cancel ghosts in time)
  --
  -- 0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
  -- └───┴─┬─┴───┘   └───┴─┬─┴───┘   └───┴─┬─┴───┘   └───┴─┬─┴───┘
  --       └───────┬───────┘               └───────┬───────┘
  --              OUT                             OUT
  --
  -- TODO: this can probably be time-multiplexed?
  --
  -------------------------------------------------------------------------------

  s0_gen : for region in 0 to PRT_WIDTH/S0_WIDTH-1 generate
    signal best     : std_logic_vector (segment_t'w - 1 downto 0);
    signal cand_slv : bus_array (0 to S0_WIDTH-1) (segment_t'w - 1 downto 0);
  begin

    cand_to_slv : for I in 0 to S0_WIDTH-1 generate
    begin
      cand_slv(I) <= convert(segments_deghost(REGION*S0_WIDTH+I), cand_slv(I));
    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        DAT_BITS    => best'length,
        QLT_BITS    => PATTERN_SORTB,
        IGNORE_BITS => PARTITION_BITS,  -- everything is the same partition here, ignore them
        WIDTH       => S0_WIDTH,
        REG_INPUT   => true,
        REG_OUTPUT  => true,
        REG_STAGES  => 3
        )
      port map (
        clock => clock,
        dav_i => segments_dav_deghost,
        dav_o => dav_priority(region),
        dat_i => cand_slv,
        dat_o => best,
        adr_o => open
        );

    segments_s0(region) <= convert(best, segments_s0(region));

  end generate;

  --------------------------------------------------------------------------------
  -- Post Filter De-ghosting
  --
  -- should use this OR the pre-filter deghosting, not both
  -- pre-filter deghosting is more expensive but more effective
  -- the improvement and cost should be quantified
  --------------------------------------------------------------------------------

  post_filter_deghost_gen : if (DEGHOST_POST) generate
    deghost_post : entity work.deghost
      generic map (
        WIDTH        => segments_o'length,
        CHECK_STRIPS => true)
      port map (
        clock      => clock,
        dav_i      => dav_priority(0),
        dav_o      => dav_o,
        segments_i => segments_s0,
        segments_o => segments_o
        );
  end generate;

  not_post_filter_deghost_gen : if (not DEGHOST_POST) generate
    segments_o <= segments_s0;
    dav_o      <= dav_priority(0);
  end generate;

end behavioral;
