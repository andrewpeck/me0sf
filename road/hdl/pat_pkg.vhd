use std.textio.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

package pat_pkg is

  --------------------------------------------------------------------------------
  -- Build Parameters
  --------------------------------------------------------------------------------

  constant S0_REGION_SIZE : positive              := 16;
  constant CNT_THRESH     : natural               := 4;
  constant PRT_WIDTH      : positive              := 192;
  constant PAT_UNIT_MUX   : positive range 1 to 8 := 8; -- 1, 2, 4, or 8

  --------------------------------------------------------------------------------
  -- Constants for Patterns
  --------------------------------------------------------------------------------

  constant CNT_BITS  : positive := 3;   -- number of bits to count 6 layers, always 3
  constant PID_BITS  : positive := 4;   -- number of bits to cnt the pids
  constant HASH_BITS : positive := 12;
  constant VALID_BIT : positive := 1;

  constant PATTERN_LENGTH : positive := CNT_BITS + PID_BITS + HASH_BITS + VALID_BIT;
  constant PATTERN_SORTB  : positive := CNT_BITS + PID_BITS + VALID_BIT;
  constant STRIP_BITS     : positive := 8;  -- 8 bits to count 0-191
  constant PARTITION_BITS : positive := 3;  -- 3 bits to count 0-7

  --------------------------------------------------------------------------------
  -- Types for patterns
  --------------------------------------------------------------------------------

  subtype layer_t is std_logic_vector(3*64-1 downto 0);
  type partition_t is array(integer range 0 to 5) of layer_t;
  type chamber_t is array(integer range 0 to 7) of partition_t;

  type int_array_t is array(integer range <>) of integer;

  type hi_lo_t is record
    hi : integer;
    lo : integer;
  end record;

  type patdef_t is record
    id  : natural;
    ly0 : hi_lo_t;
    ly1 : hi_lo_t;
    ly2 : hi_lo_t;
    ly3 : hi_lo_t;
    ly4 : hi_lo_t;
    ly5 : hi_lo_t;
  end record;

  type patdef_array_t is array (integer range <>) of patdef_t;

  type pattern_t is record
    dav  : std_logic;
    cnt  : unsigned(CNT_BITS-1 downto 0);
    id   : unsigned(PID_BITS-1 downto 0);
    hash : unsigned(HASH_BITS -1 downto 0);
  end record;

  type strip_t is record
    pattern : pattern_t;
    strip   : natural range 0 to 191;
  end record;

  type segment_t is record
    strip     : strip_t;
    partition : natural range 0 to 7;
  end record;

  constant null_pattern : pattern_t :=
    (
      dav  => '0',
      cnt  => (others => '0'),
      id   => (others => '0'),
      hash => (others => '0')
      );

  type pattern_list_slv_t is array (integer range <>) of std_logic_vector (PATTERN_LENGTH-1 downto 0);

  type pat_list_t is array (integer range <>) of pattern_t;
  type strip_list_t is array (integer range <>) of strip_t;
  type segment_list_t is array (integer range <>) of segment_t;

  type cand_array_t is array (integer range 0 to 7) of pat_list_t (PRT_WIDTH-1 downto 0);

  type cand_array_s0_t is array (integer range 0 to 7) of pat_list_t (PRT_WIDTH/S0_REGION_SIZE-1 downto 0);

  --------------------------------------------------------------------------------
  -- Pattern Helper Functions
  --------------------------------------------------------------------------------

  -- mirror a pattern unit (left/right symmetry)
  function mirror_patdef (pat : patdef_t; id : natural) return patdef_t;

  -- comparisons
  function "<"(L  : pattern_t; R : pattern_t) return boolean;
  function ">"(L  : pattern_t; R : pattern_t) return boolean;
  function "="(L  : pattern_t; R : pattern_t) return boolean;
  function ">="(L : pattern_t; R : pattern_t) return boolean;
  function "<="(L : pattern_t; R : pattern_t) return boolean;

  -- to from segment pattern
  function to_slv (segment : segment_t) return std_logic_vector;
  function to_slv (pattern : pattern_t) return std_logic_vector;
  function to_slv (strip   : strip_t) return std_logic_vector;

  function to_pattern (slv : std_logic_vector) return pattern_t;
  function to_strip (slv   : std_logic_vector (STRIP_BITS+PATTERN_LENGTH-1 downto 0)) return strip_t;
  function to_segment (slv : std_logic_vector) return segment_t;

  function check_pattern_conversion (slv : std_logic_vector) return boolean;

  procedure check_pattern_operators (nil : boolean);

  procedure print_layer (layer : layer_t);
  procedure print_partition (partition : partition_t);

  function centroid (ly : std_logic_vector; length : natural) return natural;


