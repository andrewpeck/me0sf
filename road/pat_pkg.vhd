library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

package pat_pkg is

  constant S0_REGION_SIZE  : integer := 8;
  constant CNT_THRESH      : integer := 4;
  constant FREQ            : natural := 320;
  constant PRT_WIDTH       : natural := 192;

  constant CNT_BITS  : natural := 3;    -- number of bits to count 6 layers, always 3
  constant PID_BITS  : natural := 3;    -- number of bits to cnt the pids
  constant HASH_BITS : natural := 12;

  subtype layer_t is std_logic_vector(3*64-1 downto 0);
  type partition_t is array(integer range 0 to 5) of layer_t;
  type chamber_t is array(integer range 0 to 7) of partition_t;

  type int_array_t is array(integer range <>) of integer;

  type hi_lo_t is record
    hi : integer;
    lo : integer;
  end record;

  type pat_unit_t is record
    id  : natural;
    ly0 : hi_lo_t;
    ly1 : hi_lo_t;
    ly2 : hi_lo_t;
    ly3 : hi_lo_t;
    ly4 : hi_lo_t;
    ly5 : hi_lo_t;
  end record;

  type pat_list_t is array (integer range <>) of pat_unit_t;

  type candidate_t is record
    dav  : std_logic;
    cnt  : unsigned(CNT_BITS-1 downto 0);
    id   : unsigned(PID_BITS-1 downto 0);
    hash : unsigned(HASH_BITS -1 downto 0);
  end record;

  constant null_candidate : candidate_t :=
    (
      dav  => '0',
      cnt  => (others => '0'),
      id   => (others => '0'),
      hash => (others => '0')
      );

  constant CANDIDATE_LENGTH : natural := CNT_BITS + PID_BITS + HASH_BITS + 1;

  type candidate_list_slv_t is array (integer range <>) of std_logic_vector (CANDIDATE_LENGTH-1 downto 0);

  type candidate_list_t is array (integer range <>) of candidate_t;

  type cand_array_t is array (integer range 0 to 7) of candidate_list_t (PRT_WIDTH-1 downto 0);

  type cand_array_s0_t is array (integer range 0 to 7) of candidate_list_t (PRT_WIDTH/S0_REGION_SIZE-1 downto 0);

  -- mirror a pattern unit (left/right symmetry)
  function mirror_pat_unit (pat : pat_unit_t; id : natural) return pat_unit_t;

  -- comparisons
  function "<"(L  : candidate_t; R : candidate_t) return boolean;
  function ">"(L  : candidate_t; R : candidate_t) return boolean;
  function "="(L  : candidate_t; R : candidate_t) return boolean;
  function ">="(L : candidate_t; R : candidate_t) return boolean;
  function "<="(L : candidate_t; R : candidate_t) return boolean;

  -- to from segment candidate
  function to_slv (candidate : candidate_t) return std_logic_vector;
  function to_candidate (slv : std_logic_vector) return candidate_t;

end package pat_pkg;

package body pat_pkg is

  function mirror_pat_unit (pat : pat_unit_t; id : natural) return pat_unit_t is
    variable result : pat_unit_t;
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

  function to_slv (candidate : candidate_t) return std_logic_vector is
    variable result : std_logic_vector (CANDIDATE_LENGTH-1 downto 0);
  begin
    result := std_logic_vector(candidate.hash) &
              candidate.dav &
              std_logic_vector(candidate.cnt) &
              std_logic_vector(candidate.id);
    return result;
  end;

  function to_candidate (slv : std_logic_vector) return candidate_t is
    variable candidate : candidate_t;
  begin
    candidate.id   := unsigned(slv(PID_BITS-1 downto 0));
    candidate.cnt  := unsigned(slv(CNT_BITS+PID_BITS-1 downto PID_BITS));
    candidate.dav  := slv(CNT_BITS+PID_BITS);
    candidate.hash := unsigned(slv(1+HASH_BITS+CNT_BITS+PID_BITS-1 downto 1+CNT_BITS+PID_BITS));
    return candidate;
  end;


  function "=" (L : candidate_t; R : candidate_t) return boolean is
  begin
    if (unsigned(to_slv(L)) = unsigned(to_slv(R))) then
      return true;
    else
      return false;
    end if;
  end;

  function ">" (L : candidate_t; R : candidate_t) return boolean is
  begin
    if (unsigned(to_slv(L)) > unsigned(to_slv(R))) then
      return true;
    else
      return false;
    end if;
  end;

  function "<" (L : candidate_t; R : candidate_t) return boolean is
  begin
    if (unsigned(to_slv(L)) < unsigned(to_slv(R))) then
      return true;
    else
      return false;
    end if;
  end;

  function "<=" (L : candidate_t; R : candidate_t) return boolean is
  begin
    if (unsigned(to_slv(L)) <= unsigned(to_slv(R))) then
      return true;
    else
      return false;
    end if;
  end;

  function ">=" (L : candidate_t; R : candidate_t) return boolean is
  begin
    if (unsigned(to_slv(L)) >= unsigned(to_slv(R))) then
      return true;
    else
      return false;
    end if;
  end;

end package body pat_pkg;
