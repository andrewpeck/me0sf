----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar, J. Garcia de Castro

-----------------------------------------------------------------------------------
--ME0 fitter, takes as input the output from the segment finder (a strip value from each layer, and a valid_i vector stating which
--of these values is valid), and performs a linear fit b = Y - m*X, and outputs the slope (m), the intercept (b) and the center strip (s = m * 2.5 + b).
--The computation of the slope is performed the following way: m = Σ (n*xi - Σx)*(n*yi - Σy) / Σ (n*xi - Σx)^2.  In the code this
--corresponds to slope = product_sum / square_sum. 
--The fitter is divided in 13 pipeline stages (takes 13 clock cycles to run)

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.fixed_pkg.all;

library work;
use work.reciprocal_pkg.all;

entity fit is
  generic (

    N_LAYERS : natural := 6;

    N_STAGES : natural := 13;

    STRIP_BITS : natural := 8;
    -- slope
    -- max slope is ~40 strips / 6 layers = ~7 so give it 4 bits
    M_INT_BITS  : natural := 4;
    M_FRAC_BITS : natural := 6;

    -- intercept
    -- this is the intercept at the 0th layer, different than the pattern-centered strip
    --B_INT_BITS  : natural := 6;
    B_INT_BITS  : natural := 7; -- After doubling resolution
    B_FRAC_BITS : natural := 7;

    -- strip
    -- this is the strip, centered in the 2.5 layer (center of the chamber)
    --STRIP_INT_BITS  : natural := 4;
    STRIP_INT_BITS  : natural := 5;
    STRIP_FRAC_BITS : natural := 5
    );

  port (
    clock   : in std_logic;
    ly0     : in signed (STRIP_BITS-1 downto 0);
    ly1     : in signed (STRIP_BITS-1 downto 0);
    ly2     : in signed (STRIP_BITS-1 downto 0);
    ly3     : in signed (STRIP_BITS-1 downto 0);
    ly4     : in signed (STRIP_BITS-1 downto 0);
    ly5     : in signed (STRIP_BITS-1 downto 0);
    valid_i : in std_logic_vector(N_LAYERS-1 downto 0);

    strip_o     : out sfixed (STRIP_INT_BITS-1 downto -STRIP_FRAC_BITS);
    intercept_o : out sfixed (B_INT_BITS-1 downto -B_FRAC_BITS);
    slope_o     : out sfixed (M_INT_BITS-1 downto -M_FRAC_BITS)
    );
end fit;

