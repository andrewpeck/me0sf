library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity mux_partition is
  generic(
    I : integer := 192;
    O : integer := 37
    );
  port(
    clock : in  std_logic;
    d     : in  std_logic_vector (I-1 downto 0);
    q     : out std_logic_vector (O-1 downto 0);
    sel   : in  std_logic_vector (7 downto 0)
    );
end mux_partition;

architecture behavioral of mux_partition is

  -- need to pad the left/right edges of the chamber
  -- the size of the padding is (O-1)/2, so e.g. for a 37 strip wide
  -- window we would pad with 18 zeroes
  -- so that e.g. on strip 0 we would have a "virtual" window from
  -- -18 .... 0 ... 18, giving a 37 strip wide window

  constant PAD_SIZE : natural                                := (O-1)/2;
  constant PAD      : std_logic_vector (PAD_SIZE-1 downto 0) := (others => '0');

  constant SEL_SIZE : natural := integer(ceil(log2(real(I))));

  signal padded : std_logic_vector (I-1 + 2*PAD_SIZE downto 0) := (others => '0');

begin

  -- make a copy of the input data to account for the 1 clock cycle in which
  -- sel_padded is calculated. should also improve routing
  process (clock) is
  begin
    if (rising_edge(clock)) then
      padded <= PAD & d & PAD;
    end if;
  end process;

  mux_gen : for I in 0 to O-1 generate
    signal sel_padded : natural range 0 to 2**SEL_SIZE-1;
  begin

    -- offset the sel signal by 1 for each strip
    process (clock) is
    begin
      if (rising_edge(clock)) then
        sel_padded <= I + to_integer(unsigned(sel));
      end if;
    end process;

    mux_single_inst : entity work.mux_single
      generic map (DAT_SIZE   => padded'length)
      port map (
        clock => clock,
        din   => padded,
        sel   => std_logic_vector(to_unsigned(sel_padded, SEL_SIZE)),
        dout  => q(I)
        );
  end generate;

end behavioral;
