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

  constant GHOST_REGION : integer := 2;
  constant KILLTIME     : integer := 3 * FREQ/40;  -- 3bx dead time
  constant KILLCNTB     : integer := integer(ceil(log2(real(KILLTIME))));

  type killcnt_array_t is array (integer range <>) of unsigned(KILLCNTB-1 downto 0);
  signal kill    : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal ghosted : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal killcnt : killcnt_array_t (WIDTH-1 downto 0)  := (others => (others => '0'));

  signal pat_candidates_padded,
    pat_candidates_padded_p,
    pat_candidates_padded_n
    : candidate_list_t
    (GHOST_REGION*2+WIDTH-1 downto 0) := (others => null_candidate);

  function is_ghosted (hit : integer; hits : candidate_list_t) return boolean is
    variable is_ghost : boolean := false;
  begin
    for I in 0 to GHOST_REGION-1 loop
      is_ghost := is_ghost or pat_candidates_padded(hit) < pat_candidates_padded(hit+I);   -- kill if neighbor+N is better
      is_ghost := is_ghost or pat_candidates_padded(hit) <= pat_candidates_padded(hit-I);  -- kill if a neighbor-N is better or equal
    end loop;
    return is_ghost;

  end;
begin

  -- TODO: need to kill groups of three+
  -- e.g. 23332 after GCL will result in:
  --      -333-  but we want:
  --      --3--
  slv : for I in 0 to pat_candidates_i'length-1 generate
  begin

    pat_candidates_padded(I+GHOST_REGION)   <= pat_candidates_i(I);
    pat_candidates_padded_p(I+GHOST_REGION) <= pre_gcl_pat_candidates_i_p(I);
    pat_candidates_padded_n(I+GHOST_REGION) <= pre_gcl_pat_candidates_i_n(I);

    kill (I) <= '1' when (killcnt(I) > to_unsigned(0, KILLCNTB)) else '0';

    ghosted(I) <= '1' when (is_ghosted (I+GHOST_REGION, pat_candidates_padded)
                            or pat_candidates_padded_p(I+GHOST_REGION) >= pat_candidates_padded(GHOST_REGION+I)  -- kill if Partition+1 is better or equal
                            or pat_candidates_padded_n(I+GHOST_REGION) > pat_candidates_padded(GHOST_REGION+I)   -- kill if Partition-1 is better
                            ) else '0';

    process (clock) is
    begin
      if (rising_edge(clock)) then

        if (pat_candidates_i(I).dav and not kill(I)) then
          killcnt(I) <= to_unsigned(KILLTIME, KILLCNTB);
        else
          if (killcnt(I) > 0) then
            killcnt(I) <= killcnt(I)-1;
          end if;
        end if;

        if ('1'=kill(I) or '1'=ghosted(I))
        then
          pat_candidates_o(I) <= null_candidate;
        else
          pat_candidates_o(I) <= pat_candidates_padded(I+GHOST_REGION);
        end if;
      end if;
    end process;
  end generate;

--pat_candidates_o <= pat_candidates_i;
end behavioral;
