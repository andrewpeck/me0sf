library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library work;
use work.pat_pkg.all;
use work.patterns.all;

entity ghost_cancellation is
  generic(
    WIDTH : natural := 128
    );
  port(

    clock : in std_logic;

    pat_candidates_i           : in candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_p : in candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_n : in candidate_list_t (WIDTH-1 downto 0);

    pat_candidates_o : out candidate_list_t (WIDTH-1 downto 0)

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

  signal pat_candidates_padded,
    pat_candidates_padded_p,
    pat_candidates_padded_n
    : candidate_list_t
    (GHOST_REGION*2+WIDTH-1 downto 0) := (others => null_candidate);

  function is_ghosted (strip : integer; hits : candidate_list_t) return boolean is
    variable is_ghost : boolean := false;
  begin
    is_ghost := false;
    for I in 1 to GHOST_REGION loop
      is_ghost := is_ghost or hits(strip+I) >  hits(strip);  -- dead if neighbor+N is better
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

    pat_candidates_padded(I+GHOST_REGION)   <= pat_candidates_i(I);
    pat_candidates_padded_p(I+GHOST_REGION) <= pre_gcl_pat_candidates_i_p(I);
    pat_candidates_padded_n(I+GHOST_REGION) <= pre_gcl_pat_candidates_i_n(I);

    dead (I) <= '0' when (deadcnt(I) = to_unsigned(0, DEADCNTB)) else '1';

    ghosted(I) <= '1' when (is_ghosted (I+GHOST_REGION, pat_candidates_padded)
                            or pat_candidates_padded_p(I+GHOST_REGION) >= pat_candidates_padded(GHOST_REGION+I)  -- dead if Partition+1 is better or equal
                            or pat_candidates_padded_n(I+GHOST_REGION) > pat_candidates_padded(GHOST_REGION+I)   -- dead if Partition-1 is better
                            ) else '0';

    p_deadtime : process (clock) is
    begin
      if (rising_edge(clock)) then
        if (pat_candidates_i(I).dav and not dead(I)) then
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
          pat_candidates_o(I) <= null_candidate;
        else
          pat_candidates_o(I) <= pat_candidates_padded(I+GHOST_REGION);
        end if;
      end if;
    end process;

  end generate;

end behavioral;
