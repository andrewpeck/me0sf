----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
use std.textio.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_types.all;

package pat_pkg is


  function count_ones(slv : std_logic_vector) return natural;

  function if_then_else (bool : boolean; a : integer; b : integer)
    return integer;
  function if_then_else (bool : boolean; a : boolean; b : boolean)
    return boolean;
  function if_then_else (bool : boolean; a : std_logic; b : std_logic)
    return std_logic;
  function if_then_else (bool : boolean; a : std_logic_vector; b : std_logic_vector)
    return std_logic_vector;

  constant SELECTOR_LATENCY     : positive := 4;
  
  constant NUM_PATTERNS : integer := 17;

  type chamber_t is array(integer range 0 to 7) of partition_t;
  
  type ly_thresh_t is array(integer range 0 to NUM_PATTERNS-1) of std_logic_vector(2 downto 0);

  --------------------------------------------------------------------------------
  -- Build Parameters
  --------------------------------------------------------------------------------

  constant PRT_WIDTH : positive := 192;

  --------------------------------------------------------------------------------
  -- Types for patterns
  --------------------------------------------------------------------------------

  constant null_pat_unit_pre : pat_unit_pre_t :=
    (lc => (others => '0'),
     id => (others => '0'),
     hc => (others => '0'));

  constant null_pat_unit : pat_unit_t :=
    (lc    => (others => '0'),
     id    => (others => '0'));

  constant null_pat_unit_mux : pat_unit_mux_t :=
    (lc    => (others => '0'),
     id    => (others => '0'),
     strip => (others => '0'));

  constant null_pattern : segment_t :=
    (lc        => (others => '0'),
     id        => (others => '0'),
     partition => (others => '0'),
     strip     => (others => '0'));

  --------------------------------------------------------------------------------
  -- Pattern Helper Functions
  --------------------------------------------------------------------------------

  function valid (seg : segment_t) return boolean;
  function valid (seg : pat_unit_t) return boolean;
  function valid (seg : pat_unit_mux_t) return boolean;

  -- mirror a pattern unit (left/right symmetry)
  function mirror_patdef (pat : patdef_t; id : natural) return patdef_t;

  function segment_t_get_sortb (x      : std_logic_vector) return std_logic_vector;
  function pat_unit_mux_t_get_sortb (x : std_logic_vector) return std_logic_vector;

  -- comparisons
  function "<"(L  : pat_unit_mux_t; R : pat_unit_mux_t) return boolean;
  function ">"(L  : pat_unit_mux_t; R : pat_unit_mux_t) return boolean;
  function "="(L  : pat_unit_mux_t; R : pat_unit_mux_t) return boolean;
  function ">="(L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean;
  function "<="(L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean;
  -- comparisons
  function "<"(L  : segment_t; R : segment_t) return boolean;
  function ">"(L  : segment_t; R : segment_t) return boolean;
  function "="(L  : segment_t; R : segment_t) return boolean;
  function ">="(L : segment_t; R : segment_t) return boolean;
  function "<="(L : segment_t; R : segment_t) return boolean;

  procedure check_pattern_operators (nil : boolean);

  procedure print_layer (layer         : layer_t);
  procedure print_partition (partition : partition_t);

end package pat_pkg;

package body pat_pkg is

  function count_ones(slv : std_logic_vector) return natural is
    variable n_ones : natural := 0;
  begin
    for i in slv'range loop
      if slv(i) = '1' then
        n_ones := n_ones + 1;
      end if;
    end loop;
    return n_ones;
  end function count_ones;

  function if_then_else (bool : boolean; a : std_logic; b : std_logic) return std_logic is
  begin
    if (bool) then
      return a;
    else
      return b;
    end if;
  end if_then_else;

  function if_then_else (bool : boolean; a : integer; b : integer) return integer is
  begin
    if (bool) then
      return a;
    else
      return b;
    end if;
  end if_then_else;

  function if_then_else (bool : boolean; a : boolean; b : boolean) return boolean is
  begin
    if (bool) then
      return a;
    else
      return b;
    end if;
  end if_then_else;

  function if_then_else (bool : boolean; a : std_logic_vector; b : std_logic_vector) return std_logic_vector is
  begin
    if (bool) then
      return a;
    else
      return b;
    end if;
  end if_then_else;

  function pat_unit_mux_t_get_sortb (x : std_logic_vector) return std_logic_vector is
    variable y : std_logic_vector(x'length-1 downto 0);
  begin
    y := x(x'length-1 downto 0);
    return y;
  end;

  function segment_t_get_sortb (x : std_logic_vector) return std_logic_vector is
    variable y : std_logic_vector(x'length-1 downto 0);
  begin
    y := x(x'length-1 downto 0);
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

  function valid (seg : segment_t) return boolean is
  begin return seg.lc /= 0; end;
  function valid (seg : pat_unit_t) return boolean is
  begin return seg.lc /= 0; end;
  function valid (seg : pat_unit_mux_t) return boolean is
  begin return seg.lc /= 0; end;

  --------------------------------------------------------------------------------
  -- Comparison function for pat_unit_mux types
  --------------------------------------------------------------------------------

  function "=" (L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean is
    variable left, right : std_logic_vector(pat_unit_mux_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(pat_unit_mux_t_get_sortb(left)) =
            unsigned(pat_unit_mux_t_get_sortb(right)));
  end;

  function ">" (L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean is
    variable left, right : std_logic_vector(pat_unit_mux_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(pat_unit_mux_t_get_sortb(left)) >
            unsigned(pat_unit_mux_t_get_sortb(right)));
  end;

  function "<" (L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean is
    variable left, right : std_logic_vector(pat_unit_mux_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(pat_unit_mux_t_get_sortb(left)) <
            unsigned(pat_unit_mux_t_get_sortb(right)));
  end;

  function "<=" (L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean is
  begin
    return L < R or L = R;
  end;

  function ">=" (L : pat_unit_mux_t; R : pat_unit_mux_t) return boolean is
  begin
    return L > R or L = R;
  end;

  --------------------------------------------------------------------------------
  -- Comparison function for full segments
  --------------------------------------------------------------------------------

  function "=" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(segment_t_get_sortb(left)) =
            unsigned(segment_t_get_sortb(right)));
  end;

  function ">" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(segment_t_get_sortb(left)) >
            unsigned(segment_t_get_sortb(right)));
  end;

  function "<" (L : segment_t; R : segment_t) return boolean is
    variable left, right : std_logic_vector(segment_t'w-1 downto 0);
  begin
    left  := convert(L, left);
    right := convert(R, right);
    return (unsigned(segment_t_get_sortb(left)) <
            unsigned(segment_t_get_sortb(right)));
  end;

  function "<=" (L : segment_t; R : segment_t) return boolean is
  begin
    return L < R or L = R;
  end;

  function ">=" (L : segment_t; R : segment_t) return boolean is
  begin
    return L > R or L = R;
  end;

  -- unit test function to check that the sorting operators are working correctly
  procedure check_pattern_operators (nil : boolean) is
    variable ply0 : segment_t := (lc => to_unsigned(0, LC_BITS), id => to_unsigned(16#10#, PID_BITS), partition => (others => '0'), strip => (others => '0'));
    variable ply1 : segment_t := (lc => to_unsigned(1, LC_BITS), id => to_unsigned(16#9#, PID_BITS), partition => (others => '0'), strip => (others => '0'));
    variable ply2 : segment_t := (lc => to_unsigned(2, LC_BITS), id => to_unsigned(16#8#, PID_BITS), partition => (others => '0'), strip => (others => '0'));

    variable pat0 : segment_t := (lc => to_unsigned(1, LC_BITS), id => to_unsigned(16#0#, PID_BITS), partition => (others => '0'), strip => (others => '0'));
    variable pat1 : segment_t := (lc => to_unsigned(1, LC_BITS), id => to_unsigned(16#1#, PID_BITS), partition => (others => '0'), strip => (others => '0'));
    variable pat2 : segment_t := (lc => to_unsigned(1, LC_BITS), id => to_unsigned(16#2#, PID_BITS), partition => (others => '0'), strip => (others => '0'));
  begin

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
