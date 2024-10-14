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


    DISABLE_PEAKING : boolean := false;
    NUM_SEGMENTS   : integer := 4;
    PRT_WIDTH      : natural := PRT_WIDTH;  -- width of the partition (192)
    S0_WIDTH       : natural := 8;          -- width of the pre-sorting regions
    PAT_UNIT_REUSE : natural := 8;          --
    --DEADTIME       : natural := 3;          -- deadtime in bx
    EN_HC_COMPRESS : boolean := true;

    DEGHOST_PRE  : boolean := true;     -- perform intra-partition ghost cancellation BEFORE sorting
    DEGHOST_POST : boolean := false;    -- perform intra-partition ghost cancellation AFTER sorting

    PATLIST : patdef_array_t := patdef_array
    );
  port(

    --------------------------------------------------------------------------------
    -- Control
    --------------------------------------------------------------------------------

    clock : in std_logic;

    dav_i : in  std_logic;
    dav_o : out std_logic := '0';

    -- synthesis translate_off
    dav_i_phase : out natural range 0 to 7 := 0;
    dav_o_phase : out natural range 0 to 7 := 0;
    -- synthesis translate_on

    ly_thresh : in ly_thresh_t;

    --------------------------------------------------------------------------------
    -- Inputs
    --------------------------------------------------------------------------------

    partition_i : in partition_t;

    partition_num : integer range 0 to 15 := 0;  -- just assign a number (e.g. 0-7) to each partition so we can look it up later

    --------------------------------------------------------------------------------
    -- outputs
    --------------------------------------------------------------------------------

    segments_o : out segment_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);
    trigger_o  : out std_logic_vector (PRT_WIDTH-1 downto 0)

    );
end partition;

architecture behavioral of partition is

  -- ┌───────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
  -- │ Partition │ -> │ Deghost │ -> │ Priority │ -> │ Deghost  │
  -- │           │    │         │    │ Encoder  │    │          │
  -- └───────────┘    └─────────┘    └──────────┘    └──────────┘
  --    segments       segments        segments        segments
  --                    deghost        priority        postghost

  -- segments direct from the partition
  signal segments : pat_unit_mux_list_t (PRT_WIDTH-1 downto 0);

  -- /optionally/ deghosted segments
  signal segments_deghost : pat_unit_mux_list_t (PRT_WIDTH-1 downto 0);

  -- segments out from the priority encoder
  signal segments_priority : pat_unit_mux_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);

  -- segments from the post-encoder deghoster
  signal segments_postghost : pat_unit_mux_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);

  signal dav_segments         : std_logic                                        := '0';
  signal dav_segments_deghost : std_logic                                        := '0';
  signal dav_postghost        : std_logic                                        := '0';
  signal dav_priority         : std_logic_vector (PRT_WIDTH/S0_WIDTH-1 downto 0) := (others => '0');

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
      DISABLE_PEAKING => DISABLE_PEAKING,
      WIDTH           => PRT_WIDTH,
      MUX_FACTOR      => PAT_UNIT_REUSE,
      --DEADTIME        => DEADTIME
      EN_HC_COMPRESS => EN_HC_COMPRESS
      )
    port map (
      clock => clock,

      ly_thresh => ly_thresh,

      dav_i => dav_i,
      ly0   => partition_i(0),
      ly1   => partition_i(1),
      ly2   => partition_i(2),
      ly3   => partition_i(3),
      ly4   => partition_i(4),
      ly5   => partition_i(5),

      dav_o      => dav_segments,
      segments_o => segments,
      trigger_o  => trigger_o
      );

  --------------------------------------------------------------------------------
  -- Deghost
  --------------------------------------------------------------------------------

  pre_filter_deghost_gen : if (DEGHOST_PRE) generate
    deghost_pre_inst : entity work.deghost
      generic map (
        WIDTH       => segments'length,
        EDGE_DIST   => 2,
        GROUP_WIDTH => S0_WIDTH
        )
      port map (
        clock      => clock,
        dav_i      => dav_segments,
        dav_o      => dav_segments_deghost,
        segments_i => segments,
        segments_o => segments_deghost
        );
  end generate;

  not_pre_filter_deghost_gen : if (not DEGHOST_PRE) generate
    dav_segments_deghost <= dav_segments;
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
  -- TODO: consider making the regions wider and choosing the best 2 instead of 1?
  --
  -- the second one comes for free with some very minor mods to the priority encoder
  --
  -------------------------------------------------------------------------------

  s0_gen : for region in 0 to PRT_WIDTH/S0_WIDTH-1 generate
    signal best                 : std_logic_vector (pat_unit_mux_t'w - 1 downto 0);
    signal segments_deghost_slv : bus_array (0 to S0_WIDTH-1) (pat_unit_mux_t'w - 1 downto 0);
  begin

    cand_to_slv : for I in 0 to S0_WIDTH-1 generate
    begin
      segments_deghost_slv(I) <= convert(segments_deghost(REGION*S0_WIDTH+I), segments_deghost_slv(I));
    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        DAT_BITS    => best'length,
        QLT_BITS    => best'length,
        IGNORE_BITS => 0,
        WIDTH       => segments_deghost_slv'length,
        REG_INPUT   => true,
        REG_OUTPUT  => true,
        REG_STAGES  => 2
        )
      port map (
        clock => clock,

        -- in
        dav_i => dav_segments_deghost,
        dat_i => segments_deghost_slv,

        -- out
        dav_o => dav_priority(region),
        dat_o => best,
        adr_o => open
        );

    segments_priority(region) <= convert(best, segments_priority(region));

  end generate;

  --------------------------------------------------------------------------------
  -- Post Filter De-ghosting
  --
  -- should use this OR the pre-filter deghosting, not both
  -- pre-filter deghosting is more expensive but more effective
  -- the improvement and cost should be quantified
  --------------------------------------------------------------------------------

  post_filter_deghost_gen : if (DEGHOST_POST) generate
    deghost_post_inst : entity work.deghost
      generic map (
        WIDTH        => segments_priority'length,
        CHECK_STRIPS => true)
      port map (
        clock      => clock,
        dav_i      => dav_priority(0),
        dav_o      => dav_postghost,
        segments_i => segments_priority,
        segments_o => segments_postghost
        );
  end generate;

  not_post_filter_deghost_gen : if (not DEGHOST_POST) generate
    segments_postghost <= segments_priority;
    dav_postghost      <= dav_priority(0);
  end generate;

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      dav_o <= dav_postghost;

      for I in segments_o'range loop
        segments_o(I).lc        <= segments_postghost(I).lc;
        segments_o(I).id        <= segments_postghost(I).id;
        segments_o(I).strip     <= segments_postghost(I).strip;
        segments_o(I).partition <= to_unsigned(partition_num, 4);
      end loop;
      
      -- test function to print segments in partition, delete later
--     for I in segments_deghost'range loop
--       if (segments_deghost(I).id > 0) then
--         report "I am partition"&integer'image(partition_num)&". There is a segment centered at strip "&integer'image(to_integer(unsigned(segments_deghost(I).strip)));
--       end if;
--     end loop;

    end if;
  end process;

end behavioral;
