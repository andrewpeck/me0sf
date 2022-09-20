-----------------------------------------------------------------------------------
--!     @file    bitonic_merge.vhd
--!     @brief   Bitonic Sorter Network Merge Module :
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

entity  Bitonic_Merge is
    generic (
        STAGE     :  integer :=  0;
        REGSTAGES :  integer :=  1;
        WORDS     :  integer :=  1;
        WORD_BITS :  integer := 64;
        COMP_HIGH :  integer := 63;
        COMP_LOW  :  integer := 32;
        INFO_BITS :  integer :=  4
    );
    port (
        CLK       :  in  std_logic;
        RST       :  in  std_logic;
        CLR       :  in  std_logic;
        I_SORT    :  in  std_logic;
        I_UP      :  in  std_logic;
        I_DATA    :  in  std_logic_vector(WORDS*WORD_BITS-1 downto 0);
        I_INFO    :  in  std_logic_vector(      INFO_BITS-1 downto 0);
        O_SORT    :  out std_logic;
        O_UP      :  out std_logic;
        O_DATA    :  out std_logic_vector(WORDS*WORD_BITS-1 downto 0);
        O_INFO    :  out std_logic_vector(      INFO_BITS-1 downto 0)
    );
end Bitonic_Merge;
library ieee;
use     ieee.std_logic_1164.all;
architecture RTL of Bitonic_Merge is
begin
    ONE: if (WORDS = 1) generate
        O_DATA <= I_DATA;
        O_INFO <= I_INFO;
        O_SORT <= I_SORT;
        O_UP   <= I_UP;
    end generate;
    ANY: if (WORDS > 1) generate
        constant DIST   :  integer := WORDS / 2;
        signal   s_data :  std_logic_vector(WORDS*WORD_BITS-1 downto 0);
        signal   q_data :  std_logic_vector(WORDS*WORD_BITS-1 downto 0);
        signal   q_info :  std_logic_vector(      INFO_BITS-1 downto 0);
        signal   q_sort :  std_logic;
        signal   q_up   :  std_logic;
    begin
        XCHG: for i in 0 to DIST-1 generate
            U: entity work.Bitonic_Exchange generic map(WORD_BITS, COMP_HIGH, COMP_LOW)
            port map (
                I_SORT  => I_SORT,
                I_UP    => I_UP  ,
                I_A     => I_DATA(WORD_BITS*(i     +1)-1 downto WORD_BITS*(i     )),
                I_B     => I_DATA(WORD_BITS*(i+DIST+1)-1 downto WORD_BITS*(i+DIST)),
                O_A     => s_data(WORD_BITS*(i     +1)-1 downto WORD_BITS*(i     )),
                O_B     => s_data(WORD_BITS*(i+DIST+1)-1 downto WORD_BITS*(i+DIST))
            );
        end generate;

        process (CLK, RST) begin
            if (RST = '1') then
                    q_data <= (others => '0');
                    q_info <= (others => '0');
                    q_sort <= '1';
                    q_up   <= '1';
            elsif (rising_edge(CLK) or (STAGE mod REGSTAGES /= 0)) then
                if (CLR = '1') then
                    q_data <= (others => '0');
                    q_info <= (others => '0');
                    q_sort <= '1';
                    q_up   <= '1';
                else
                    q_data <= s_data;
                    q_info <= I_INFO;
                    q_sort <= I_SORT;
                    q_up   <= I_UP;
                end if;
            end if;
        end process;
        FIRST : entity work.Bitonic_Merge generic map (STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, INFO_BITS)
            port map (
                CLK     => CLK,
                RST     => RST,
                CLR     => CLR,
                I_SORT  => q_sort,
                I_UP    => q_up,
                I_INFO  => q_info,
                I_DATA  => q_data(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0),
                O_SORT  => O_SORT,
                O_UP    => O_UP,
                O_INFO  => O_INFO,
                O_DATA  => O_DATA(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0)
            );
        SECOND: entity work.Bitonic_Merge generic map (STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, INFO_BITS)
            port map (
                CLK     => CLK,
                RST     => RST,
                CLR     => CLR,
                I_SORT  => q_sort,
                I_UP    => q_up,
                I_INFO  => q_info,
                I_DATA  => q_data(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2)),
                O_SORT  => open,
                O_UP    => open,
                O_INFO  => open,
                O_DATA  => O_DATA(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2))
            );
    end generate;
end RTL;
