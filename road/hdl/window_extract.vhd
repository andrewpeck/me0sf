----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 07/18/2025 04:34:38 PM
-- Design Name: 
-- Module Name: window_extract - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
-- Input: 48x6 (strip x layer) sbit window, desired strip center, and desired PID.
-- Output: 6 std_logic_vectors of size 6. These are the sbits from the specified pattern.
--
-- From the strip center, finds where in the window the center of the desired pattern is (derived from sbit BRAM architecture).
-- From the PID, takes only the leftmost bit, and follwing 5 bits from each layer.
-- Since patterns can have 1-6 bits, depending on PID and layer, this module also zeros bits that are not part of the pattern, and shifts the desired sbits
-- such that they are centered. Odd sized layers (1, 3, 5) have an additional 0 to the left, that must be accounted for later. This is done since the size of these vectors
-- must be constant.
----------------------------------------------------------------------------------


use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity window_extract is
  generic (
    patlist        : patdef_array_t := patdef_array
  );
  port (
    clock          : in std_logic;
    window_i       : in  sbit_window_t;
    wanted_strip_i : in std_logic_vector (STRIP_BITS-1 downto 0);
    wanted_PID_i   : in std_logic_vector (PID_BITS-1 downto 0);
    pat_sbits      : out pat_sbits_t
    );
end window_extract;

architecture Behavioral of window_extract is
    
--TODO: consider shifting this range from [18, 29] -> [0, 11], and reduce from 5->4 bits
signal center_position : unsigned (4 downto 0) := to_unsigned(18, 5); --Can be [18, 29], so 5 bits
signal ly_offsets : ly_offsets_t;

function get_offsets_from_pats (pid_std : std_logic_vector) return ly_offsets_t is
    variable pid : unsigned (PID_BITS-1 downto 0);
    variable ly_offsets : ly_offsets_t;
  begin
    pid := unsigned(pid_std);
    if pid >= 1 and pid <= 17 then
      ly_offsets(0) := to_signed(patdef_array(to_integer(pid)-1).ly0.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
      ly_offsets(1) := to_signed(patdef_array(to_integer(pid)-1).ly1.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
      ly_offsets(2) := to_signed(patdef_array(to_integer(pid)-1).ly2.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
      ly_offsets(3) := to_signed(patdef_array(to_integer(pid)-1).ly3.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
      ly_offsets(4) := to_signed(patdef_array(to_integer(pid)-1).ly4.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
      ly_offsets(5) := to_signed(patdef_array(to_integer(pid)-1).ly5.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.

    else
      for I in 0 to 5 loop
        ly_offsets(I) := to_signed(0, 6);
      end loop;
    end if;

    return ly_offsets;
  end function;

begin

  center_position <= to_unsigned((to_integer(unsigned(wanted_strip_i)) mod 12) + 18, center_position'length); -- Indexing from right, and by 0
  ly_offsets <= get_offsets_from_pats(wanted_PID_i);

  ly_sbit_select_g : for I in 0 to 5 generate
    signal LMB : integer range 0 to 47 := 5; --Can be 5 to 47 (but initializing to 0 for some reason), so 6 bits
  begin
      LMB <= to_integer(center_position - unsigned(ly_offsets(I))); -- Can just interpret ly_offsets(I) as unsigned, since subtraction for unsiged vs. signed is identical. Can take result as unsigned, since it is guaranteed to be non-negative
      pat_sbits(I) <= window_i(I)(LMB downto LMB-5) when LMB >= 5 else (others => '0');
  end generate;

end Behavioral;
