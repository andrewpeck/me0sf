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

    pat_candidates_i : in  candidate_list_t (WIDTH-1 downto 0);
    pat_candidates_o : out candidate_list_t (WIDTH-1 downto 0)
    );
end ghost_cancellation;

architecture behavioral of ghost_cancellation is

  constant GHOST_REGION : integer := 1;
  constant KILLTIME     : integer := 3 * FREQ/40;
  constant KILLCNTB     : integer := integer(ceil(log2(real(KILLTIME))));

  type killcnt_array_t is array (integer range <>) of unsigned(KILLCNTB-1 downto 0);
  signal kill    : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal killcnt : killcnt_array_t (WIDTH-1 downto 0)  := (others => (others => '0'));

  signal pat_candidates_padded : candidate_list_t
    (GHOST_REGION*2+WIDTH-1 downto 0) := (others => null_candidate);

begin

  assert GHOST_REGION=1 report "Only ghost region size of 1 is supported." severity error;

  -- TODO: need to kill groups of three+
  -- e.g. 23332 after GCL will result in:
  --      -333-  but we want:
  --      --3--
  slv : for I in 0 to pat_candidates_i'length-1 generate
  begin

    pat_candidates_padded(I+GHOST_REGION) <= pat_candidates_i(I);

    kill (I) <= '1' when (killcnt(I) > to_unsigned(0,KILLCNTB)) else '0';

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

        -- FIXME: higher level function to parameterize this to ghost region?
        if ('1'=kill(I)
          or pat_candidates_padded(I+GHOST_REGION) <= pat_candidates_padded(GHOST_REGION+I+1) -- kill if a neighbor is better or equal
          or pat_candidates_padded(I+GHOST_REGION) > pat_candidates_padded(GHOST_REGION+I-1)
          )
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
