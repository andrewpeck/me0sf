library work;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber_tb is
  generic (
    NUM_SEGMENTS : integer := 16;
    MUX_FACTOR   : integer := 1
    );
end chamber_prbs;

architecture behavioral of chamber_prbs is

  signal In_Valid : std_logic;
  signal In_IsKey : std_logic;
  signal clock    : std_logic;
  signal reset    : std_logic;
  signal phase : integer := 0;
  signal sbits : chamber_t;
  signal segs  : candidate_list_t (NUM_SEGMENTS-1 downto 0);

  constant clk_period : time := 3 ns;
  constant sim_period : time := 50 ms;

begin

  clk : process
  begin
    wait for clk_period/2.0;
    clock <= '0';
    wait for clk_period/2.0;
    clock <= '1';
  end process;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      if (phase < 8) then
        phase <= phase + 1;
      else
        phase <= 0;
      end if;
    end if;
  end process;


  chamber_inst : entity work.chamber
    generic map (
      NUM_SEGMENTS => NUM_SEGMENTS,
      MUX_FACTOR   => MUX_FACTOR)
    port map (
      In_Valid => In_Valid,
      In_IsKey => In_IsKey,
      clock    => clock,
      sbits_i    => sbits,
      segs_o     => segs);

end behavioral;
