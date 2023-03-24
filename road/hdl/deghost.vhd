library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

entity deghost is
  generic(
    WIDTH        : positive := 191;
    GROUP_WIDTH  : natural  := 0;
    EDGE_DIST    : natural  := 2;
    CHECK_IDS    : boolean  := false;
    CHECK_STRIPS : boolean  := false
    );
  port(
    clock      : in  std_logic;
    dav_i      : in  std_logic;
    dav_o      : out std_logic;
    segments_i : in  segment_list_t (WIDTH-1 downto 0);
    segments_o : out segment_list_t (WIDTH-1 downto 0)
    );
end deghost;

architecture behavioral of deghost is

  function at_edge (X : integer; W : integer; D : integer)
    return boolean is
  begin
    return ((X mod W) < D or (X mod W) >= (W-D));
  end;

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then

      dav_o <= dav_i;

      for I in segments_i'range loop

        if (GROUP_WIDTH > 0 and not at_edge(I, GROUP_WIDTH, EDGE_DIST)) then

          segments_o(I) <= segments_i(I);

        elsif (I /= WIDTH-1 and

            -- FIXME: either the I+1 or the I-1 should probably be a <=
            -- so that they don't all just cancel and get lost?
            (segments_i(I) < segments_i(I+1))

            and

            (not CHECK_STRIPS or
             (segments_i(I+1).strip - segments_i(I).strip < 2))

            and

            (not CHECK_IDS or
             ((segments_i(I).id = segments_i(I+1).id) or
              segments_i(I).id = segments_i(I+1).id + 2 or
              segments_i(I).id + 2 = segments_i(I+1).id))) then

          segments_o(I) <= null_pattern;

        elsif (I /= 0 and

               (segments_i(I) < segments_i(I-1))

               and

               (not CHECK_STRIPS or
                (segments_i(I).strip - segments_i(I-1).strip) < 2)

               and

               (not CHECK_IDS or
                ((segments_i(I).id = segments_i(I-1).id) or
                 segments_i(I).id = segments_i(I-1).id - 2 or
                 segments_i(I).id - 2 = segments_i(I-1).id))) then

          segments_o(I) <= null_pattern;

        else

          segments_o(I) <= segments_i(I);

        end if;
      end loop;
    end if;
  end process;

end behavioral;
