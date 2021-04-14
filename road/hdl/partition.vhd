library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity partition is
  generic(
    NUM_SEGMENTS  : integer := 4;
    PARTITION_NUM : integer := 0;
    PRT_WIDTH     : natural := PRT_WIDTH;
    MUX_FACTOR    : natural := FREQ/40;
    S0_WIDTH      : natural := 8;
    S1_WIDTH      : natural := 2
    );
  port(

    --------------------------------------------------------------------------------
    -- Control
    --------------------------------------------------------------------------------

    clock : in  std_logic;
    dav_i : in  std_logic;
    dav_o : out std_logic;

    --------------------------------------------------------------------------------
    -- Inputs
    --------------------------------------------------------------------------------
    --
    -- take in all hits from the partition and from its neighbor data from
    -- partition n and n+1 is combined to do cross-partition pattern finding
    partition_i : in partition_t;
    neighbor_i  : in partition_t;

    --------------------------------------------------------------------------------
    -- cross partition pattern sharing, for cancellation
    --------------------------------------------------------------------------------

    -- -- send patterns out to partition n+1 and n-1
    -- pre_gcl_pats_o : out candidate_list_t (PRT_WIDTH-1 downto 0);

    -- -- bring patterns in from partition n+1
    -- pre_gcl_pats_i_p : in candidate_list_t (PRT_WIDTH-1 downto 0);

    -- -- bring patterns in from partition n-1
    -- pre_gcl_pats_i_n : in candidate_list_t (PRT_WIDTH-1 downto 0);

    --------------------------------------------------------------------------------
    -- outputs
    --------------------------------------------------------------------------------

    pats_o : out candidate_list_t (PRT_WIDTH/S0_WIDTH/S1_WIDTH-1 downto 0)

    );
end partition;

architecture behavioral of partition is

  -- Need padding for half the width of the pattern this is to handle the edges
  -- of the chamber where some virtual chamber of all zeroes exists... to be
  -- trimmed away by the compiler during optimization
  constant PADDING : integer := (get_max_span(pat_list)-1)/2;

  -- (partially) or together this partition and its minus neighbor only need the
  -- minus neighbor since we are only interested in things pointing from the IP
  signal lyor : partition_t;

  -- pre-and post ghost-cancellation patterns, 1 per strip
  signal pats    : candidate_list_t (PRT_WIDTH-1 downto 0);
  signal pats_s0 : candidate_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);
  signal pats_s1 : candidate_list_t (PRT_WIDTH/S0_WIDTH/S1_WIDTH-1 downto 0);

  -- signal pats_gcl : candidate_list_t (PRT_WIDTH-1 downto 0);

begin

  --------------------------------------------------------------------------------
  -- Neighbor Partition OR
  --
  -- details to come....
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- FIXME: this should be parameterized, and depend on the station matters
      -- which layer and the orientation of chambers wrt the ip or something
      -- like that but this stupid approach is ok for now
      lyor(5) <= partition_i(5);
      lyor(4) <= partition_i(4);
      lyor(3) <= partition_i(3);
      lyor(2) <= partition_i(2) or neighbor_i(2);
      lyor(1) <= partition_i(1) or neighbor_i(1);
      lyor(0) <= partition_i(0) or neighbor_i(0);
    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Pattern Unit Mux
  --
  -- Find 0 or 1 patterns per strip.
  --
  -- To reduce resources, a mux is wrapped around the pattern unit. Each pattern
  -- can be reused N times per clock cycle
  --------------------------------------------------------------------------------

  pat_unit_mux_inst : entity work.pat_unit_mux
    generic map (
      WIDTH      => PRT_WIDTH,
      PADDING    => PADDING,
      MUX_FACTOR => MUX_FACTOR
      )
    port map (
      clock => clock,

      dav_i => dav_i,
      dav_o => dav_o,

      ly0 => lyor(0),
      ly1 => lyor(1),
      ly2 => lyor(2),
      ly3 => lyor(3),
      ly4 => lyor(4),
      ly5 => lyor(5),

      patterns_o => pats
      );

  --pre_gcl_pats_o <= pats;

  -- --------------------------------------------------------------------------------
  -- -- s0 Pre-filter the candidates to limit to 1 segment in every N strips
  -- --------------------------------------------------------------------------------

  s0_gen : for region in 0 to PRT_WIDTH/S0_WIDTH-1 generate
    signal best     : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
    signal cand_slv : bus_array (0 to S0_WIDTH-1) (CANDIDATE_LENGTH-1 downto 0);
  begin

    cand_to_slv : for I in 0 to S0_WIDTH-1 generate
    begin
      cand_slv(I) <= to_slv(pats(I));
    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        DAT_BITS   => CANDIDATE_LENGTH,
        QLT_BITS   => CANDIDATE_LENGTH - null_candidate.hash'length,
        WIDTH      => S0_WIDTH,
        REG_INPUT  => false,
        REG_OUTPUT => true,
        REG_STAGES => 3
        )
      port map (
        clock => clock,
        dat_i => cand_slv,
        dat_o => best,
        adr_o => open
        );

    pats_s0(region) <= to_candidate(best);

  end generate;

  -- --------------------------------------------------------------------------------
  -- -- S1 Filter
  -- --------------------------------------------------------------------------------

  assert S1_WIDTH = 2 report "S1_WIDTH must be 2 for now..." severity error;

  -- FIXME: replace with priority encoder.. should be okay even for size 2
  -- it should infer the correct thing
  s1gen : for I in 0 to PRT_WIDTH/S0_WIDTH/S1_WIDTH-1 generate
  begin
    process (clock) is
    begin
      if (rising_edge(clock)) then
        if (pats_s0(I*2+1) > pats_s0(I*2)) then
          pats_s1(I) <= pats_s0(I*2+1);
        else
          pats_s1(I) <= pats_s0(I*2);
        end if;
      end if;
    end process;
  end generate;

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  pats_o <= pats_s1;

  -- --------------------------------------------------------------------------------
  -- -- Ghost Cancellation
  -- --
  -- -- Look at adjacent strips to cancel off duplicated hits
  -- --
  -- --------------------------------------------------------------------------------
  -- --
  -- -- FIXME: the mux logic needs to be checked and correctly timed....
  -- -- should pass dav flags around

  -- -- gcl_inst : entity work.ghost_cancellation
  -- --   generic map (
  -- --     WIDTH => PRT_WIDTH
  -- --     )
  -- --   port map (
  -- --     clock                      => clock,
  -- --     pats_i           => pats,
  -- --     pre_gcl_pats_i_p => pre_gcl_pats_i_p,
  -- --     pre_gcl_pats_i_n => pre_gcl_pats_i_n,
  -- --     pats_o           => pats_o
  -- --     );

end behavioral;
