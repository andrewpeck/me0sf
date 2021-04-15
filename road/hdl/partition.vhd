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
    S0_WIDTH      : natural := 1
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
    -- outputs
    --------------------------------------------------------------------------------

    --pats_o : out pat_list_t (192-1 downto 0)
    pats_o : out pat_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0)

    );
end partition;

architecture behavioral of partition is

  -- (partially) or together this partition and its minus neighbor only need the
  -- minus neighbor since we are only interested in things pointing from the IP
  signal lyor : partition_t;

  -- pre-and post ghost-cancellation patterns, 1 per strip
  signal pats : pat_list_t (PRT_WIDTH-1 downto 0);

  --type pat_list_array_t is array (integer range 0 to FILTER_STAGES) of pat_list_t;
  -- FIXME put these in an array somehow...
  signal pats_s0 : pat_list_t (PRT_WIDTH/S0_WIDTH-1 downto 0);

  -- signal pats_gcl : pat_list_t (PRT_WIDTH-1 downto 0);

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

  -------------------------------------------------------------------------------
  -- Pre-filter the patterns to limit to 1 segment in every N strips using a
  -- priority encoded sorting tree...

  s0_gen : for region in 0 to PRT_WIDTH/S0_WIDTH-1 generate
    signal best     : std_logic_vector (PATTERN_LENGTH-1 downto 0);
    signal cand_slv : bus_array (0 to S0_WIDTH-1) (PATTERN_LENGTH-1 downto 0);
  begin

    cand_to_slv : for I in 0 to S0_WIDTH-1 generate
    begin
      cand_slv(I) <= to_slv(pats(REGION*S0_WIDTH+I));
    end generate;

    priority_encoder_inst : entity work.priority_encoder
      generic map (
        DAT_BITS   => PATTERN_LENGTH,
        QLT_BITS   => PATTERN_LENGTH - null_pattern.hash'length,
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

    pats_s0(region) <= to_pattern(best);

  end generate;

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  pats_o <= pats_s0;

end behavioral;
