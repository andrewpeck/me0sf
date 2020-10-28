library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

package pat_pkg is

  constant CNT_BITS  : natural := 3;
  constant PAT_BITS  : natural := 4;
  constant HASH_BITS : natural := 12;

  type int_array_t is array(integer range <>) of integer;

  type hi_lo_t is record
    hi : integer;
    lo : integer;
  end record;

  type pat_t is record
    id  : natural;
    ly0 : hi_lo_t;
    ly1 : hi_lo_t;
    ly2 : hi_lo_t;
    ly3 : hi_lo_t;
    ly4 : hi_lo_t;
    ly5 : hi_lo_t;
  end record;

  type pat_list_t is array (integer range <>) of pat_t;

  type candidate_t is record
    cnt  : unsigned(CNT_BITS-1 downto 0);
    id   : unsigned(PAT_BITS-1 downto 0);
    hash : unsigned(HASH_BITS -1 downto 0);
  end record;

  constant CANDIDATE_LENGTH : natural := CNT_BITS + PAT_BITS + HASH_BITS;

  type candidate_list_t is array (integer range <>) of candidate_t;

  function mirror_pat (pat : pat_t; id : natural) return pat_t;

end package pat_pkg;

package body pat_pkg is
  function mirror_pat (pat : pat_t; id : natural) return pat_t is
    variable result : pat_t;
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
end package body pat_pkg;
