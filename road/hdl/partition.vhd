library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_pkg.all;
use work.patterns.all;

entity partition is
  generic(
    NUM_SEGMENTS  : integer := 0;
    PARTITION_NUM : integer := 0;
    WIDTH         : natural := PRT_WIDTH;
    MUX_FACTOR    : natural := FREQ/40
    );
  port(

    clock : in std_logic;
    dav_i : in  std_logic;
    dav_o : out std_logic;

    partition_i : in partition_t;
    neighbor_i  : in partition_t;

    pat_candidates_o : out candidate_list_t (WIDTH-1 downto 0);

    pre_gcl_pat_candidates_o   : out candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_p : in  candidate_list_t (WIDTH-1 downto 0);
    pre_gcl_pat_candidates_i_n : in  candidate_list_t (WIDTH-1 downto 0);

    sump : out std_logic

    );
end partition;

architecture behavioral of partition is

  constant PADDING : integer := (get_max_span(pat_list)-1)/2;  -- pad to half the width of the pattern

  signal lyor : partition_t;

  signal pat_candidates     : candidate_list_t (WIDTH-1 downto 0);
  signal pat_candidates_gcl : candidate_list_t (WIDTH-1 downto 0);

  function pad_layer (pad : natural; data : std_logic_vector)
    return std_logic_vector is
    variable pad_slv  : std_logic_vector (pad-1 downto 0) := (others => '0');
  begin
    return pad_slv & data & pad_slv;
  end;

  signal phase : integer range 0 to 7 := 0;

begin

  process (clock) is
  begin
    if (rising_edge(clock)) then
      if (phase < 8) then
        phase <= phase + 1;
      else
        phase <= 0;
      end if;
    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Neighbor Partition OR
  --
  -- details to come....
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- FIXME: this should be parameterized, and depend on the station
      -- matters which layer and the orientation of chambers wrt the ip
      -- or something like that
      -- but this stupid approach is ok for now
      lyor(5) <= partition_i(5);
      lyor(4) <= partition_i(4);
      lyor(3) <= partition_i(3);
      lyor(2) <= partition_i(2) or neighbor_i(2);
      lyor(1) <= partition_i(1) or neighbor_i(1);
      lyor(0) <= partition_i(0) or neighbor_i(0);
    end if;
  end process;

  --------------------------------------------------------------------------------
  --
  --------------------------------------------------------------------------------

  pat_unit_mux_inst : entity work.pat_unit_mux
    generic map (
      WIDTH      => WIDTH,
      PADDING    => PADDING,
      MUX_FACTOR => MUX_FACTOR
      )
    port map (
      clock      => clock,

      dav_i        => dav_i,
      dav_o        => dav_o,

      ly0_padded => pad_layer(PADDING, lyor(0)),
      ly1_padded => pad_layer(PADDING, lyor(1)),
      ly2_padded => pad_layer(PADDING, lyor(2)),
      ly3_padded => pad_layer(PADDING, lyor(3)),
      ly4_padded => pad_layer(PADDING, lyor(4)),
      ly5_padded => pad_layer(PADDING, lyor(5)),

      patterns_o => pat_candidates
      );

  pre_gcl_pat_candidates_o <= pat_candidates;

  --------------------------------------------------------------------------------
  -- Ghost Cancellation
  --------------------------------------------------------------------------------
  -- FIXME: the mux logic needs to be checked and correctly timed....
  -- should pass dav flags around

  gcl_inst : entity work.ghost_cancellation
    generic map (
      WIDTH => WIDTH
      )
    port map (
      clock                      => clock,
      pat_candidates_i           => pat_candidates,
      pre_gcl_pat_candidates_i_p => pre_gcl_pat_candidates_i_p,
      pre_gcl_pat_candidates_i_n => pre_gcl_pat_candidates_i_n,
      pat_candidates_o           => pat_candidates_o
      );

end behavioral;
