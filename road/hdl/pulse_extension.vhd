library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity pulse_extension is
  generic(
    MAX : integer := 8
    );
  port(
    clock : in  std_logic;
    d     : in  std_logic;
    q     : out std_logic
    );
end pulse_extension;

architecture behavioral of pulse_extension is
  signal cnt : integer range 0 to MAX;
begin

  process (cnt, d) is
  begin
    if (d = '1' or cnt > 0) then
      q <= '1';
    else
      q <= '0';
    end if;
  end process;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      if (d = '1') then
        cnt <= MAX;
      elsif (cnt > 0) then
        cnt <= cnt - 1;
      end if;
    end if;
  end process;

end behavioral;
