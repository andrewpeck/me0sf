library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity mult_sgn_12x12 is
  generic (
    WIDTH_A : integer := 14;
    WIDTH_B : integer := 13
  );
  port ( 
    clock    : in  std_logic;
    input_a  : in  signed(WIDTH_A-1 downto 0);  -- Variable width A
    input_b  : in  signed(WIDTH_B-1 downto 0);  -- Variable width B
    output   : out signed(WIDTH_A + WIDTH_B - 1 downto 0)  -- Output width adjusted based on inputs
  );
end mult_sgn_12x12;

architecture rtl of mult_sgn_12x12 is

  signal r_ma       : signed(WIDTH_A-1 downto 0);
  signal r_mb       : signed(WIDTH_B-1 downto 0);
  signal r_m_stage1 : signed(WIDTH_A + WIDTH_B - 1 downto 0);  -- Stage 1 pipeline register
  signal r_m_stage2 : signed(WIDTH_A + WIDTH_B - 1 downto 0);  -- Stage 2 pipeline register

begin

  output  <= r_m_stage2;  -- Output after the final pipeline stage

  p_mult : process(clock)
  begin
    if rising_edge(clock) then
      -- Stage 1: Register inputs
      r_ma <= input_a;
      r_mb <= input_b;
      
      -- Stage 2: Multiply and register result
      r_m_stage1 <= r_ma * r_mb;
      
      -- Stage 3: Register final result for output
      r_m_stage2 <= r_m_stage1;
    end if;
  end process p_mult;

end rtl;