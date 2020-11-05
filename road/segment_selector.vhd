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
    WIDTH       : natural := 3;
    NUM_OUTPUTS : natural := 1
    );
  port(

    clock : in std_logic;

    pat_candidates_i : in  candidate_list_t (WIDTH-1 downto 0);
    pat_candidates_o : out candidate_list_t (NUM_OUTPUTS-1 downto 0);

    sump : out std_logic

    );
end segment_selector;

architecture behavioral of segment_selector is
  constant SORTER_SIZE    : natural := 16;
  signal candidate_sorted : candidate_list_t (WIDTH-1 downto 0);
  --type    T_SLM                 is array(natural range <>, natural range <>) of std_logic;

  signal In_Data  : T_SLM(15 downto 0, CANDIDATE_LENGTH - 1 downto 0) := (others => (others => '0'));
  signal Out_Data : T_SLM(15 downto 0, CANDIDATE_LENGTH - 1 downto 0);

  signal local_sump : std_logic_vector (WIDTH-1 downto 0);

  attribute DONT_TOUCH : string;
  --attribute DONT_TOUCH of sortnet_oddevenmergesort_1 : label is "true";

begin

  sortnet_oddevenmergesort_1 : entity PoC.sortnet_oddevenmergesort

    generic map (
      INPUTS               => 16,                -- input count -- FIXME: size should be WIDTH up to the next power of 2
      KEY_BITS             => CANDIDATE_LENGTH,  --CNT_BITS + PID_BITS,  -- the first KEY_BITS of In_Data are used as a sorting critera (key)
      DATA_BITS            => CANDIDATE_LENGTH,  -- inclusive KEY_BITS
      META_BITS            => 0,                 -- additional bits, not sorted but delayed as long as In_Data
      PIPELINE_STAGE_AFTER => 2,                 -- add a pipline stage after n sorting stages
      ADD_INPUT_REGISTERS  => false,             --
      ADD_OUTPUT_REGISTERS => true)              --
    port map (
      clock     => clock,
      reset     => '0',
      inverse   => '0',                          -- sl
      in_valid  => '1',                          -- sl FIXME
      in_iskey  => '0',                          -- sl FIXME
      in_data   => in_data,                      -- slm (inputs x databits)
      in_meta   => (others => '0'),              -- slv (meta bits)
      out_valid => open,                         -- sl
      out_iskey => open,                         -- sl
      out_data  => out_data,                     -- slm (inputs x databits)
      out_meta  => open                          -- slv (meta bits)
      );

  --------------------------------------------------------------------------------
  -- Assign data into matrix for merge sort
  --------------------------------------------------------------------------------

  data_assign : for strip in 0 to WIDTH-1 generate

    -- temporary intermediate slvs to map to/from records to matrix, i.e.
    -- record <--> slv <--> matrix
    signal candidate_i : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
    signal candidate_o : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);

  begin

    local_sump (strip) <= xor_reduce(candidate_i) xor xor_reduce(candidate_o);

    -- input to slv
    candidate_i <= to_slv (pat_candidates_i(strip));

    -- slv to Matrix Map
    in_bitmap : for bit in 0 to CANDIDATE_LENGTH-1 generate
      In_Data(strip, bit) <= candidate_i(bit);
    end generate;

    -- from sorter Matrix Map
    out_bitmap : for bit in 0 to CANDIDATE_LENGTH-1 generate
      candidate_o(bit) <= Out_Data(strip, bit);
    end generate;

    -- from slv to pat
    candidate_sorted (strip) <= to_candidate (candidate_o);

  end generate;

  -- Select a subset of outputs from the sorter
  outloop : for I in 0 to NUM_OUTPUTS-1 generate
  begin
    pat_candidates_o(I) <= candidate_sorted(I);
  end generate;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      sump <= xor_reduce(local_sump);
    end if;
  end process;

end behavioral;
