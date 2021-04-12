
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity dav_to_phase is
  generic(
    MAX : natural := 8
    );
  port(

    clock   : in  std_logic;
    dav     : in  std_logic;
    phase_o : out natural range 0 to MAX-1

    );
end dav_to_phase;

architecture behavioral of dav_to_phase is
  signal phase : natural range 0 to MAX-1;
begin

  phase_o <= phase;

  process (clock) is
  begin

    if (rising_edge(clock)) then
      if (phase = 7) then
        phase <= 0;
      else
        phase <= phase + 1;
      end if;

      if (dav = '1') then
        phase <= 1;
      end if;

    end if;
  end process;


end behavioral;
