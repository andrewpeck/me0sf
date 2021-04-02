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
    id  => 14,
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
    id  => 12,
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
    id  => 10,
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
    id  => 8,
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
    id  => 6,
    ly0 => (lo => -11, hi => -8),
    ly1 => (lo => -9, hi => -5),
    ly2 => (lo => -3, hi => 0),
    ly3 => (lo => 0, hi => 3),
    ly4 => (lo => 5, hi => 9),
    ly5 => (lo => 8, hi => 11)
    );

  constant pat_r5 : pat_unit_t := mirror_pat_unit (pat_l5, pat_l5.id-1);

  --------------------------------------------------------------------------------

  constant pat_l6 : pat_unit_t := (
    id  => 4,
    ly0 => (lo => -15, hi => -11),
    ly1 => (lo => -11, hi => -9),
    ly2 => (lo => -9, hi => 4),
    ly3 => (lo => 4, hi => 9),
    ly4 => (lo => 9, hi => 11),
    ly5 => (lo => 11, hi => 15)
    );

  constant pat_r6 : pat_unit_t := mirror_pat_unit (pat_l6, pat_l6.id-1);

  --------------------------------------------------------------------------------

  constant pat_l7 : pat_unit_t := (
    id  => 2,
    ly0 => (lo => -18, hi => -10),
    ly1 => (lo => -14, hi => -6),
    ly2 => (lo => -9, hi => 2),
    ly3 => (lo => 2, hi => 9),
    ly4 => (lo => 6, hi => 14),
    ly5 => (lo => 10, hi => 18)
    );

  constant pat_r7 : pat_unit_t := mirror_pat_unit (pat_l7, pat_l7.id-1);

  --------------------------------------------------------------------------------

  constant NUM_PATTERNS : integer := 15;
  constant pat_list : pat_list_t (NUM_PATTERNS-1 downto 0) := (pat_straight,
                                                   pat_l, pat_r,
                                                   pat_l2, pat_r2,
                                                   pat_l3, pat_r3,
                                                   pat_l4, pat_r4,
                                                   pat_l5, pat_r5,
                                                   pat_l6, pat_r6,
                                                   pat_l7, pat_r7
                                                   );

  procedure print_pattern (pat : pat_unit_t);
  function get_max_span (list  : pat_list_t) return integer;
  function get_pat_span (pat   : pat_unit_t) return integer;

end package patterns;

package body patterns is

  procedure print_pattern (pat : pat_unit_t) is
    variable span : integer := get_pat_span(pat);
    variable ly0 : string (1 to span);
    variable ly1 : string (1 to span);
    variable ly2 : string (1 to span);
    variable ly3 : string (1 to span);
    variable ly4 : string (1 to span);
    variable ly5 : string (1 to span);
  begin

    for I in 1 to span loop
      ly0(I):='-';
      ly1(I):='-';
      ly2(I):='-';
      ly3(I):='-';
      ly4(I):='-';
      ly5(I):='-';

      if (I-(span-1)/2-1 >= pat.ly0.lo and I-(span-1)/2-1 <= pat.ly0.hi) then
        ly0(I):='x';
      end if;
      if (I-(span-1)/2-1 >= pat.ly1.lo and I-(span-1)/2-1 <= pat.ly1.hi) then
        ly1(I):='x';
      end if;
      if (I-(span-1)/2-1 >= pat.ly2.lo and I-(span-1)/2-1 <= pat.ly2.hi) then
        ly2(I):='x';
      end if;
      if (I-(span-1)/2-1 >= pat.ly3.lo and I-(span-1)/2-1 <= pat.ly3.hi) then
        ly3(I):='x';
      end if;
      if (I-(span-1)/2-1 >= pat.ly4.lo and I-(span-1)/2-1 <= pat.ly4.hi) then
        ly4(I):='x';
      end if;
      if (I-(span-1)/2-1 >= pat.ly5.lo and I-(span-1)/2-1 <= pat.ly5.hi) then
        ly5(I):='x';
      end if;

    end loop;

    report "--pat=" & integer'image(pat.id) &
"  span=" & integer'image(span)
      severity note;
    report "ly0 " & ly0 severity note;
    report "ly1 " & ly1 severity note;
    report "ly2 " & ly2 severity note;
    report "ly3 " & ly3 severity note;
    report "ly4 " & ly4 severity note;
    report "ly5 " & ly5 severity note;

  end;

  function get_max_span (list : pat_list_t) return integer is
    variable max : integer := 0;
    variable tmp : integer := 0;
  begin
    for I in list'range loop
      tmp := get_pat_span(list(I));
      if (tmp > max) then
        max := tmp;
      end if;
    end loop;
    return 2*max+1;
  end;

  function get_pat_span (pat : pat_unit_t) return integer is
    variable min_l : integer := 99;
    variable max_r : integer := -99;
    variable ly    : hi_lo_t;
  begin

    for layer in 0 to 5 loop
    if (layer = 0) then
      ly := pat.ly0;
    elsif (layer = 1) then
      ly := pat.ly1;
    elsif (layer = 2) then
      ly := pat.ly2;
    elsif (layer = 3) then
      ly := pat.ly3;
    elsif (layer = 4) then
      ly := pat.ly4;
    elsif (layer = 5) then
      ly := pat.ly5;
    end if;

    if (ly.lo < min_l) then
      min_l := ly.lo;
    end if;

    if (ly.hi > max_r) then
      max_r := ly.hi;
    end if;
    end loop;

    return (max_r - min_l)+1;
  end;

end package body patterns;
