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
  generic (

    N_LAYERS : natural := 6;

    N_STAGES : natural := 10;

    STRIP_BITS : natural := 6;

    -- slope
    --
    -- max slope is ~40 strips / 6 layers = ~7 so give it 4 bits
    M_INT_BITS  : natural := 4;
    M_FRAC_BITS : natural := 6;

    -- intercept
    --
    --intercepts are by construction centered around 0 with just some wander of
    -- a few strips around the center
    --
    -- it is too large right now because the fit is not being correctly
    -- constrained to the center
    --
    B_INT_BITS  : natural := 6;
    B_FRAC_BITS : natural := 6

    );

  port (
    clock   : in std_logic;
    ly0     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly1     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly2     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly3     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly4     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    ly5     : in signed (STRIP_BITS-1 downto 0)        := (others => '0');
    valid_i : in std_logic_vector(N_LAYERS-1 downto 0) := (others => '1');

    strip_o     : out sfixed (B_INT_BITS-1 downto -B_FRAC_BITS);
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

  type cnt_array_t is array (integer range 0 to 7) of
    integer range 0 to 6;               -- number of layers hit
  signal cnt : cnt_array_t := (others => 6);

  type x_sum_array_t is array (integer range 1 to 5) of integer range 0 to 15;  -- (min=0, max=0+1+2+3+4+5)
  signal x_sum : x_sum_array_t := (others => 0);                                -- sum (x_i)

  -- since tracks are designed to go through the center, the positive and negative
  -- will mostly offset and the sum will mostly be a small number, so the range can be restricted
  -- the simulator will barf if we exceed it
  type y_sum_array_t is array (integer range 1 to 6) of integer range -63 to 63;
  signal y_sum : y_sum_array_t := (others => 0);  -- sum (y_i)

  -- n * x
  type n_x_array_t is array (integer range 0 to N_LAYERS-1) of integer range 0 to 5*6;  -- ly=5 * cnt=6
  type n_y_array_t is array (integer range 0 to N_LAYERS-1) of integer range -255 to 255;
  signal n_x : n_x_array_t := (others => 1);
  signal n_y : n_y_array_t := (others => 0);

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  type x_diff_array_t is array (integer range 0 to N_LAYERS-1) of integer range -15 to 15;

  type y_diff_array_t is array (integer range 0 to N_LAYERS-1) of integer range -127 to 127;
  signal x_diff : x_diff_array_t := (others => 1);  -- (x - mean(x))
  signal y_diff : y_diff_array_t := (others => 0);  -- (y - mean(y))

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  type square_array_t is array (integer range 0 to N_LAYERS-1) of integer range 0 to 255;
  type product_array_t is array (integer range 0 to N_LAYERS-1) of integer range -4095 to 4095;

  signal product : product_array_t := (others => 0);  -- (x - mean(x)) * (y - mean(y))
  signal square  : square_array_t  := (others => 0);  -- (x - mean(x)) ** 2

  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  -- Σ (n*xi - Σx)*(n*yi - Σy)
  --
  signal product_sum : integer range -8191 to 8191 := 0;

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
  signal square_sum_reciprocal : sfixed (1 downto -13);

  --------------------------------------------------------------------------------
  -- s5
  --------------------------------------------------------------------------------

  -- type slope_array_t is array (integer range 5 to 8) of
  --   sfixed (M_INT_BITS-1 downto - M_FRAC_BITS) := (others => '0');

  signal slope, slope_s6, slope_s7, slope_s8, slope_s9 :
    sfixed (M_INT_BITS-1 downto - (M_FRAC_BITS)) := (others => '0');

  signal slope_s8_x5 :
    sfixed (M_INT_BITS+3-1 downto -(M_FRAC_BITS-4));

  signal slope_s9_2p5 :
    sfixed (M_INT_BITS+2-1 downto -(M_FRAC_BITS-4));

  --------------------------------------------------------------------------------
  -- s6
  --------------------------------------------------------------------------------

  signal slope_times_x : sfixed
    (4+M_INT_BITS-1 downto -M_FRAC_BITS-1) := (others => '0');

  --------------------------------------------------------------------------------
  -- s7
  --------------------------------------------------------------------------------

  signal y_minus_mb : sfixed
    (3+B_INT_BITS-1 downto -(M_FRAC_BITS+1)) := (others => '0');

  --------------------------------------------------------------------------------
  -- s8
  --------------------------------------------------------------------------------

  constant MULT_RECIP_FRACB : integer := 14;

  signal intercept_signed : signed
    (y_minus_mb'length+MULT_RECIP_FRACB+2-1 downto 0) := (others => '0');

  constant intercept_mult_decb : integer := 1+M_FRAC_BITS+MULT_RECIP_FRACB;

  signal intercept_smult : sfixed
    (intercept_signed'length-intercept_mult_decb-1
     downto -(intercept_mult_decb)) := (others => '0');

  signal intercept : sfixed
    (B_INT_BITS-1 downto - B_FRAC_BITS) := (others => '0');

  --------------------------------------------------------------------------------
  -- functions
  --------------------------------------------------------------------------------

  -- sum 6 signed numbers with an enable for each number
  function sum6 (p0, p1, p2, p3, p4, p5 : integer;
                 en                     : std_logic_vector (5 downto 0))
    return integer is
    variable result : integer;
  begin
    result := 0;
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

  cnt(0) <= zero_to_one(count_ones(valid_i));

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

      y_sum(1) <= sum6(to_integer(ly(0)), to_integer(ly(1)), to_integer(ly(2)),
                       to_integer(ly(3)), to_integer(ly(4)), to_integer(ly(5)), valid_i);
      x_sum(1) <= sum6(0, 1, 2, 3, 4, 5, valid_i);

      -- n * y_i
      -- n * x_i
      n_xy_loop : for I in 0 to N_LAYERS-1 loop
        n_y(I) <= cnt(0) * to_integer(ly(I));
        n_x(I) <= cnt(0) * I;
      end loop;

      -- delays

      cnt(1) <= cnt(0);
      cnt(2) <= cnt(1);
      cnt(3) <= cnt(2);
      cnt(4) <= cnt(3);
      cnt(5) <= cnt(4);
      cnt(6) <= cnt(5);
      cnt(7) <= cnt(6);
      -- cnt_dly : for idly in 2 to 7 loop
      --   cnt(idly) <= cnt(idly-1);
      -- end loop;

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
      product_sum <= sum6(product(0), product(1), product(2),
                          product(3), product(4), product(5), valid(3));

      -- Σ (n*xi - Σx)^2
      square_sum_reciprocal <= reciprocal (
        sum6(square(0), square(1), square(2),
             square(3), square(4), square(5), valid(3)),
        -square_sum_reciprocal'low);


      --------------------------------------------------------------------------------
      -- s5 slope= Σ (n*xi - Σx)*(n*yi - Σy) / Σ (n*xi - Σx)^2
      --------------------------------------------------------------------------------

      -- FIXME: pull the number of bits from the integer (somehow)
      -- need 13 bits to represent the number 8192
      slope <= resize (to_sfixed(product_sum, 13) * square_sum_reciprocal, slope);

      --------------------------------------------------------------------------------
      -- s6 slope*Σx
      --------------------------------------------------------------------------------

      -- FIXME: pull the number of bits from the integer (somehow)
      slope_times_x <= resize(slope * to_sfixed(x_sum(5), 5), slope_times_x);
      slope_s6      <= slope;

      --------------------------------------------------------------------------------
      -- s7 Σy-mb = Σy - slope*Σx
      --------------------------------------------------------------------------------

      -- 13 = number of bits needed
      y_minus_mb <= resize((to_sfixed(y_sum(6), 7) - slope_times_x), y_minus_mb);
      slope_s7   <= slope_s6;

      --------------------------------------------------------------------------------
      -- s8 b = (Σy - slope*Σx) / n
      --------------------------------------------------------------------------------

      -- (multiplication pipelined below)
      slope_s8 <= slope_s7;
      slope_s8_x5 <= resize(slope_s7*5.0, slope_s8_x5);

      --------------------------------------------------------------------------------
      -- s9 (pipelined multiplier) takes 2 clock cycles
      --------------------------------------------------------------------------------

      slope_s9     <= slope_s8;
      slope_s9_2p5 <= resize(slope_s8_x5/2.0, slope_s9_2p5);

      --------------------------------------------------------------------------------
      -- s9 coordinate transform + output registers
      --------------------------------------------------------------------------------

      strip_o     <= resize(slope_s9_2p5 + intercept, strip_o);
      intercept_o <= resize(intercept, intercept_o);
      slope_o     <= resize(slope_s9, slope_o);

    end if;
  end process;

  intercept_multiplier : entity work.pipelined_smult
    generic map (
      WIDTH_A => y_minus_mb'length,
      WIDTH_B => MULT_RECIP_FRACB+2
      )
    port map (
      clock   => clock,
      input_a => signed(to_slv(y_minus_mb)),
      input_b => signed(to_slv(reciprocal6(cnt(7), MULT_RECIP_FRACB))),
      output  => intercept_signed
      );

  intercept_smult <=
    to_sfixed(std_logic_vector(intercept_signed),
              intercept_smult'high,
              intercept_smult'low);

  intercept <= resize(intercept_smult, intercept);

end behavioral;
