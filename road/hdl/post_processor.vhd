library work;
use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity post_processor is
  generic(
    NUM_PRT      : natural               := 8;     -- Number of REAL partitions, should always be 8
    PRT_SIZE     : natural               := 192;   -- Size of a partition, should always be 192
    PAT_SIZE     : natural               := 37;    -- Size of a pattern unit, may vary, should be set to MAX_SPAN
    SBIT_BX_DLY  : natural range 0 to 32 := 6;     -- Number of BX to delay the S-bits to account for pattern finding latency
    X_PRT_DLY    : natural range 0 to 32 := 6;     -- Number of 320 Mhz cycles to delay xprt flags
    SEL_NOLATCH  : boolean               := false  -- See description below
    );
  port(
    clock       : in std_logic;
    clock40     : in std_logic;
    segments_i  : in segment_list_t (3 downto 0);
    sbits_i_dav : in std_logic;
    sbits_i     : in chamber_t
    );
end post_processor;

architecture behavioral of post_processor is

  signal mux_phase : natural range 0 to 7 := 0;
  signal mux_dav   : std_logic            := '0';

  signal segment_is_xprt     : std_logic_vector (3 downto 0) := (others => '0');
  signal segment_is_xprt_dly : std_logic_vector (3 downto 0) := (others => '0');

  type ly_array_t is array (0 to 5) of std_logic_vector(PAT_SIZE-1 downto 0);

  signal ly    : ly_array_t;
  signal ly_n  : ly_array_t;
  signal ly_or : ly_array_t;

begin

  --------------------------------------------------------------------------------
  -- Chamber Data Mux
  --------------------------------------------------------------------------------

  mux_chamber_multi_inst : entity work.mux_chamber_multi
    generic map (
      NUM_PRT     => NUM_PRT,
      PRT_SIZE    => PRT_SIZE,
      PAT_SIZE    => PAT_SIZE,
      SBIT_BX_DLY => SBIT_BX_DLY,
      SEL_NOLATCH => SEL_NOLATCH)
    port map (

      clock   => clock,
      clock40 => clock40,

      sbits_i_dav => sbits_i_dav,
      sbits_i     => sbits_i,

      dav_i => dav_i,
      dav_o => mux_dav,

      strip_sel0 => segments_i(0).strip,
      strip_sel1 => segments_i(0).strip,
      strip_sel2 => segments_i(1).strip,
      strip_sel3 => segments_i(1).strip,
      strip_sel4 => segments_i(2).strip,
      strip_sel5 => segments_i(2).strip,
      strip_sel6 => segments_i(3).strip,
      strip_sel7 => segments_i(3).strip,

      prt_sel0 => std_logic_vector(segments_i(0).prt),
      prt_sel1 => std_logic_vector(segments_i(0).prt-1),
      prt_sel2 => std_logic_vector(segments_i(1).prt),
      prt_sel3 => std_logic_vector(segments_i(1).prt-1),
      prt_sel4 => std_logic_vector(segments_i(2).prt),
      prt_sel5 => std_logic_vector(segments_i(2).prt-1),
      prt_sel6 => std_logic_vector(segments_i(3).prt),
      prt_sel7 => std_logic_vector(segments_i(3).prt-1),

      ly0_o => ly(0),
      ly1_o => ly(1),
      ly2_o => ly(2),
      ly3_o => ly(3),
      ly4_o => ly(4),
      ly5_o => ly(5)
      );

  --------------------------------------------------------------------------------
  -- X-prt ORing
  --
  -- To avoid doubling the size of the multiplexers, we only multiplex the
  -- original (unORed) data. The ORing of data needed for cross-partition data
  -- sharing happens again here.
  --
  -- This is done by running the multiplexers for both partition i and
  -- partition i-1.
  --
  -- The data for partition i will come out in clock cycle n, data for
  -- partition i-1 will come out in clock cycle n+1.
  --
  -- There will be some fickle timing because we must keep track of, for a
  -- given segment, whether when its muxed data comes out several clock cycles
  -- later, should it be ORed or not?
  --
  --------------------------------------------------------------------------------

  process (clock) is
  begin
    if (rising_edge(clock)) then
      for I in segment_is_xprt'range loop
        if (segments(I).prt mod 2 = 0) then
          segment_is_xprt(I) <= '0';
        else
          segment_is_xprt(I) <= '1';
        end if;
      end loop;
    end if;
  end process;

  fixed_delay_sf_inst : entity work.fixed_delay_sf
    generic map (
      DELAY => X_PRT_DLY,
      WIDTH => segment_is_xprt'length
      )
    port map (
      clock  => clock,
      data_i => segment_is_xprt,
      data_o => segment_is_xprt_dly
      );

  process (clock) is
  begin
    if (rising_edge(clock)) then

      for I in 0 to 5 loop
        ly_n(0) <= ly(0);

        if (segment_is_x_prt_dly(I)) then
          ly_or(I) <= ly_n(I) or ly(I);
        else
          ly_or(I) <= ly_n(I);
        end if;

      end loop;

    end if;
  end process;


end behavioral;
