library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

entity subtract_tester is
  generic(
    EDGE_DIST : natural := 2
  );
  port (
    clock : in std_logic;

    dav_i : in std_logic;
    dav_o : out std_logic;

    seg_l_i : in segment_t;
    seg_r_i : in segment_t;
    bool_o_compress : out boolean;
    bool_o_uncompress : out boolean
  );
end subtract_tester;

architecture Behavioral of subtract_tester is

function are_segs_in_range(l_seg : segment_t; r_seg : segment_t) return boolean is
    variable out_bool : boolean;
    
    variable upper_bits_xor : std_logic_vector (STRIP_BITS-1 downto 2);

    variable lower_bits_diff : unsigned (2 downto 0);

    begin
      -- Check if either segment is null
      if unsigned(l_seg.lc) > 0 and unsigned(r_seg.lc) > 0 then
        for i in STRIP_BITS-1 downto 2 loop
          upper_bits_xor(i) := l_seg.strip(i) xor r_seg.strip(i);
        end loop;
        --report("UPPER BITS XOR: "&integer'image(to_integer(unsigned(upper_bits_xor))));
           
        lower_bits_diff := unsigned(abs(signed(unsigned('0'&l_seg.strip(1 downto 0))) - signed(unsigned('0'&r_seg.strip(1 downto 0)))));
        --report "LOWER BITS DIFF: "&integer'image(to_integer(lower_bits_diff)) severity note;
  
        out_bool := false when (or_reduce(upper_bits_xor) = '1') or (lower_bits_diff(1 downto 0) > EDGE_DIST) else true;
      else
        out_bool := false;
      end if;
      
      return out_bool;
    end;

begin
  process (clock) begin
    if (rising_edge(clock)) then
      --report "SEG L LC : "&integer'image(to_integer(unsigned(seg_l_i.lc)));
      --report "BOOL_O_COMPRESS : "&boolean'image(bool_o_compress);
      --report "BOOL_O_UNCOMPRESS : "&boolean'image(bool_o_uncompress);
    bool_o_compress <= are_segs_in_range(seg_l_i, seg_r_i);
    bool_o_uncompress <= true when (unsigned(seg_l_i.lc) > 0 and unsigned(seg_r_i.lc) > 0 and abs(signed('0'&seg_l_i.strip) - signed('0'&seg_r_i.strip)) <= EDGE_DIST) else false;
    end if;
  end process;
end Behavioral;

