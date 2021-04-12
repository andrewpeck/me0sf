-- this is the PoC bitonic sort module with modifications to let it run without the rest of the poc library
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.bitonic_sort_pkg.all;

entity sortnet_bitonicsort is
  generic (
    INPUTS               : positive := 32;     -- input count
    KEY_BITS             : positive := 32;     -- the first KEY_BITS of In_Data are used as a sorting critera (key)
    DATA_BITS            : positive := 64;     -- inclusive KEY_BITS
    META_BITS            : natural  := 2;      -- additional bits, not sorted but delayed as long as In_Data
    PIPELINE_STAGE_AFTER : natural  := 2;      -- add a pipline stage after n sorting stages
    ADD_INPUT_REGISTERS  : boolean  := false;  --
    ADD_OUTPUT_REGISTERS : boolean  := true    --
    );
  port (
    clock : in std_logic;
    reset : in std_logic;

    inverse : in std_logic := '0';

    in_valid : in std_logic;
    in_iskey : in std_logic;
    in_data  : in T_SLM(INPUTS - 1 downto 0, DATA_BITS - 1 downto 0);
    in_meta  : in std_logic_vector(META_BITS - 1 downto 0);

    out_valid : out std_logic;
    out_iskey : out std_logic;
    out_data  : out T_SLM(INPUTS - 1 downto 0, DATA_BITS - 1 downto 0);
    out_meta  : out std_logic_vector(META_BITS - 1 downto 0)
    );
end entity;


