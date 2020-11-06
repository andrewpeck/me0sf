library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use work.pat_pkg.all;

package patterns is

  constant pat_straight : pat_unit_t := (
    id  => 7,
    ly0 => (lo => -1, hi => 1),
    ly1 => (lo => -1, hi => 1),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo => -1, hi => 1),
    ly5 => (lo => -1, hi => 1)
    );

  constant pat_l : pat_unit_t := (
    id  => 6,
    ly0 => (lo => -4, hi => -1),
    ly1 => (lo => -3, hi => 0),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo =>  0, hi => 3),
    ly5 => (lo =>  1, hi => 4)
    );

  constant pat_r : pat_unit_t := mirror_pat_unit (pat_l, 3);

  constant pat_ll : pat_unit_t := (
    id  => 5,
    ly0 => (lo => -5, hi => 2),
    ly1 => (lo => -4, hi => 1),
    ly2 => (lo => -1, hi => 1),
    ly3 => (lo => -1, hi => 1),
    ly4 => (lo =>  1, hi => 4),
    ly5 => (lo =>  2, hi => 5)
    );

  constant pat_rr : pat_unit_t := mirror_pat_unit (pat_ll, 4);

  constant pat_list : pat_list_t := (pat_straight, pat_l, pat_r, pat_ll,pat_rr);

end package patterns;
