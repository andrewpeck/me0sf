----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--
-- The pattern unit multiplexer time-multiplexes a pattern unit across a
-- collection of strips. An individual pattern unit looks at a single strip.
-- Because of its fully pipelined design, however, it can be time-multiplexed to
-- process a different strip in every clock cycle.
--
-- We run the logic clock at 320MHz (8x the LHC clock), so that we can process
-- eight strips with a single pattern unit block.
--
-- This pat_unit_mux module multiplexes 8 strips into each pattern unit, then
-- demultiplexes the outputs. So in the end we process 192 strips using
-- 192/8=24 pattern units, and produce 192 output segments.
--
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.pat_types.all;
use work.priority_encoder_pkg.all;

entity pat_unit_mux is
  generic(

    DEBUG : boolean := false;

    VERBOSE : boolean := false;

    DISABLE_PEAKING : boolean := false;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);
    LY2_SPAN : natural := get_max_span(patdef_array);
    LY3_SPAN : natural := get_max_span(patdef_array);
    LY4_SPAN : natural := get_max_span(patdef_array);
    LY5_SPAN : natural := get_max_span(patdef_array);

    PATLIST : patdef_array_t := patdef_array;
    WIDTH   : natural        := PRT_WIDTH;

    DEADTIME : natural := 3;            -- deadtime in bx

    -- Need padding for half the width of the pattern this is to handle the edges
    -- of the chamber where some virtual chamber of all zeroes exists... to be
    -- trimmed away by the compiler during optimization
    MUX_FACTOR : natural := 8
    );
  port(

    clock : in std_logic;

    ly_thresh : in std_logic_vector (2 downto 0);

    dav_i : in  std_logic;
    dav_o : out std_logic := '0';

    -- synthesis translate_off
    dav_i_phase : out natural range 0 to 7 := 0;
    dav_o_phase : out natural range 0 to 7 := 0;
    -- synthesis translate_on

    ly0 : in std_logic_vector (WIDTH-1 downto 0);
    ly1 : in std_logic_vector (WIDTH-1 downto 0);
    ly2 : in std_logic_vector (WIDTH-1 downto 0);
    ly3 : in std_logic_vector (WIDTH-1 downto 0);
    ly4 : in std_logic_vector (WIDTH-1 downto 0);
    ly5 : in std_logic_vector (WIDTH-1 downto 0);

    segments_o : out pat_unit_mux_list_t (WIDTH-1 downto 0)

    );
end pat_unit_mux;

architecture behavioral of pat_unit_mux is

  component ila_chamber
    port (
      clk : in std_logic;

      probe0  : in std_logic_vector(5 downto 0);
      probe1  : in std_logic_vector(5 downto 0);
      probe2  : in std_logic_vector(5 downto 0);
      probe3  : in std_logic_vector(2 downto 0);
      probe4  : in std_logic_vector(2 downto 0);
      probe5  : in std_logic_vector(3 downto 0);
      probe6  : in std_logic_vector(2 downto 0);
      probe7  : in std_logic_vector(3 downto 0);
      probe8  : in std_logic_vector(7 downto 0);
      probe9  : in std_logic_vector(3 downto 0);
      probe10 : in std_logic_vector(2 downto 0);
      probe11 : in std_logic_vector(3 downto 0);
      probe12 : in std_logic_vector(7 downto 0);
      probe13 : in std_logic_vector(3 downto 0);
      probe14 : in std_logic_vector(2 downto 0);
      probe15 : in std_logic_vector(3 downto 0);
      probe16 : in std_logic_vector(7 downto 0);
      probe17 : in std_logic_vector(3 downto 0);
      probe18 : in std_logic_vector(2 downto 0);
      probe19 : in std_logic_vector(3 downto 0);
      probe20 : in std_logic_vector(7 downto 0)
      );
  end component;

  function pad_layer (pad : natural; data : std_logic_vector)
    -- function to take slv + padding and pad both the left and right sides
    return std_logic_vector is
    variable pad_slv : std_logic_vector (pad-1 downto 0) := (others => '0');
  begin
    return pad_slv & data & pad_slv;
  end;

  constant PADDING : natural := (get_max_span(patdef_array)-1)/2;

  constant NUM_SECTORS : positive := WIDTH/MUX_FACTOR;

  constant LY_SPAN : natural := get_max_span(patdef_array);

  signal ly0_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly1_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly2_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly3_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly4_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly5_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);

  signal patterns_mux : pat_unit_list_t (NUM_SECTORS-1 downto 0);

  -- convert to strip type, appends the strip # to the format
  signal strips_demux : pat_unit_mux_list_t (WIDTH-1 downto 0);

  signal phase_i, patterns_mux_phase : natural range 0 to MUX_FACTOR-1;

  attribute MAX_FANOUT                       : integer;
  attribute MAX_FANOUT of patterns_mux_phase : signal is 128;

  signal dav_reg     : std_logic := '0';
  signal dav_peaking : std_logic := '0';
  signal dav_demux   : std_logic := '0';

  signal pat_unit_dav : std_logic_vector(NUM_SECTORS-1 downto 0);

  signal dead : std_logic_vector (PRT_WIDTH-1 downto 0) := (others => '0');
  signal trig : std_logic_vector (PRT_WIDTH-1 downto 0) := (others => '0');

  signal segments      : pat_unit_mux_list_t (WIDTH-1 downto 0);
  signal segments_last : pat_unit_mux_list_t (WIDTH-1 downto 0);

  signal dbg : std_logic_vector(5 downto 0);

