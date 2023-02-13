----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;

entity ghost_cancellation is
  generic(
    FREQ  : natural := 320;
    WIDTH : natural := 128
    );
  port(

    clock : in std_logic;

    pats_i           : in pat_list_t (WIDTH-1 downto 0);
    pre_gcl_pats_i_p : in pat_list_t (WIDTH-1 downto 0);
    pre_gcl_pats_i_n : in pat_list_t (WIDTH-1 downto 0);

    pats_o : out pat_list_t (WIDTH-1 downto 0)

    );
end ghost_cancellation;

architecture behavioral of ghost_cancellation is

  constant GHOST_REGION : integer := 2;            -- check strips +- n for a better pattern
  constant DEADTIME     : integer := 3 * FREQ/40;  -- 3bx dead time
  constant DEADCNTB     : integer := integer(ceil(log2(real(DEADTIME))));

  type deadcnt_array_t is array (integer range <>) of unsigned(DEADCNTB-1 downto 0);
  signal dead    : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal ghosted : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal deadcnt : deadcnt_array_t (WIDTH-1 downto 0)  := (others => (others => '0'));

  signal pats_padded,
    pats_padded_p,
    pats_padded_n
    : pat_list_t
    (GHOST_REGION*2+WIDTH-1 downto 0) := (others => null_pattern);

  function is_ghosted (strip : integer; hits : pat_list_t) return boolean is
    variable is_ghost : boolean := false;
  begin
    is_ghost := false;
    for I in 1 to GHOST_REGION loop
      is_ghost := is_ghost or hits(strip+I) > hits(strip);   -- dead if neighbor+N is better
      is_ghost := is_ghost or hits(strip-I) >= hits(strip);  -- dead if a neighbor-N is better or equal
    end loop;
    return is_ghost;
  end;

  attribute DONT_TOUCH            : string;
  attribute DONT_TOUCH of dead    : signal is "true";
  attribute DONT_TOUCH of ghosted : signal is "true";

begin

  slv : for I in 0 to WIDTH-1 generate
  begin

    pats_padded(I+GHOST_REGION)   <= pats_i(I);
    pats_padded_p(I+GHOST_REGION) <= pre_gcl_pats_i_p(I);
    pats_padded_n(I+GHOST_REGION) <= pre_gcl_pats_i_n(I);

    dead (I) <= '0' when (deadcnt(I) = to_unsigned(0, DEADCNTB)) else '1';

    ghosted(I) <= '1' when (is_ghosted (I+GHOST_REGION, pats_padded)
                            or pats_padded_p(I+GHOST_REGION) >= pats_padded(GHOST_REGION+I)  -- dead if Partition+1 is better or equal
                            or pats_padded_n(I+GHOST_REGION) > pats_padded(GHOST_REGION+I)   -- dead if Partition-1 is better
                            ) else '0';

    p_deadtime : process (clock) is
    begin
      if (rising_edge(clock)) then
        if (pats_i(I).dav and not dead(I)) then
          deadcnt(I) <= to_unsigned(DEADTIME, DEADCNTB);
        else
          if (deadcnt(I) > 0) then
            deadcnt(I) <= deadcnt(I)-1;
          end if;
        end if;
      end if;
    end process;

    p_outputs : process (clock) is
    begin
      if (rising_edge(clock)) then
        if ('1'=dead(I) or '1'=ghosted(I)) then
          pats_o(I) <= null_pattern;
        else
          pats_o(I) <= pats_padded(I+GHOST_REGION);
        end if;
      end if;
    end process;

  end generate;

end behavioral;
