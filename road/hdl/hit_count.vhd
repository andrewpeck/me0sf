
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity hit_count is
  generic(
    HCB : integer := 4;
    LCB : integer := 2
    );
  port(
    clk : in  std_logic;
    ly0 : in  std_logic_vector;
    ly1 : in  std_logic_vector;
    ly2 : in  std_logic_vector;
    ly3 : in  std_logic_vector;
    ly4 : in  std_logic_vector;
    ly5 : in  std_logic_vector;
    hc  : out unsigned (HCB-1 downto 0);
    lc  : out unsigned (LCB-1 downto 0)
    );
end hit_count;

architecture behavioral of hit_count is

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

  -- this ugly function reduces the LUT count by about 18 LUT / pat unit
  -- (6912 LUTs total) compared to a more straightforward implementation
  function count6_floor (slv : std_logic_vector (5 downto 0))
    return natural is
    variable n_ones : natural := 0;
  begin
    case slv is
      when "000000" => return 0;
      when "000001" => return 0;
      when "000010" => return 0;
      when "000011" => return 0;
      when "000100" => return 0;
      when "000101" => return 0;
      when "000110" => return 0;
      when "000111" => return 0;
      when "001000" => return 0;
      when "001001" => return 0;
      when "001010" => return 0;
      when "001011" => return 0;
      when "001100" => return 0;
      when "001101" => return 0;
      when "001110" => return 0;
      when "001111" => return 1;
      when "010000" => return 0;
      when "010001" => return 0;
      when "010010" => return 0;
      when "010011" => return 0;
      when "010100" => return 0;
      when "010101" => return 0;
      when "010110" => return 0;
      when "010111" => return 1;
      when "011000" => return 0;
      when "011001" => return 0;
      when "011010" => return 0;
      when "011011" => return 1;
      when "011100" => return 0;
      when "011101" => return 1;
      when "011110" => return 1;
      when "011111" => return 2;
      when "100000" => return 0;
      when "100001" => return 0;
      when "100010" => return 0;
      when "100011" => return 0;
      when "100100" => return 0;
      when "100101" => return 0;
      when "100110" => return 0;
      when "100111" => return 1;
      when "101000" => return 0;
      when "101001" => return 0;
      when "101010" => return 0;
      when "101011" => return 1;
      when "101100" => return 0;
      when "101101" => return 1;
      when "101110" => return 1;
      when "101111" => return 2;
      when "110000" => return 0;
      when "110001" => return 0;
      when "110010" => return 0;
      when "110011" => return 1;
      when "110100" => return 0;
      when "110101" => return 1;
      when "110110" => return 1;
      when "110111" => return 2;
      when "111000" => return 0;
      when "111001" => return 1;
      when "111010" => return 1;
      when "111011" => return 2;
      when "111100" => return 1;
      when "111101" => return 2;
      when "111110" => return 2;
      when "111111" => return 3;
      when others   => return 0;
    end case;
  end function count6_floor;

  function hc_quality (cnt : natural) return natural is
  begin
    case cnt is
      when 0 | 1 | 2 | 3 | 4 | 5 | 6 => return cnt;
      when others                    => return 7;
    end case;
  end;

  function lc_floor (a : integer) return integer is
  begin
    case a is
      when 0 | 1  => return 0;
      when others => return a-3;
    end case;
  end;

  --------------------------------------------------------------------------------
  --  prodcedural function to sum number of layers hit into a binary value - rom version
  --  returns   count6 = (inp[5]+inp[4]+inp[3])+(inp[2]+inp[1]+inp[0]);
  --
  --  compared to using a more obvious implementation, this function reduced the
  --  resource usage of the pattern unit by 13 LUTs.. ~20,000 LUTs total
  --  reduction by helping the synth tool. Uhg.
  --
  --------------------------------------------------------------------------------

  function count6 (x : std_logic_vector(5 downto 0))
    return unsigned is
  begin
    case(to_integer(unsigned(x))) is
      when 0  => return to_unsigned(0, 3);
      when 1  => return to_unsigned(1, 3);
      when 2  => return to_unsigned(1, 3);
      when 3  => return to_unsigned(2, 3);
      when 4  => return to_unsigned(1, 3);
      when 5  => return to_unsigned(2, 3);
      when 6  => return to_unsigned(2, 3);
      when 7  => return to_unsigned(3, 3);
      when 8  => return to_unsigned(1, 3);
      when 9  => return to_unsigned(2, 3);
      when 10 => return to_unsigned(2, 3);
      when 11 => return to_unsigned(3, 3);
      when 12 => return to_unsigned(2, 3);
      when 13 => return to_unsigned(3, 3);
      when 14 => return to_unsigned(3, 3);
      when 15 => return to_unsigned(4, 3);
      when 16 => return to_unsigned(1, 3);
      when 17 => return to_unsigned(2, 3);
      when 18 => return to_unsigned(2, 3);
      when 19 => return to_unsigned(3, 3);
      when 20 => return to_unsigned(2, 3);
      when 21 => return to_unsigned(3, 3);
      when 22 => return to_unsigned(3, 3);
      when 23 => return to_unsigned(4, 3);
      when 24 => return to_unsigned(2, 3);
      when 25 => return to_unsigned(3, 3);
      when 26 => return to_unsigned(3, 3);
      when 27 => return to_unsigned(4, 3);
      when 28 => return to_unsigned(3, 3);
      when 29 => return to_unsigned(4, 3);
      when 30 => return to_unsigned(4, 3);
      when 31 => return to_unsigned(5, 3);
      when 32 => return to_unsigned(1, 3);
      when 33 => return to_unsigned(2, 3);
      when 34 => return to_unsigned(2, 3);
      when 35 => return to_unsigned(3, 3);
      when 36 => return to_unsigned(2, 3);
      when 37 => return to_unsigned(3, 3);
      when 38 => return to_unsigned(3, 3);
      when 39 => return to_unsigned(4, 3);
      when 40 => return to_unsigned(2, 3);
      when 41 => return to_unsigned(3, 3);
      when 42 => return to_unsigned(3, 3);
      when 43 => return to_unsigned(4, 3);
      when 44 => return to_unsigned(3, 3);
      when 45 => return to_unsigned(4, 3);
      when 46 => return to_unsigned(4, 3);
      when 47 => return to_unsigned(5, 3);
      when 48 => return to_unsigned(2, 3);
      when 49 => return to_unsigned(3, 3);
      when 50 => return to_unsigned(3, 3);
      when 51 => return to_unsigned(4, 3);
      when 52 => return to_unsigned(3, 3);
      when 53 => return to_unsigned(4, 3);
      when 54 => return to_unsigned(4, 3);
      when 55 => return to_unsigned(5, 3);
      when 56 => return to_unsigned(3, 3);
      when 57 => return to_unsigned(4, 3);
      when 58 => return to_unsigned(4, 3);
      when 59 => return to_unsigned(5, 3);
      when 60 => return to_unsigned(4, 3);
      when 61 => return to_unsigned(5, 3);
      when 62 => return to_unsigned(5, 3);
      when 63 => return to_unsigned(6, 3);
      when others   => assert false report "Missing case in count6=" & integer'image(to_integer(unsigned(x))) severity error;
    end case;
  end;

begin

  process (clk) is
  begin
    if (rising_edge(clk)) then

      hc <= to_unsigned(hc_quality(count_ones(ly0)) +
                        -- count_ones(ly1) +
                        -- count_ones(ly2) +
                        -- count_ones(ly3) +
                        -- count_ones(ly4) +
                        hc_quality(count_ones(ly5)), HCB);

      lc <= count6(or_reduce(ly0) &
                   or_reduce(ly1) &
                   or_reduce(ly2) &
                   or_reduce(ly3) &
                   or_reduce(ly4) &
                   or_reduce(ly5));

    end if;
  end process;
end behavioral;
