----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
-- https://www.varsitytutors.com/hotmath/hotmath_help/topics/line-of-best-fit
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial.html
-- https://vhdlguru.blogspot.com/2010/03/fixed-point-operations-in-vhdl-tutorial_29.html
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

    N_STAGES : natural := 11;

    STRIP_BITS : natural := 6;
    -- slope
    -- max slope is ~40 strips / 6 layers = ~7 so give it 4 bits
    M_INT_BITS  : natural := 4;
    M_FRAC_BITS : natural := 6;

    -- intercept
    -- this is the intercept at the 0th layer, different than the pattern-centered strip
    -- (for debugging)
    B_INT_BITS  : natural := 6;
    B_FRAC_BITS : natural := 6;

    -- strip
    -- this is the strip, centered in the 2.5 layer (center of the chamber)
    STRIP_INT_BITS  : natural := 4;
    STRIP_FRAC_BITS : natural := 5

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

    strip_o     : out sfixed (STRIP_INT_BITS-1 downto -STRIP_FRAC_BITS);
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

  type valid_array_t is array (integer range 0 to 3) of
    std_logic_vector(N_LAYERS-1 downto 0);
  signal valid : valid_array_t := (others => (others => '1'));

  --------------------------------------------------------------------------------
  -- s1
  --------------------------------------------------------------------------------

  type cnt_array_t is array (integer range 0 to 13) of integer range 0 to 6;
  signal cnt : cnt_array_t := (others => 6);

  type x_sum_array_t is array (integer range 1 to 6) of integer range 0 to 15;  
  signal x_sum : x_sum_array_t := (others => 0);

  signal x_sum_fixed : sfixed(4 downto 0) := (others => '0');

  type y_sum_array_t is array (integer range 1 to 15) of integer range -40 to 40;
  signal y_sum : y_sum_array_t := (others => 0);  -- sum (y_i)


  -- n * x
  type n_x_array_t is array (integer range 0 to 5) of integer range 0 to 30;  -- ly=5 * cnt=6
  type n_y_array_t is array (integer range 0 to 5) of integer range -255 to 255;
  signal n_x : n_x_array_t := (others => 0);
  signal n_y : n_y_array_t := (others => 0);

  --------------------------------------------------------------------------------
  -- s2
  --------------------------------------------------------------------------------

  type x_diff_array_t is array (integer range 0 to 5) of integer range -15 to 15;
  type y_diff_array_t is array (integer range 0 to 5) of integer range -127 to 127;
  signal x_diff : x_diff_array_t := (others => 0);  -- (x - mean(x))
  signal y_diff : y_diff_array_t := (others => 0);  -- (y - mean(y))

  signal result : integer;

  --------------------------------------------------------------------------------
  -- s3
  --------------------------------------------------------------------------------

  type square_array_t is array (integer range 0 to 5) of integer range -2047 to 2047;
  type product_array_t is array (integer range 0 to 5) of integer range -8191 to 8191;


  signal square : square_array_t  := (others => 0);
  signal product : product_array_t := (others => 0);

  
  --------------------------------------------------------------------------------
  -- s4
  --------------------------------------------------------------------------------

  -- Σ (n*xi - Σx)*(n*yi - Σy)
  --
  signal product_sum : integer range -8191 to 8191 := 0;
  signal product_sum_1 : integer range -8191 to 8191 := 0;

  
  signal square_sum_reciprocal : sfixed (1 downto -13);
  signal square_sum : integer range -8191 to 8191 := 0;

  --------------------------------------------------------------------------------
  -- s5
  --------------------------------------------------------------------------------

  signal slope_signed : signed (28 downto 0) := (others => '0');
  --signal slope_signed : signed (27 downto 0) := (others => '0');
  signal slope_sfixed : sfixed (15 downto -13) := (others => '0');
  --signal slope_sfixed : sfixed (15 downto -12) := (others => '0');

  signal slope, slope_s5, slope_s6, slope_s7, slope_s8, slope_s9, slope_s10, slope_s11: sfixed (3 downto -4) := (others => '0');


  signal slope_s7_x5 : sfixed (6 downto -2);
  signal slope_s6_mult : sfixed (7 downto -8);

  signal slope_s8_2p5, slope_s9_2p5, slope_s10_2p5, slope_s11_2p5, slope_s12_2p5 : sfixed (M_INT_BITS+2-1 downto -(M_FRAC_BITS-4));

  signal reciprocal_input : integer;

  --------------------------------------------------------------------------------
  -- s6
  --------------------------------------------------------------------------------

  signal slope_mult : sfixed(8 downto -4) := (others => '0');
  signal slope_times_x : sfixed(7 downto -5) := (others => '0');

  --------------------------------------------------------------------------------
  -- s7int
  --------------------------------------------------------------------------------

  signal y_minus_mb : sfixed(8 downto -5) := (others => '0');
  signal y_minus_mb_s6 : sfixed(8 downto -5) := (others => '0');

  --------------------------------------------------------------------------------
  -- s8
  --------------------------------------------------------------------------------

  constant MULT_RECIP_FRACB : integer := 14;
  signal intercept_mult : sfixed(10 downto -15);
  signal intercept : sfixed(5 downto -6) := (others => '0');


  type signed_vector is array (natural range <>) of signed;

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
      product_sum_1 <= sum6(product(0), product(1), product(2), product(3), product(4), product(5), valid(3));
      product_sum <= product_sum_1;

      -- Σ (n*xi - Σx)^2
      square_sum <= sum6(square(0), square(1), square(2), square(3), square(4), square(5), valid(3));
      square_sum_reciprocal <= reciprocal (square_sum ,-square_sum_reciprocal'low);


      --------------------------------------------------------------------------------
      -- s5: slope= Σ (n*xi - Σx)*(n*yi - Σy) / Σ (n*xi - Σx)^2
      --------------------------------------------------------------------------------

      slope_s5 <= slope;
      x_sum_fixed<= to_sfixed(x_sum(6), 4);
      slope_mult <= slope_s5 * x_sum_fixed; 
      slope_times_x <= resize(slope_mult, slope_times_x); 

      y_sum_dly_2 : for I in 7 to 12 loop
        y_sum(I) <= y_sum(I-1);
      end loop;

      --------------------------------------------------------------------------------
      -- s6: b = (Σy - slope*Σx) / n
      -- s6: Σy-mb = Σy - slope*Σx
      --------------------------------------------------------------------------------

      y_minus_mb <= to_sfixed(y_sum(11), 7) - slope_times_x;
      y_minus_mb_s6 <= y_minus_mb(y_minus_mb_s6'high downto y_minus_mb_s6'low) ;  
      intercept_mult <= reciprocal6(cnt(7), 10) * y_minus_mb_s6;          
      intercept <= intercept_mult(5 downto -6);
      slope_s6 <= slope_s5;

      --------------------------------------------------------------------------------
      -- s7, s8, s9, s10, s11, s12: Coordinate transform, delay slope and output
      --------------------------------------------------------------------------------

      slope_s6_mult <= slope_s6*5.0;
      slope_s7_x5 <= slope_s6_mult(slope_s7_x5'high downto slope_s7_x5'low);

      slope_s7 <= slope_s6;
      slope_s8 <= slope_s7;      
      slope_s8_2p5 <= resize(slope_s7_x5/2.0, slope_s8_2p5);                               
      
      slope_s9 <= slope_s8;
      slope_s9_2p5 <= slope_s8_2p5;

      slope_s10 <= slope_s9;
      slope_s10_2p5 <= slope_s9_2p5;

      slope_s11 <= slope_s10;

      strip_o     <= resize(slope_s10_2p5 + intercept, strip_o);
      intercept_o <= resize(intercept, intercept_o);        
      slope_o     <= resize(slope_s11, slope_o);                                                         

    end if;
  end process;



  slope_multiplier : entity work.mult_sgn_12x12
    generic map (
      WIDTH_A => 14,
      WIDTH_B => 15
      --WIDTH_B => 14
      )
    port map (
      clock   => clock,
      input_a => to_signed(product_sum, 14),
      --input_b => signed(to_slv(square_sum_reciprocal_narrow)),
      input_b => signed(to_slv(square_sum_reciprocal)),
      output  => slope_signed
      );
  slope_sfixed <= to_sfixed(std_logic_vector(slope_signed), slope_sfixed'high, slope_sfixed'low);
  slope <= resize(slope_sfixed, slope);
end behavioral;