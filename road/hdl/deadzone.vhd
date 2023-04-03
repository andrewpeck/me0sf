
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity deadzone is
  generic(
    WIDTH    : integer := 192;
    DEADTIME : integer := 4
    );
  port(
    clock  : in  std_logic;
    trg_i  : in  std_logic_vector(WIDTH-1 downto 0);
    dead_o : out std_logic_vector(WIDTH-1 downto 0)
    );
end deadzone;

architecture behavioral of deadzone is
  signal trg_r : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      trg_r <= trg_i;
    end if;
  end process;

  deadgen : for I in 0 to WIDTH-1 generate
    signal deadcnt : integer range 0 to DEADTIME;
  begin

    dead_o(I) <= '1' when deadcnt /= 0 else '0';

    process (clock) is
    begin
      if (rising_edge(clock)) then
        if (deadcnt = 0 and trg_i(I) = '1' and trg_r(I) = '0') then
          deadcnt <= DEADTIME;
        elsif (deadcnt > 0) then
          deadcnt <= deadcnt - 1;
        end if;
      end if;
    end process;

  end generate;

end behavioral;
