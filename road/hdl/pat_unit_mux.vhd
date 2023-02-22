----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, C. Grubb, J. Chismar
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
    VERBOSE : boolean := false;
    PARTITION_NUM : integer := 0;

    LATENCY : natural := PAT_UNIT_MUX_LATENCY;

    PATLIST    : patdef_array_t := patdef_array;
    WIDTH      : natural        := 192;
    -- Need padding for half the width of the pattern this is to handle the edges
    -- of the chamber where some virtual chamber of all zeroes exists... to be
    -- trimmed away by the compiler during optimization
    PADDING    : natural        := (get_max_span(patdef_array)-1)/2;
    MUX_FACTOR : natural        := 1
    );
  port(

    clock : in std_logic;

    thresh : in std_logic_vector (2 downto 0);

    dav_i : in  std_logic;
    dav_o : out std_logic;

    ly0 : in std_logic_vector (WIDTH-1 downto 0);
    ly1 : in std_logic_vector (WIDTH-1 downto 0);
    ly2 : in std_logic_vector (WIDTH-1 downto 0);
    ly3 : in std_logic_vector (WIDTH-1 downto 0);
    ly4 : in std_logic_vector (WIDTH-1 downto 0);
    ly5 : in std_logic_vector (WIDTH-1 downto 0);

    segments_o : out segment_list_t (WIDTH-1 downto 0)

    );
end pat_unit_mux;

architecture behavioral of pat_unit_mux is

  function pad_layer (pad : natural; data : std_logic_vector)
    -- function to take slv + padding and pad both the left and right sides
    return std_logic_vector is
    variable pad_slv : std_logic_vector (pad-1 downto 0) := (others => '0');
  begin
    return pad_slv & data & pad_slv;
  end;

  constant NUM_SECTORS : positive := WIDTH/MUX_FACTOR;

  constant LY0_SPAN : natural := get_max_span(patdef_array);
  constant LY1_SPAN : natural := get_max_span(patdef_array);
  constant LY2_SPAN : natural := get_max_span(patdef_array);
  constant LY3_SPAN : natural := get_max_span(patdef_array);
  constant LY4_SPAN : natural := get_max_span(patdef_array);
  constant LY5_SPAN : natural := get_max_span(patdef_array);

  signal ly0_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly1_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly2_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly3_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly4_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
  signal ly5_padded : std_logic_vector (WIDTH-1 + 2*PADDING downto 0);

  signal patterns_mux : segment_list_t (NUM_SECTORS-1 downto 0);

  -- convert to strip type, appends the strip # to the format
  signal strips_reg : segment_list_t (WIDTH-1 downto 0);

  signal phase_i, patterns_mux_phase : natural range 0 to MUX_FACTOR-1;

  signal lyX_in_dav : std_logic := '0';

  signal dav_reg : std_logic := '0';

  signal pat_unit_dav : std_logic_vector(NUM_SECTORS-1 downto 0);

begin

  --------------------------------------------------------------------------------
  -- Asserts
  --------------------------------------------------------------------------------

  assert WIDTH mod MUX_FACTOR = 0
    report "pat_unit_mux WIDTH must be divisible by MUX_FACTOR"
    severity error;

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

    signal ly0_in : std_logic_vector (LY0_SPAN - 1 downto 0) := (others => '0');
    signal ly1_in : std_logic_vector (LY1_SPAN - 1 downto 0) := (others => '0');
    signal ly2_in : std_logic_vector (LY2_SPAN - 1 downto 0) := (others => '0');
    signal ly3_in : std_logic_vector (LY3_SPAN - 1 downto 0) := (others => '0');
    signal ly4_in : std_logic_vector (LY4_SPAN - 1 downto 0) := (others => '0');
    signal ly5_in : std_logic_vector (LY5_SPAN - 1 downto 0) := (others => '0');

  begin

    process (clock) is
    begin
      if (rising_edge(clock)) then

        ly0_in <= ly0_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly1_in <= ly1_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly2_in <= ly2_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly3_in <= ly3_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly4_in <= ly4_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);
        ly5_in <= ly5_padded (phase_i+I*MUX_FACTOR+PADDING*2 downto phase_i+I*MUX_FACTOR);

        lyX_in_dav <= dav_i;

      end if;
    end process;

    pat_unit_inst : entity work.pat_unit
      generic map (VERBOSE => verbose)
      port map (

        clock => clock,

        thresh => thresh,

        dav_i => lyX_in_dav,
        ly0   => ly0_in,
        ly1   => ly1_in,
        ly2   => ly2_in,
        ly3   => ly3_in,
        ly4   => ly4_in,
        ly5   => ly5_in,

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

      dav_reg <= pat_unit_dav(0);       -- delay for unfolder
      dav_o   <= dav_reg;               -- delay for output reg

      -- unfold the pattern unit multiplexer and assign the strip number
      for I in 0 to NUM_SECTORS-1 loop
        strips_reg(I*MUX_FACTOR+patterns_mux_phase) <= patterns_mux(I);
        strips_reg(I*MUX_FACTOR+patterns_mux_phase).strip <=
          to_unsigned(I*MUX_FACTOR+patterns_mux_phase, STRIP_BITS);
        strips_reg(I*MUX_FACTOR+patterns_mux_phase).partition <=
          to_unsigned(PARTITION_NUM, segments_o(I).partition'length);
      end loop;

      -- copy the unfolded outputs to be stable for a 25 ns clock period since
      -- the unfolder changes every clock cycle
      if (dav_reg='1') then
        segments_o <= strips_reg;
      end if;

    end if;
  end process;

end behavioral;
