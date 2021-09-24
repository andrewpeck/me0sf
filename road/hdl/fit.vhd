-- https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial.html
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial_29.html
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library ieee;
use ieee.fixed_pkg.all;

library work;
use work.reciprocal_pkg.all;

entity fit is
  generic(

    DIVIDER : string := "FP";

    N_LAYERS : natural := 6;

    N_STAGES : natural := 8;

    STRIP_BITS : natural := 6;

    -- slope
    --
    -- max slope is ~40 strips / 6 layers = ~7 so give it 4 bits
    M_INT_BITS  : natural := 4;
    M_FRAC_BITS : natural := 5;

    -- intercept
    --
    --intercepts are by construction centered around 0 with just some wander of
    -- a few strips around the center
    --
    -- it is too large right now because the fit is not being correctly
    -- constrained to the center
    --
    B_INT_BITS  : natural := 5;
    B_FRAC_BITS : natural := 6

    );
  port

    (

      clock   : in std_logic;
      ly0     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      ly1     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      ly2     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      ly3     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      ly4     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      ly5     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
      valid_i : in std_logic_vector(N_LAYERS-1 downto 0) := (others => '1');

      intercept_o : out sfixed (B_INT_BITS-1 downto -B_FRAC_BITS);
      slope_o     : out sfixed (M_INT_BITS-1 downto -M_FRAC_BITS)
      );
end fit;

