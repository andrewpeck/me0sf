--------------------------------------------------------------------------------
-- bitonic sort
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

    KEY_BITS             : positive := 32;    -- the first KEY_BITS of In_Data are used as a sorting critera (key)
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

  --type t_slm is array(natural range <>, natural range <>) of std_logic;

  -- in case the # of inputs is not a power of two, round it up and zero pad...
  -- Xilinx should trim away the logic
  constant SORTER_SIZE : natural                                               := 2**integer(ceil(log2(real(INPUTS))));
  signal in_data_slm   : t_slm(SORTER_SIZE-1 downto 0, DATA_BITS - 1 downto 0) := (others => (others => '0'));
  signal out_data_slm  : t_slm(SORTER_SIZE-1 downto 0, DATA_BITS - 1 downto 0);

begin

  in_assign : for input in 0 to INPUTS-1 generate
  begin
    -- slv to Matrix Map
    in_bitmap : for bit in 0 to DATA_BITS-1 generate
      in_data_slm(input, bit) <= data_i(input*DATA_BITS+bit);
    end generate;
  end generate;

  out_assign : for output in 0 to OUTPUTS-1 generate
    -- from sorter Matrix Map
    out_bitmap : for bit in 0 to DATA_BITS-1 generate
      data_o(output*DATA_BITS+bit) <= out_data_slm(output, bit);
    end generate;
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
      inverse   => '0',                 -- sl
      in_valid  => '1',                 -- sl
      in_iskey  => '1',                 -- sl
      in_data   => in_data_slm,         -- slm (inputs x databits)
      in_meta   => meta_i,             -- slv (meta bits)
      out_valid => open,                -- sl
      out_iskey => open,                -- sl
      out_data  => out_data_slm,        -- slm (inputs x databits)
      out_meta  => meta_o             -- slv (meta bits)
      );

end behavioral;
