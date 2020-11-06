library work; use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber is
  generic (
    NUM_SEGMENTS : integer := 16;
    MUX_FACTOR   : integer := 1
    );
  port(
    In_Valid : in std_logic;
    In_IsKey : in std_logic;

    clock : in  std_logic;
    phase : in  integer;
    sbits : in  chamber_t;
    segs  : out candidate_list_t (NUM_SEGMENTS-1 downto 0)

    );
end chamber;

architecture behavioral of chamber is

  signal pat_candidates, pat_candidates_r : cand_array_t;
  signal pat_candidates_s0 : cand_array_s0_t;

  signal pat_candidates_mux : candidate_list_t (PRT_WIDTH/S0_REGION_SIZE-1 downto 0);

  signal segs_cat : candidate_list_t (NUM_SEGMENTS*8-1 downto 0);

  signal selector_s1_o : candidate_list_t (NUM_SEGMENTS-1 downto 0);
  signal selector_s2_o : candidate_list_t (NUM_SEGMENTS-1 downto 0);

  type seg_array_t is array (integer range 0 to 7) of candidate_list_t (NUM_SEGMENTS-1 downto 0);
  signal segs_r, segs_rr : seg_array_t;

begin

  --------------------------------------------------------------------------------
  -- Get 192 pattern unit candidates for each partition
  --------------------------------------------------------------------------------

  partition_gen : for I in 0 to 7 generate
    signal neighbor : partition_t := (others => (others => '0'));
  begin

    p0 : if (I > 0) generate
      neighbor <= sbits(I-1);
    end generate;

    partition_inst : entity work.partition
      generic map (PARTITION_NUM => I)

      port map (
        clock => clock,

        -- primary layer
        partition => sbits(I),

        -- neighbor layer
        neighbor => neighbor,

        -- output candidates
        pat_candidates_o => pat_candidates(I),

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
      begin

        process (clock) is
          variable best : candidate_t;
        begin
          if (rising_edge(clock)) then

            best := null_candidate;

            for I in S0_REGION_SIZE-1 downto 0 loop

              if (pat_candidates_r(partition)(S0_REGION_SIZE*region + I) > best) then
                best := pat_candidates_r(partition)(S0_REGION_SIZE*region + I);
              end if;
            end loop;

          end if;

          pat_candidates_s0(partition)(region) <= best;

        end process;

    end generate;
    end generate;

    --------------------------------------------------------------------------------
    -- Mux candidates for input into s1 sorter
    --------------------------------------------------------------------------------

    process (clock) is
    begin
      if (rising_edge(clock)) then
        pat_candidates_mux <= pat_candidates_s0(phase);
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
          In_Valid         => In_Valid,
          In_IsKey         => In_IsKey,
          pat_candidates_i => pat_candidates_mux,
          pat_candidates_o => selector_s1_o,
          sump             => open
          );

      process (clock) is
      begin
        if (rising_edge(clock)) then
          segs_r(phase) <= selector_s1_o;

          if (phase = 0) then
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

    segment_selector_2nd : entity work.segment_selector
      generic map (NUM_OUTPUTS => NUM_SEGMENTS,
                   WIDTH       => NUM_SEGMENTS*8)
      port map (
        clock            => clock,
        In_Valid         => In_Valid,
        In_IsKey         => In_IsKey,
        pat_candidates_i => segs_cat,
        pat_candidates_o => segs,
        sump             => open
        );


  end behavioral;
