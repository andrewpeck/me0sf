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
----------------------------------------------------------------------------------


use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.std_logic_misc.all;

entity sbit_bram is
  port (
    clock320 : in  std_logic;
    clock40  : in  std_logic;
    sbits_i  : in  chamber_t;
    my_out   : out std_logic_vector
    );
end sbit_bram;

architecture Behavioral of sbit_bram is

begin

my_bram : entity work.blk_mem_gen_0
  port map (
    clka => clock40,
    wea => "1",
    addra => 0,
    dina => "00000000000000000000000000000000" & sbits_i(0)(0) & "00000000000000000000000000000000",
    clkb => clock320,
    addrb => 0,
    doutb => my_out
  );

end Behavioral;