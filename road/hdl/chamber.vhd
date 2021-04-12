-------------------------------------------------------------------------------
-- Title      : Chamber
-------------------------------------------------------------------------------
-- File       : chamber.vhd
-- Last update: 2021-04-12
-- Standard   : VHDL'2008
-------------------------------------------------------------------------------
-- Description:
--
--   Segment finding for a single ME0 chamber
--
-------------------------------------------------------------------------------

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber is
  generic (
    NUM_SEGMENTS  : integer := 4;
    PARTITION_NUM : integer := 0;
    MUX_FACTOR    : integer := FREQ/40
    );
  port(
    clock   : in  std_logic;             -- 320 MHz clock
    dav_i   : in  std_logic;
    dav_o   : out std_logic;
    sbits_i : in  chamber_t;
    segs_o  : out candidate_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber;

architecture behavioral of chamber is

  signal pat_candidates, pat_candidates_r : cand_array_t;
  signal pat_candidates_s0                : cand_array_s0_t;

  signal pat_candidates_mux : candidate_list_t (PRT_WIDTH/S0_REGION_SIZE-1 downto 0);

  signal segs_cat : candidate_list_t (NUM_SEGMENTS*8-1 downto 0);

  signal pre_gcl_pat_candidates     : candidate_list_t (PRT_WIDTH-1 downto 0);
  type pre_gcl_array_t is array (integer range 0 to 7) of candidate_list_t (PRT_WIDTH-1 downto 0);
  signal pre_gcl_pat_candidates_o   : pre_gcl_array_t;
  signal pre_gcl_pat_candidates_i_p : pre_gcl_array_t;
  signal pre_gcl_pat_candidates_i_n : pre_gcl_array_t;

  signal selector_s1_o : candidate_list_t (NUM_SEGMENTS-1 downto 0);
  signal selector_s2_o : candidate_list_t (NUM_SEGMENTS-1 downto 0);

  type seg_array_t is array (integer range 0 to 7) of candidate_list_t (NUM_SEGMENTS-1 downto 0);
  signal segs_r, segs_rr : seg_array_t;

  signal phase_candidate_mux : natural;
  signal phase_selector : natural;

begin

  dav_to_phase_mux_inst : entity work.dav_to_phase
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase => phase_candidate_mux);

  dav_to_phase_selector_inst : entity work.dav_to_phase
    generic map (MAX => MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase => phase_selector);

  --------------------------------------------------------------------------------
  -- Get pattern unit candidates for each partition, one for each strip
  --------------------------------------------------------------------------------

  pre_gcl_pat_candidates_i_n (0) <= (others => null_candidate);
  pre_gcl_pat_candidates_i_n (1) <= pre_gcl_pat_candidates_o (0);
  pre_gcl_pat_candidates_i_n (2) <= pre_gcl_pat_candidates_o (1);
  pre_gcl_pat_candidates_i_n (3) <= pre_gcl_pat_candidates_o (2);
  pre_gcl_pat_candidates_i_n (4) <= pre_gcl_pat_candidates_o (3);
  pre_gcl_pat_candidates_i_n (5) <= pre_gcl_pat_candidates_o (4);
  pre_gcl_pat_candidates_i_n (6) <= pre_gcl_pat_candidates_o (5);
  pre_gcl_pat_candidates_i_n (7) <= pre_gcl_pat_candidates_o (6);

  pre_gcl_pat_candidates_i_p (0) <= pre_gcl_pat_candidates_o (1);
  pre_gcl_pat_candidates_i_p (1) <= pre_gcl_pat_candidates_o (2);
  pre_gcl_pat_candidates_i_p (2) <= pre_gcl_pat_candidates_o (3);
  pre_gcl_pat_candidates_i_p (3) <= pre_gcl_pat_candidates_o (4);
  pre_gcl_pat_candidates_i_p (4) <= pre_gcl_pat_candidates_o (5);
  pre_gcl_pat_candidates_i_p (5) <= pre_gcl_pat_candidates_o (6);
  pre_gcl_pat_candidates_i_p (6) <= pre_gcl_pat_candidates_o (7);
  pre_gcl_pat_candidates_i_n (7) <= (others => null_candidate);

  partition_gen : for I in 0 to 7 generate
    signal neighbor : partition_t := (others => (others => '0'));
  begin

    p0 : if (I > 0) generate
      neighbor <= sbits_i(I-1);
    end generate;

    partition_inst : entity work.partition
      generic map (
        NUM_SEGMENTS  => NUM_SEGMENTS,
        PARTITION_NUM => I)
      port map (

        clock => clock,
        dav_i => dav_i,
        dav_o => dav_o,

        -- primary layer
        partition_i => sbits_i(I),

        -- neighbor layer
        neighbor_i => neighbor,

        -- output candidates
        pat_candidates_o => pat_candidates(I),

        -- x-partition ghost cancellation
        pre_gcl_pat_candidates_o   => pre_gcl_pat_candidates_o(I),
        pre_gcl_pat_candidates_i_p => pre_gcl_pat_candidates_i_p(I),
        pre_gcl_pat_candidates_i_n => pre_gcl_pat_candidates_i_n(I),

        sump => open

        );
  end generate;

  --------------------------------------------------------------------------------
  -- s0 Pre-filter the candidates to limit to 1 segment in every N strips
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      pat_candidates_r <= pat_candidates;
    end if;
  end process;

  prtgen : for partition in 0 to 7 generate
  begin

    region : for region in 0 to 192/S0_REGION_SIZE-1 generate
      signal best     : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
      signal cand_slv : bus_array (S0_REGION_SIZE - 1 downto 0) (CANDIDATE_LENGTH-1 downto 0);
    begin

      cand_to_slv : for I in 0 to S0_REGION_SIZE-1 generate
      begin
        cand_slv(I) <= to_slv(pat_candidates_r(partition)(S0_REGION_SIZE*region + I));
      end generate;

      priority_encoder_inst : entity work.priority_encoder
        generic map (
          DAT_BITS   => CANDIDATE_LENGTH,
          QLT_BITS   => CANDIDATE_LENGTH - null_candidate.hash'length,
          WIDTH      => S0_REGION_SIZE,
          REG_INPUT  => true,
          REG_OUTPUT => true,
          REG_STAGES => 2
          )
        port map (
          clock => clock,
          dat_i => cand_slv,
          dat_o => best,
          adr_o => open
          );

      pat_candidates_s0(partition)(region) <= to_candidate(best);

    end generate;
  end generate;

  --------------------------------------------------------------------------------
  -- Mux candidates for input into s1 sorter
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      pat_candidates_mux <= pat_candidates_s0(phase_candidate_mux);
    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Sort from 192 segment candidates downto N outputs (e.g. 16) per partition
  --------------------------------------------------------------------------------

  mux : for I in 0 to MUX_FACTOR-1 generate
  begin

    segment_selector_1st : entity work.segment_selector
      generic map (NUM_OUTPUTS => NUM_SEGMENTS,
                   WIDTH       => PRT_WIDTH/S0_REGION_SIZE)
      port map (
        clock            => clock,
        pat_candidates_i => pat_candidates_mux,
        pat_candidates_o => selector_s1_o,
        sump             => open
        );

    process (clock) is
    begin
      if (rising_edge(clock)) then
        segs_r(phase_selector) <= selector_s1_o;

        if (phase_selector = 0) then
          segs_rr <= segs_r;
        end if;

      end if;
    end process;

  end generate;

  segs_cat <= segs_rr(7) & segs_rr(6) & segs_rr(5) & segs_rr(4) &
              segs_rr(3) & segs_rr(2) & segs_rr(1) & segs_rr(0);

  --------------------------------------------------------------------------------
  -- Sort from N segments per partition * 8 partitions downto N segments total
  --------------------------------------------------------------------------------
  -- FIXME: append the partition number before sorting
  --
  segment_selector_2nd : entity work.segment_selector
    generic map (NUM_OUTPUTS => NUM_SEGMENTS,
                 WIDTH       => NUM_SEGMENTS*8)
    port map (
      clock            => clock,
      pat_candidates_i => segs_cat,
      pat_candidates_o => segs_o,
      sump             => open
      );

end behavioral;
