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
      if l_seg.lc = 0 or r_seg.lc = 0 then
        return false;
      end if;

      for i in STRIP_BITS-1 downto 2 loop
          upper_bits_xor(i) := l_seg.strip(i) xor r_seg.strip(i);
      end loop;
      --report("UPPER BITS XOR: "&integer'image(to_integer(unsigned(upper_bits_xor))));
         
      lower_bits_diff := unsigned(abs(signed(unsigned('0'&l_seg.strip(1 downto 0))) - signed(unsigned('0'&r_seg.strip(1 downto 0)))));
      --report "LOWER BITS DIFF: "&integer'image(to_integer(lower_bits_diff)) severity note;

      out_bool := false when (or_reduce(upper_bits_xor) = '1') or (lower_bits_diff(1 downto 0) > EDGE_DIST) else true;
      
      return out_bool;
    end;

begin
  bool_o_compress <= are_segs_in_range(seg_l_i, seg_r_i);
  bool_o_uncompress <= true when (seg_l_i.lc > 0 and seg_r_i.lc > 0 and abs(signed(unsigned(seg_l_i.strip) - unsigned(seg_r_i.strip))) <= EDGE_DIST) else false;    
end Behavioral;
