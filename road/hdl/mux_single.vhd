----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
--
-- TODO: look into using DSPs as the multiplexing elements? dsps are otherwise
-- very unused
--
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library unisim;
use unisim.vcomponents.all;

entity mux_single is

  generic(
    REG_STAGES     : natural := 2;      -- 0=no registers, 1=every stage, 2=every other stage
    STAGE          : natural := 0;
    DAT_SIZE       : natural := 128;
    SEL_SIZE       : natural := integer(ceil(log2(real(DAT_SIZE))));
    RECURSE_THRESH : natural := 8
    );

  port(
    clock : in  std_logic;
    din   : in  std_logic_vector(DAT_SIZE-1 downto 0);
    sel   : in  std_logic_vector(SEL_SIZE-1 downto 0);
    dout  : out std_logic
    );
end mux_single;

architecture behavioral of mux_single is

  constant NUM_BITS         : natural := integer(ceil(log2(real(din'length))));
  constant DIN_PADDED_WIDTH : natural := 2**NUM_BITS;

  signal din_padded : std_logic_vector (DIN_PADDED_WIDTH - 1 downto 0)
    := (others => '0');

  signal d_muxed : std_logic := '0';

  function stage_is_registered (stg : integer; reg_stgs : integer)
    return boolean is
  begin
    if (reg_stgs = 0) then
      return false;
    elsif (stg mod reg_stgs = 0) then
      return true;
    else
      return false;
    end if;
  end function;

begin

  assert sel'length = NUM_BITS
    report "length of sel does not match expected number of bits" &
    "sel=" & integer'image(to_integer(unsigned(sel))) &
    "num_bits=" & integer'image(NUM_BITS)
    severity error;

  --------------------------------------------------------------------------------
  -- Zero padding
  --------------------------------------------------------------------------------

  din_padded(din'range) <= din(din'range);

  --------------------------------------------------------------------------------
  -- Recursive Instantiation
  --------------------------------------------------------------------------------

  muxr : if (din'length > RECURSE_THRESH) generate

    signal din_msbs : std_logic_vector (DIN_PADDED_WIDTH/2-1 downto 0);
    signal din_lsbs : std_logic_vector (DIN_PADDED_WIDTH/2-1 downto 0);

    signal dout_msbs : std_logic := '0';
    signal dout_lsbs : std_logic := '0';

  begin

    din_msbs <= din_padded (DIN_PADDED_WIDTH-1 downto DIN_PADDED_WIDTH/2);
    din_lsbs <= din_padded (DIN_PADDED_WIDTH/2-1 downto 0);

    mux_msbs : entity work.mux_single
      generic map (
        REG_STAGES => REG_STAGES,
        STAGE      => STAGE+1,
        SEL_SIZE   => SEL_SIZE - 1,
        DAT_SIZE   => DIN_PADDED_WIDTH/2
        )
      port map (
        clock => clock,
        sel   => sel(sel'length-2 downto 0),
        din   => din_msbs,
        dout  => dout_msbs
        );

    mux_lsbs : entity work.mux_single
      generic map (
        REG_STAGES => REG_STAGES,
        STAGE      => STAGE+1,
        SEL_SIZE   => SEL_SIZE - 1,
        DAT_SIZE   => DIN_PADDED_WIDTH/2
        )
      port map (
        clock => clock,
        sel   => sel(sel'length-2 downto 0),
        din   => din_lsbs,
        dout  => dout_lsbs
        );

    -- use a muxf9 / f8 / f7 etc
    -- manual instantiation of these components reduced resource usage by ~70000 LUTs
    -- since the Vivado tools were failing to infer the MUXF9

    f9 : if (din'length=32) generate
      MUXF9_inst : MUXF9
        port map (O => d_muxed, I0 => dout_lsbs, I1 => dout_msbs, S => sel(sel'left));
    end generate;

    f8 : if (din'length=16) generate
      MUXF8_inst : MUXF8
        port map (O => d_muxed, I0 => dout_lsbs, I1 => dout_msbs, S => sel(sel'left));
    end generate;

    f7 : if (din'length=8) generate
      MUXF7_inst : MUXF7
        port map (O => d_muxed, I0 => dout_lsbs, I1 => dout_msbs, S => sel(sel'left));
    end generate;

    b : if (din'length /= 8 and din'length /= 16 and din'length /= 32) generate
      d_muxed <= dout_lsbs when sel(sel'left) = '0' else dout_msbs;
    end generate;

  end generate;

  muxf : if (din'length <= RECURSE_THRESH) generate
    d_muxed <= din(to_integer(unsigned(sel)));
  end generate;

  process (all) is
  begin
    if (not stage_is_registered(STAGE, REG_STAGES) or
        rising_edge(clock)) then
      dout <= d_muxed;
    end if;
  end process;

end behavioral;
