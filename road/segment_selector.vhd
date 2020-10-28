library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library work;
use work.pat_pkg.all;
use work.patterns.all;

library PoC;
use PoC.math.all;
use PoC.config.all;
use PoC.utils.all;
use PoC.vectors.all;
use PoC.components.all;

entity segment_selector is
  generic(
    PARTITION_WIDTH : natural := 7;
    NUM_SORTERS     : natural := 1;
    NUM_OUTPUTS     : natural := 16
    );
  port(

    clock : in std_logic;

    pat_candidates_i : in  candidate_list_t (PARTITION_WIDTH-1 downto 0);
    pat_candidates_o : out candidate_list_t (NUM_OUTPUTS-1 downto 0);

    sump : out std_logic

    );
end segment_selector;

architecture behavioral of segment_selector is
  constant SORTER_SIZE : natural := PARTITION_WIDTH / NUM_SORTERS;
  signal pat_sorted    : candidate_list_t (PARTITION_WIDTH-1 downto 0);
begin

  assert (PARTITION_WIDTH mod NUM_SORTERS = 0)
    report "for now can't handle a number width mod sorters != 0"
    severity error;

  --type    T_SLM                 is array(natural range <>, natural range <>) of std_logic;
  sorter_gen : for I in 0 to NUM_SORTERS-1 generate

    signal In_Data  : T_SLM(255 downto 0, CANDIDATE_LENGTH - 1 downto 0) := (others => (others => '0'));
    signal Out_Data : T_SLM(255 downto 0, CANDIDATE_LENGTH - 1 downto 0);
  begin

    data_assign : for J in 0 to SORTER_SIZE-1 generate
      signal candidate_i : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
      signal candidate_o : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
    begin

      candidate_i <= std_logic_vector(pat_candidates_i(I*SORTER_SIZE+J).hash) &
                     std_logic_vector(pat_candidates_i(I*SORTER_SIZE+J).cnt) &
                     std_logic_vector(pat_candidates_i(I*SORTER_SIZE+J).id);

      bitmap : for K in 0 to CANDIDATE_LENGTH-1 generate
        In_Data(J, K)  <= candidate_i(K);
        candidate_o(K) <= Out_Data(J, K);
      end generate;

      -- FIXME: do this with a function or something
      pat_sorted (I*SORTER_SIZE+J).id   <= unsigned(candidate_o(PAT_BITS-1 downto 0));
      pat_sorted (I*SORTER_SIZE+J).cnt  <= unsigned(candidate_o(CNT_BITS+PAT_BITS-1 downto PAT_BITS));
      pat_sorted (I*SORTER_SIZE+J).hash <= unsigned(candidate_o(HASH_BITS+CNT_BITS+PAT_BITS-1 downto CNT_BITS+PAT_BITS));

    end generate;

    sortnet_oddevenmergesort_1 : entity PoC.sortnet_oddevenmergesort

      generic map (
        INPUTS               => 256,                  -- input count
        KEY_BITS             => CNT_BITS + PAT_BITS,  -- the first KEY_BITS of In_Data are used as a sorting critera (key)
        DATA_BITS            => CANDIDATE_LENGTH,     -- inclusive KEY_BITS
        META_BITS            => 0,                    -- additional bits, not sorted but delayed as long as In_Data
        PIPELINE_STAGE_AFTER => 2,                    -- add a pipline stage after n sorting stages
        ADD_INPUT_REGISTERS  => false,                --
        ADD_OUTPUT_REGISTERS => true)                 --
      port map (
        clock     => clock,
        reset     => '0',
        inverse   => '0',                             -- sl
        in_valid  => '1',                             -- sl FIXME
        in_iskey  => '0',                             -- sl FIXME
        in_data   => in_data,                         -- slm (inputs x databits)
        in_meta   => (others => '0'),                 -- slv (meta bits)
        out_valid => open,                            -- sl
        out_iskey => open,                            -- sl
        out_data  => out_data,                        -- slm (inputs x databits)
        out_meta  => open                             -- slv (meta bits)
        );
  end generate;


  outloop : for I in 0 to NUM_OUTPUTS-1 generate
  begin
    pat_candidates_o(I) <= pat_sorted(I);
  end generate;

end behavioral;
