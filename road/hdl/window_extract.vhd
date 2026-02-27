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
-- From the PID, takes only the leftmost bit, and following 5 bits from each layer.
-- Since patterns can have 1-6 bits, depending on PID and layer, this module also zeros bits that are not part of the pattern, and shifts the desired sbits
-- such that they are centered. Odd sized layers (1, 3, 5) have an additional 0 to the right, that must be accounted for later. This is done since the size of these vectors
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
    wanted_strip_i : in unsigned (STRIP_BITS-1 downto 0);
    wanted_PID_i   : in unsigned (PID_BITS-1 downto 0);
    pat_sbits      : out pat_sbits_t
    );
end window_extract;

architecture Behavioral of window_extract is

----------------------------------------------------------------------------------------------------------------------------
-- Find sizes of patterns by layer, should all be pre-computed by compiler
----------------------------------------------------------------------------------------------------------------------------

-- Types for the bit widths of layers, depending on PID. This is constant, and depends only on the patterns.
type pat_sbits_size_t is array (0 to 5) of unsigned(2 downto 0); --Sizes can be [2, 6]. TODO: Consider reducing to 2 bits
type patlist_sbits_size_t is array (0 to 16) of pat_sbits_size_t;

-- Function to find the bit widths of each layer, for each pattern
function get_pat_sbit_sizes (patlist : patdef_array_t) return patlist_sbits_size_t is
  variable patlist_sbit_sizes : patlist_sbits_size_t;
  constant entry_bitwidth : integer := patlist_sbit_sizes(0)(0)'length; -- Get entry bitwidth here for generability, and code clarity
begin
  for pid in 0 to 16 loop
    -- Can't do a loop, since layer values are named signals like ly0, ly1, ...
    patlist_sbit_sizes(pid)(0) := to_unsigned(patlist(pid).ly0.hi - patlist(pid).ly0.lo + 1, entry_bitwidth);
    patlist_sbit_sizes(pid)(1) := to_unsigned(patlist(pid).ly1.hi - patlist(pid).ly1.lo + 1, entry_bitwidth);
    patlist_sbit_sizes(pid)(2) := to_unsigned(patlist(pid).ly2.hi - patlist(pid).ly2.lo + 1, entry_bitwidth);
    patlist_sbit_sizes(pid)(3) := to_unsigned(patlist(pid).ly3.hi - patlist(pid).ly3.lo + 1, entry_bitwidth);
    patlist_sbit_sizes(pid)(4) := to_unsigned(patlist(pid).ly4.hi - patlist(pid).ly4.lo + 1, entry_bitwidth);
    patlist_sbit_sizes(pid)(5) := to_unsigned(patlist(pid).ly5.hi - patlist(pid).ly5.lo + 1, entry_bitwidth);
  end loop;

  return patlist_sbit_sizes;
end function;

-- Lookup table of the bit widths, dimensions = (num_patterns x num_layers) = (17 x 6)
constant pat_sbits_size_LUT : patlist_sbits_size_t := get_pat_sbit_sizes(patlist);

----------------------------------------------------------------------------------------------------------------------------
-- Signal and function for finding the layer offset values from the patterns, TODO: consider removing this function doing the same in the main body
----------------------------------------------------------------------------------------------------------------------------
signal ly_offsets : ly_offsets_t;

function get_offsets_from_pats (pid_index : unsigned) return ly_offsets_t is
  variable ly_offsets : ly_offsets_t;
