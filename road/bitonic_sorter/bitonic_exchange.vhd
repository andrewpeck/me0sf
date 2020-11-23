-----------------------------------------------------------------------------------
--!     @file    bitonic_exchange.vhd
--!     @brief   Bitonic Sorter Network Exchange Module :
--!     @version 0.0.1
--!     @date    2015/12/26
--!     @author  Ichiro Kawazome <ichiro_k@ca2.so-net.ne.jp>
-----------------------------------------------------------------------------------
--
--      Copyright (C) 2015 Ichiro Kawazome
--      All rights reserved.
--
--      Redistribution and use in source and binary forms, with or without
--      modification, are permitted provided that the following conditions
--      are met:
--
--        1. Redistributions of source code must retain the above copyright
--           notice, this list of conditions and the following disclaimer.
--
--        2. Redistributions in binary form must reproduce the above copyright
--           notice, this list of conditions and the following disclaimer in
--           the documentation and/or other materials provided with the
--           distribution.
--
--      THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
--      "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
--      LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
--      A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
--      OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
--      SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
--      LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
--      DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
--      THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
--      (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
--      OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--
-----------------------------------------------------------------------------------
library ieee;
use     ieee.std_logic_1164.all;
entity  Bitonic_Exchange is
    generic (
        WORD_BITS :  integer := 64;
        COMP_HIGH :  integer := 63;
        COMP_LOW  :  integer := 32
    );
    port (
        I_SORT    :  in  std_logic;
        I_UP      :  in  std_logic;
        I_A       :  in  std_logic_vector(WORD_BITS-1 downto 0);
        I_B       :  in  std_logic_vector(WORD_BITS-1 downto 0);
        O_A       :  out std_logic_vector(WORD_BITS-1 downto 0);
        O_B       :  out std_logic_vector(WORD_BITS-1 downto 0)
    );
end Bitonic_Exchange;
library ieee;
use     ieee.std_logic_1164.all;
use     ieee.numeric_std.all;
architecture RTL of Bitonic_Exchange is
    
begin
    process(I_SORT, I_UP, I_A, I_B)
        variable comp_a  :  unsigned(COMP_HIGH-COMP_LOW downto 0);
        variable comp_b  :  unsigned(COMP_HIGH-COMP_LOW downto 0);
        variable a_gt_b  :  boolean;
    begin
        comp_a := unsigned(I_A(COMP_HIGH downto COMP_LOW));
        comp_b := unsigned(I_B(COMP_HIGH downto COMP_LOW));
        a_gt_b := (comp_a > comp_b);
        if (I_SORT = '1' and I_UP = '1' and a_gt_b = TRUE ) or
           (I_SORT = '1' and I_UP = '0' and a_gt_b = FALSE) then
            O_A <= I_B;
            O_B <= I_A;
        else
            O_A <= I_A;
            O_B <= I_B;
        end if;
    end process;
end RTL;
