library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use work.pat_pkg.all;

package patterns is

  constant pat_straight : pat_unit_t := (
    id  => 15,
    ly0 => (lo => -1, hi => 1),
    ly1 => (lo => -1, hi => 1),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo => -1, hi => 1),
    ly5 => (lo => -1, hi => 1)
    );

  --------------------------------------------------------------------------------

  constant pat_l : pat_unit_t := (
    id  => 12,
    ly0 => (lo => -4, hi => -1),
    ly1 => (lo => -3, hi => 0),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo => 0, hi => 3),
    ly5 => (lo => 1, hi => 4)
    );

  constant pat_r : pat_unit_t := mirror_pat_unit (pat_l, pat_l.id-1);

  --------------------------------------------------------------------------------

  constant pat_l2 : pat_unit_t := (
    id  => 10,
    ly0 => (lo => -5, hi => -2),
    ly1 => (lo => -4, hi => 1),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo => 1, hi => 4),
    ly5 => (lo => 2, hi => 5)
    );

  constant pat_r2 : pat_unit_t := mirror_pat_unit (pat_l2, pat_l2.id-1);

  --------------------------------------------------------------------------------

  constant pat_l3 : pat_unit_t := (
    id  => 8,
    ly0 => (lo => -8, hi => -5),
    ly1 => (lo => -7, hi => -4),
    ly2 => (lo => -3, hi => 0),
    ly3 => (lo => -2, hi => 2),
    ly4 => (lo => 4, hi => 7),
    ly5 => (lo => 5, hi => 8)
    );

  constant pat_r3 : pat_unit_t := mirror_pat_unit (pat_l3, pat_l3.id-1);

  --------------------------------------------------------------------------------

  constant pat_l4 : pat_unit_t := (
    id  => 6,
    ly0 => (lo => -8, hi => -5),
    ly1 => (lo => -7, hi => -4),
    ly2 => (lo => -3, hi => 0),
    ly3 => (lo => -2, hi => 2),
    ly4 => (lo => 4, hi => 7),
    ly5 => (lo => 5, hi => 8)
    );

  constant pat_r4 : pat_unit_t := mirror_pat_unit (pat_l4, pat_l4.id-1);

  --------------------------------------------------------------------------------

  constant pat_l5 : pat_unit_t := (
    id  => 4,
    ly0 => (lo => -11, hi => -8),
    ly1 => (lo => -9, hi => -5),
    ly2 => (lo => -3, hi => 0),
    ly3 => (lo => 0, hi => 3),
    ly4 => (lo => 5, hi => 9),
    ly5 => (lo => 8, hi => 11)
    );

  constant pat_r5 : pat_unit_t := mirror_pat_unit (pat_l5, pat_l5.id-1);

  --------------------------------------------------------------------------------

  constant pat_list : pat_list_t (10 downto 0) := (pat_straight,
                                                   pat_l, pat_r,
                                                   pat_l2, pat_r2,
                                                   pat_l3, pat_r3,
                                                   pat_l4, pat_r4,
                                                   pat_l5, pat_r5
                                                   );

  function get_max_span (layer : integer; pat_list : pat_list_t) return integer;

end package patterns;

package body patterns is
  function get_max_span (layer : integer; pat_list : pat_list_t) return integer is
    variable min_l : integer := 0;
    variable max_r : integer := 0;
    variable ly    : hi_lo_t;
  begin
    for I in pat_list'range loop
      if (layer = 0) then
        ly := pat_list(I).ly0;
      elsif (layer = 1) then
        ly := pat_list(I).ly1;
      elsif (layer = 2) then
        ly := pat_list(I).ly2;
      elsif (layer = 3) then
        ly := pat_list(I).ly3;
      elsif (layer = 4) then
        ly := pat_list(I).ly4;
      elsif (layer = 5) then
        ly := pat_list(I).ly5;
      end if;

      if (ly.lo < min_l) then
        min_l := ly.lo;
      end if;

      if (ly.hi > max_r) then
        max_r := ly.hi;
      end if;
    end loop;
    return max_r - min_l + 1;
  end;

end package body patterns;
