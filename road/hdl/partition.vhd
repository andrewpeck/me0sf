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

    NUM_SEGMENTS  : integer := 4;
    PARTITION_NUM : integer := 0;  -- just assign a number (e.g. 0-7) to each partition so we can look it up later
    PRT_WIDTH     : natural := PRT_WIDTH;  -- width of the partition (192)
    S0_WIDTH      : natural := 8;       -- width of the pre-sorting regions

    PATLIST : patdef_array_t := patdef_array;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY2_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY3_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY4_SPAN : natural := get_max_span(patdef_array);  -- TODO: variably size the other layers instead of using the max
    LY5_SPAN : natural := get_max_span(patdef_array)  -- TODO: variably size the other layers instead of using the max
    );
  port(

    --------------------------------------------------------------------------------
    -- Control
    --------------------------------------------------------------------------------

    clock : in  std_logic;
    dav_i : in  std_logic;
    dav_o : out std_logic := '0';

    thresh : in std_logic_vector (2 downto 0);

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

  signal strips     : segment_list_t (PRT_WIDTH-1 downto 0);
  signal strips_dav : std_logic := '0';
  signal strips_s0  : segment_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);

  signal dav_priority : std_logic_vector (PRT_WIDTH/S0_WIDTH-1 downto 0) := (others => '0');

begin

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
      MUX_FACTOR    => PAT_UNIT_MUX,
      PARTITION_NUM => PARTITION_NUM
      )
    port map (
      clock => clock,

      thresh => thresh,

      dav_i => dav_i,
      ly0   => partition_i(0),
      ly1   => partition_i(1),
      ly2   => partition_i(2),
      ly3   => partition_i(3),
      ly4   => partition_i(4),
      ly5   => partition_i(5),

      dav_o      => strips_dav,
      segments_o => strips
      );

  -------------------------------------------------------------------------------
  -- Pre-filter the patterns to limit to 1 segment in every N strips using a
  -- priority encoded sorting tree...
  --
  -- FIXME: this will make ghosts at the sorting boundaries... need to add in
  -- some ghost cancellation (also need to cancel ghosts in time)
  --
  -- 0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
  -- └───┴─┬─┴───┘   └───┴─┬─┴───┘   └───┴─┬─┴───┘   └───┴─┬─┴───┘
  --       └───────┬───────┘               └───────┬───────┘
  --              OUT                             OUT
  -------------------------------------------------------------------------------

  s0_gen : for region in 0 to PRT_WIDTH/S0_WIDTH-1 generate
    signal best     : std_logic_vector (segment_t'w - 1 downto 0);
    signal cand_slv : bus_array (0 to S0_WIDTH-1) (segment_t'w - 1 downto 0);
  begin

    cand_to_slv : for I in 0 to S0_WIDTH-1 generate
    begin
      cand_slv(I) <= convert(strips(REGION*S0_WIDTH+I), cand_slv(I));
    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        DAT_BITS   => best'length,
        QLT_BITS   => PATTERN_SORTB,
        WIDTH      => S0_WIDTH,
        REG_INPUT  => true,
        REG_OUTPUT => true,
        REG_STAGES => 3
        )
      port map (
        clock => clock,
        dav_i => strips_dav,
        dav_o => dav_priority(region),
        dat_i => cand_slv,
        dat_o => best,
        adr_o => open
        );

    strips_s0(region) <= convert(best, strips_s0(region));

  end generate;

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  segments_o <= strips_s0;
  dav_o      <= dav_priority(0);

end behavioral;
