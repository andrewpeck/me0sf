library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.pat_pkg.all;
use work.patterns.all;

entity ghost_cancellation is
  generic(
    WIDTH       : natural := 3;
    NUM_OUTPUTS : natural := 1
    );
  port(

    clock : in std_logic;

    pat_candidates_i : in  candidate_list_t (WIDTH-1 downto 0);
    pat_candidates_o : out candidate_list_t (NUM_OUTPUTS-1 downto 0)
    );
end ghost_cancellation;

architecture behavioral of ghost_cancellation is
begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      pat_candidates_o <= pat_candidates_i;
    end if;
  end process;

end behavioral;
