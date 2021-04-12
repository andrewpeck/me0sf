library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity segment_selector is
  generic(
    WIDTH       : natural := 0;
    NUM_OUTPUTS : natural := 0
    );
  port(

    clock : in std_logic;

    pat_candidates_i : in  candidate_list_t (WIDTH-1 downto 0);
    pat_candidates_o : out candidate_list_t (NUM_OUTPUTS-1 downto 0);

    sump : out std_logic

    );
end segment_selector;

architecture behavioral of segment_selector is

  signal candidate_sorted : candidate_list_t (WIDTH-1 downto 0);

  constant CLOG_WIDTH : natural := 2**integer(ceil(log2(real(WIDTH))));

  signal local_sump : std_logic_vector (WIDTH-1 downto 0);

  type cand_i_array_t is array (integer range 0 to WIDTH-1)
    of std_logic_vector(CANDIDATE_LENGTH-1 downto 0);
  type cand_o_array_t is array (integer range 0 to NUM_OUTPUTS-1)
    of std_logic_vector(CANDIDATE_LENGTH-1 downto 0);

  signal pat_candidates_i_slv : cand_i_array_t;
  signal pat_candidates_o_slv : cand_o_array_t;

begin

  assert WIDTH >= NUM_OUTPUTS
    report "Width of segment selector must be >= # of inputs" severity error;

  inloop : for I in 0 to CLOG_WIDTH-1 generate
  begin

    in_assign : if (I < WIDTH) generate
      pat_candidates_i_slv(I) <= pat_candidates_i(I);
    end generate;

    null_assign : if (I >= WIDTH) generate
      pat_candidates_i_slv(I) <= null_candidate;
    end generate;

  end generate;

  -- Select a subset of outputs from the sorter
  outloop : for I in 0 to NUM_OUTPUTS-1 generate
  begin
    pat_candidates_o(I) <= to_candidate(pat_candidates_o_slv(I));
  end generate;

  bitonic_sort_1 : entity work.bitonic_sort
    generic map (
      INPUTS               => CLOG_WIDTH,
      OUTPUTS              => NUM_OUTPUTS,
      DATA_BITS            => CANDIDATE_LENGTH,
      KEY_BITS             => CANDIDATE_LENGTH,  -- FIXME: only sort on some bits
      META_BITS            => 0,
      PIPELINE_STAGE_AFTER => 2,
      ADD_INPUT_REGISTERS  => false,
      ADD_OUTPUT_REGISTERS => true
      )
    port map (
      clock  => clock,
      reset  => '0',
      data_i => pat_candidates_i_slv,
      data_o => pat_candidates_o_slv,
      meta_i => (others => '0'),
      meta_o => open
      );

  sump <= '0';

end behavioral;
