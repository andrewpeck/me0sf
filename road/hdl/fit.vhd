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
    ly0   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly1   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly2   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly3   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly4   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly5   : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    valid : in std_logic_vector(N_LAYERS-1 downto 0) := (others => '1');

    intercept_o : out sfixed (B_INT_BITS-1 downto -B_FRAC_BITS);
    slope_o     : out sfixed (M_INT_BITS-1 downto -M_FRAC_BITS)
    );
end fit;

architecture behavioral of fit is

  -- Array (0 to N_LAYERS-1) of layer hits
  type ly_array_t is array (integer range 0 to N_LAYERS-1) of signed (STRIP_BITS-1 downto 0);
  signal ly : ly_array_t := (others => (others => '0'));

  --------------------------------------------------------------------------------
  -- delays
  --------------------------------------------------------------------------------

  type valid_array_t is array (integer range 0 to 3) of std_logic_vector(N_LAYERS-1 downto 0);
  signal valid_dly : valid_array_t := (others => (others => '1'));

  --------------------------------------------------------------------------------
  -- s1
  --------------------------------------------------------------------------------

  type cnt_array_t is array (integer range 0 to 6) of signed(LY_BITS-1 downto 0);  -- number of layers hit
  signal cnt : cnt_array_t := (others => (others => '1'));

  type x_sum_array_t is array (integer range 1 to 5) of signed (3+LY_BITS-1 downto 0);
  type y_sum_array_t is array (integer range 1 to 5) of signed (3+STRIP_BITS-1 downto 0);
  signal x_sum : x_sum_array_t := (others => (others => '0'));  -- sum (x_i); need extra 3 bits for sum
  signal y_sum : y_sum_array_t := (others => (others => '0'));  -- sum (y_i); need extra 3 bits for sum

  -- n * x
  type n_y_array_t is array (integer range 0 to N_LAYERS-1) of signed (4+STRIP_BITS-1 downto 0);
  type n_x_array_t is array (integer range 0 to N_LAYERS-1) of signed (7 downto 0);
  signal n_y : n_y_array_t := (others => (others => '0'));
  signal n_x : n_x_array_t := (others => (others => '1'));

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  type x_diff_array_t is array (integer range 0 to N_LAYERS-1) of signed (4+LY_BITS-1 downto 0);
  type y_diff_array_t is array (integer range 0 to N_LAYERS-1) of signed (4+STRIP_BITS-1 downto 0);
  signal y_diff : y_diff_array_t := (others => (others => '0'));  -- (y - mean(y))
  signal x_diff : x_diff_array_t := (others => (others => '1'));  -- (x - mean(x))

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  type product_array_t is array (integer range 0 to N_LAYERS-1) of signed (x_diff(0)'length + y_diff(0)'length-1 downto 0);
  type square_array_t is array (integer range 0 to N_LAYERS-1) of signed (2*x_diff(0)'length-1 downto 0);

  signal product : product_array_t := (others => (others => '0'));  -- (x - mean(x)) * (y - mean(y))
  signal square  : square_array_t  := (others => (others => '1'));  -- (x - mean(x)) ** 2

  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  -- sum ( (x - mean(x)) * (y - mean(y)) )
  signal product_sum : signed (17 downto 0)                 := (others => '0');
  -- sum ((x - mean(x)) ** 2)
  signal square_sum  : signed (3+square(0)'length-1 downto 0) := (others => '1');

  --------------------------------------------------------------------------------
  -- s5
  --------------------------------------------------------------------------------

  signal slope, slope_r : sfixed (19 downto -19) := (others => '0');

  --------------------------------------------------------------------------------
  -- s6
  --------------------------------------------------------------------------------

  signal intercept : sfixed (29 downto -23) := (others => '0');

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

  -- round zero up to one to prevent division by 0
  function zero_to_one(n : natural) return natural is
  begin
    if n = 0 then
      return 1;
    else
      return n;
    end if;
  end function zero_to_one;

begin

  valid_dly(0) <= valid;
  ly(0)        <= ly0;
  ly(1)        <= ly1;
  ly(2)        <= ly2;
  ly(3)        <= ly3;
  ly(4)        <= ly4;
  ly(5)        <= ly5;

  process (clock) is
  begin
    if (rising_edge(clock)) then

      --------------------------------------------------------------------------------
      -- delays
      --------------------------------------------------------------------------------

      valid_dly_map : for idly in 1 to valid_dly'length-1 loop
        valid_dly(idly) <= valid_dly(idly-1);
      end loop;

      --------------------------------------------------------------------------------
      -- s1
      --
      -- + count the # of layers hit
      -- + take the Σx, Σy
      -- + ff stage for registering the inputs
      --------------------------------------------------------------------------------

      cnt(0) <= to_signed(zero_to_one(count_ones(valid_dly(0))), LY_BITS);

      cnt_dly : for idly in 1 to cnt'length-1 loop
        cnt(idly) <= cnt(idly-1);
      end loop;

      -- Σx, Σy
      y_sum(1) <= resize(sum6(ly(0), ly(1), ly(2), ly(3), ly(4), ly(5), valid, y_sum(1)'length), y_sum(1)'length);
      x_sum(1) <= resize(sum6(x"0", x"1", x"2", x"3", x"4", x"5", valid, x_sum(1)'length), x_sum(1)'length);

      -- n * y_i
      -- n * x_i
      n_xy_dly : for I in 0 to N_LAYERS-1 loop
        n_y(I) <= cnt(0) * ly(I);
        n_x(I) <= cnt(0) * I;
      end loop;

      sum_dly : for I in 2 to x_sum'length-1 loop
        x_sum(I) <= x_sum(I-1);
        y_sum(I) <= y_sum(I-1);
      end loop;

      --------------------------------------------------------------------------------
      -- s2
      --------------------------------------------------------------------------------

      -- (n * x_i - Σx)
      -- (n * y_i - Σy)
      diff_loop : for I in 0 to N_LAYERS-1 loop
        x_diff(I) <= n_x(I) - x_sum(1);
        y_diff(I) <= n_y(I) - y_sum(1);
      end loop;

      --------------------------------------------------------------------------------
      -- s3
      --------------------------------------------------------------------------------

      -- (n*xi - Σx)(n*yi - Σy)
      -- (n*xi - Σx)^2
      s3_loop : for I in 0 to N_LAYERS-1 loop
        product(I) <= x_diff(I) * y_diff(I);
        square(I)  <= x_diff(I) * x_diff(I);
      end loop;

      --------------------------------------------------------------------------------
      -- s4
      --------------------------------------------------------------------------------

      -- Σ (n*xi - Σx)*(n*yi - Σy)
      product_sum <= sum6(product(0), product(1), product(2), product(3),
                          product(4), product(5), valid_dly(3), product_sum'length);
      -- Σ (n*xi - Σx)^2
      square_sum <= sum6(square(0), square(1), square(2), square(3),
                         square(4), square(5), valid_dly(3), square_sum'length);

      --------------------------------------------------------------------------------
      -- s5
      --------------------------------------------------------------------------------

      slope <= to_sfixed(product_sum, product_sum'length) /
               to_sfixed(square_sum, square_sum'length);

      --------------------------------------------------------------------------------
      -- s6 y= (mean(x) - slope*sum(y)) / n
      --------------------------------------------------------------------------------

      -- TODO: split into 2 stages?

      intercept <= (to_sfixed(y_sum(5), y_sum(5)'length) - slope *
                    to_sfixed(x_sum(5), x_sum(5)'length)) /
                   to_sfixed(cnt(5), cnt(5)'length);

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