architecture rtl of sortnet_bitonicsort is
  constant C_VERBOSE : boolean := false;

  function log2ceil(arg : positive) return natural is
    variable tmp : positive;
    variable log : natural;
  begin
    if arg = 1 then return 0; end if;
    tmp := 1;
    log := 0;
    while arg > tmp loop
      tmp := tmp * 2;
      log := log + 1;
    end loop;
    return log;
  end function;

  function triangularNumber(N : natural) return natural is
    variable T : natural;
  begin
    return (N * (N + 1) / 2);
  end function;

  -- if-then-else (ite)
  -- ==========================================================================
  function ite(cond : boolean; value1 : boolean; value2 : boolean) return boolean is
  begin
    if cond then
      return value1;
    else
      return value2;
    end if;
  end function;

  function registered(signal clock : std_logic; constant isregistered : boolean) return boolean is
  begin
    return ite(isregistered, rising_edge(clock), true);
  end function;

  function ite(cond : boolean; value1 : std_logic; value2 : std_logic) return std_logic is
  begin
    if cond then
      return value1;
    else
      return value2;
    end if;
  end function;

  function to_sl(value : boolean) return std_logic is
  begin
    return ite(value, '1', '0');
  end function;

  constant BLOCKS      : positive := log2ceil(INPUTS);
  constant STAGES      : positive := triangularNumber(BLOCKS);
  constant COMPARATORS : positive := STAGES * (INPUTS / 2);

  constant META_VALID_BIT   : natural  := 0;
  constant META_ISKEY_BIT   : natural  := 1;
  constant META_VECTOR_BITS : positive := META_BITS + 2;

  subtype T_META is std_logic_vector(META_VECTOR_BITS - 1 downto 0);
  type T_META_VECTOR is array(natural range <>) of T_META;

  subtype T_DATA is std_logic_vector(DATA_BITS - 1 downto 0);
  type T_DATA_VECTOR is array(natural range <>) of T_DATA;
  type T_DATA_MATRIX is array(natural range <>) of T_DATA_VECTOR(INPUTS - 1 downto 0);

  function to_dv(slm : T_SLM) return T_DATA_VECTOR is
    variable Result : T_DATA_VECTOR(slm'range(1));
  begin
    for i in slm'range(1) loop
      for j in slm'high(2) downto slm'low(2) loop
        Result(i)(j) := slm(i, j);
      end loop;
    end loop;
    return Result;
  end function;

  function to_slm(dv : T_DATA_VECTOR) return T_SLM is
    variable Result : T_SLM(dv'range, T_DATA'range);
  begin
    for i in dv'range loop
      for j in T_DATA'range loop
        Result(i, j) := dv(i)(j);
      end loop;
    end loop;
    return Result;
  end function;

  function ffdre(q : std_logic; d : std_logic; rst : std_logic := '0'; en : std_logic := '1'; constant INIT : std_logic := '0') return std_logic is
  begin
    if (INIT = '0') then
      return ((d and en) or (q and not en)) and not rst;
    elsif (INIT = '1') then
      return ((d and en) or (q and not en)) or rst;
    else
      report "Unsupported INIT value for synthesis." severity failure;
      return 'X';
    end if;
  end function;

  function mux(sel : std_logic; sl0 : std_logic; sl1 : std_logic) return std_logic is
  begin
    return (sl0 and not sel) or (sl1 and sel);
  end function;

  function mux(sel : std_logic; slv0 : std_logic_vector; slv1 : std_logic_vector) return std_logic_vector is
  begin
    return (slv0 and not (slv0'range => sel)) or (slv1 and (slv1'range => sel));
  end function;

  signal In_Valid_d : std_logic                                          := '0';
  signal In_IsKey_d : std_logic                                          := '0';
  signal In_Data_d  : T_SLM(INPUTS - 1 downto 0, DATA_BITS - 1 downto 0) := (others => (others => '0'));
  signal In_Meta_d  : std_logic_vector(META_BITS - 1 downto 0)           := (others => '0');

  signal MetaVector : T_META_VECTOR(STAGES downto 0) := (others => (others => '0'));
  signal DataMatrix : T_DATA_MATRIX(STAGES downto 0) := (others => (others => (others => '0')));

  signal MetaOutputs_d : T_META                                             := (others => '0');
  signal DataOutputs_d : T_SLM(INPUTS - 1 downto 0, DATA_BITS - 1 downto 0) := (others => (others => '0'));

begin
  assert (not C_VERBOSE)
    report "sortnet_BitonicSort:" & LF &
    "  DATA_BITS=" & integer'image(DATA_BITS) &
    "  KEY_BITS=" & integer'image(KEY_BITS) &
    "  META_BITS=" & integer'image(META_BITS)
    severity note;

  In_Valid_d <= In_Valid when registered(Clock, ADD_INPUT_REGISTERS);
  In_IsKey_d <= In_IsKey when registered(Clock, ADD_INPUT_REGISTERS);
  In_Data_d  <= In_Data  when registered(Clock, ADD_INPUT_REGISTERS);
  In_Meta_d  <= In_Meta  when registered(Clock, ADD_INPUT_REGISTERS);

  DataMatrix(0)                                                           <= to_dv(In_Data_d);
  MetaVector(0)(META_VALID_BIT)                                           <= In_Valid_d;
  MetaVector(0)(META_ISKEY_BIT)                                           <= In_IsKey_d;
  MetaVector(0)(META_VECTOR_BITS - 1 downto META_VECTOR_BITS - META_BITS) <= In_Meta_d;

  genBlocks : for b in 0 to BLOCKS - 1 generate
    constant START_DISTANCE : positive := 2**b;
  begin
    genStage : for s in 0 to b generate
      constant STAGE_INDEX              : natural  := triangularNumber(b) + s;
      constant DISTANCE                 : positive := 2**(b - s);
      constant GROUPS                   : positive := INPUTS / (DISTANCE * 2);
      constant INSERT_PIPELINE_REGISTER : boolean  := (PIPELINE_STAGE_AFTER /= 0) and (STAGE_INDEX mod PIPELINE_STAGE_AFTER = 0);
    begin
      MetaVector(STAGE_INDEX + 1) <= MetaVector(STAGE_INDEX) when registered(Clock, INSERT_PIPELINE_REGISTER);

      genGroups : for g in 0 to GROUPS - 1 generate
        constant INV : std_logic := to_sl((g / (2 ** s) mod 2 = 1));
      begin
        genLoop : for l in 0 to DISTANCE - 1 generate
          constant SRC0 : natural := g * (DISTANCE * 2) + l;
          constant SRC1 : natural := SRC0 + DISTANCE;

          signal Greater   : std_logic;
          signal Switch_d  : std_logic;
          signal Switch_en : std_logic;
          signal Switch_r  : std_logic := '0';
          signal Switch    : std_logic;
          signal NewData0  : T_DATA;
          signal NewData1  : T_DATA;

        begin
          Greater   <= to_sl(unsigned(DataMatrix(STAGE_INDEX)(SRC0)(KEY_BITS - 1 downto 0)) > unsigned(DataMatrix(STAGE_INDEX)(SRC1)(KEY_BITS - 1 downto 0)));
          Switch_d  <= Greater xor Inverse xor INV;
          Switch_en <= MetaVector(STAGE_INDEX)(META_ISKEY_BIT) and MetaVector(STAGE_INDEX)(META_VALID_BIT);
          Switch_r  <= ffdre(q => Switch_r, d => Switch_d, en => Switch_en) when rising_edge(Clock);
          Switch    <= mux(Switch_en, Switch_r, Switch_d);

          NewData0 <= mux(Switch, DataMatrix(STAGE_INDEX)(SRC0), DataMatrix(STAGE_INDEX)(SRC1));
          NewData1 <= mux(Switch, DataMatrix(STAGE_INDEX)(SRC1), DataMatrix(STAGE_INDEX)(SRC0));

          DataMatrix(STAGE_INDEX + 1)(SRC0) <= NewData0 when registered(Clock, INSERT_PIPELINE_REGISTER);
          DataMatrix(STAGE_INDEX + 1)(SRC1) <= NewData1 when registered(Clock, INSERT_PIPELINE_REGISTER);
        end generate;
      end generate;
    end generate;
  end generate;

  MetaOutputs_d <= MetaVector(STAGES)         when registered(Clock, ADD_OUTPUT_REGISTERS);
  DataOutputs_d <= to_slm(DataMatrix(STAGES)) when registered(Clock, ADD_OUTPUT_REGISTERS);

  Out_Valid <= MetaOutputs_d(META_VALID_BIT);
  Out_IsKey <= MetaOutputs_d(META_ISKEY_BIT);
  Out_Data  <= DataOutputs_d;
  Out_Meta  <= MetaOutputs_d(META_VECTOR_BITS - 1 downto META_VECTOR_BITS - META_BITS);
end architecture;