begin

  dbg(0) <= ly0_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);
  dbg(1) <= ly1_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);
  dbg(2) <= ly2_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);
  dbg(3) <= ly3_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);
  dbg(4) <= ly4_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);
  dbg(5) <= ly5_padded (phase_i+0*MUX_FACTOR+PADDING*2 downto phase_i+0*MUX_FACTOR)(PADDING+2);

  debug_gen : if (DEBUG) generate

    ila_partition_inst : ila_chamber
      port map (
        clk => clock,

        -- (ly)(strip)
        probe0(0) => ly0(0),
        probe0(1) => ly1(0),
        probe0(2) => ly2(0),
        probe0(3) => ly3(0),
        probe0(4) => ly4(0),
        probe0(5) => ly5(0),

        -- (ly)(strip)
        probe1(0) => dbg(0),
        probe1(1) => dbg(1),
        probe1(2) => dbg(2),
        probe1(3) => dbg(3),
        probe1(4) => dbg(4),
        probe1(5) => dbg(5),

        probe2(0) => dav_i,
        probe2(1) => dav_o,
        probe2(2) => dav_reg,
        probe2(3) => pat_unit_dav(0),
        probe2(4) => '0',
        probe2(5) => '0',

        probe3 => std_logic_vector(to_unsigned(patterns_mux_phase, 3)),

        probe4 => (others => '0'),

        probe5 => (others => '0'),
        probe6 => std_logic_vector(segments_o(3).lc),
        probe7 => std_logic_vector(segments_o(3).id),
        probe8 => std_logic_vector(segments_o(3).strip),

        probe9  => (others => '0'),
        probe10 => std_logic_vector(segments_o(2).lc),
        probe11 => std_logic_vector(segments_o(2).id),
        probe12 => std_logic_vector(segments_o(2).strip),

        probe13 => (others => '0'),
        probe14 => std_logic_vector(patterns_mux(0).lc),
        probe15 => std_logic_vector(patterns_mux(0).id),
        probe16 => (others => '0'),

        probe17 => (others => '0'),
        probe18 => std_logic_vector(strips_demux(2).lc),
        probe19 => std_logic_vector(strips_demux(2).id),
        probe20 => std_logic_vector(strips_demux(2).strip)

        );
  end generate;

  --------------------------------------------------------------------------------
  -- Asserts
  --------------------------------------------------------------------------------

  assert WIDTH mod MUX_FACTOR = 0
    report "pat_unit_mux WIDTH must be divisible by MUX_FACTOR"
    severity error;

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
  -- Padding
  --
  -- pad the edges of the chamber with zeroes so that strips at the edges
  -- can still do pattern finding using the normal machanism
  --------------------------------------------------------------------------------

  ly0_padded <= pad_layer(PADDING, ly0);
  ly1_padded <= pad_layer(PADDING, ly1);
  ly2_padded <= pad_layer(PADDING, ly2);
  ly3_padded <= pad_layer(PADDING, ly3);
  ly4_padded <= pad_layer(PADDING, ly4);
  ly5_padded <= pad_layer(PADDING, ly5);

  --------------------------------------------------------------------------------
  -- Pattern Units Input Mux
  --
  -- for some # of strips, e.g. 192 ... we divide it into different sectors of
  -- width=MUX_FACTOR
  --
  -- so in this case we divide into 24 sectors of 8 wide each
  --
  -- we loop over those 24 sectors and mux together the inputs / outputs
  --------------------------------------------------------------------------------

  dav_to_phase_i_inst : entity work.dav_to_phase
    generic map (DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_i);

  patgen : for I in 0 to NUM_SECTORS-1 generate

    signal ly0_unit, ly1_unit, ly2_unit, ly3_unit, ly4_unit, ly5_unit
      : std_logic_vector (LY_SPAN - 1 downto 0) := (others => '0');

    signal lyx_unit_dav : std_logic := '0';

  begin

    process (clock) is
    begin
      if (rising_edge(clock)) then

        ly0_unit <= ly0_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly1_unit <= ly1_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly2_unit <= ly2_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly3_unit <= ly3_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly4_unit <= ly4_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly5_unit <= ly5_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);

        lyx_unit_dav <= dav_i;

      end if;
    end process;

    pat_unit_inst : entity work.pat_unit
      generic map (VERBOSE => verbose)
      port map (

        clock => clock,

        ly_thresh => ly_thresh,

        dav_i => lyx_unit_dav,
        ly0   => ly0_unit,
        ly1   => ly1_unit,
        ly2   => ly2_unit,
        ly3   => ly3_unit,
        ly4   => ly4_unit,
        ly5   => ly5_unit,

        dav_o => pat_unit_dav(I),
        pat_o => patterns_mux(I)

        );

  end generate;

  --------------------------------------------------------------------------------
  -- Pattern Units Outputs Demux
  --------------------------------------------------------------------------------

  dav_to_phase_o_inst : entity work.dav_to_phase
    generic map (DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => pat_unit_dav(0), phase_o => patterns_mux_phase);

  process (clock) is
  begin
    if (rising_edge(clock)) then

      if (patterns_mux_phase = 0) then
        dav_peaking <= '1';
        dav_demux   <= '1';
      else
        dav_peaking <= '0';
        dav_demux   <= '0';
      end if;

      -- unfold the pattern unit multiplexer and assign the strip number
      for I in 0 to NUM_SECTORS-1 loop
        strips_demux(I*MUX_FACTOR+patterns_mux_phase).id    <= patterns_mux(I).id;
        strips_demux(I*MUX_FACTOR+patterns_mux_phase).lc    <= patterns_mux(I).lc;
        strips_demux(I*MUX_FACTOR+patterns_mux_phase).strip <= to_unsigned(I*MUX_FACTOR+patterns_mux_phase, STRIP_BITS);
      end loop;

      -- copy the unfolded outputs to be stable for a 25 ns clock period since
      -- the unfolder changes every clock cycle
      if (patterns_mux_phase = 0) then
        segments      <= strips_demux;
        segments_last <= segments;
      end if;

      --------------------------------------------------------------------------------
      -- Peak finding logic
      --------------------------------------------------------------------------------
      --
      -- A problem that was quickly discovered in developing the segment finding
      -- algorithms was that due to the poor timing resolution of the GEM
      -- chamber, not all hits arrive in a single clock cycle.
      --
      -- To account for this, pulse stretching is used to make each S-bit hit
      -- last for e.g. 3 clock cycles.
      --
      -- A problem in this approach though is that the pattern unit will fire on
      -- the early hits, which e.g. may only have 4 layers, while the remaining
      -- 2 layers can come in across the next two clock cycles.
      --
      -- To prevent this "early-firing" phenomena, a simple mechanism "peaking"
      -- mechanism is used.
      --
      -- This works by buffering the found segments for a single clock cycle,
      -- and waiting until a time bin where the quality of the found pattern
      -- decreases, then doing a 1 clock cycle lookback and using the segments
      -- found in the /previous/ clock cycle.
      --
      --
      -- so for example say the hits are coming in out of time... with pulse
      -- extension=3
      --
      -- bx N we have 4 layers
      -- bx N+1 we have 6 layers
      -- bx N+2 we have 6 layers
      -- bx N + 3 we have 2 layers
      --
      -- we'd know from the transition of 6->2 layers that we gathered all of
      -- the hits, so in this case we use BX N+2 as the actual segment
      --
      --
      --                   ─────┬───┬───┬───┬─────────────────────────────────────────
      -- segments               │ 5 │ 6 │ 5 │
      --   lyc             ─────┴───┴───┴───┴─────────────────────────────────────────
      --
      --                   ─────────┬───┬───┬───┬─────────────────────────────────────
      -- segments_last              │ 5 │ 6 │ 5 │
      --   lyc             ─────────┴───┴───┴───┴─────────────────────────────────────
      --
      --                                ┌───┐
      -- segments <        ─────────────┘   └─────────────────────────────────────────
      -- segments_last
      --
      --                   ──────────────┬───┬────────────────────────────────────────
      -- segments_o                      │ 6 │
      --   lyc             ──────────────┴───┴────────────────────────────────────────
      --
      --------------------------------------------------------------------------------

      if (dav_demux = '1') then
        for I in segments_o'range loop
          if DISABLE_PEAKING or segments(I).lc < segments_last(I).lc then
            segments_o(I) <= segments_last(I);
          else
            segments_o(I) <= zero(segments_o(I));
          end if;
        end loop;
      end if;

      dav_o <= dav_peaking;

    end if;  -- rising_edge(clock)

  end process;

end behavioral;
