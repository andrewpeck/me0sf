----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity dav_to_phase is
  generic(
    MAX : natural := 8;
    DIV : natural := 1;
    DLY : natural := 0
    );
  port(

    clock   : in  std_logic;
    dav     : in  std_logic;
    phase_o : out natural range 0 to MAX/DIV-1 := 0

    );
end dav_to_phase;

architecture behavioral of dav_to_phase is

  signal delay   : std_logic_vector (DLY-1 downto 0);
  signal dav_dly : std_logic := '0';

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

    dav_dly_gen : if (DLY>0) generate
      process (clock) is
      begin
        if (rising_edge(clock)) then
          delay(0) <= dav;
          for I in 1 to DLY-1 loop
            delay(I) <= delay(I-1);
          end loop;
        end if;
      end process;
      dav_dly <= delay(DLY-1);
    end generate;

    dav_nodly_gen : if (DLY=0) generate
      dav_dly <= dav;
    end generate;

    process (clock) is
    begin

      if (rising_edge(clock)) then

        if (dav_dly = '1' and DIV = 1) then
          phase_cnt <= 1;
        elsif (div_cnt = DIV-1) then
          if (phase_cnt = MAX/DIV-1) then
            phase_cnt <= 0;
          else
            phase_cnt <= phase_cnt + 1;
          end if;
        end if;

        if (dav_dly = '1') then
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
