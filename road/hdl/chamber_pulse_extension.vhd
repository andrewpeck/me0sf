----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--   Pulse extension for a whole chamber
----------------------------------------------------------------------------------

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity chamber_pulse_extension is
  generic(
    LENGTH : integer := 4
    );
  port(
    clock   : in  std_logic;
    sbits_i : in  chamber_t;
    sbits_o : out chamber_t
    );
end chamber_pulse_extension;

architecture behavioral of chamber_pulse_extension is

begin
  

  prt_gen : for I in 0 to 7 generate
    ly_gen : for J in 0 to 5 generate
      strip_gen : for K in 0 to 191 generate

        pulse_extension_1 : entity work.pulse_extension
          generic map
          (MAX => LENGTH)
          port map
          (clock  => clock, d => sbits_i(I)(J)(K), q => sbits_o(I)(J)(K));

      end generate;
    end generate;
  end generate;  

end behavioral;
