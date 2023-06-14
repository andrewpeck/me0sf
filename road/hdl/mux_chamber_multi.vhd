library work;
use work.pat_types.all;
use work.pat_pkg.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity mux_chamber_multi is
  generic(
    NUM_PRT     : natural               := 8;     -- Number of REAL partitions, should always be 8
    PRT_SIZE    : natural               := 192;   -- Size of a partition, should always be 192
    PAT_SIZE    : natural               := 37;    -- Size of a pattern unit, may vary, should be set to MAX_SPAN
    SBIT_BX_DLY : natural range 0 to 32 := 6;     -- Number of BX to delay the S-bits to account for pattern finding latency
    SEL_NOLATCH : boolean               := false  -- See description below
    );
  port(

    clock   : in std_logic;
    clock40 : in std_logic;

    sbits_i_dav : in std_logic;
    sbits_i     : in chamber_t;         -- (prt)(ly)(strip)

    dav_i : in  std_logic;
    dav_o : out std_logic;

    strip_sel0 : in std_logic_vector (7 downto 0);
    strip_sel1 : in std_logic_vector (7 downto 0);
    strip_sel2 : in std_logic_vector (7 downto 0);
    strip_sel3 : in std_logic_vector (7 downto 0);
    strip_sel4 : in std_logic_vector (7 downto 0);
    strip_sel5 : in std_logic_vector (7 downto 0);
    strip_sel6 : in std_logic_vector (7 downto 0);

    prt_sel0 : in std_logic_vector (2 downto 0);
    prt_sel1 : in std_logic_vector (2 downto 0);
    prt_sel2 : in std_logic_vector (2 downto 0);
    prt_sel3 : in std_logic_vector (2 downto 0);
    prt_sel4 : in std_logic_vector (2 downto 0);
    prt_sel5 : in std_logic_vector (2 downto 0);
    prt_sel6 : in std_logic_vector (2 downto 0);
    prt_sel7 : in std_logic_vector (2 downto 0);

    strip_sel7 : in std_logic_vector (7 downto 0);

    ly0_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly1_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly2_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly3_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly4_o : out std_logic_vector(PAT_SIZE-1 downto 0);
    ly5_o : out std_logic_vector(PAT_SIZE-1 downto 0)

    );
end mux_chamber_multi;

architecture behavioral of mux_chamber_multi is

  signal dav_i_phase   : natural range 0 to 7 := 0;
  signal sbits_i_phase : natural range 0 to 7 := 0;

  signal strip_sel : std_logic_vector (7 downto 0);
  signal prt_sel   : std_logic_vector (2 downto 0);

  signal sbits_dly : chamber_t;         -- (prt)(ly)(strip)

  type strip_sel_array_t is array (7 downto 0) of std_logic_vector(7 downto 0);
  type prt_sel_array_t is array (7 downto 0) of std_logic_vector(2 downto 0);

  signal strip_sel_arr : strip_sel_array_t;
  signal prt_sel_arr   : prt_sel_array_t;

begin

  --------------------------------------------------------------------------------
  -- Strip / Prt Selection Delays, to align with the 40MHz clock
  --
  -- we need to either align the S-bits to the select signals, or the select
  -- signals to the S-bits. Given how many S-bits there are though and that they
  -- need to be delayed for many clock cycles, I opted to delay on the 40MHz
  -- clock to reduce the number of SRLs. This means that the segments must be
  -- delayed <1 bx to align to the 40MHz clock again.
  --
  -- The SEL_NOLATCH option skips the 40MHz FF, and can be used to reduce
  -- latency in case the SEL signals are already aligned to the 40MHz clock
  --
  --------------------------------------------------------------------------------

  process (all) is
  begin
    if (SEL_NOLATCH or rising_edge(clock40)) then

      prt_sel_arr(0) <= prt_sel0;
      prt_sel_arr(1) <= prt_sel1;
      prt_sel_arr(2) <= prt_sel2;
      prt_sel_arr(3) <= prt_sel3;
      prt_sel_arr(4) <= prt_sel4;
      prt_sel_arr(5) <= prt_sel5;
      prt_sel_arr(6) <= prt_sel6;
      prt_sel_arr(7) <= prt_sel7;

      strip_sel_arr(0) <= strip_sel0;
      strip_sel_arr(1) <= strip_sel1;
      strip_sel_arr(2) <= strip_sel2;
      strip_sel_arr(3) <= strip_sel3;
      strip_sel_arr(4) <= strip_sel4;
      strip_sel_arr(5) <= strip_sel5;
      strip_sel_arr(6) <= strip_sel6;
      strip_sel_arr(7) <= strip_sel7;

    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Demultiplex the strip / partition select signals
  --------------------------------------------------------------------------------

  dav_to_phase_sbits_i : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => sbits_i_dav, phase_o => sbits_i_phase);

  process (clock) is
  begin
    if (rising_edge(clock)) then
      case sbits_i_phase is

        when 0 => strip_sel <= strip_sel_arr(0); prt_sel <= prt_sel_arr(0);
        when 1 => strip_sel <= strip_sel_arr(1); prt_sel <= prt_sel_arr(1);
        when 2 => strip_sel <= strip_sel_arr(2); prt_sel <= prt_sel_arr(2);
        when 3 => strip_sel <= strip_sel_arr(3); prt_sel <= prt_sel_arr(3);
        when 4 => strip_sel <= strip_sel_arr(4); prt_sel <= prt_sel_arr(4);
        when 5 => strip_sel <= strip_sel_arr(5); prt_sel <= prt_sel_arr(5);
        when 6 => strip_sel <= strip_sel_arr(6); prt_sel <= prt_sel_arr(6);
        when 7 => strip_sel <= strip_sel_arr(7); prt_sel <= prt_sel_arr(7);

        when others => strip_sel <= strip_sel_arr(0); prt_sel <= prt_sel_arr(0);

      end case;

    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Implement a delay line to delay the S-bits until the segments are found
  --------------------------------------------------------------------------------

  prt : for IPRT in 0 to 7 generate
    constant bx_dly : std_logic_vector (3 downto 0) :=
      std_logic_vector(to_unsigned(SBIT_BX_DLY-1, 4));
  begin

    ly : for ILY in 0 to 5 generate

      dly_sbits_bx : entity work.fixed_delay_sf
        generic map (
          DELAY => SBIT_BX_DLY,
          WIDTH => PRT_WIDTH
          )
        port map (
          clock  => clock40,
          data_i => sbits_i(IPRT)(ILY),
          data_o => sbits_dly(IPRT)(ILY)
          );

    end generate;
  end generate;

  --------------------------------------------------------------------------------
  -- Multiplex the chamber into its pat window outputs
  -- can get 8 different pat windows in one bx
  --------------------------------------------------------------------------------

  mux_chamber_inst : entity work.mux_chamber
    generic map (
      NUM_PRT  => NUM_PRT,
      PRT_SIZE => PRT_WIDTH,
      PAT_SIZE => PAT_SIZE)
    port map (
      clock     => clock,
      sbits_i   => sbits_dly,
      strip_sel => strip_sel,
      prt_sel   => prt_sel,
      ly0_o     => ly0_o,
      ly1_o     => ly1_o,
      ly2_o     => ly2_o,
      ly3_o     => ly3_o,
      ly4_o     => ly4_o,
      ly5_o     => ly5_o
      );

end behavioral;
