library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity pulse_extension is
  generic(
    MAX : positive := 2
    );
  port(
    clock : in  std_logic;
    d     : in  std_logic;
    q     : out std_logic
    );
end pulse_extension;

architecture behavioral of pulse_extension is
  signal sr : std_logic_vector (MAX-1 downto 0) := (others => '0');
begin

  q <= d or or_reduce(sr) when MAX > 0 else d;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      sr <= sr(sr'left-1 downto 0) & d;
    end if;
  end process;
end behavioral;
