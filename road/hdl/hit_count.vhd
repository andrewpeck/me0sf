
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity hit_count is
  generic(
    HCB : integer := 4;
    LCB : integer := 3;
    EN_HC_COMPRESS : boolean := true
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
      when 0  => return to_unsigned(0, 2);
      when 1  => return to_unsigned(0, 2);
      when 2  => return to_unsigned(0, 2);
      when 3  => return to_unsigned(0, 2);
      when 4  => return to_unsigned(0, 2);
      when 5  => return to_unsigned(0, 2);
      when 6  => return to_unsigned(0, 2);
      when 7  => return to_unsigned(0, 2);
      when 8  => return to_unsigned(0, 2);
      when 9  => return to_unsigned(0, 2);
      when 10 => return to_unsigned(0, 2);
      when 11 => return to_unsigned(0, 2);
      when 12 => return to_unsigned(0, 2);
      when 13 => return to_unsigned(0, 2);
      when 14 => return to_unsigned(0, 2);
      when 15 => return to_unsigned(1, 2);
      when 16 => return to_unsigned(0, 2);
      when 17 => return to_unsigned(0, 2);
      when 18 => return to_unsigned(0, 2);
      when 19 => return to_unsigned(0, 2);
      when 20 => return to_unsigned(0, 2);
      when 21 => return to_unsigned(0, 2);
      when 22 => return to_unsigned(0, 2);
      when 23 => return to_unsigned(1, 2);
      when 24 => return to_unsigned(0, 2);
      when 25 => return to_unsigned(0, 2);
      when 26 => return to_unsigned(0, 2);
      when 27 => return to_unsigned(1, 2);
      when 28 => return to_unsigned(0, 2);
      when 29 => return to_unsigned(1, 2);
      when 30 => return to_unsigned(1, 2);
      when 31 => return to_unsigned(2, 2);
      when 32 => return to_unsigned(0, 2);
      when 33 => return to_unsigned(0, 2);
      when 34 => return to_unsigned(0, 2);
      when 35 => return to_unsigned(0, 2);
      when 36 => return to_unsigned(0, 2);
      when 37 => return to_unsigned(0, 2);
      when 38 => return to_unsigned(0, 2);
      when 39 => return to_unsigned(1, 2);
      when 40 => return to_unsigned(0, 2);
      when 41 => return to_unsigned(0, 2);
      when 42 => return to_unsigned(0, 2);
      when 43 => return to_unsigned(1, 2);
      when 44 => return to_unsigned(0, 2);
      when 45 => return to_unsigned(1, 2);
      when 46 => return to_unsigned(1, 2);
      when 47 => return to_unsigned(2, 2);
      when 48 => return to_unsigned(0, 2);
      when 49 => return to_unsigned(0, 2);
      when 50 => return to_unsigned(0, 2);
      when 51 => return to_unsigned(1, 2);
      when 52 => return to_unsigned(0, 2);
      when 53 => return to_unsigned(1, 2);
      when 54 => return to_unsigned(1, 2);
      when 55 => return to_unsigned(2, 2);
      when 56 => return to_unsigned(0, 2);
      when 57 => return to_unsigned(1, 2);
      when 58 => return to_unsigned(1, 2);
      when 59 => return to_unsigned(2, 2);
      when 60 => return to_unsigned(1, 2);
      when 61 => return to_unsigned(2, 2);
      when 62 => return to_unsigned(2, 2);
      when 63 => return to_unsigned(3, 2);
      when others   => assert false report "Missing case in count6=" & integer'image(to_integer(unsigned(x))) severity error;
    end case;
  end;
  
  function count6_uncompressed (x : std_logic_vector(5 downto 0))
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
                        
      if (EN_HC_COMPRESS) then
        lc <= "0"&count6(or_reduce(ly0) & or_reduce(ly1) &
                     or_reduce(ly2) & or_reduce(ly3) &
                     or_reduce(ly4) & or_reduce(ly5));
      else
        lc <= count6_uncompressed(or_reduce(ly0) & or_reduce(ly1) &
                     or_reduce(ly2) & or_reduce(ly3) &
                     or_reduce(ly4) & or_reduce(ly5));
      end if;
    end if;
  end process;
end behavioral;