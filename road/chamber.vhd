library work;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber is
  port(
    In_Valid : in std_logic;
    In_IsKey : in std_logic;

    clock : in  std_logic;
    phase : in  integer;
    sbits : in  chamber_t;
    segs  : out seg_array_t

    );
end chamber;

architecture behavioral of chamber is

  signal pat_candidates, pat_candidates_r : cand_array_t;

  signal pat_candidates_mux : candidate_list_t (PRT_WIDTH-1 downto 0);

  signal selector_o : candidate_list_t (NUM_SEGMENTS-1 downto 0);
  signal segs_r     : seg_array_t;

begin

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

  process (clock) is
  begin
    if (rising_edge(clock)) then
      pat_candidates_r   <= pat_candidates;
      pat_candidates_mux <= pat_candidates_r(phase);
    end if;
  end process;

  segment_selector_1 : entity work.segment_selector
    generic map (NUM_OUTPUTS => NUM_SEGMENTS,
                 WIDTH       => PRT_WIDTH)
    port map (
      clock            => clock,
      In_Valid         => In_Valid,
      In_IsKey         => In_IsKey,
      pat_candidates_i => pat_candidates_mux,
      pat_candidates_o => selector_o,
      sump             => open
      );

  process (clock) is
  begin
    if (rising_edge(clock)) then
      segs_r(phase) <= selector_o;

      if (phase = 0) then
        segs <= segs_r;
      end if;

    end if;
  end process;



end behavioral;