architecture behavioral of fit is

  -- Array (0 to N_LAYERS-1) of layer hits
  type ly_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (STRIP_BITS-1 downto 0);
  signal ly : ly_array_t := (others => (others => '0'));

  --------------------------------------------------------------------------------
  -- delays
  --------------------------------------------------------------------------------

  type valid_array_t is array (integer range 0 to 3) of
    std_logic_vector(N_LAYERS-1 downto 0);
  signal valid : valid_array_t := (others => (others => '1'));

  --------------------------------------------------------------------------------
  -- s1
  --------------------------------------------------------------------------------

  -- add 1 just to make everything signed...
  constant LY_BITS : natural := 4;      -- 1 + integer(ceil(log2(real(N_LAYERS))));

  type cnt_array_t is array (integer range 0 to 7) of
    signed(LY_BITS-1 downto 0);         -- number of layers hit
  signal cnt : cnt_array_t := (others => to_signed(6, LY_BITS));

  constant NUM_EXTRA_SUM_BITS : natural
    := integer(ceil(log2(real(N_LAYERS))));

  type x_sum_array_t is array (integer range 1 to 5) of
    signed (NUM_EXTRA_SUM_BITS+LY_BITS-1 downto 0);
  type y_sum_array_t is array (integer range 1 to 6) of
    signed (NUM_EXTRA_SUM_BITS+STRIP_BITS-1 downto 0);
  signal x_sum : x_sum_array_t := (others => (others => '0'));  -- sum (x_i); need extra 3 bits for sum
  signal y_sum : y_sum_array_t := (others => (others => '0'));  -- sum (y_i); need extra 3 bits for sum

  -- n * x
  type n_y_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (cnt(1)'length+ly(0)'length-1 downto 0);
  type n_x_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (cnt(1)'length+NUM_EXTRA_SUM_BITS downto 0);
  signal n_y : n_y_array_t := (others => (others => '0'));
  signal n_x : n_x_array_t := (others => (others => '1'));

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  type x_diff_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (NUM_EXTRA_SUM_BITS+1+LY_BITS-1 downto 0);
  type y_diff_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (cnt(1)'length+ly(0)'length-1 downto 0);
  signal y_diff : y_diff_array_t := (others => (others => '0'));  -- (y - mean(y))
  signal x_diff : x_diff_array_t := (others => (others => '1'));  -- (x - mean(x))

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  type product_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (x_diff(0)'length + y_diff(0)'length-1 downto 0);
  type square_array_t is array (integer range 0 to N_LAYERS-1) of
    signed (2*x_diff(0)'length-1 downto 0);

  signal product : product_array_t := (others => (others => '0'));  -- (x - mean(x)) * (y - mean(y))
  signal square  : square_array_t  := (others => (others => '0'));  -- (x - mean(x)) ** 2

  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  -- Σ (n*xi - Σx)*(n*yi - Σy)
  --
  -- experimentally derived # of bits... should do something more comprehensive
  signal product_sum : signed (13 downto 0) := (others => '0');

  -- Σ (n*xi - Σx)^2
  --
  -- since x is just a set of numbers from 0-5, this number can't possibly be
  -- bigger than +630 so only 11 bits are needed to represent it (it could be a
  -- 10 bit unsigned, just just put the extra bit here to keep everything
  -- signed)
  --
  -- 630 = 6^2 * [ (0 - 2.5)^2 + (1 - 2.5)^2 + (2 - 2.5)^2 + (3 - 2.5)^2 + (4 - 2.5)^2 + (5 - 2.5)^2 ]
  --
  -- initialize to 1 to prevent a divide by zero in simulation
  --
  signal square_sum : integer range 0 to 630 := 1;
  --signal square_sum : signed (10 downto 0) := (others => '1');

  --------------------------------------------------------------------------------
  -- s5
  --------------------------------------------------------------------------------

  -- type slope_array_t is array (integer range 5 to 8) of
  --   sfixed (M_INT_BITS-1 downto - M_FRAC_BITS) := (others => '0');

  signal slope, slope_s6, slope_s7, slope_s8 :
    sfixed (M_INT_BITS-1 downto - M_FRAC_BITS) := (others => '0');

  --------------------------------------------------------------------------------
  -- s6
  --------------------------------------------------------------------------------

  signal slope_times_x : sfixed
    (M_INT_BITS + x_sum(1)'length-1 downto - M_FRAC_BITS+1) := (others => '0');

  --------------------------------------------------------------------------------
  -- s7
  --------------------------------------------------------------------------------

  signal y_minus_mb : sfixed
    (B_INT_BITS+3-1 downto - M_FRAC_BITS+1) := (others => '0');

  --------------------------------------------------------------------------------
  -- s8
  --------------------------------------------------------------------------------

  signal intercept : sfixed
    (B_INT_BITS-1 downto - B_FRAC_BITS) := (others => '0');

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
  function count_ones(slv : std_logic_vector) return integer is
    variable n_ones : integer := 0;
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

  --------------------------------------------------------------------------------
  -- s0
  --
  -- + asynchronous remap of signals into vectors
  -- + count_s0
  --------------------------------------------------------------------------------

  valid(0) <= valid_i;

  ly(0) <= ly0;
  ly(1) <= ly1;
  ly(2) <= ly2;
  ly(3) <= ly3;
  ly(4) <= ly4;
  ly(5) <= ly5;

  cnt(0) <= to_signed(zero_to_one(count_ones(valid_i)), LY_BITS);

  process (clock) is
  begin
    if (rising_edge(clock)) then

      --------------------------------------------------------------------------------
      -- delays
      --------------------------------------------------------------------------------

      valid_dly : for idly in 1 to valid'length-1 loop
        valid(idly) <= valid(idly-1);
      end loop;

      --------------------------------------------------------------------------------
      -- s1
      --
      -- + count the # of layers hit
      -- + take the Σx, Σy
      -- + ff stage for registering the inputs
      --------------------------------------------------------------------------------

      -- Σx, Σy

      y_sum(1) <= resize(sum6(ly(0), ly(1), ly(2), ly(3), ly(4), ly(5), valid_i,
                              y_sum(1)'length), y_sum(1)'length);

      x_sum(1) <= resize(sum6(x"0", x"1", x"2", x"3", x"4", x"5", valid_i,
                              x_sum(1)'length), x_sum(1)'length);

      -- n * y_i
      -- n * x_i
      n_xy_loop : for I in 0 to N_LAYERS-1 loop
        n_y(I) <= cnt(0) * ly(I);
        n_x(I) <= cnt(0) * to_signed(I, LY_BITS);
      end loop;

      -- delays

      cnt_dly : for idly in cnt'low+1 to cnt'high loop
        cnt(idly) <= cnt(idly-1);
      end loop;

      x_sum_dly : for I in x_sum'low+1 to x_sum'high loop
        x_sum(I) <= x_sum(I-1);
      end loop;

      y_sum_dly : for I in y_sum'low+1 to y_sum'high loop
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
      product_sum <= resize(
        sum6(product(0), product(1),
             product(2), product(3),
             product(4), product(5),
             valid(3), 18), product_sum'length);

      -- Σ (n*xi - Σx)^2
      square_sum <= to_integer(sum6(square(0), square(1),
                                    square(2), square(3),
                                    square(4), square(5),
                                    valid(3), 19));


      --------------------------------------------------------------------------------
      -- s5 slope= Σ (n*xi - Σx)*(n*yi - Σy) / Σ (n*xi - Σx)^2
      --------------------------------------------------------------------------------

      slope <= resize (to_sfixed(product_sum, product_sum'length) * reciprocal(square_sum), slope);
      -- slope <= resize (to_sfixed(product_sum, product_sum'length) /
      --                  to_sfixed(square_sum, square_sum'length), slope);

      --------------------------------------------------------------------------------
      -- s6 slope*Σx
      --------------------------------------------------------------------------------

      slope_times_x <= resize(slope * to_sfixed(x_sum(5), x_sum(5)'length), slope_times_x);
      slope_s6      <= slope;

      --------------------------------------------------------------------------------
      -- s7 Σy-mb = Σy - slope*Σx
      --------------------------------------------------------------------------------

      y_minus_mb <= resize((to_sfixed(y_sum(6), y_sum(6)'length) - slope_times_x), y_minus_mb);
      slope_s7   <= slope_s6;

      --------------------------------------------------------------------------------
      -- s8 b = (Σy - slope*Σx) / n
      --------------------------------------------------------------------------------

      intercept <= resize(y_minus_mb / to_sfixed(cnt(7), cnt(7)'length), intercept);
      slope_s8  <= slope_s7;

    end if;
  end process;

  -- div_gen : if (DIVIDER="IP") generate
  --   -- https://www.xilinx.com/html_docs/ip_docs/pru_files/div-gen.html
  --   U0 : div_gen_v5_1_17
  --     generic map (

  --       -- General Options
  --       C_XDEVICEFAMILY => "virtexuplus",
  --       C_HAS_ARESETN   => 0,
  --       C_HAS_ACLKEN    => 0,
  --       C_LATENCY       => 4,
  --       ALGORITHM_TYPE  => 3,             -- 3=High Radix

  --       -- Widths
  --       DIVISOR_WIDTH    => square_sum'length,
  --       DIVIDEND_WIDTH   => product_sum'length,
  --       FRACTIONAL_B     => 1,
  --       FRACTIONAL_WIDTH => 10,

  --       -- Signed vs. Unsigned
  --       SIGNED_B => 1,

  --       DIVCLK_SEL        => 1,           --
  --       C_HAS_DIV_BY_ZERO => 0,
  --       C_THROTTLE_SCHEME => 3,

  --       -- Misc AXIS Settings
  --       C_TLAST_RESOLUTION            => 0,
  --       C_HAS_S_AXIS_DIVISOR_TUSER    => 0,
  --       C_HAS_S_AXIS_DIVISOR_TLAST    => 0,
  --       C_S_AXIS_DIVISOR_TUSER_WIDTH  => 1,
  --       C_HAS_S_AXIS_DIVIDEND_TUSER   => 0,
  --       C_HAS_S_AXIS_DIVIDEND_TLAST   => 0,
  --       C_S_AXIS_DIVIDEND_TUSER_WIDTH => 1,
  --       C_M_AXIS_DOUT_TUSER_WIDTH     => 1,

  --       -- Data widths
  --       C_S_AXIS_DIVISOR_TDATA_WIDTH  => 16,
  --       C_S_AXIS_DIVIDEND_TDATA_WIDTH => 16,
  --       C_M_AXIS_DOUT_TDATA_WIDTH     => 32
  --       )
  --     port map (
  --       aclk                   => aclk,
  --       aclken                 => '1',
  --       aresetn                => '1',

  --       -- unused axis settings
  --       s_axis_divisor_tvalid  => '1',
  --       s_axis_dividend_tvalid => '1',
  --       s_axis_divisor_tready  => open,
  --       s_axis_dividend_tready => open,
  --       s_axis_divisor_tuser   => std_logic_vector(to_unsigned(0, 1)),
  --       s_axis_divisor_tlast   => '0',
  --       s_axis_dividend_tuser  => std_logic_vector(to_unsigned(0, 1)),
  --       s_axis_dividend_tlast  => '0',
  --       m_axis_dout_tready     => '0',
  --       m_axis_dout_tvalid     => open,

  --       -- unused axis settings
  --       s_axis_divisor_tdata   => square_sum,
  --       s_axis_dividend_tdata  => product_sum,
  --       m_axis_dout_tdata      => slope
  --       );
  -- end generate;

  -- truncation, don't need to register
  intercept_o <= intercept(B_INT_BITS-1 downto -B_FRAC_BITS);
  slope_o     <= slope_s8(M_INT_BITS-1 downto -M_FRAC_BITS);

end behavioral;
