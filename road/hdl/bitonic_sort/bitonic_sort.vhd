--------------------------------------------------------------------------------
-- bitonic sort
--
-- Lightweight wrapper around PoC bitonic sort core..
-- converts from their custom 'slm' type to a std_logic_vector for ease of use
--
-- Also handles zero padding the input since the sorter only accepts powers of two
--
--------------------------------------------------------------------------------

use work.bitonic_sort_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity bitonic_sort is
  generic(
    INPUTS  : positive := 32;           -- input  count
    OUTPUTS : positive := 32;           -- output count

    SORTER : string := "KAWAZOME";      -- POC or KAWAZOME

    KEY_BITS             : positive := 32;    -- the first KEY_BITS of In_Data are used as a sorting critera (key)
    IGNORE_BITS          : natural  := 0;     --
    DATA_BITS            : positive := 32;    -- inclusive KEY_BITS
    META_BITS            : natural  := 0;     -- additional bits, not sorted but delayed as long as In_Data
    PIPELINE_STAGE_AFTER : natural  := 2;     -- add a pipline stage after n sorting stages
    ADD_INPUT_REGISTERS  : boolean  := true;  --
    ADD_OUTPUT_REGISTERS : boolean  := true   --
    );
  port(
    clock  : in  std_logic;
    reset  : in  std_logic;
    data_i : in  std_logic_vector (INPUTS *DATA_BITS-1 downto 0);
    data_o : out std_logic_vector (OUTPUTS*DATA_BITS-1 downto 0);
    meta_i : in  std_logic_vector (META_BITS-1 downto 0);
    meta_o : out std_logic_vector (META_BITS-1 downto 0)
    );
end bitonic_sort;

architecture behavioral of bitonic_sort is

  -- in case the # of inputs is not a power of two, round it up and zero pad...
  -- Xilinx should trim away the logic
  constant SORTER_SIZE : natural := 2**integer(ceil(log2(real(INPUTS))));
begin

  --------------------------------------------------------------------------------
  -- POC
  --------------------------------------------------------------------------------

  poc_gen : if (SORTER = "POC") generate
    -- types required by the sorter code...
    signal in_data_slm  : t_slm(SORTER_SIZE-1 downto 0, DATA_BITS - 1 downto 0) := (others => (others => '0'));
    signal out_data_slm : t_slm(SORTER_SIZE-1 downto 0, DATA_BITS - 1 downto 0);
    signal out_data_slv : std_logic_vector (INPUTS *DATA_BITS-1 downto 0);

  --type t_slm is array(natural range <>, natural range <>) of std_logic;
  begin

    in_data_slm  <= to_slm(data_i, INPUTS, DATA_BITS);
    out_data_slv <= to_slv(out_data_slm);

    out_reverse : for I in 0 to OUTPUTS-1 generate
      constant J : natural := INPUTS-I-1;
    begin
      data_o((I+1)*DATA_BITS-1 downto (I)*DATA_BITS)
        <= out_data_slv((J+1)*DATA_BITS-1 downto (J)*DATA_BITS);
    end generate;

    sortnet_inst : entity work.sortnet_bitonicsort
      generic map (
        INPUTS               => SORTER_SIZE,
        KEY_BITS             => KEY_BITS,
        DATA_BITS            => DATA_BITS,
        META_BITS            => META_BITS,
        PIPELINE_STAGE_AFTER => PIPELINE_STAGE_AFTER,
        ADD_INPUT_REGISTERS  => ADD_INPUT_REGISTERS,
        ADD_OUTPUT_REGISTERS => ADD_OUTPUT_REGISTERS
        )
      port map (
        clock     => clock,
        reset     => reset,
        inverse   => '0',               -- sl
        in_valid  => '1',               -- sl
        in_iskey  => '1',               -- sl
        in_data   => in_data_slm,       -- slm (inputs x databits)
        in_meta   => meta_i,            -- slv (meta bits)
        out_valid => open,              -- sl
        out_iskey => open,              -- sl
        out_data  => out_data_slm,      -- slm (inputs x databits)
        out_meta  => meta_o             -- slv (meta bits)
        );
  end generate;

  --------------------------------------------------------------------------------
  -- Kawazome
  --------------------------------------------------------------------------------

  kawazome_gen : if (SORTER = "KAWAZOME") generate
    signal data_sorted : std_logic_vector (data_i'range);
  begin
    bitonic_sort_inst : entity work.Bitonic_Sorter
      generic map (
        WORDS       => INPUTS,
        WORD_BITS   => DATA_BITS,
        COMP_HIGH   => KEY_BITS-1,      -- This is used directly as a COMP_HIGH downto 0, so you must factor in the -1
        COMP_LOW    => IGNORE_BITS,
        INFO_BITS   => META_BITS,
        REGSTAGES   => PIPELINE_STAGE_AFTER,
        REG_OUTPUTS => ADD_OUTPUT_REGISTERS,
        REG_MERGES  => false
        )
      port map (
        CLK    => clock,
        RST    => '0',                  -- async reset
        CLR    => '0',                  -- sync clr
        I_SORT => '1',                  -- set to 0 and the module won't sort
        I_UP   => '0',                  -- set to 0 to prefer the highest number on the lowest input
        I_DATA => data_i,
        O_DATA => data_sorted,
        O_SORT => open,
        O_UP   => open,
        I_INFO => meta_i,
        O_INFO => meta_o
        );

    data_o <= data_sorted(data_o'range);

  end generate;

end behavioral;
