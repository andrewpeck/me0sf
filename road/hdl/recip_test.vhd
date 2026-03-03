library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.fixed_pkg.all;

library work;
use work.reciprocal_pkg.all;

entity recip_test is  port (
    clock    : in std_logic;
    v_in     : in integer;
    v_out    : out sfixed (1 downto -13)
    );
end recip_test;

architecture behavioral of recip_test is
begin
  process (clock) is
  begin
    if (rising_edge(clock)) then
        v_out <= reciprocal(v_in, 13);
    end if;
  end process;
end behavioral;
