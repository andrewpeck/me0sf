-----------------------------------------------------------------------------------
--!     @file    bitonic_sorter.vhd
--!     @brief   Bitonic Sorter Module :
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
use ieee.std_logic_1164.all;

entity bitonic_sorter is
  generic (
    STAGE       : integer := 0;
    REGSTAGES   : integer := 1;
    WORDS       : integer := 8;
    WORD_BITS   : integer := 64;
    COMP_HIGH   : integer := 63;
    COMP_LOW    : integer := 32;
    INFO_BITS   : integer := 4;
    REG_OUTPUTS : boolean := false;
    REG_MERGES  : boolean := false
    );
  port (
    clk    : in  std_logic := '0';
    rst    : in  std_logic := '0';
    clr    : in  std_logic := '0';
    i_sort : in  std_logic := '0';
    i_up   : in  std_logic := '0';
    i_data : in  std_logic_vector(WORDS*WORD_BITS-1 downto 0) := (others => '0');
    i_info : in  std_logic_vector(INFO_BITS-1 downto 0) := (others => '0');
    o_sort : out std_logic;
    o_up   : out std_logic;
    o_data : out std_logic_vector(WORDS*WORD_BITS-1 downto 0);
    o_info : out std_logic_vector(INFO_BITS-1 downto 0)
    );
end bitonic_sorter;

architecture RTL of bitonic_sorter is
begin

  ONE : if (WORDS <= 1) generate
    process (clk, i_data, i_info, i_sort, i_up) is
    begin
      if (rising_edge(clk) or not REG_OUTPUTS) then
        o_data <= i_data;
        o_info <= i_info;
        o_sort <= i_sort;
        o_up   <= i_up;
      end if;
    end process;
  end generate;

  ANY : if (WORDS > 1) generate
    constant UP_POS : integer := I_INFO'high+1;
    signal s_info   : std_logic_vector(I_INFO'high+1 downto 0);
    signal q_info   : std_logic_vector(I_INFO'high+1 downto 0);
    signal q_data   : std_logic_vector(WORDS*WORD_BITS-1 downto 0);
    signal q_sort   : std_logic;
  begin

    s_info(UP_POS)       <= I_UP;
    s_info(I_INFO'range) <= I_INFO;

    FIRST : entity work.bitonic_sorter
      generic map (
        STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, s_info'length, REG_OUTPUTS)
      port map (
        clk    => clk,
        rst    => rst,
        clr    => clr,
        i_sort => i_sort,
        i_up   => '1',
        i_info => s_info,
        i_data => i_data(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0),
        o_sort => q_sort,
        o_up   => open,
        o_info => q_info,
        o_data => q_data(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0)
        );

    SECOND : entity work.bitonic_sorter
      generic map (
        STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, s_info'length, REG_OUTPUTS, REG_MERGES)
      port map (
        clk    => clk,
        rst    => rst,
        clr    => clr,
        i_sort => i_sort,
        i_up   => '0',
        i_info => s_info,
        i_data => i_data(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2)),
        o_sort => open,
        o_up   => open,
        o_info => open,
        o_data => q_data(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2))
        );

    MERGE : entity work.Bitonic_Merge
      generic map (
        STAGE+1, REGSTAGES, WORDS, WORD_BITS, COMP_HIGH, COMP_LOW, INFO_BITS, REG_MERGES)
      port map (
        clk    => clk,
        rst    => rst,
        clr    => clr,
        i_sort => q_sort,
        i_up   => q_info(UP_POS),
        i_info => q_info(i_info'range),
        i_data => q_data,
        o_sort => o_sort,
        o_up   => o_up,
        o_info => o_info,
        o_data => o_data
        );

  end generate;
end RTL;
