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
use ieee.std_logic_1164.all;

entity Bitonic_Merge is
  generic (
    STAGE      : integer := 0;
    REGSTAGES  : integer := 1;
    WORDS      : integer := 1;
    WORD_BITS  : integer := 64;
    COMP_HIGH  : integer := 63;
    COMP_LOW   : integer := 32;
    INFO_BITS  : integer := 4;
    REG_MERGES : boolean := false
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
end Bitonic_Merge;

architecture RTL of Bitonic_Merge is
begin

--------------------------------------------------------------------------------
-- If there is only one word left, then output it
--------------------------------------------------------------------------------

  ONE : if (WORDS = 1) generate
    process (clk, i_data, i_info, i_sort, i_up) is
    begin
      if (rising_edge(clk) or not REG_MERGES) then
        o_data <= i_data;
        o_info <= i_info;
        o_sort <= i_sort;
        o_up   <= i_up;
      end if;
    end process;
  end generate;

  ANY : if (WORDS > 1) generate
    constant DIST : integer := WORDS / 2;
    signal s_data : std_logic_vector(WORDS*WORD_BITS-1 downto 0);
    signal q_data : std_logic_vector(WORDS*WORD_BITS-1 downto 0);
    signal q_info : std_logic_vector(INFO_BITS-1 downto 0);
    signal q_sort : std_logic;
    signal q_up   : std_logic;
  begin

    --------------------------------------------------------------------------------
    -- Generate N exchanges (asynchronously)
    --------------------------------------------------------------------------------

    XCHG : for i in 0 to DIST-1 generate
      U : entity work.Bitonic_Exchange
        generic map(
          WORD_BITS, COMP_HIGH, COMP_LOW)
        port map (
          i_sort => i_sort,
          i_up   => i_up,
          i_a    => i_data(WORD_BITS*(i +1)-1 downto WORD_BITS*(i)),
          i_b    => i_data(WORD_BITS*(i+DIST+1)-1 downto WORD_BITS*(i+DIST)),
          o_a    => s_data(WORD_BITS*(i +1)-1 downto WORD_BITS*(i)),
          o_b    => s_data(WORD_BITS*(i+DIST+1)-1 downto WORD_BITS*(i+DIST))
          );
    end generate;

    --------------------------------------------------------------------------------
    -- Register the exchanged data
    --------------------------------------------------------------------------------

    process (clk, rst)
    begin
      if (rst = '1') then
        q_data <= (others => '0');
        q_info <= (others => '0');
        q_sort <= '1';
        q_up   <= '1';
      elsif (rising_edge(clk) or (STAGE mod REGSTAGES /= 0)) then
        if (clr = '1') then
          q_data <= (others => '0');
          q_info <= (others => '0');
          q_sort <= '1';
          q_up   <= '1';
        else
          q_data <= s_data;
          q_info <= i_info;
          q_sort <= i_sort;
          q_up   <= i_up;
        end if;
      end if;
    end process;

    --------------------------------------------------------------------------------
    -- Split the exhanged data into two halves and merge recursively
    --------------------------------------------------------------------------------

    first : entity work.bitonic_merge
      generic map (
        STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, INFO_BITS, REG_MERGES)
      port map (
        clk    => clk,
        rst    => rst,
        clr    => clr,
        i_sort => q_sort,
        i_up   => q_up,
        i_info => q_info,
        i_data => q_data(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0),
        o_sort => o_sort,
        o_up   => o_up,
        o_info => o_info,
        o_data => o_data(WORD_BITS*(WORDS/2)-1 downto WORD_BITS*0)
        );

    second : entity work.bitonic_merge
      generic map (
        STAGE+1, REGSTAGES, WORDS/2, WORD_BITS, COMP_HIGH, COMP_LOW, INFO_BITS, REG_MERGES)
      port map (
        clk    => clk,
        rst    => rst,
        clr    => clr,
        i_sort => q_sort,
        i_up   => q_up,
        i_info => q_info,
        i_data => q_data(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2)),
        o_sort => open,
        o_up   => open,
        o_info => open,
        o_data => o_data(WORD_BITS*(WORDS)-1 downto WORD_BITS*(WORDS/2))
        );

  end generate;
end RTL;
