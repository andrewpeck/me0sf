library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity fixed_delay is
  generic(
    DELAY : natural := 16;
    WIDTH : natural := 16
    );
  port(
    clock  : in  std_logic;
    data_i : in  std_logic_vector (WIDTH-1 downto 0);
    data_o : out std_logic_vector (WIDTH-1 downto 0)
    );
end fixed_delay;

architecture behavioral of fixed_delay is
begin

  latency_zero : if (DELAY = 0) generate
    data_o <= data_i;
  end generate;

  latency_nonzero : if (DELAY > 0) generate
    type data_array_t is array (DELAY-1 downto 0) of std_logic_vector(WIDTH-1 downto 0);
    signal data : data_array_t;
  begin

    process (clock) is
    begin
      if (rising_edge(clock)) then
        data(0) <= data_i;
        for I in 0 to data'length-2 loop
          data(I+1) <= data(I);
        end loop;
      end if;
    end process;

    data_o <= data(data'length-1);

  end generate;

end behavioral;
