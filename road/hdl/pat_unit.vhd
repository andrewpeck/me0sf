----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
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

    LATENCY : natural := PAT_UNIT_LATENCY;

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

    ly_thresh  : in std_logic_vector (2 downto 0);
    hit_thresh : in std_logic_vector (5 downto 0);

    ly0 : in std_logic_vector (LY0_SPAN-1 downto 0);
    ly1 : in std_logic_vector (LY1_SPAN-1 downto 0);
    ly2 : in std_logic_vector (LY2_SPAN-1 downto 0);
    ly3 : in std_logic_vector (LY3_SPAN-1 downto 0);
    ly4 : in std_logic_vector (LY4_SPAN-1 downto 0);
    ly5 : in std_logic_vector (LY5_SPAN-1 downto 0);

    pat_o : out segment_t

    );
end pat_unit;

architecture behavioral of pat_unit is

  signal dav_s1 : std_logic := '0';

  signal pats     : segment_list_t (NUM_PATTERNS-1 downto 0) := (others => null_pattern);

  signal pats_dav : std_logic                                := '0';
  signal priority_dav : std_logic                                := '0';

  function count_ones(slv : std_logic_vector) return natural is
    variable n_ones : natural := 0;
  begin
    for i in slv'range loop
      if slv(i) = '1' then
        n_ones := n_ones + 1;
      end if;
    end loop;
    return n_ones;
  end function count_ones;

  signal best_slv : std_logic_vector (segment_t'w-1 downto 0);
  signal best     : segment_t;
  signal cand_slv : bus_array (0 to NUM_PATTERNS-1) (segment_t'w-1 downto 0);

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

    function get_ly_size (ly     : natural;
                          ly_pat : hi_lo_t)
      return natural is
    begin
      return (ly_pat.hi-ly_pat.lo+1);
    end;

    function get_ly_mask (size   : natural;
                          ly     : std_logic_vector;
                          ly_pat : hi_lo_t)
      return std_logic_vector is
      variable result : std_logic_vector(size-1 downto 0);
      variable center : natural := ly'length / 2;  -- FIXME: check the rounding on this
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

    ly0_mask <= get_ly_mask (ly0_size, ly0, patlist(I).ly0);
    ly1_mask <= get_ly_mask (ly1_size, ly1, patlist(I).ly1);
    ly2_mask <= get_ly_mask (ly2_size, ly2, patlist(I).ly2);
    ly3_mask <= get_ly_mask (ly3_size, ly3, patlist(I).ly3);
    ly4_mask <= get_ly_mask (ly4_size, ly4, patlist(I).ly4);
    ly5_mask <= get_ly_mask (ly5_size, ly5, patlist(I).ly5);

    process (clock) is
    begin
      if (rising_edge(clock)) then

        pats_dav <= dav_i;

        pats(I) <= null_pattern;

        -- count
        pats(I).hc <=
          to_unsigned(count_ones(ly0_mask) +
                      count_ones(ly1_mask) +
                      count_ones(ly2_mask) +
                      count_ones(ly3_mask) +
                      count_ones(ly4_mask) +
                      count_ones(ly5_mask), HC_BITS);

        pats(I).lc <=
          to_unsigned(count_ones(or_reduce(ly0_mask) &
                                 or_reduce(ly1_mask) &
                                 or_reduce(ly2_mask) &
                                 or_reduce(ly3_mask) &
                                 or_reduce(ly4_mask) &
                                 or_reduce(ly5_mask)), LC_BITS);

        -- pattern id
        pats(I).id <= to_unsigned(patlist(I).id, PID_BITS);

      end if;
    end process;

    --------------------------------------------------------------------------------
    -- Centroid Finding
    -- done in parallel with count ones etc
    --------------------------------------------------------------------------------

    centroid_finder_0 : entity work.centroid_finder
      generic map (LENGTH => ly0_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly0_mask,
        dout => pats(I).hits(0)
        );

    centroid_finder_1 : entity work.centroid_finder
      generic map (LENGTH => ly1_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly1_mask,
        dout => pats(I).hits(1)
        );

    centroid_finder_2 : entity work.centroid_finder
      generic map (LENGTH => ly2_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly2_mask,
        dout => pats(I).hits(2)
        );

    centroid_finder_3 : entity work.centroid_finder
      generic map (LENGTH => ly3_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly3_mask,
        dout => pats(I).hits(3)
        );

    centroid_finder_4 : entity work.centroid_finder
      generic map (LENGTH => ly4_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly4_mask,
        dout => pats(I).hits(4)
        );

    centroid_finder_5 : entity work.centroid_finder
      generic map (LENGTH => ly5_size, NBITS => CENTROID_BITS)
      port map (
        clk  => clock,
        din  => ly5_mask,
        dout => pats(I).hits(5)
        );

  end generate;

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
      QLT_BITS    => PATTERN_SORTB,
      IGNORE_BITS => STRIP_BITS + PARTITION_BITS,
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
  begin
    if (rising_edge(clock)) then

      dav_o <= priority_dav;

      if (best.lc >= to_integer(unsigned(ly_thresh)) and
          best.hc >= to_integer(unsigned(hit_thresh))) then
        pat_o <= best;
      else
        pat_o <= zero(pat_o);
      end if;
    end if;
  end process;

end behavioral;
