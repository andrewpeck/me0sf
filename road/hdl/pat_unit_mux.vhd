library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity pat_unit_mux is
  generic(
    VERBOSE    : boolean := false;
    WIDTH      : natural := 192;
    -- Need padding for half the width of the pattern this is to handle the edges
    -- of the chamber where some virtual chamber of all zeroes exists... to be
    -- trimmed away by the compiler during optimization
    PADDING    : natural := (get_max_span(patdef_array)-1)/2;
    MUX_FACTOR : natural := 1
    );
  port(

    clock : in  std_logic;
    dav_i : in  std_logic;
    dav_o : out std_logic;

    ly0 : in std_logic_vector (WIDTH-1 downto 0);
    ly1 : in std_logic_vector (WIDTH-1 downto 0);
    ly2 : in std_logic_vector (WIDTH-1 downto 0);
    ly3 : in std_logic_vector (WIDTH-1 downto 0);
    ly4 : in std_logic_vector (WIDTH-1 downto 0);
    ly5 : in std_logic_vector (WIDTH-1 downto 0);

    strips_o : out strip_list_t (WIDTH-1 downto 0)

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

  signal patterns_mux_dav : std_logic := '0';
  signal patterns_mux     : pat_list_t (NUM_SECTORS-1 downto 0);

  -- convert to strip type, appends the strip # to the format
  signal strips_reg : strip_list_t (WIDTH-1 downto 0);

  signal phase_i, patterns_mux_phase : natural range 0 to MUX_FACTOR-1;

  signal lyX_in_dav : std_logic := '0';

  signal dav_d0, dav_d1, dav_d2, dav_d3, dav_d4, dav_d5: std_logic;

begin

  ly0_padded <= pad_layer(PADDING, ly0);
  ly1_padded <= pad_layer(PADDING, ly1);
  ly2_padded <= pad_layer(PADDING, ly2);
  ly3_padded <= pad_layer(PADDING, ly3);
  ly4_padded <= pad_layer(PADDING, ly4);
  ly5_padded <= pad_layer(PADDING, ly5);

  assert WIDTH mod MUX_FACTOR = 0
    report "pat_unit_mux WIDTH must be divisible by MUX_FACTOR"
    severity error;

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
    generic map (MAX => 8, DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_i);

  dav_to_phase_o_inst : entity work.dav_to_phase
    generic map (MAX => 8, DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => dav_d1, phase_o => patterns_mux_phase);

  patgen : for I in 0 to NUM_SECTORS-1 generate

    signal ly0_in : std_logic_vector (LY0_SPAN - 1 downto 0) := (others => '0');
    signal ly1_in : std_logic_vector (LY1_SPAN - 1 downto 0) := (others => '0');
    signal ly2_in : std_logic_vector (LY2_SPAN - 1 downto 0) := (others => '0');
    signal ly3_in : std_logic_vector (LY3_SPAN - 1 downto 0) := (others => '0');
    signal ly4_in : std_logic_vector (LY4_SPAN - 1 downto 0) := (others => '0');
    signal ly5_in : std_logic_vector (LY5_SPAN - 1 downto 0) := (others => '0');

    signal dav : std_logic := '0';

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
      generic map (
        VERBOSE => false
        )
      port map (

        clock => clock,

        dav_i => lyX_in_dav,
        ly0   => ly0_in,
        ly1   => ly1_in,
        ly2   => ly2_in,
        ly3   => ly3_in,
        ly4   => ly4_in,
        ly5   => ly5_in,

        dav_o => dav,
        pat_o => patterns_mux(I)
        );

    muxzero : if (I = 0) generate
      patterns_mux_dav <= dav;
    end generate;
  end generate;

  --------------------------------------------------------------------------------
  -- Pattern Units Outputs Demux
  --------------------------------------------------------------------------------
  -- FIXME: the mux logic needs to be checked and correctly timed....
  -- should pass dav flags around

  process (clock) is
  begin
    if (rising_edge(clock)) then

      dav_d0 <= patterns_mux_dav;
      dav_d1 <= dav_d0;
      dav_d2 <= dav_d1;
      dav_d3 <= dav_d2;
      dav_d4 <= dav_d3;
      dav_d5 <= dav_d4;

      dav_o <= patterns_mux_dav;

      for I in 0 to NUM_SECTORS-1 loop
        strips_reg(I*MUX_FACTOR+patterns_mux_phase).pattern <= patterns_mux(I);
        strips_reg(I*MUX_FACTOR+patterns_mux_phase).strip   <= I*MUX_FACTOR+patterns_mux_phase;
      end loop;

    end if;
  end process;

  strips_o <= strips_reg;

end behavioral;
