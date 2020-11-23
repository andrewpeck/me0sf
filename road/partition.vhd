library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.pat_pkg.all;
use work.patterns.all;

entity partition is
  generic(
    WIDTH         : natural := PRT_WIDTH;
    PARTITION_NUM : natural := 0  -- FIXME: append the partition number before sorting
    );
  port(

    clock : in std_logic;

    partition : in partition_t;
    neighbor  : in partition_t;

    pat_candidates_o : out candidate_list_t (WIDTH-1 downto 0);

    sump : out std_logic

    );
end partition;

architecture behavioral of partition is

  constant padding_width : integer := (get_max_span(0, pat_list)-1)/2; -- pad to half the width of the pattern
  constant padding       : std_logic_vector
    (padding_width -1 downto 0) := (others => '0');

  signal lyor : partition_t;

  signal ly0_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly1_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly2_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly3_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly4_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);
  signal ly5_padded : std_logic_vector (WIDTH-1 + 2*padding_width downto 0);

  signal pat_candidates     : candidate_list_t (WIDTH-1 downto 0);
  signal pat_candidates_gcl : candidate_list_t (WIDTH-1 downto 0);

  attribute DONT_TOUCH             : string;
  attribute DONT_TOUCH of gcl_inst : label is "true";

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- FIXME: this should be parameterized, and depend on the station
      -- matters which layer and the orientation of chambers wrt the ip
      -- or something like that
      -- but this stupid approach is ok for now
      lyor(0) <= partition(0) or neighbor(0);
      lyor(1) <= partition(1) or neighbor(1);
      lyor(2) <= partition(2) or neighbor(2);
      lyor(3) <= partition(3) or neighbor(3);
      lyor(4) <= partition(4) or neighbor(4);
      lyor(5) <= partition(5) or neighbor(5);
    end if;
  end process;

  -- pad the edges with zero for input to pat_units
  ly0_padded <= padding & lyor(0) & padding;
  ly1_padded <= padding & lyor(1) & padding;
  ly2_padded <= padding & lyor(2) & padding;
  ly3_padded <= padding & lyor(3) & padding;
  ly4_padded <= padding & lyor(4) & padding;
  ly5_padded <= padding & lyor(5) & padding;

  patgen : for I in 0 to WIDTH-1 generate
    attribute DONT_TOUCH                  : string;
    attribute DONT_TOUCH of pat_unit_inst : label is "true";
  begin
    pat_unit_inst : entity work.pat_unit
      port map (
        clock => clock,
        ly0   => ly0_padded (I+padding_width*2 downto I),
        ly1   => ly1_padded (I+padding_width*2 downto I),
        ly2   => ly2_padded (I+padding_width*2 downto I),
        ly3   => ly3_padded (I+padding_width*2 downto I),
        ly4   => ly4_padded (I+padding_width*2 downto I),
        ly5   => ly5_padded (I+padding_width*2 downto I),
        pat_o => pat_candidates(I)
        );
  end generate;

  gcl_inst : entity work.ghost_cancellation
    generic map (
      WIDTH => WIDTH
      )
    port map (
      clock            => clock,
      pat_candidates_i => pat_candidates,
      pat_candidates_o => pat_candidates_o
      );

end behavioral;
