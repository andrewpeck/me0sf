library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity pipelined_smult is
  generic(
    WIDTH_A : integer := 8;
    WIDTH_B : integer := 8
    );
  port(

    clock   : in  std_logic;
    input_a : in  signed (WIDTH_A-1 downto 0);
    input_b : in  signed (WIDTH_B-1 downto 0);
    output  : out signed (WIDTH_A+WIDTH_B-1 downto 0)
    );
end pipelined_smult;

architecture behavioral of pipelined_smult is

  constant A_HI_BITS : integer := WIDTH_A / 2;
  constant A_LO_BITS : integer := WIDTH_A / 2 + (WIDTH_A mod 2);

  constant B_HI_BITS : integer := WIDTH_B / 2;
  constant B_LO_BITS : integer := WIDTH_B / 2 + (WIDTH_B mod 2);

  signal a_hi : signed (A_HI_BITS-1 downto 0);
  signal a_lo : signed (1+A_LO_BITS-1 downto 0);

  signal b_hi : signed (B_HI_BITS-1 downto 0);
  signal b_lo : signed (1+B_LO_BITS-1 downto 0);

  signal hi_mult : signed (A_HI_BITS + B_HI_BITS - 1 downto 0);
  signal lo_mult : signed (A_LO_BITS + B_LO_BITS - 1 downto 0);

  signal m_a_hi_b_hi : signed (A_HI_BITS + B_HI_BITS - 1 downto 0);
  signal m_a_hi_b_lo : signed (A_HI_BITS + B_LO_BITS + 1 - 1 downto 0);
  signal m_a_lo_b_hi : signed (A_LO_BITS + B_HI_BITS + 1 - 1 downto 0);
  signal m_a_lo_b_lo : signed (A_LO_BITS + B_LO_BITS + 2 - 1 downto 0);

  signal sum, sum_t0, sum_t1, sum_t2, sum_t3 : signed (WIDTH_A + WIDTH_B - 1 downto 0);

begin

  assert false report "A_HI_BITS=" & integer'image(A_HI_BITS) severity note;
  assert false report "A_LO_BITS=" & integer'image(A_LO_BITS) severity note;
  assert false report "B_HI_BITS=" & integer'image(B_HI_BITS) severity note;
  assert false report "B_LO_BITS=" & integer'image(B_LO_BITS) severity note;

  -- split inputs into high and low bits
  a_hi <= signed(input_a(A_HI_BITS + A_LO_BITS - 1 downto A_LO_BITS));
  b_hi <= signed(input_b(B_HI_BITS + B_LO_BITS - 1 downto B_LO_BITS));

  a_lo <= signed('0' & input_a(A_LO_BITS - 1 downto 0));
  b_lo <= signed('0' & input_b(B_LO_BITS - 1 downto 0));

  m_a_hi_b_hi <= a_hi * b_hi;
  m_a_hi_b_lo <= a_hi * b_lo;
  m_a_lo_b_hi <= a_lo * b_hi;
  m_a_lo_b_lo <= a_lo * b_lo;

  p_mult : process(clock)
  begin
    if(rising_edge(clock)) then
      sum_t0 <= resize(m_a_hi_b_hi,sum_t0'length) sll (A_LO_BITS + B_LO_BITS);
      sum_t1 <= resize(m_a_hi_b_lo,sum_t1'length) sll (A_LO_BITS);
      sum_t2 <= resize(m_a_lo_b_hi,sum_t2'length) sll (B_LO_BITS);
      sum_t3 <= resize(m_a_lo_b_lo,sum_t3'length);
      sum    <= sum_t0 + sum_t1 + sum_t2 + sum_t3;
    end if;
  end process p_mult;

  output <= sum;

end behavioral;
