use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber_prbs is
  generic (
    NUM_SEGMENTS : integer := 4
    );
  port(
    reset : in  std_logic;
    clock : in  std_logic;
    segs  : out candidate_list_t (NUM_SEGMENTS-1 downto 0)
    );
end chamber_prbs;

architecture behavioral of chamber_prbs is

  signal phase : integer := 0;
  signal sbits : chamber_t;

begin

  prtgen : for partition in 0 to 7 generate
  begin
    layergen : for layer in 0 to 5 generate
    begin
      halffatgen : for halffat in 0 to 5 generate
      begin

        PRBS31_32BIT_GEN_1 : entity work.PRBS31_32BIT_GEN
          port map (
            DATAIN        => std_logic_vector(to_unsigned(partition + layer + halffat, 32)),
            PRBS_DATA_OUT => sbits(partition)(layer)(32*(halffat+1)-1 downto 32*halffat),
            DATA_VALID_IN => '0',
            comma_type    => "00",
            CLK           => clock,
            RESET         => reset
            );

      end generate;
    end generate;
  end generate;

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
      NUM_SEGMENTS => NUM_SEGMENTS
      )
    port map (
      clock    => clock,
      phase    => phase,
      sbits    => sbits,
      segs     => segs);

end behavioral;
