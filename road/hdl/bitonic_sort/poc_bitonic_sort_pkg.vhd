library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

package bitonic_sort_pkg is
  type t_slm is array(natural range <>, natural range <>) of std_logic;
  function to_slm(slv : std_logic_vector; ROWS : positive; COLS : positive) return T_SLM;  -- create matrix from vector
  function to_slv(slm : T_SLM) return std_logic_vector;

end package bitonic_sort_pkg;

package body bitonic_sort_pkg is
  -- create matrix from vector
  function to_slm(slv : std_logic_vector; ROWS : positive; COLS : positive) return T_SLM is
    variable slm : T_SLM(ROWS - 1 downto 0, COLS - 1 downto 0);
  begin
    for i in 0 to ROWS - 1 loop
      for j in 0 to COLS - 1 loop
        slm(i, j) := slv((i * COLS) + j);
      end loop;
    end loop;
    return slm;
  end function;

  -- convert matrix to flatten vector
  function to_slv(slm : T_SLM) return std_logic_vector is
    variable slv : std_logic_vector((slm'length(1) * slm'length(2)) - 1 downto 0);
  begin
    for i in slm'range(1) loop
      for j in slm'high(2) downto slm'low(2) loop  -- WORKAROUND: Xilinx iSIM work-around, because 'range(2) evaluates to 'range(1); see work-around notes at T_SLM type declaration
        slv((i * slm'length(2)) + j) := slm(i, j);
      end loop;
    end loop;
    return slv;
  end function;

end package body;