architecture behavioral of fit is

  --------------------------------------------------------------------------------
  -- s0
  --------------------------------------------------------------------------------

  type ly_array_t is array (integer range 0 to N_LAYERS-1) of signed (STRIP_BITS-1 downto 0);
  signal ly : ly_array_t := (others => (others => '0'));
  signal result : integer;

  --------------------------------------------------------------------------------
  -- delays
  --------------------------------------------------------------------------------
  
  type valid_array_t is array (integer range 0 to 4) of std_logic_vector(N_LAYERS-1 downto 0);
  signal valid : valid_array_t;

  type cnt_array_t is array (integer range 0 to 9) of integer range 0 to 6;
  signal cnt : cnt_array_t := (others => 6);

  type x_sum_array_t is array (integer range 1 to 6) of integer range 0 to 15;  
  signal x_sum : x_sum_array_t := (others => 0);

  --type y_sum_array_t is array (integer range 1 to 9) of integer range -255 to 255;
  type y_sum_array_t is array (integer range 1 to 9) of integer range -511 to 511; -- After doubling resolution
  signal y_sum : y_sum_array_t := (others => 0);  -- sum (y_i)

  --------------------------------------------------------------------------------
  -- s1
  --------------------------------------------------------------------------------

  type n_x_array_t is array (integer range 0 to 5) of integer range 0 to 30;  -- ly=5 * cnt=6
  --type n_y_array_t is array (integer range 0 to 5) of integer range -255 to 255;  -- n_y on average is at most ~ +/-40, 40 * 6 ~ 240
  type n_y_array_t is array (integer range 0 to 5) of integer range -511 to 511; -- After doubling resolution
  signal n_x : n_x_array_t := (others => 0);
  signal n_y : n_y_array_t := (others => 0);

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  type x_diff_array_t is array (integer range 0 to N_LAYERS-1) of integer range -30 to 30;  --x_diff = n_x - x_sum, max value is 30
  signal x_diff : x_diff_array_t := (others => 0);

  --type y_diff_array_t is array (integer range 0 to N_LAYERS-1) of integer range -255 to 255;  --y_diff = n_y - y_sum, max value is +/- 255
  type y_diff_array_t is array (integer range 0 to N_LAYERS-1) of integer range -511 to 511; -- After doubling resolution
  signal y_diff : y_diff_array_t := (others => 0);

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  type square_array_t is array (integer range 0 to N_LAYERS-1) of integer range -2047 to 2047;
  signal square : square_array_t  := (others => 0);

  --type product_array_t is array (integer range 0 to N_LAYERS-1) of integer range -8191 to 8191;
  type product_array_t is array (integer range 0 to N_LAYERS-1) of integer range -16383 to 16383; -- After doubling resolution
  signal product : product_array_t := (others => 0);

  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  signal product_sum : integer range -8191 to 8191 := 0;
  signal product_sum_1 : integer range -8191 to 8191 := 0;
  signal product_sum_sfixed : sfixed(13 downto 0);

  signal square_sum : integer range -8191 to 8191 := 0;
  signal square_sum_reciprocal : sfixed (1 downto -13);

  --------------------------------------------------------------------------------
  -- s6,7 (pipelined multiplier)
  --------------------------------------------------------------------------------

  signal r_ma       : signed(13 downto 0);
  signal r_mb       : signed(14 downto 0);
  signal r_m_stage1 : signed(26 downto 0);

  --------------------------------------------------------------------------------
  -- slopes and intercept
  --------------------------------------------------------------------------------

  signal x_sum_fixed : sfixed(5 downto 0) := (others => '0');

  signal slope_signed : signed (28 downto 0) := (others => '0');
  signal slope_sfixed : sfixed (15 downto -13) := (others => '0');

  signal slope_signed_test : signed (28 downto 0) := (others => '0');
  signal slope_sfixed_test : sfixed (15 downto -13) := (others => '0');

  signal slope, slope_s9, slope_s10, slope_s11, slope_s12: sfixed (3 downto -6) := (others => '0');
  signal slope_test : sfixed (15 downto -13) := (others => '0');

  signal slope_s10_mult : sfixed (7 downto -12);
  signal slope_s11_x5 : sfixed (6 downto -2);
  signal slope_s12_2p5 : sfixed (6 downto -8);

  signal slope_mult : sfixed(9 downto -6) := (others => '0');
  signal slope_times_x : sfixed(7 downto -7) := (others => '0');

  signal intercept_mult : sfixed(10 downto -21);
  signal intercept : sfixed(6 downto -8) := (others => '0');

  --------------------------------------------------------------------------------
  -- functions
  --------------------------------------------------------------------------------

  -- sum 6 signed numbers with an enable for each number
  function sum6 (p0, p1, p2, p3, p4, p5 : integer; en: std_logic_vector (5 downto 0))
    return integer is variable result : integer;
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
  --------------------------------------------------------------------------------

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

      -------------------------------------------------------------------------
      -- Stage 1
      -------------------------------------------------------------------------

      y_sum(1) <= sum6(to_integer(ly(0)), to_integer(ly(1)), to_integer(ly(2)), to_integer(ly(3)), to_integer(ly(4)), to_integer(ly(5)), valid_i);
      x_sum(1) <= sum6(0, 1, 2, 3, 4, 5, valid_i);

      n_xy_loop : for I in 0 to N_LAYERS-1 loop
        n_y(I) <= cnt(0) * to_integer(ly(I));
        n_x(I) <= cnt(0) * I;
      end loop;

      -------------------------------------------------------------------------
      -- DELAYS
      -------------------------------------------------------------------------

      valid(0) <= valid_i;
      valid_dly : for idly in 1 to valid'length-1 loop
        valid(idly) <= valid(idly-1);
      end loop;

      cnt(1) <= cnt(0);
      cnt(2) <= cnt(1);
      cnt(3) <= cnt(2);
      cnt(4) <= cnt(3);
      cnt(5) <= cnt(4);
      cnt(6) <= cnt(5);
      cnt(7) <= cnt(6);
      cnt(8) <= cnt(7);
      cnt(9) <= cnt(8); --cnt is used in stage 9

      x_sum_dly : for I in 2 to 6 loop --x_sum is used in stage 6
        x_sum(I) <= x_sum(I-1);
      end loop;

      y_sum_dly : for I in 2 to 9 loop  --y_sum is used in stage 9
        y_sum(I) <= y_sum(I-1);
      end loop;

      -------------------------------------------------------------------------
      -- Stage 2
      -------------------------------------------------------------------------

      diff_loop : for I in 0 to 5 loop
        x_diff(I) <= n_x(I) - x_sum(1);
        y_diff(I) <= n_y(I) - y_sum(1);
      end loop;

      -------------------------------------------------------------------------
      -- Stage 3
      -------------------------------------------------------------------------

      s3_loop : for I in 0 to 5 loop
        product(I) <= x_diff(I) * y_diff(I);
        square(I)  <= x_diff(I) * x_diff(I);
      end loop;

      -------------------------------------------------------------------------
      -- Stage 4, 5
      -------------------------------------------------------------------------

      -- Σ (n*xi - Σx)*(n*yi - Σy), numerator of slope
      product_sum_1 <= sum6(product(0), product(1), product(2), product(3), product(4), product(5), valid(2));
      product_sum <= product_sum_1; --To account for the delay needed in square_sum_reciprocal

      product_sum_sfixed <= to_sfixed(product_sum_1, product_sum_sfixed'high, product_sum_sfixed'low);

      -- Σ (n*xi - Σx)^2, denominator of slope
      square_sum <= sum6(square(0), square(1), square(2), square(3), square(4), square(5), valid(2));
      square_sum_reciprocal <= reciprocal (square_sum ,-square_sum_reciprocal'low); --Instead of dividing, find the reciprocal in a lookup table

      ---------------------------------------------------------------------------
      -- Stages 6-7: Pipelined Multiplier (takes 2 clock cycles), product_sum * square_sum_reciprocal, 
      ---------------------------------------------------------------------------

      slope_test <= square_sum_reciprocal * product_sum_sfixed;
      slope <= resize(slope_test, slope);

      x_sum_fixed<= to_sfixed(x_sum(6), 5);
      --x_sum_fixed<= to_sfixed(x_sum(5), 5);

      -------------------------------------------------------------------------
      -- Stage 8
      -------------------------------------------------------------------------

      slope_mult <= slope * x_sum_fixed;
      --slope_mult <= slope_test * x_sum_fixed;

      -------------------------------------------------------------------------
      -- Stage 9
      -------------------------------------------------------------------------

      slope_times_x <= resize(slope_mult, slope_times_x); 
      slope_s9 <= slope;
      --slope_s9 <= slope_test;

      -------------------------------------------------------------------------
      -- Stage 10, 11, 12
      -------------------------------------------------------------------------

      intercept_mult <= reciprocal6(cnt(9), 14) * (to_sfixed(y_sum(9), 7) - slope_times_x);
      --intercept_mult <= reciprocal6(cnt(8), 14) * (to_sfixed(y_sum(8), 7) - slope_times_x);
      slope_s10_mult <= slope_s9*5.0;
      slope_s10 <= slope_s9;

      slope_s11_x5 <= slope_s10_mult(slope_s11_x5'high downto slope_s11_x5'low);
      slope_s11 <= slope_s10;

      slope_s12_2p5 <= resize(slope_s11_x5/2.0, slope_s12_2p5); 
      slope_s12 <= slope_s11;
      intercept <= intercept_mult(6 downto -8);

      -------------------------------------------------------------------------
      -- Stage 13: Output
      -------------------------------------------------------------------------

      strip_o     <= resize(slope_s12_2p5 + intercept, strip_o);
      intercept_o <= resize(intercept, intercept_o);
      slope_o     <= resize(slope_s12, slope_o);

    end if;
  end process;

  --------------------------------------------------------------------------------------------------------------
  -- Pipelined Multiplier
  --------------------------------------------------------------------------------------------------------------

  --slope_multiplier : entity work.mult_sgn_12x12
  --  generic map (
  --    WIDTH_A => 14,
  --    WIDTH_B => 15
  --    )
  --  port map (
  --    clock   => clock,
  --    input_a => to_signed(product_sum, 14),
  --    input_b => signed(to_slv(square_sum_reciprocal)),
  --    output  => slope_signed
  --    );
  --slope_sfixed <= to_sfixed(std_logic_vector(slope_signed), slope_sfixed'high, slope_sfixed'low);
  --slope <= resize(slope_sfixed, slope);
end behavioral;
