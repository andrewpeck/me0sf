----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 07/18/2025 04:34:38 PM
-- Design Name: 
-- Module Name: sbit_bram - Behavioral
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

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity window_extract is
  port (
    clock          : in std_logic;
    window_i       : in  sbit_window_t;
    wanted_strip_i : in std_logic_vector (STRIP_BITS-1 downto 0);
    wanted_PID_i   : in std_logic_vector (PID_BITS-1 downto 0);
    pat_sbits      : out pat_sbits_t;
    center_position : out unsigned(5 downto 0)
    );
end window_extract;

architecture Behavioral of window_extract is
    
--signal center_position : unsigned (5 downto 0); --Can be [0, 47], so 6 bits

begin

  center_position <= to_unsigned((to_integer(unsigned(wanted_strip_i)) mod 12) + 18, center_position'length); -- Indexing from left, and by 0

end Behavioral;
