----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--
-- The pattern unit is the most fundamental element of the ME0 Road Based
-- Pattern Finder. It is instantiated around a single strip, and looks for the
-- best candidate pattern that can be identified on that strip.
--
-- Because this module is so heavily replicated, great care must be taken in
-- making modifications, since small changes in resource usage will have huge
-- ramifications for overall firmware usage.
--
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;
use work.pat_types.all;

entity pat_unit is
  generic(
    VERBOSE : boolean        := false;
    PATLIST : patdef_array_t := patdef_array;

    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);
    LY2_SPAN : natural := get_max_span(patdef_array);
    LY3_SPAN : natural := get_max_span(patdef_array);
    LY4_SPAN : natural := get_max_span(patdef_array);
    LY5_SPAN : natural := get_max_span(patdef_array)
    );

  port(

    clock : in std_logic;

    dav_i : in  std_logic;
    dav_o : out std_logic;

    ly_thresh : in ly_thresh_t;

    ly0 : in std_logic_vector (LY0_SPAN-1 downto 0);
    ly1 : in std_logic_vector (LY1_SPAN-1 downto 0);
    ly2 : in std_logic_vector (LY2_SPAN-1 downto 0);
    ly3 : in std_logic_vector (LY3_SPAN-1 downto 0);
    ly4 : in std_logic_vector (LY4_SPAN-1 downto 0);
    ly5 : in std_logic_vector (LY5_SPAN-1 downto 0);

    pat_o : out pat_unit_t

    );
end pat_unit;

