-- https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial.html
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial_29.html
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library ieee;
use ieee.fixed_pkg.all;

entity fit is
  generic(
    N_LAYERS : natural := 6;

    STRIP_BITS : natural := 6;
    LY_BITS    : natural := 4;

    -- slope
    M_INT_BITS  : natural := 4;
    M_FRAC_BITS : natural := 6;

    -- intercept
    B_INT_BITS  : natural := 6;
    B_FRAC_BITS : natural := 6

    );
  port(

    clock : in std_logic;
    ly0   : in signed (STRIP_BITS-1 downto 0);
    ly1   : in signed (STRIP_BITS-1 downto 0);
    ly2   : in signed (STRIP_BITS-1 downto 0);
    ly3   : in signed (STRIP_BITS-1 downto 0);
    ly4   : in signed (STRIP_BITS-1 downto 0);
    ly5   : in signed (STRIP_BITS-1 downto 0);
    valid : in std_logic_vector(5 downto 0);

    intercept_o : out sfixed (B_INT_BITS-1 downto -B_FRAC_BITS);
    slope_o     : out sfixed (M_INT_BITS-1 downto -M_FRAC_BITS)
    );
end fit;

architecture behavioral of fit is

  --------------------------------------------------------------------------------
  -- delays
  --------------------------------------------------------------------------------

  signal valid_s1 : std_logic_vector (N_LAYERS-1 downto 0) := (others => '0');
  signal valid_s2 : std_logic_vector (N_LAYERS-1 downto 0) := (others => '0');
  signal valid_s3 : std_logic_vector (N_LAYERS-1 downto 0) := (others => '0');
  signal valid_s4 : std_logic_vector (N_LAYERS-1 downto 0) := (others => '0');
  signal valid_s5 : std_logic_vector (N_LAYERS-1 downto 0) := (others => '0');

  signal ly0_s1, ly1_s1, ly2_s1, ly3_s1, ly4_s1, ly5_s1 : signed (STRIP_BITS-1 downto 0);
  signal ly0_s2, ly1_s2, ly2_s2, ly3_s2, ly4_s2, ly5_s2 : signed (STRIP_BITS-1 downto 0);

  --------------------------------------------------------------------------------
  -- s1
  --------------------------------------------------------------------------------

  signal cnt, cnt_s1, cnt_s2, cnt_s3, cnt_s4, cnt_s5, cnt_s6 : signed (LY_BITS-1 downto 0);  -- number of layers hit

  signal x_sum, x_sum_s2, x_sum_s3, x_sum_s4, x_sum_s5, x_sum_s6, x_sum_s7 : signed (3+LY_BITS-1 downto 0);     -- sum (x_i); need extra 3 bits for sum
  signal y_sum, y_sum_s2, y_sum_s3, y_sum_s4, y_sum_s5, y_sum_s6, y_sum_s7 : signed (3+STRIP_BITS-1 downto 0);  -- sum (y_i); need extra 3 bits for sum

  signal n_y0, n_y1, n_y2, n_y3, n_y4, n_y5 : signed (4+STRIP_BITS-1 downto 0);
  signal n_x0, n_x1, n_x2, n_x3, n_x4, n_x5 : signed (7 downto 0);

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  -- (x - mean(x))
  signal x_diff0, x_diff1, x_diff2, x_diff3, x_diff4, x_diff5 : signed (4+LY_BITS-1 downto 0);  -- layer 0-5
  signal y_diff0, y_diff1, y_diff2, y_diff3, y_diff4, y_diff5 : signed (4+STRIP_BITS-1 downto 0);

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  -- (x - mean(x)) * (y - mean(y))
  signal product0, product1, product2, product3, product4, product5 : signed (x_diff0'length + y_diff0'length-1 downto 0);
  -- (x - mean(x)) ** 2
  signal square0, square1, square2, square3, square4, square5       : signed (2*x_diff0'length-1 downto 0);

  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  -- sum ( (x - mean(x)) * (y - mean(y)) )
  signal product_sum : signed (17 downto 0);
  -- sum ((x - mean(x)) ** 2)
  signal square_sum  : signed (3+square0'length-1 downto 0);

  --------------------------------------------------------------------------------
  -- s5
  --------------------------------------------------------------------------------

  signal slope, slope_r : sfixed (19 downto -19);

  --------------------------------------------------------------------------------
  -- s6
  --------------------------------------------------------------------------------

  signal intercept : sfixed (29 downto -23);

  --------------------------------------------------------------------------------
  -- functions
  --------------------------------------------------------------------------------

  -- sum 6 signed numbers with an enable for each number
  function sum6 (p0    : signed;
                 p1    : signed;
                 p2    : signed;
                 p3    : signed;
                 p4    : signed;
                 p5    : signed;
                 en    : std_logic_vector (5 downto 0);
                 nbits : natural)
    return signed is
    variable result : signed (nbits-1 downto 0);
  begin
    result := (others => '0');
    if ('1' = en(0)) then
      result := result + p0;
    end if;
    if ('1' = en(1)) then
      result := result + p1;
    end if;
    if ('1' = en(2)) then
      result := result + p2;
    end if;
    if ('1' = en(3)) then
      result := result + p3;
    end if;
    if ('1' = en(4)) then
      result := result + p4;
    end if;
    if ('1' = en(5)) then
      result := result + p5;
    end if;
    return result;
  end;

  -- returns the count of the the number of set ones in a SLV
  function count_ones(slv : std_logic_vector) return natural is
    variable n_ones : natural := 0;
  begin
    for i in slv'range loop
      if slv(i) = '1' then
        n_ones := n_ones + 1;
      end if;
    end loop;
    return n_ones;
  end function count_ones;

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then

      --------------------------------------------------------------------------------
      --
      --------------------------------------------------------------------------------

      valid_s1 <= valid;
      valid_s2 <= valid_s1;
      valid_s3 <= valid_s2;
      valid_s4 <= valid_s3;
      valid_s5 <= valid_s4;


      ly0_s2 <= ly0_s1;
      ly1_s2 <= ly1_s1;
      ly2_s2 <= ly2_s1;
      ly3_s2 <= ly3_s1;
      ly4_s2 <= ly4_s1;
      ly5_s2 <= ly5_s1;

      -- ly0_s3 <= ly0_s2;
      -- ly1_s3 <= ly1_s2;
      -- ly2_s3 <= ly2_s2;
      -- ly3_s3 <= ly3_s2;
      -- ly4_s3 <= ly4_s2;
      -- ly5_s3 <= ly5_s2;

      --------------------------------------------------------------------------------
      -- s1
      --
      -- + count the # of layers hit
      -- + take the Σx, Σy
      -- + ff stage for registering the inputs
      --------------------------------------------------------------------------------

      cnt    <= to_signed(count_ones(valid), LY_BITS);
      cnt_s1 <= cnt;
      cnt_s2 <= cnt_s1;
      cnt_s3 <= cnt_s2;
      cnt_s4 <= cnt_s3;
      cnt_s5 <= cnt_s4;
      cnt_s6 <= cnt_s5;

      ly0_s1 <= ly0;
      ly1_s1 <= ly1;
      ly2_s1 <= ly2;
      ly3_s1 <= ly3;
      ly4_s1 <= ly4;
      ly5_s1 <= ly5;

      -- Σx, Σy
      y_sum <= resize(sum6(ly0, ly1, ly2, ly3, ly4, ly5, valid, y_sum'length), y_sum'length);
      x_sum <= resize(sum6(x"0", x"1", x"2", x"3", x"4", x"5", valid, x_sum'length), x_sum'length);

      -- n * y_i
      n_y0 <= cnt * ly0;
      n_y1 <= cnt * ly1;
      n_y2 <= cnt * ly2;
      n_y3 <= cnt * ly3;
      n_y4 <= cnt * ly4;
      n_y5 <= cnt * ly5;

      -- n * x_i
      n_x0 <= cnt * 0;
      n_x1 <= cnt * 1;
      n_x2 <= cnt * 2;
      n_x3 <= cnt * 3;
      n_x4 <= cnt * 4;
      n_x5 <= cnt * 5;

      -- delays
      x_sum_s2 <= x_sum;
      x_sum_s3 <= x_sum_s2;
      x_sum_s4 <= x_sum_s3;
      x_sum_s5 <= x_sum_s4;
      x_sum_s6 <= x_sum_s5;
      x_sum_s7 <= x_sum_s6;

      y_sum_s2 <= y_sum;
      y_sum_s3 <= y_sum_s2;
      y_sum_s4 <= y_sum_s3;
      y_sum_s5 <= y_sum_s4;
      y_sum_s6 <= y_sum_s5;
      y_sum_s7 <= y_sum_s6;

      --------------------------------------------------------------------------------
      -- s2
      --------------------------------------------------------------------------------

      -- (n * x_i - Σx)
      x_diff0 <= n_x0 - x_sum;
      x_diff1 <= n_x1 - x_sum;
      x_diff2 <= n_x2 - x_sum;
      x_diff3 <= n_x3 - x_sum;
      x_diff4 <= n_x4 - x_sum;
      x_diff5 <= n_x5 - x_sum;

      -- (n * y_i - Σy)
      y_diff0 <= n_y0 - y_sum;
      y_diff1 <= n_y1 - y_sum;
      y_diff2 <= n_y2 - y_sum;
      y_diff3 <= n_y3 - y_sum;
      y_diff4 <= n_y4 - y_sum;
      y_diff5 <= n_y5 - y_sum;

      --------------------------------------------------------------------------------
      -- s3
      --------------------------------------------------------------------------------

      -- (n*xi - Σx)(n*yi - Σy)
      product0 <= x_diff0 * y_diff0;
      product1 <= x_diff1 * y_diff1;
      product2 <= x_diff2 * y_diff2;
      product3 <= x_diff3 * y_diff3;
      product4 <= x_diff4 * y_diff4;
      product5 <= x_diff5 * y_diff5;

      -- (n*xi - Σx)^2
      square0 <= x_diff0 * x_diff0;
      square1 <= x_diff1 * x_diff1;
      square2 <= x_diff2 * x_diff2;
      square3 <= x_diff3 * x_diff3;
      square4 <= x_diff4 * x_diff4;
      square5 <= x_diff5 * x_diff5;

      --------------------------------------------------------------------------------
      -- s4
      --------------------------------------------------------------------------------

      -- Σ (n*xi - Σx)*(n*yi - Σy)
      product_sum <= sum6(product0, product1, product2, product3,
                          product4, product5, valid_s3, product_sum'length);
      -- Σ (n*xi - Σx)^2
      square_sum <= sum6(square0, square1, square2, square3,
                         square4, square5, valid_s3, square_sum'length);

      --------------------------------------------------------------------------------
      -- s5
      --------------------------------------------------------------------------------

      slope <= to_sfixed(product_sum, product_sum'length) /
               to_sfixed(square_sum, square_sum'length);

      --------------------------------------------------------------------------------
      -- s6 y= (mean(x) - slope*sum(y)) / n
      --------------------------------------------------------------------------------

      -- TODO: split into 2 stages?

      intercept <= (to_sfixed(y_sum_s5, y_sum_s5'length) - slope *
                    to_sfixed(x_sum_s5, x_sum_s5'length)) /
                   to_sfixed(cnt_s5, cnt_s5'length);

      slope_r <= slope;

      --------------------------------------------------------------------------------
      -- s7
      --------------------------------------------------------------------------------


    end if;
  end process;

  -- truncation, don't need to register
  intercept_o <= intercept(B_INT_BITS-1 downto -B_FRAC_BITS);
  slope_o     <= slope_r(M_INT_BITS-1 downto -M_FRAC_BITS);

end behavioral;
