use std.textio.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_types.all;

package pat_pkg is

  --------------------------------------------------------------------------------
  -- Build Parameters
  --------------------------------------------------------------------------------

  constant S0_REGION_SIZE : positive              := 16;
  constant CNT_THRESH     : natural               := 4;
  constant PRT_WIDTH      : positive              := 192;
  constant PAT_UNIT_MUX   : positive range 1 to 8 := 8; -- 1, 2, 4, or 8

  --------------------------------------------------------------------------------
  -- Types for patterns
  --------------------------------------------------------------------------------

  constant null_pattern : segment_t :=
    (
      cnt       => (others => '0'),
      id        => (others => '0'),
      hits      => (others => (others => '0')),
      partition => (others => '0'),
      strip     => (others => '0')
      );

  --------------------------------------------------------------------------------
  -- Pattern Helper Functions
  --------------------------------------------------------------------------------

  -- mirror a pattern unit (left/right symmetry)
  function mirror_patdef (pat : patdef_t; id : natural) return patdef_t;

  function get_sortb (x : std_logic_vector) return std_logic_vector;

  -- comparisons
  function "<"(L  : segment_t; R : segment_t) return boolean;
  function ">"(L  : segment_t; R : segment_t) return boolean;
  function "="(L  : segment_t; R : segment_t) return boolean;
  function ">="(L : segment_t; R : segment_t) return boolean;
  function "<="(L : segment_t; R : segment_t) return boolean;

  procedure check_pattern_operators (nil : boolean);

  procedure print_layer (layer : layer_t);
  procedure print_partition (partition : partition_t);

end package pat_pkg;

package body pat_pkg is

  function get_sortb (x : std_logic_vector) return std_logic_vector is
    variable y : std_logic_vector(PATTERN_SORTB-1 downto 0);
  begin
    y := x(PATTERN_SORTB-1 downto 0);
    return y;
  end;

  function mirror_patdef (pat : patdef_t; id : natural) return patdef_t is
    variable result : patdef_t;
  begin
    result.id  := id;
    result.ly0 := (hi => pat.ly0.lo * (-1), lo => pat.ly0.hi * (-1));
    result.ly1 := (hi => pat.ly1.lo * (-1), lo => pat.ly1.hi * (-1));
    result.ly2 := (hi => pat.ly2.lo * (-1), lo => pat.ly2.hi * (-1));
    result.ly3 := (hi => pat.ly3.lo * (-1), lo => pat.ly3.hi * (-1));
    result.ly4 := (hi => pat.ly4.lo * (-1), lo => pat.ly4.hi * (-1));
    result.ly5 := (hi => pat.ly5.lo * (-1), lo => pat.ly5.hi * (-1));
    return result;
  end;

  function "=" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left := convert(L, left);
    right := convert(R, right);
    return (unsigned(get_sortb(left)) = unsigned(get_sortb(right)));
  end;

  function ">" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left := convert(L, left);
    right := convert(R, right);
    return (unsigned(get_sortb(left)) > unsigned(get_sortb(right)));
  end;

  function "<" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left := convert(L, left);
    right := convert(R, right);

    -- report "Comparison L < R" & LF & " > left  cnt=" & to_string(get_sortb(left)(6 downto 4))
    --   & " pid=" & to_string(get_sortb(left)(3 downto 0)) &  LF &
    --   " > right cnt=" & to_string(get_sortb(right)(6 downto 4))
    --   & " pid=" & to_string(get_sortb(right)(3 downto 0))
    -- severity note;

    return (unsigned(get_sortb(left)) < unsigned(get_sortb(right)));
  end;

  function "<=" (L : segment_t; R : segment_t) return boolean is
  begin
    return L<R or L=R;
  end;

  function ">=" (L : segment_t; R : segment_t) return boolean is
  begin
    return L>R or L=R;
  end;

  -- unit test function to check that the sorting operators are working correctly
  procedure check_pattern_operators (nil : boolean) is
    variable ply0 : segment_t := (cnt => to_unsigned(0, CNT_BITS), id => x"A", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));
    variable ply1 : segment_t := (cnt => to_unsigned(1, CNT_BITS), id => x"9", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));
    variable ply2 : segment_t := (cnt => to_unsigned(2, CNT_BITS), id => x"8", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));

    variable pat0 : segment_t := (cnt => to_unsigned(1, CNT_BITS), id => x"0", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));
    variable pat1 : segment_t := (cnt => to_unsigned(1, CNT_BITS), id => x"1", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));
    variable pat2 : segment_t := (cnt => to_unsigned(1, CNT_BITS), id => x"2", hits => (others => (others => '0')), partition => (others => '0'), strip => (others => '0'));
  begin

    report "===========================" severity note;
    report "Testing pattern comparators" severity note;
    report "===========================" severity note;

    -- > testing
    assert ply2 > ply1 report "ERROR: pattern > failure" severity error;
    assert ply1 > ply0 report "ERROR: pattern > failure" severity error;
    assert pat2 > pat1 report "ERROR: pattern > failure" severity error;
    assert pat1 > pat0 report "ERROR: pattern > failure" severity error;

    -- < testing
    assert ply0 < ply1 report "ERROR: pattern < failure" severity error;
    assert ply0 < ply2 report "ERROR: pattern < failure" severity error;
    assert ply1 < ply2 report "ERROR: pattern < failure" severity error;
    assert pat0 < pat1 report "ERROR: pattern < failure" severity error;
    assert pat0 < pat2 report "ERROR: pattern < failure" severity error;
    assert pat1 < pat2 report "ERROR: pattern < failure" severity error;

    -- <= testing
    assert ply0 <= ply0 report "ERROR: pattern <= failure" severity error;
    assert ply0 <= ply1 report "ERROR: pattern <= failure" severity error;
    assert pat0 <= pat0 report "ERROR: pattern <= failure" severity error;
    assert pat0 <= pat1 report "ERROR: pattern <= failure" severity error;

    -- >= testing
    assert ply0 >= ply0 report "ERROR: pattern >= failure" severity error;
    assert ply1 >= ply0 report "ERROR: pattern >= failure" severity error;
    assert pat0 >= pat0 report "ERROR: pattern >= failure" severity error;
    assert pat1 >= pat0 report "ERROR: pattern >= failure" severity error;

    -- = testing
    assert ply0 = ply0 report "ERROR: pattern = failure" severity error;
    assert ply1 = ply1 report "ERROR: pattern = failure" severity error;
    assert ply2 = ply2 report "ERROR: pattern = failure" severity error;
    assert pat0 = pat0 report "ERROR: pattern = failure" severity error;
    assert pat1 = pat1 report "ERROR: pattern = failure" severity error;
    assert pat2 = pat2 report "ERROR: pattern = failure" severity error;

  end;

  procedure print_layer (layer : layer_t) is
    variable lyline : line;
  begin
    write (lyline, layer);
    writeline(output, lyline);
  end procedure;

  procedure print_partition (partition : partition_t) is
  begin
    print_layer(partition(0));
    print_layer(partition(1));
    print_layer(partition(2));
    print_layer(partition(3));
    print_layer(partition(4));
    print_layer(partition(5));
  end procedure;

end package body pat_pkg;