begin
  if pid_index <= 16 then
    ly_offsets(0) := to_signed(patdef_array(to_integer(pid_index)).ly0.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
    ly_offsets(1) := to_signed(patdef_array(to_integer(pid_index)).ly1.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
    ly_offsets(2) := to_signed(patdef_array(to_integer(pid_index)).ly2.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
    ly_offsets(3) := to_signed(patdef_array(to_integer(pid_index)).ly3.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
    ly_offsets(4) := to_signed(patdef_array(to_integer(pid_index)).ly4.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
    ly_offsets(5) := to_signed(patdef_array(to_integer(pid_index)).ly5.lo, 6); --For now, PID=0 is NaN segment, so subtract 1 to index with it.
  else
    for I in 0 to 5 loop
      ly_offsets(I) := to_signed(0, 6);
    end loop;
  end if;

  return ly_offsets;
end function;

----------------------------------------------------------------------------------------------------------------------------
-- Function for extracting the desired sbits from the window, and zero padding based on a given layer's size
----------------------------------------------------------------------------------------------------------------------------

function get_sbits_and_zero_pad (window : sbit_window_t; center_position : unsigned; ly_offsets : ly_offsets_t; sizes_by_ly : pat_sbits_size_t) return pat_sbits_t is
  variable pat_sbits : pat_sbits_t;
  variable LMB : integer range 5 to 47;
  variable ly_size : integer range 2 to 6;
begin
  for I in 0 to 5 loop
    LMB := to_integer(center_position - unsigned(ly_offsets(I))); -- Can just interpret ly_offsets(I) as unsigned, since subtraction for unsiged vs. signed is identical. Can take result as unsigned, since it is guaranteed to be non-negative
    ly_size := to_integer(sizes_by_ly(I));

    if ly_size = 2 then
        pat_sbits(I) := "0000" & window(5-I)(LMB downto LMB-1); -- Indexing is backwards somewhere, the 5-I fixes it for now
    elsif ly_size = 3 then
        pat_sbits(I) := "000" & window(5-I)(LMB downto LMB-2);
    elsif ly_size = 4 then
        pat_sbits(I) := "00" & window(5-I)(LMB downto LMB-3);
    elsif ly_size = 5 then
        pat_sbits(I) := "0" & window(5-I)(LMB downto LMB-4);
    elsif ly_size = 6 then
        pat_sbits(I) := window(5-I)(LMB downto LMB-5);
    end if;
  end loop;

  return pat_sbits;
end function;

--TODO: consider shifting this range from [18, 29] -> [0, 11], and reduce from 5->4 bits
signal center_position : unsigned (4 downto 0); --Can be [18, 29], so 5 bits
signal sbit_ly_sizes : pat_sbits_size_t;
signal wanted_pid_index : unsigned (PID_BITS-1 downto 0); 

begin

  -- Since PID is currently indexing by 1, need to subtract 1. But 0 is invalid, so need to take care if it initializes to this.
  wanted_pid_index <= wanted_PID_i - 1 when wanted_PID_i /= 0 else (others => '0');

  -- Find where in the window the center is, f(strip) only, but depends on BRAM ring buffer architecture
  center_position <= to_unsigned((to_integer(wanted_strip_i) mod 12) + 18, center_position'length); -- Indexing from right, and by 0

  -- Get the leftmost bit offset for each layer based on PID
  ly_offsets <= get_offsets_from_pats(wanted_pid_index);

  -- Get the width of the desired pattern for each layer
  sbit_ly_sizes <= pat_sbits_size_LUT(to_integer(wanted_pid_index));

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- Extract desired sbits from the window, zero padding to make it a 6 bit vector
      pat_sbits <= get_sbits_and_zero_pad(window_i, center_position, ly_offsets, sbit_ly_sizes);
    end if;
  end process;

  -- Old way to get 6 bit vector starting from LMB and going right. Potentially obsolete, keeping commented for now.
  -- ly_sbit_select_g : for I in 0 to 5 generate
  --   signal LMB : integer range 0 to 47 := 5; --Can be 5 to 47 (but initializing to 0 for some reason), so 6 bits
  -- begin
  --     LMB <= to_integer(center_position - unsigned(ly_offsets(I))); -- Can just interpret ly_offsets(I) as unsigned, since subtraction for unsiged vs. signed is identical. Can take result as unsigned, since it is guaranteed to be non-negative
  --     pat_sbits(I) <= window_i(I)(LMB downto LMB-5) when LMB >= 5 else (others => '0');
  -- end generate;

  -- Alternatively, can get the 6 bit vector starting from LMB and going right. Then, shift and zero pad. TODO: see if this is any better
  -- vec <= bits[left downto left-6];
  -- right_shift_amount <= (6-size) >> 1;
  -- zeros_amount <= (7-size) >> 1;
  -- shifted_vec <= rightshift(vec, right_shift_amount);
  -- out_vec <= shifted_vec

end Behavioral;
