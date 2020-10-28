library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.pat_pkg.all;
use work.patterns.all;

entity partition is
  generic(
    PARTITION_NUM : natural := 0;
    NUM_OUTPUTS   : natural := 16;
    LY_SPAN       : natural := 11
    );
  port(

    clock : in std_logic;

    ly0 : in std_logic_vector (3*64-1 downto 0);
    ly1 : in std_logic_vector (3*64-1 downto 0);
    ly2 : in std_logic_vector (3*64-1 downto 0);
    ly3 : in std_logic_vector (3*64-1 downto 0);
    ly4 : in std_logic_vector (3*64-1 downto 0);
    ly5 : in std_logic_vector (3*64-1 downto 0);

    nx0 : in std_logic_vector (3*64-1 downto 0);
    nx1 : in std_logic_vector (3*64-1 downto 0);
    nx2 : in std_logic_vector (3*64-1 downto 0);
    nx3 : in std_logic_vector (3*64-1 downto 0);
    nx4 : in std_logic_vector (3*64-1 downto 0);
    nx5 : in std_logic_vector (3*64-1 downto 0);

    pat_candidates_o : out candidate_list_t (NUM_OUTPUTS-1 downto 0);

    sump : out std_logic

    );
end partition;

architecture behavioral of partition is

  constant padding_width                                                        : integer                                      := 5;  -- FIXME: please no constants
  constant padding                                                              : std_logic_vector (padding_width -1 downto 0) := (others => '0');
  signal ly0_or, ly1_or, ly2_or, ly3_or, ly4_or, ly5_or                         : std_logic_vector (3*64-1 downto 0);
  signal ly0_padded, ly1_padded, ly2_padded, ly3_padded, ly4_padded, ly5_padded : std_logic_vector (3*64-1 + 2*padding_width downto 0);

  signal pat_candidates : candidate_list_t (ly0'length-1 downto 0);

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- FIXME: this should be parameterized, and depend on the station
      -- matters which layer and the orientation of chambers wrt the ip
      ly0_or <= ly0 or nx0;
      ly1_or <= ly1 or nx1;
      ly2_or <= ly2 or nx2;
      ly3_or <= ly3 or nx3;
      ly4_or <= ly4 or nx4;
      ly5_or <= ly5 or nx5;
    end if;
  end process;

  ly0_padded <= padding & ly0_or & padding;
  ly1_padded <= padding & ly1_or & padding;
  ly2_padded <= padding & ly2_or & padding;
  ly3_padded <= padding & ly3_or & padding;
  ly4_padded <= padding & ly4_or & padding;
  ly5_padded <= padding & ly5_or & padding;

  patgen : for I in 0 to ly0'length-1 generate
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


  -- FIXME: need to add ghost cancellation logic

--  segment_selector_1 : entity work.segment_selector
--    generic map (NUM_OUTPUTS => NUM_OUTPUTS)
--    port map (
--      clock            => clock,
--      pat_candidates_i => pat_candidates_i,
--      pat_candidates_o => pat_candidates_o,
--      sump             => sump);

end behavioral;
