library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity dav_to_phase is
  generic(
    MAX : natural := 8;
    DIV : natural := 1
    );
  port(

    clock   : in  std_logic;
    dav     : in  std_logic;
    phase_o : out natural range 0 to MAX/DIV-1 := 0

    );
end dav_to_phase;

architecture behavioral of dav_to_phase is

  -- Example outputs for MAX=8 at different
  -- divider settings
  --
  --          0   1   2   3   4   5   6   7   0
  --          ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐
  -- CLK320  ─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─
  --          ┌───┐                       ┌───┐
  -- dav     ─┘   └───────────────────────┘   └───
  --         ─┬───┬───┬───┬───┬───┬───┬───┬───┬───
  -- div=1    │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │
  --         ─┴───┴───┴───┴───┴───┴───┴───┴───┴───
  --         ─┬───────┬───────┬───────┬───────┬───
  -- div=2    │   0   │   1   │   2   │   3   │
  --         ─┴───────┴───────┴───────┴───────┴───
  --         ─┬───────────────┬───────────────┬───
  -- div=4    │       0       │       1       │
  --         ─┴───────────────┴───────────────┴───
  --         ─┬───────────────────────────────┬───
  -- div=8    │               0               │
  --         ─┴───────────────────────────────┴───

begin

  EQUALP : if (MAX = DIV) generate
    phase_o <= 0;
  end generate;

  NEQUALP : if (MAX /= DIV) generate
    signal cnt       : natural range 0 to MAX-1;
    signal div_cnt   : natural range 0 to DIV-1;
    signal phase_cnt : natural range 0 to MAX/DIV-1;
  begin

    phase_o <= phase_cnt;

    div_cnt <= cnt mod DIV;

    process (clock) is
    begin

      if (rising_edge(clock)) then

        if (div_cnt = DIV-1) then
          if (dav = '1') then
            phase_cnt <= 1;
          elsif (phase_cnt = MAX/DIV-1) then
            phase_cnt <= 0;
          else
            phase_cnt <= phase_cnt + 1;
          end if;
        end if;

        if (dav = '1') then
          cnt <= 1;
        else
          if (cnt = MAX-1) then
            cnt <= 0;
          else
            cnt <= cnt + 1;
          end if;
        end if;

      end if;
    end process;
  end generate;

end behavioral;
