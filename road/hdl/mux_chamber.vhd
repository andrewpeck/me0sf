library work;
use work.pat_types.all;
use work.pat_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity mux_chamber is
  generic(
    NUM_PRT     : natural := 8;
    PRT_SIZE    : natural := 192;
    PAT_SIZE    : natural := 37;
    MUX_LATENCY : natural := 8
    );
  port(

    clock   : in std_logic;
    sbits_i : in chamber_t;             -- (prt)(ly)(strip)

    strip_sel : in std_logic_vector (7 downto 0);
    prt_sel   : in std_logic_vector (2 downto 0);

    ly0_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly1_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly2_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly3_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly4_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly5_o : out std_logic_vector(PAT_SIZE-1 downto 0)

    );
end mux_chamber;

architecture behavioral of mux_chamber is

  type prt_mux_array_t is array (0 to NUM_PRT-1) of
    std_logic_vector(PAT_SIZE-1 downto 0);

  type ly_mux_array_t is array (0 to 5) of
    prt_mux_array_t;

  signal mux_array : ly_mux_array_t;

  type prt_sel_dly_t is array (0 to MUX_LATENCY-1) of
    std_logic_vector(prt_sel'range);

  signal prt_sel_dly : prt_sel_dly_t;

begin


  --------------------------------------------------------------------------------
  -- Intra-Partition Multiplexer
  --------------------------------------------------------------------------------

  ly_gen : for ILY in 0 to 5 generate
  begin
    prt_gen : for IPRT in 0 to NUM_PRT-1 generate
    begin

      mux_partition_inst : entity work.mux_partition
        generic map (
          I => PRT_SIZE,
          O => PAT_SIZE
          )
        port map (
          clock => clock,
          d     => sbits_i(IPRT)(ILY),
          q     => mux_array(ILY)(IPRT),
          sel   => strip_sel);

    end generate;

    --------------------------------------------------------------------------------
    -- Inter-Partition Multiplexer
    --
    -- Need to delay the select signals so that the correct select is available
    -- when data comes out from the partition mux
    --------------------------------------------------------------------------------

    process (clock) is
    begin
      if (rising_edge(clock)) then
        prt_sel_dly(0) <= prt_sel;
        for I in 1 to prt_sel_dly'length-1 loop
          prt_sel_dly(I) <= prt_sel_dly(I-1);
        end loop;
      end if;
    end process;

    -- 8:1 Mux to select the partition
    process (clock) is
    begin
      if (rising_edge(clock)) then
        ly0_o <= mux_array(0)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
        ly1_o <= mux_array(1)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
        ly2_o <= mux_array(2)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
        ly3_o <= mux_array(3)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
        ly4_o <= mux_array(4)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
        ly5_o <= mux_array(5)(to_integer(unsigned(prt_sel_dly(prt_sel_dly'high))));
      end if;
    end process;

  end generate;


end behavioral;
