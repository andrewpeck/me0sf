--!-----------------------------------------------------------------------------
--!                                                                           --
--!           BNL - Brookhaven National Lboratory                             --
--!                       Physics Department                                  --
--!                         Omega Group                                       --
--!-----------------------------------------------------------------------------
--|
--! author:      Kai Chen    (kchen@bnl.gov)
--!
--!
--!-----------------------------------------------------------------------------
--
--
-- Create Date: 2016/05/10 12:02:10 PM
-- Design Name: PRBS31_GEN
-- Module Name: PRBS31_GEN - Behavioral
-- Project Name:
-- Target Devices:
-- Tool Versions: Vivado
-- Description:
--              The PRBS31 Gen
-- Dependencies:
--
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- Copyright: All rights reserved
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity PRBS31_32BIT_GEN is
  port
    (
      DATAIN        : in  std_logic_vector(31 downto 0);
      PRBS_DATA_OUT : out std_logic_vector(31 downto 0);
      DATA_VALID_IN : in  std_logic;
      comma_type    : in  std_logic_vector(1 downto 0);

      CLK   : in std_logic;
      RESET : in std_logic
      );

end PRBS31_32BIT_GEN;

architecture RTL of PRBS31_32BIT_GEN is


  signal poly            : std_logic_vector(30 downto 0);
  signal DATA_VALID_IN_r : std_logic;
  signal poly31          : std_logic;
  signal comma_type_r    : std_logic_vector(1 downto 0);


begin

  process(CLK)
  begin
    if(CLK'event and CLK = '1') then
      if (RESET = '1') then
        poly <= "000" & x"0000000";
      elsif DATA_VALID_IN = '1' then
        poly31   <= poly(3) xor poly(0) xor datain(0);
        poly(0)  <= poly(4) xor poly(1) xor datain(1);
        poly(1)  <= poly(5) xor poly(2) xor datain(2);
        poly(2)  <= poly(6) xor poly(3) xor datain(3);
        poly(3)  <= poly(7) xor poly(4) xor datain(4);
        poly(4)  <= poly(8) xor poly(5) xor datain(5);
        poly(5)  <= poly(9) xor poly(6) xor datain(6);
        poly(6)  <= poly(10) xor poly(7) xor datain(7);
        poly(7)  <= poly(11) xor poly(8) xor datain(8);
        poly(8)  <= poly(12) xor poly(9) xor datain(9);
        poly(9)  <= poly(13) xor poly(10) xor datain(10);
        poly(10) <= poly(14) xor poly(11) xor datain(11);
        poly(11) <= poly(15) xor poly(12) xor datain(12);
        poly(12) <= poly(16) xor poly(13) xor datain(13);
        poly(13) <= poly(17) xor poly(14) xor datain(14);
        poly(14) <= poly(18) xor poly(15) xor datain(15);
        poly(15) <= poly(19) xor poly(16) xor datain(16);
        poly(16) <= poly(20) xor poly(17) xor datain(17);
        poly(17) <= poly(21) xor poly(18) xor datain(18);
        poly(18) <= poly(22) xor poly(19) xor datain(19);
        poly(19) <= poly(23) xor poly(20) xor datain(20);
        poly(20) <= poly(24) xor poly(21) xor datain(21);
        poly(21) <= poly(25) xor poly(22) xor datain(22);
        poly(22) <= poly(26) xor poly(23) xor datain(23);
        poly(23) <= poly(27) xor poly(24) xor datain(24);
        poly(24) <= poly(28) xor poly(25) xor datain(25);
        poly(25) <= poly(29) xor poly(26) xor datain(26);
        poly(26) <= poly(30) xor poly(27) xor datain(27);
        poly(27) <= poly(3) xor poly(0) xor datain(0) xor poly(28) xor datain(28);
        poly(28) <= poly(4) xor poly(1) xor datain(1) xor poly(29) xor datain(29);
        poly(29) <= poly(5) xor poly(2) xor datain(2) xor poly(30) xor datain(30);
        poly(30) <= poly(6) xor poly(3) xor datain(3) xor poly(3) xor poly(0) xor datain(0) xor datain(31);
      else
        poly <= poly;
      end if;

      if (RESET = '1') then
        PRBS_DATA_OUT <= (others => '0');
      elsif (DATA_VALID_IN_r = '1') then
        PRBS_DATA_OUT <= poly & poly31;
      else
        if comma_type_r = "01" then
          PRBS_DATA_OUT <= x"1234563C";
        elsif comma_type_r = "10" then
          PRBS_DATA_OUT <= x"123456DC";
        else
          PRBS_DATA_OUT <= x"123456BC";
        end if;
      end if;

      DATA_VALID_IN_r <= DATA_VALID_IN;
      comma_type_r    <= comma_type;
    end if;
  end process;


end RTL;
