library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_pkg.all;
use work.patterns.all;

entity partition is
  generic(
    NUM_SEGMENTS  : integer := 0;
    PARTITION_NUM : integer := 0;
    WIDTH         : natural := PRT_WIDTH;
    MUX_FACTOR    : natural := FREQ/40
    );
  port(

    clock : in std_logic;

    partition : in partition_t;
    neighbor  : in partition_t;

    pat_candidates_o : out candidate_list_t (WIDTH-1 downto 0);

    pre_gcl_pat_candidates_o   : out candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_p : in  candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_n : in  candidate_list_t (WIDTH-1 downto 0);

    sump : out std_logic

    );
end partition;

architecture behavioral of partition is

  constant padding_width : integer := (get_max_span(pat_list)-1)/2;  -- pad to half the width of the pattern
  constant padding       : std_logic_vector
    (padding_width -1 downto 0) := (others => '0');

  signal lyor : partition_t;

  signal ly0_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly1_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly2_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly3_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly4_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly5_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);

  signal pat_candidates_mux : candidate_list_t (WIDTH/MUX_FACTOR-1 downto 0);
  signal pat_candidates     : candidate_list_t (WIDTH-1 downto 0);
  signal pat_candidates_gcl : candidate_list_t (WIDTH-1 downto 0);

  attribute DONT_TOUCH             : string;
  attribute DONT_TOUCH of gcl_inst : label is "true";

  signal phase : integer range 0 to 7 := 0;

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      if (phase < 8) then
        phase <= phase + 1;
      else
        phase <= 0;
      end if;
    end if;
  end process;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- FIXME: this should be parameterized, and depend on the station
      -- matters which layer and the orientation of chambers wrt the ip
      -- or something like that
      -- but this stupid approach is ok for now
      lyor(5) <= partition(5);
      lyor(4) <= partition(4);
      lyor(3) <= partition(3);
      lyor(2) <= partition(2) or neighbor(2);
      lyor(1) <= partition(1) or neighbor(1);
      lyor(0) <= partition(0) or neighbor(0);
    end if;
  end process;

  -- pad the edges with zero for input to pat_units
  ly0_padded <= padding & lyor(0) & padding;
  ly1_padded <= padding & lyor(1) & padding;
  ly2_padded <= padding & lyor(2) & padding;
  ly3_padded <= padding & lyor(3) & padding;
  ly4_padded <= padding & lyor(4) & padding;
  ly5_padded <= padding & lyor(5) & padding;

  patgen : for I in 0 to WIDTH/MUX_FACTOR-1 generate
    attribute DONT_TOUCH                  : string;
    attribute DONT_TOUCH of pat_unit_inst : label is "true";
  begin
    pat_unit_inst : entity work.pat_unit
      port map (
        clock => clock,
        ly0   => ly0_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        ly1   => ly1_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        ly2   => ly2_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        ly3   => ly3_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        ly4   => ly4_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        ly5   => ly5_padded (phase+I*MUX_FACTOR+padding_width*2 downto phase+I*MUX_FACTOR),
        pat_o => pat_candidates_mux(I)
        );
  end generate;

  -- FIXME: the mux logic needs to be checked and correctly timed.... should pass dav flags around
  process (clock) is
  begin
    if (rising_edge(clock)) then
      for I in 0 to WIDTH/MUX_FACTOR-1 loop
        pat_candidates(I*MUX_FACTOR+phase) <= pat_candidates_mux(I);
      end loop;
    end if;
  end process;

  pre_gcl_pat_candidates_o <= pat_candidates;

  gcl_inst : entity work.ghost_cancellation
    generic map (
      WIDTH => WIDTH
      )
    port map (
      clock                      => clock,
      pat_candidates_i           => pat_candidates,
      pre_gcl_pat_candidates_i_p => pre_gcl_pat_candidates_i_p,
      pre_gcl_pat_candidates_i_n => pre_gcl_pat_candidates_i_n,
      pat_candidates_o           => pat_candidates_o
      );

end behavioral;
