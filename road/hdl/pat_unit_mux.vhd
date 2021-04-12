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
    VERBOSE          : boolean := false;
    WIDTH            : natural := 192;
    PADDING          : natural := 8;
    PAT_UNIT_LATENCY : natural := 4;    -- FIXME: time this in
    MUX_FACTOR       : natural := 8
    );
  port(

    clock : in  std_logic;
    dav_i : in  std_logic;
    dav_o : out std_logic;

    ly0_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
    ly1_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
    ly2_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
    ly3_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
    ly4_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);
    ly5_padded : in std_logic_vector (WIDTH-1 + 2*PADDING downto 0);

    patterns_o : out candidate_list_t (WIDTH-1 downto 0)

    );
end pat_unit_mux;

architecture behavioral of pat_unit_mux is

  constant NUM_SECTORS : positive := WIDTH/MUX_FACTOR;

  constant LY0_SPAN : natural := get_max_span(pat_list);
  constant LY1_SPAN : natural := get_max_span(pat_list);
  constant LY2_SPAN : natural := get_max_span(pat_list);
  constant LY3_SPAN : natural := get_max_span(pat_list);
  constant LY4_SPAN : natural := get_max_span(pat_list);
  constant LY5_SPAN : natural := get_max_span(pat_list);

  signal patterns_mux : candidate_list_t (NUM_SECTORS-1 downto 0);

  signal patterns_reg : candidate_list_t (WIDTH-1 downto 0);

  signal phase_i, phase_pat_o : natural range 0 to MUX_FACTOR;

  signal dav_pat_i, dav_pat_o : std_logic := '0';

begin

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
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_i);

  dav_to_phase_o_inst : entity work.dav_to_phase
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_pat_o, phase_o => phase_pat_o);

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

        dav_pat_i <= dav_i;

      end if;
    end process;

    pat_unit_inst : entity work.pat_unit
      port map (

        clock => clock,

        dav_i => dav_pat_i,
        dav_o => dav_pat_o,

        ly0 => ly0_in,
        ly1 => ly1_in,
        ly2 => ly2_in,
        ly3 => ly3_in,
        ly4 => ly4_in,
        ly5 => ly5_in,

        pat_o => patterns_mux(I)
        );

  end generate;

  --------------------------------------------------------------------------------
  -- Pattern Units Outputs Demux
  --------------------------------------------------------------------------------
  -- FIXME: the mux logic needs to be checked and correctly timed....
  -- should pass dav flags around

  process (clock) is
  begin
    if (rising_edge(clock)) then
      for I in 0 to NUM_SECTORS-1 loop
        patterns_reg(I*MUX_FACTOR+phase_pat_o) <= patterns_mux(I);
      end loop;
    end if;
  end process;

  patterns_o <= patterns_reg;

end behavioral;