architecture behavioral of pat_unit is

  signal dav_s1 : std_logic := '0';

  signal pats : pat_unit_pre_list_t (NUM_PATTERNS-1 downto 0)
    := (others => null_pat_unit_pre);

  signal pats_dav     : std_logic := '0';
  signal priority_dav : std_logic := '0';

  signal best_slv : std_logic_vector (pat_unit_pre_t'w-1 downto 0);
  signal best     : pat_unit_pre_t;
  signal cand_slv : bus_array (0 to NUM_PATTERNS-1) (pat_unit_pre_t'w-1 downto 0);

begin

  check_pattern_operators(true);

  assert (LY0_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY0_SPAN) & ")" severity error;
  assert (LY1_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY1_SPAN) & ")" severity error;
  assert (LY2_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY2_SPAN) & ")" severity error;
  assert (LY3_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY3_SPAN) & ")" severity error;
  assert (LY4_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY4_SPAN) & ")" severity error;
  assert (LY5_SPAN mod 2 = 1) report "Layer Span Must be Odd (span=" & integer'image(LY5_SPAN) & ")" severity error;

  --------------------------------------------------------------------------------
  -- Layer Processing
  --------------------------------------------------------------------------------

  patgen : for I in 0 to patlist'length-1 generate

    function get_ly_mask (size   : natural;
                          ly     : std_logic_vector;
                          ly_pat : hi_lo_t)
      return std_logic_vector is
      variable result : std_logic_vector(size-1 downto 0);
      variable center : natural := ly'length / 2;
    begin
      result := ly (center + ly_pat.hi downto center + ly_pat.lo);
      return result;
    end;

    constant ly0_size : natural := get_ly_size (0, patlist(I).ly0);
    constant ly1_size : natural := get_ly_size (1, patlist(I).ly1);
    constant ly2_size : natural := get_ly_size (2, patlist(I).ly2);
    constant ly3_size : natural := get_ly_size (3, patlist(I).ly3);
    constant ly4_size : natural := get_ly_size (4, patlist(I).ly4);
    constant ly5_size : natural := get_ly_size (5, patlist(I).ly5);

    signal ly0_mask : std_logic_vector (ly0_size-1 downto 0);
    signal ly1_mask : std_logic_vector (ly1_size-1 downto 0);
    signal ly2_mask : std_logic_vector (ly2_size-1 downto 0);
    signal ly3_mask : std_logic_vector (ly3_size-1 downto 0);
    signal ly4_mask : std_logic_vector (ly4_size-1 downto 0);
    signal ly5_mask : std_logic_vector (ly5_size-1 downto 0);

  begin

    lysize : if (VERBOSE) generate

      print_pattern (patlist(I));

      assert false report "ly0_size=" & integer'image(ly0_size) severity note;
      assert false report "ly1_size=" & integer'image(ly1_size) severity note;
      assert false report "ly2_size=" & integer'image(ly2_size) severity note;
      assert false report "ly3_size=" & integer'image(ly3_size) severity note;
      assert false report "ly4_size=" & integer'image(ly4_size) severity note;
      assert false report "ly5_size=" & integer'image(ly5_size) severity note;

    end generate;

    -- for each pattern, slice off just the bits that are included as part of
    -- the pattern mask; this subset of bits is passed into the hit count module
    -- and used for sorting

    ly0_mask <= get_ly_mask (ly0_size, ly0, patlist(I).ly0);
    ly1_mask <= get_ly_mask (ly1_size, ly1, patlist(I).ly1);
    ly2_mask <= get_ly_mask (ly2_size, ly2, patlist(I).ly2);
    ly3_mask <= get_ly_mask (ly3_size, ly3, patlist(I).ly3);
    ly4_mask <= get_ly_mask (ly4_size, ly4, patlist(I).ly4);
    ly5_mask <= get_ly_mask (ly5_size, ly5, patlist(I).ly5);

    -- hit_count module is the workhorse of the segment finder...
    -- everything else is just sorting

    i_hit_count : entity work.hit_count
      generic map(
        HCB => HC_BITS,
        LCB => LC_BITS)
      port map (
        clk => clock,
        ly0 => ly0_mask,
        ly1 => ly1_mask,
        ly2 => ly2_mask,
        ly3 => ly3_mask,
        ly4 => ly4_mask,
        ly5 => ly5_mask,
        hc  => pats(I).hc,
        lc  => pats(I).lc);

    -- copy the (constant) pattern id
    pats(I).id <= to_unsigned(patlist(I).id, PID_BITS);

  end generate;

  process (clock) is
  begin
    if (rising_edge(clock)) then
      pats_dav <= dav_i;
    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Choose the best 1 of N possible segments
  --------------------------------------------------------------------------------

  priority_encoder_inst : entity work.priority_encoder
    generic map (
      WIDTH       => NUM_PATTERNS,
      REG_INPUT   => true,
      REG_OUTPUT  => true,
      REG_STAGES  => 2,
      DAT_BITS    => best_slv'length,
      QLT_BITS    => best_slv'length,
      IGNORE_BITS => 0,                 -- 1 to ignore the bend of the pattern id, 2 and 3 are the same, 4, 5 are the same, etc
      ADR_BITS_o  => integer(ceil(log2(real(NUM_PATTERNS))))
      )
    port map (
      clock => clock,
      dav_i => pats_dav,
      dav_o => priority_dav,
      dat_i => cand_slv,
      dat_o => best_slv,
      adr_o => open
      );

  -- record -> slv for priority encoder
  cand_to_slv : for I in 0 to NUM_PATTERNS-1 generate
  begin
    cand_slv(I) <= convert(pats(I), cand_slv(I));
  end generate;

  -- slv -> record from priority encoder
  best <= convert(best_slv, best);

  --------------------------------------------------------------------------------
  -- Put a threshold, make sure the pattern is above some minimum layer cnt
  --------------------------------------------------------------------------------

  process (clock) is
  --variable increase_thresh : std_logic_vector (2 downto 0) := "000";
  begin
    if (rising_edge(clock)) then

      dav_o <= priority_dav;

      if (best.lc >= unsigned(ly_thresh(to_integer(best.id)))) then
        pat_o.lc <= best.lc;
        pat_o.id <= best.id;
      else
        pat_o <= zero(pat_o);
      end if;

    end if;
  end process;

end behavioral;