end package pat_pkg;

package body pat_pkg is

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

  --------------------------------------------------------------------------------
  -- Pattern Helper functions
  --------------------------------------------------------------------------------

  function to_slv (pattern : pattern_t) return std_logic_vector is
    variable result : std_logic_vector (PATTERN_LENGTH-1 downto 0);
  begin
    result := std_logic_vector(pattern.hash) &
              pattern.dav &
              std_logic_vector(pattern.cnt) &
              std_logic_vector(pattern.id);
    return result;
  end;

  function to_slv (strip : strip_t) return std_logic_vector is
    variable result : std_logic_vector (STRIP_BITS + PATTERN_LENGTH-1 downto 0);
  begin
    result := std_logic_vector(to_unsigned(strip.strip, STRIP_BITS)) & to_slv(strip.pattern);
    return result;
  end;

  function to_slv (segment : segment_t) return std_logic_vector is
    variable result : std_logic_vector (PARTITION_BITS + STRIP_BITS + PATTERN_LENGTH - 1 downto 0);
  begin
    result := std_logic_vector(to_unsigned(segment.partition, PARTITION_BITS)) &
              to_slv(segment.strip);
    return result;
  end;

  function to_pattern (slv : std_logic_vector)
    return pattern_t is
    variable slv_rerange : std_logic_vector (slv'length-1 downto 0);
    variable pattern     : pattern_t;
  begin

    slv_rerange := slv;

    pattern.id  := unsigned(slv_rerange(PID_BITS-1 downto 0));
    pattern.cnt := unsigned(slv_rerange(CNT_BITS+PID_BITS-1 downto PID_BITS));
    pattern.dav := slv_rerange(CNT_BITS+PID_BITS);
    pattern.hash := unsigned(slv_rerange(VALID_BIT+HASH_BITS+CNT_BITS+PID_BITS-1
                                         downto VALID_BIT+CNT_BITS+PID_BITS));
    return pattern;
  end;

  function to_strip (slv : std_logic_vector (STRIP_BITS+PATTERN_LENGTH-1 downto 0))
    return strip_t is
    variable strip       : strip_t;
    variable slv_rerange : std_logic_vector (slv'length-1 downto 0);
  begin

    slv_rerange := slv;

    strip.strip :=
      to_integer(unsigned(
        slv_rerange(STRIP_BITS + PATTERN_LENGTH - 1 downto PATTERN_LENGTH)));

    strip.pattern := to_pattern (slv_rerange(PATTERN_LENGTH -1 downto 0));
    return strip;
  end;

  function to_segment (slv : std_logic_vector)
    return segment_t is
    variable segment     : segment_t;
    variable slv_rerange : std_logic_vector (slv'length-1 downto 0);
  begin

    slv_rerange := slv;

    segment.partition :=
      to_integer(unsigned(slv_rerange(
        PARTITION_BITS + STRIP_BITS + PATTERN_LENGTH - 1 downto
        STRIP_BITS + PATTERN_LENGTH)));

    segment.strip := to_strip (slv_rerange(STRIP_BITS+PATTERN_LENGTH-1 downto 0));
    return segment;

  end;

  -- helper function converts from slv to pattern and back..
  -- to be used in asserts to make sure the conversion always works
  function check_pattern_conversion (slv : std_logic_vector)
    return boolean is
    variable slv_o : std_logic_vector(PATTERN_LENGTH-1 downto 0);
  begin
    slv_o := to_slv(to_pattern(slv));

    if (slv_o /= slv) then
      assert false report "conv_in=" & to_hstring(slv) severity note;
      assert false report "conv_out=" & to_hstring(slv_o) severity note;
    end if;

    return slv_o = slv;
  end;

  function "=" (L : pattern_t; R : pattern_t) return boolean is
  begin
    if (unsigned(to_slv(L)(PATTERN_SORTB-1 downto 0)) =
        unsigned(to_slv(R)(PATTERN_SORTB-1 downto 0))) then
      return true;
    else
      return false;
    end if;
  end;

  function ">" (L : pattern_t; R : pattern_t) return boolean is
  begin
    if (unsigned(to_slv(L)(PATTERN_SORTB-1 downto 0)) >
        unsigned(to_slv(R)(PATTERN_SORTB-1 downto 0))) then
      return true;
    else
      return false;
    end if;
  end;

  function "<" (L : pattern_t; R : pattern_t) return boolean is
  begin
    if (unsigned(to_slv(L)(PATTERN_SORTB-1 downto 0)) <
        unsigned(to_slv(R)(PATTERN_SORTB-1 downto 0))) then
      return true;
    else
      return false;
    end if;
  end;

  function "<=" (L : pattern_t; R : pattern_t) return boolean is
  begin
    if (unsigned(to_slv(L)(PATTERN_SORTB-1 downto 0)) <=
        unsigned(to_slv(R)(PATTERN_SORTB-1 downto 0))) then
      return true;
    else
      return false;
    end if;
  end;

  function ">=" (L : pattern_t; R : pattern_t) return boolean is
  begin
    if (unsigned(to_slv(L)(PATTERN_SORTB-1 downto 0)) >=
        unsigned(to_slv(R)(PATTERN_SORTB-1 downto 0))) then
      return true;
    else
      return false;
    end if;
  end;

  -- unit test function to check that the sorting operators are working correctly
  procedure check_pattern_operators (nil : boolean) is
    variable ply0 : pattern_t := (dav => '1', cnt => to_unsigned(0, CNT_BITS), id => x"A", hash => (others => '0'));
    variable ply1 : pattern_t := (dav => '1', cnt => to_unsigned(1, CNT_BITS), id => x"A", hash => (others => '0'));
    variable ply2 : pattern_t := (dav => '1', cnt => to_unsigned(2, CNT_BITS), id => x"A", hash => (others => '0'));

    variable pat0 : pattern_t := (dav => '1', cnt => to_unsigned(1, CNT_BITS), id => x"0", hash => (others => '0'));
    variable pat1 : pattern_t := (dav => '1', cnt => to_unsigned(1, CNT_BITS), id => x"1", hash => (others => '0'));
    variable pat2 : pattern_t := (dav => '1', cnt => to_unsigned(1, CNT_BITS), id => x"2", hash => (others => '0'));
  begin

    -- > testing
    assert ply2 > ply1 report "pattern > failure" severity error;
    assert ply1 > ply0 report "pattern > failure" severity error;
    assert pat2 > pat1 report "pattern > failure" severity error;
    assert pat1 > pat0 report "pattern > failure" severity error;

    -- < testing
    assert ply0 < ply1 report "pattern < failure" severity error;
    assert ply0 < ply2 report "pattern < failure" severity error;
    assert ply1 < ply2 report "pattern < failure" severity error;
    assert pat0 < pat1 report "pattern < failure" severity error;
    assert pat0 < pat2 report "pattern < failure" severity error;
    assert pat1 < pat2 report "pattern < failure" severity error;

    -- <= testing
    assert ply0 <= ply0 report "pattern <= failure" severity error;
    assert ply0 <= ply1 report "pattern <= failure" severity error;
    assert pat0 <= pat0 report "pattern <= failure" severity error;
    assert pat0 <= pat1 report "pattern <= failure" severity error;

    -- >= testing
    assert ply0 >= ply0 report "pattern >= failure" severity error;
    assert ply1 >= ply0 report "pattern >= failure" severity error;
    assert pat0 >= pat0 report "pattern >= failure" severity error;
    assert pat1 >= pat0 report "pattern >= failure" severity error;

    -- = testing
    assert ply0 = ply0 report "pattern = failure" severity error;
    assert ply1 = ply1 report "pattern = failure" severity error;

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

  function centroid (ly : std_logic_vector; length : natural) return natural is
    variable index : natural;
  begin

    if (length = 1) then
      index := 0 when ly = "0" else
               1 when ly = "1";
    end if;

    if (length = 2) then
      index := 0 when ly = "00" else
               1 when ly = "01" else
               2 when ly = "10" else
               3 when ly = "11" else 0;
    end if;

    if (length = 3) then
      index := 0 when ly = "000" else
               1 when ly = "001" else
               1 when ly = "011" else
               2 when ly = "010" else
               2 when ly = "111" else
               2 when ly = "101" else
               3 when ly = "100" else
               3 when ly = "110" else 0;
    end if;

    if (length = 4) then
      index :=
        0 when ly = "0000" else
        1 when ly = "0001" else
        2 when ly = "0010" else
        1 when ly = "0011" else
        2 when ly = "0111" else
        4 when ly = "1000" else
        1 when ly = "1001" else
        2 when ly = "0101" else
        3 when ly = "0100" else
        1 when ly = "0110" else
        3 when ly = "1011" else
        3 when ly = "1010" else
        2 when ly = "1111" else
        3 when ly = "1101" else
        3 when ly = "1100" else
        3 when ly = "1110" else
        0;
    end if;


    return index;
  end;

end package body pat_pkg;
