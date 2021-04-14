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
end chamber_tb;

architecture behavioral of chamber_tb is

  signal clock    : std_logic;
  signal phase    : integer := 0;
  signal sbits    : chamber_t := (others => (others => (others => '0')));
  signal segs     : candidate_list_t (NUM_SEGMENTS-1 downto 0);

  signal dav_i : std_logic := '0';

  constant clk_period : time := 50 ns;
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
      if (phase < 7) then
        phase <= phase + 1;
      else
        phase <= 0;
      end if;
    end if;
  end process;


  dav_i <= '1' when phase = 0 else '0';

  sbits(0)(0)(1) <= '1';
  sbits(0)(1)(1) <= '1';
  sbits(0)(2)(1) <= '1';
  sbits(0)(3)(1) <= '1';
  sbits(0)(4)(1) <= '1';
  sbits(0)(5)(1) <= '1';

  chamber_inst : entity work.chamber
    generic map (
      NUM_SEGMENTS => NUM_SEGMENTS
      )
    port map (
      clock   => clock,
      dav_i   => dav_i,
      dav_o   => open,
      sbits_i => sbits,
      segs_o  => segs);

end behavioral;
