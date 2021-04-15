use std.textio.all;

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
    MUX_FACTOR : integer := 1
    );
end chamber_tb;

architecture behavioral of chamber_tb is

  signal clk40 : std_logic;
  signal clock : std_logic;
  signal phase : integer := 0;
  signal sbits : chamber_t := (others => (others => (others => '0')));
  signal segs : segment_list_t (NUM_SEGMENTS-1 downto 0);

  signal dav_i : std_logic := '0';

  constant clk_period : time := 10 ns;
  constant sim_period : time := 50 ms;

begin

  slowclk : process
  begin
    wait for 8*clk_period/2.0;
    clk40 <= '0';
    wait for 8*clk_period/2.0;
    clk40 <= '1';
  end process;

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

  stim : process
  begin

-- FIXME: for some reason 191 gets "stuck"
    for prt in 0 to 7 loop
      for ch in 0 to 190 loop

        sbits(prt)(0)(ch) <= '1';
        sbits(prt)(1)(ch) <= '1';
        sbits(prt)(2)(ch) <= '1';
        sbits(prt)(3)(ch) <= '1';
        sbits(prt)(4)(ch) <= '1';
        sbits(prt)(5)(ch) <= '1';

        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);
        wait until rising_edge(clock);

        -- print_partition(sbits(0));
        sbits(prt)(0)(ch) <= '0';
        sbits(prt)(1)(ch) <= '0';
        sbits(prt)(2)(ch) <= '0';
        sbits(prt)(3)(ch) <= '0';
        sbits(prt)(4)(ch) <= '0';
        sbits(prt)(5)(ch) <= '0';

        -- write(output, "pulsing " &
        --       " strip = " & integer'image(ch) &
        --       " prt   = " & integer'image(prt) & LF);

      end loop;
    end loop;

    std.env.finish;

  end process;

  rep : process
  begin
    --if ('1' = segs(0).strip.pattern.dav) then
    --if (segs(0).strip.pattern.cnt > 0) then
    wait until rising_edge(clock);
    if (phase = 0 and '1' = segs(0).strip.pattern.dav) then
    write(output, "  > output : prt=" & integer'image(segs(0).partition) &
          " strip = " & integer'image(segs(0).strip.strip) &
          " cnt = " & to_hstring(segs(0).strip.pattern.cnt) &
          " pid = " & to_hstring(segs(0).strip.pattern.id) & LF);
    end if;
  end process;

  chamber_inst : entity work.chamber
    generic map (
      NUM_SEGMENTS => NUM_SEGMENTS
      )
    port map (
      clock => clock,
      dav_i => dav_i,
      dav_o => open,
      sbits_i => sbits,
      segs_o => segs
      );

end behavioral;
