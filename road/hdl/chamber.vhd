----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--   Segment finding for a single ME0 chamber
--
-- Notes:
--
-- + Only apply threshold at the end.. there is no reason to have a choke point
-- anywhere in early in segment finding if we need to do a full sort anyway..
-- might as well just output the raw segments and for the final N outputs apply
-- the layer etc thresholds-- or rather, we can have two different thresholds:
--
--      pretrigger threshold would be applied at the segment creation level and
--      would determine whether a segment forms at all. This could be a lower
--      threshold which would be used for the pretrigger. the full trigger
--      threshold would be applied at the end and can be higher
--
----------------------------------------------------------------------------------

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;
use ieee.fixed_pkg.all;

entity chamber is
  generic (
    DISABLE_PEAKING : boolean := false;  -- true to disable peaking logic; useful for simulation until the tb is updated
    X_PRT_EN        : boolean := true;   -- true to enable x-prt segment finding
    EN_NON_POINTING : boolean := false;  -- true to enable x-prt segment finding on non-pointing muons
    NUM_SEGMENTS    : integer := 8;      -- number of output segments
    S0_WIDTH        : natural := 16;     -- chunk each partition into groups this size and choose only 1 segment from each group
    S1_REUSE        : natural := 4;      -- reuse sorters
    REG_OUTPUTS     : boolean := false;  -- true to  register outputs on the 40MHz clock
    PULSE_EXTEND    : integer := 2;      -- how long pulses should be extended by
    --DEADTIME        : natural := 3;      -- deadtime in bx
    EN_HC_COMPRESS : boolean := false;   -- true to enable compression of hit count function (REQUIRED: minimum ly_thresh value is 4)
    X_DEGHOST_EDGE_DIST : natural := 2;  -- radius for cross partition deghosting
    SBIT_BRAM_PHASE : integer := 0;
    BRAM_LATENCY : integer := 64; -- Add 8 (1 BX) if peaking is enabled
    
    LY0_SPAN : natural := get_max_span(patdef_array);
    LY1_SPAN : natural := get_max_span(patdef_array);
    LY2_SPAN : natural := get_max_span(patdef_array);
    LY3_SPAN : natural := get_max_span(patdef_array);
    LY4_SPAN : natural := get_max_span(patdef_array);
    LY5_SPAN : natural := get_max_span(patdef_array);

    PATLIST : patdef_array_t := patdef_array
    );
  port(
    clock             : in  std_logic;                     -- MUST BE 320MHZ
    clock40           : in  std_logic;                     -- MUST BE  40MHZ

    -- synthesis translate_off
    dav_i_phase       : out natural range 0 to 7;
    dav_o_phase       : out natural range 0 to 7;
    -- synthesis translate_on

    sbits_i           : in  chamber_t;
    ly_thresh_i         : in  ly_thresh_chamber; -- Layer threshold, 0 to 6
    vfat_pretrigger_o : out std_logic_vector (23 downto 0);
    segment_o        : out segment_w_fit_t;
    
    dav_i             : in  std_logic;
    dav_o             : out std_logic
    );
    
end chamber;

architecture behavioral of chamber is

  --------------------------------------------------------------------------------
  -- Constants
  --------------------------------------------------------------------------------

  --------------------------------------------------------------------------------
  --Used for testing, delete later. Allows to set all inputs to 0 and leave them hanging,
  --since there are not enough real I/O pins to use chamber as a top level entity.--
  --------------------------------------------------------------------------------
--  signal sbits_i : chamber_t;
--  attribute dont_touch : string;
--  attribute dont_touch of sbits_i : signal is "true";
--  
--  signal vfat_pretrigger_o : std_logic_vector(23 downto 0);
--  attribute dont_touch of vfat_pretrigger_o : signal is "true";
-- 
--  signal segment_o        : segment_w_fit_t;
--  attribute dont_touch of segment_o : signal is "true";
-- 
--  signal ly_thresh_i : ly_thresh_chamber := (others => (others => "100"));
--  attribute dont_touch of ly_thresh_i : signal is "true";
  --------------------------------------------------------------------------------

  constant NUM_PARTITIONS : integer := 8;

  -- Number of segments output from each partition, e.g. 24
  constant NUM_SEGS_PER_PRT : natural := PRT_WIDTH/S0_WIDTH;

  -- number of di-partition segment selectors in the firmware
  -- at the most basic level, it is 1 for each 2 partitions
  -- but we can have a time-multiplexing re-use factor that reduces it further
  --
  -- include a +1 offset so the 15 case divides to 8, while 8 divides to 4
  --
  -- | X_PRT | S1_REUSE | N_SELECTORS |
  -- |-------+----------+-------------|
  -- |     f |        1 |           4 |
  -- |     f |        2 |           2 |
  -- |     f |        4 |           1 |
  -- |     t |        1 |           8 |
  -- |     t |        2 |           4 |
  -- |     t |        4 |           2 |

  constant NUM_FINDERS : integer := if_then_else (X_PRT_EN, 15, 8);

  -- use a CEIL here so that 15/2 -> 8 instead of 7..
  -- otherwise the highest partition is dropped
  constant NUM_FINDERS_DIV2 : integer := integer(ceil(real(NUM_FINDERS)/2.0));
  
  constant MIN_LY_THRESH : natural := 4;

  constant FIT_DELAY : natural := 13-1; -- TODO: Find what this is currently

  --------------------------------------------------------------------------------
  -- Extension
  --------------------------------------------------------------------------------

  signal sbits_extend : chamber_t;
  signal dav_extend   : std_logic;

  --------------------------------------------------------------------------------
  -- Segments
  --------------------------------------------------------------------------------

  signal all_segs            : segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0)    := (others => null_pattern);  -- get all segments from each partition
  signal all_segs_x_deghosted  : segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0)    := (others => null_pattern);  -- all segments after x-partition deghosting
  signal two_prt_sorted_segs : segment_list_t (NUM_FINDERS_DIV2 * NUM_SEGMENTS - 1 downto 0)   := (others => null_pattern);  -- sort down to number of output segments for each 2 partitions
  signal one_prt_sorted_segs : segment_list_t (NUM_FINDERS_DIV2*2 * NUM_SEGMENTS - 1 downto 0) := (others => null_pattern);  -- sort down to the number of output segments for each partition
  signal final_segs          : segment_list_t (NUM_SEGMENTS - 1 downto 0); 
  signal final_segs_phase    : unsigned (2 downto 0)                                           := (others => '0');
  signal fit_segment : segment_w_fit_t;

  --------------------------------------------------------------------------------
  -- Pretriggers
  --------------------------------------------------------------------------------

  type strip_triggers_array_t is array (NUM_FINDERS-1 downto 0) of
    std_logic_vector(PRT_WIDTH-1 downto 0);

  type vfat_pretrigger_t is array (integer range <>) of
    std_logic_vector(2 downto 0);

  signal strip_triggers       : strip_triggers_array_t;
  signal vfat_pretrigger_xprt : vfat_pretrigger_t(NUM_FINDERS-1 downto 0);
  signal vfat_pretrigger      : vfat_pretrigger_t(7 downto 0);

  --------------------------------------------------------------------------------
  -- Data valids
  --------------------------------------------------------------------------------

  signal all_segs_dav : std_logic_vector (NUM_FINDERS - 1 downto 0) := (others => '0');
  signal all_segs_dav_deghosted : std_logic_vector (NUM_FINDERS - 1 downto 0) := (others => '0');

  signal one_prt_sorted_dav : std_logic_vector (NUM_FINDERS-1 downto 0)      := (others => '0');
  signal two_prt_sorted_dav : std_logic_vector (NUM_FINDERS_DIV2-1 downto 0) := (others => '0');
  signal final_segs_dav     : std_logic;

  signal outclk : std_logic := '0';
  
  --------------------------------------------------------------------------------
  -- Layer Thresholding
  --------------------------------------------------------------------------------
  signal ly_thresh_compressed : ly_thresh_chamber;
  
  --Function to save on bits required to represent layer hits. Instead of a real layer count
  --such as 4, changes the threshold to 0, with the understanding this is the value above
  --the minimum threshold.
  function compress_ly_count (ly_thresh : ly_thresh_chamber)
    return ly_thresh_chamber is
    variable ly_thresh_compressed : ly_thresh_chamber;
  begin
    for i in 0 to 15-1 loop
      for j in 0 to NUM_PATTERNS-1 loop
        ly_thresh_compressed(i)(j) := std_logic_vector(unsigned(ly_thresh(i)(j)) - MIN_LY_THRESH);
      end loop;
    end loop;
    return ly_thresh_compressed;
  end;

  function decompress_ly_count (segment : segment_w_fit_t) return segment_w_fit_t is
    variable tmp : segment_w_fit_t := segment;
  begin
      if segment.lc > 0 then
        tmp.lc := segment.lc + 3;
      end if;
    return tmp;
  end;

  --------------------------------------------------------------------------------
  -- Sbit BRAM
  --------------------------------------------------------------------------------
  signal bram_in : chamber_w_virtual_t;
  signal bram_out : sbit_window_t;
  signal bram_seg_select_phase : unsigned (2 downto 0) := (others => '0');

  type seg_info_buffer_t is array (0 to 5+FIT_DELAY) of segment_t;

  --signal seg_info_buffer : seg_info_buffer_t;
  signal seg_info_buffer : segment_list_t (5+FIT_DELAY downto 0);
  
  --------------------------------------------------------------------------------
  -- Centroids
  --------------------------------------------------------------------------------
    
  signal centroids_in : pat_sbits_t;
  signal centroids : centroids_t;
  signal centroids_offset : centroids_offset_t;
  signal valid_hits : std_logic_vector (5 downto 0);
  
  --------------------------------------------------------------------------------
  -- Fitter
  --------------------------------------------------------------------------------
 
  -- Outputs from fitter module 
  signal strip_o : sfixed (5-1 downto -5);
  signal intercept_o : sfixed (7-1 downto -7);
  signal slope_o : sfixed (4-1 downto -6);

  -- Intermediary signals for the coordinate conversion
  signal patspan_adjust : sfixed (5 downto 0);
  signal fit_strip_div2 : sfixed (3 downto strip_o'low-1);
  signal seg_strip_sfixed : sfixed (8 downto -6); 
  
  -- Constants (per pattern, per layer) for the offsets for each pattern's sbits in each signal
  -- E.g. in this example, the centroid finders only receive the single bit in the place of the X per layer, but their true positions are offset
  -- from one another
  -- --X
  -- -X-
  -- X--
  -- These are constants computed at compile time, so don't need to worry about resources for implementation
  
  type ly_offsets_t is array (0 to 5) of integer;
  type pat_ly_offsets_t is array (0 to NUM_PATTERNS-1) of ly_offsets_t;
  
  function find_offsets (patlist : patdef_array_t) return pat_ly_offsets_t is
    variable rightmost_position : integer;
    variable ly_hi : integer;
    variable offsets : pat_ly_offsets_t;
  begin
    for pat_i in 0 to NUM_PATTERNS-1 loop
      -- First, find rightmost positions for each pattern, which must be in either layer 0 or layer 5
      rightmost_position := maximum(patlist(pat_i).ly0.hi, patlist(pat_i).ly5.hi);
      -- Then, find the offset for each layer in the pattern
      for ly_i in 0 to 5 loop
        -- Have to do it this way since the ly0, ly1, ... values in the patlist are currently implemented as separately named signals
        if ly_i = 0 then
          ly_hi := patlist(pat_i).ly0.hi;
        elsif ly_i = 1 then
          ly_hi := patlist(pat_i).ly1.hi;
        elsif ly_i = 2 then
          ly_hi := patlist(pat_i).ly2.hi;
        elsif ly_i = 3 then
          ly_hi := patlist(pat_i).ly3.hi;
        elsif ly_i = 4 then
          ly_hi := patlist(pat_i).ly4.hi;
        elsif ly_i = 5 then
          ly_hi := patlist(pat_i).ly5.hi;
        end if;
        
        offsets(pat_i)(ly_i) := (rightmost_position - ly_hi) * 2; -- Factor of 2 for double resolution that comes from centroid finder
      end loop; 
    end loop;
    
    return offsets;
  end function;
  
  constant offsets : pat_ly_offsets_t := find_offsets(PATLIST);
  
  -- Prepare LUT for patspans, for use after the fitter to shift coordinates to full chamber frame
  type patspan_LUT_t is array (0 to NUM_PATTERNS-1) of integer; 
  function find_all_pat_spans (patlist : patdef_array_t) return patspan_LUT_t is
    variable LUT : patspan_LUT_t;
  begin
    for pat_i in 0 to NUM_PATTERNS-1 loop
      LUT(pat_i) := -1 * (get_pat_span(patlist(pat_i)) / 2 + 1); -- Divide by 2 for half the span, and subtract 1 to account for 1-based indexing of centroids
    end loop;
    
    return LUT;
  end function;
  
  constant PATSPAN_LUT : patspan_LUT_t := find_all_pat_spans(PATLIST);
  
  signal seg_fit_list_phase : unsigned (2 downto 0) := to_unsigned(8 - (BRAM_LATENCY mod 8), 3); --TODO: Check this generalization, might depend on some other phase(s)

  --------------------------------------------------------------------------------
  -- Final Clearance
  --------------------------------------------------------------------------------

  signal final_clearance_segs : segment_list_t (15 downto 0); -- 2 BXs of segments -> length = 8*2 = 16

  function final_clearance (segs : segment_list_t; phase : unsigned) return segment_list_t is
    variable kill_mask : std_logic_vector (15 downto 0) := (others => '0');
    variable strip_diff : integer range 0 to PRT_WIDTH-1; -- TODO: Try changing these to unsigneds, see if it helps resources
    variable prt_diff : integer range 0 to 15-1;
    variable output_segs : segment_list_t (segs'length-1 downto 0) := segs;
  begin
    -- Always active. If spatial comparisons, can skip quality comparison, since segments are sorted within a BX.
    for I in 1 to 15 loop
      strip_diff := to_integer(segs(0).strip) - to_integer(segs(I).strip);
      prt_diff := to_integer(segs(0).partition) - to_integer(segs(I).partition);

      if I <= 8 or phase <= (15-I) then -- First 8 comparators are always active. Other 7 depend on phase. I=9 -> phase <= 6, I=10 -> phase <= 5, ..., I=15 -> phase <= 0.
        if abs(strip_diff) <= 5 and abs(prt_diff) <= 1 then -- If segments are nearby, cancel one.
          if I <= 7 and phase <= (7-I) then -- Skip quality comparison, since this is an intra-BX comparison. I = 0 -> phase <= 7, I = 1 -> phase <= 6, ..., I = 7 -> phase <= 0.
            kill_mask(I) := '1';
          else
            if segs(0) < segs(I) then
              kill_mask(0) := '1';
            else
              kill_mask(I) := '1';
            end if;
          end if; 
        end if;
      end if;
    end loop;

    for I in segs'range loop
      if kill_mask(I) = '1' then
        output_segs(I).valid := '0';
      end if;
    end loop;

    return output_segs;
  end function;

begin

  assert X_PRT_EN = TRUE
    report "Disabling cross partitions is not compatible with eta-dependent thresholding"
    severity error;

  ly_thresh_compressed <= compress_ly_count(ly_thresh_i) when EN_HC_COMPRESS else ly_thresh_i;

  assert S1_REUSE = 1 or S1_REUSE = 2 or S1_REUSE = 4
    report "Only allowed values for s1 reuse are 1,2, and 4"
    severity error;

  --Safety check to ensure compression works correctly
  process (clock) begin
    if (rising_edge(clock)) then
      for i in 0 to 15-1 loop
        for j in 0 to ly_thresh_i'length-1 loop
          assert not EN_HC_COMPRESS or unsigned(ly_thresh_i(i)(j)) >= 4 report "Minimum threshold cannot be below 4 if compression is enabled" severity error;
        end loop;
      end loop;
    end if;
  end process;

  -- synthesis translate_off
  dav_to_phase_i_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_i, phase_o => dav_i_phase);
  dav_to_phase_o_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_o, phase_o => dav_o_phase);
  -- synthesis translate_on

  --------------------------------------------------------------------------------
  -- Pulse Extension
  --------------------------------------------------------------------------------

  pulse_extension_gen : if PULSE_EXTEND > 0 generate
    chamber_pulse_extension_inst : entity work.chamber_pulse_extension
      generic map (LENGTH => PULSE_EXTEND)
      port map (
        clock   => clock40,
        sbits_i => sbits_i,
        sbits_o => sbits_extend);
  else generate
    sbits_extend <= sbits_i;
  end generate;

  dav_extend <= dav_i;

  --------------------------------------------------------------------------------
  -- Input signal assignment
  --------------------------------------------------------------------------------

  partition_gen : for I in 0 to NUM_FINDERS-1 generate
    signal partition_or     : partition_t;
    signal partition_or_reg : partition_t;
    signal dav_or           : std_logic := '0';
  begin

    single_partitions : if (NUM_FINDERS <= 8) generate
      partition_or <= sbits_extend(I);
    end generate;

    half_partitions : if (NUM_FINDERS > 8) generate

      -- for even finders, just take the partition as it is
      even_gen : if (I mod 2 = 0) generate
        partition_or <= sbits_extend(I/2);
      end generate;

      -- for odd finders, or adjacent partitions
      odd_gen : if (I mod 2 = 1) generate

        -- look for only straight and pointing segments (for cms)
        pointing : if (not EN_NON_POINTING) generate
          partition_or(0) <=                         sbits_extend(I/2 + 1)(0);
          partition_or(1) <=                         sbits_extend(I/2 + 1)(1);
          partition_or(2) <= sbits_extend(I/2)(2) or sbits_extend(I/2 + 1)(2);
          partition_or(3) <= sbits_extend(I/2)(3) or sbits_extend(I/2 + 1)(3);
          partition_or(4) <= sbits_extend(I/2)(4);
          partition_or(5) <= sbits_extend(I/2)(5);
        end generate;

        -- look for both x-partition segments toward the IP and away
        -- (for cosmic test stand)
        non_pointing : if (EN_NON_POINTING) generate
        begin
          assert false report "NON_POINTING not supported yet" severity error;
        end generate;

      end generate;
      -- Pass sbits to BRAM
      bram_in(I) <= partition_or;
    end generate;

    process (clock) is
    begin
      if (rising_edge(clock)) then
        dav_or           <= dav_extend;
        partition_or_reg <= partition_or;
      end if;
    end process;

    --------------------------------------------------------------------------------
    -- Per Partition Pattern Finders
    --------------------------------------------------------------------------------
    
    partition_inst : entity work.partition
      generic map (
        DISABLE_PEAKING => DISABLE_PEAKING,
        NUM_SEGMENTS    => NUM_SEGMENTS,
        S0_WIDTH        => S0_WIDTH,
        --DEADTIME        => DEADTIME
        EN_HC_COMPRESS => EN_HC_COMPRESS
        )
      port map (

        clock => clock,
        dav_i => dav_or,

        partition_num => I,

        ly_thresh  => ly_thresh_compressed(I),

        -- primary layer
        partition_i => partition_or_reg,

        -- output patterns
        dav_o      => all_segs_dav(I),
        segments_o => all_segs((I+1)*NUM_SEGS_PER_PRT-1 downto I*NUM_SEGS_PER_PRT),
        trigger_o  => strip_triggers(I)
        );
    
  end generate;
  
  --------------------------------------------------------------------------------
  -- Sbit BRAM
  --------------------------------------------------------------------------------

  sbit_bram_inst : entity work.sbit_bram
    generic map (
      LATENCY320 => BRAM_LATENCY,
      SBIT_PHASE => SBIT_BRAM_PHASE
    )
    port map (
      clock320 => clock,
      sbits_i  => bram_in,
      wanted_strip => seg_info_buffer(0).strip,
      wanted_prt => seg_info_buffer(0).partition,
      bram_o => bram_out
    );

  --------------------------------------------------------------------------------
  -- Pretrigger
  --------------------------------------------------------------------------------

  pretrig_gen : for iprt in 0 to NUM_PARTITIONS-1 generate

    constant ifinder : integer := if_then_else (X_PRT_EN, iprt*2, iprt);

    signal active_m1 : std_logic_vector (2 downto 0) := (others => '0');
    signal active_p1 : std_logic_vector (2 downto 0) := (others => '0');

  begin

    -- do a reduce_or to get 1 bit per vfat for both the real and cross
    -- partitions
    process (clock) is
    begin
      if (rising_edge(clock)) then
        for ivfat in 0 to 2 loop
          vfat_pretrigger_xprt(iprt)(ivfat) <=
            or_reduce(strip_triggers(iprt)((ivfat+1) * 64 - 1 downto 64*ivfat));
        end loop;
      end if;
    end process;

    -- get the negative and positive active flags
    --
    m_1 : if (X_PRT_EN and ifinder > 0) generate
      active_m1 <= vfat_pretrigger_xprt(iprt-1);
    end generate;

    p_1 : if (X_PRT_EN and ifinder < NUM_FINDERS-1 ) generate
      active_p1 <= vfat_pretrigger_xprt(iprt+1);
    end generate;


        -- -- or together the real and virtual partitions to get an active VFAT flag
    vfat_pretrigger(iprt) <= active_m1 or active_p1 or
                                  vfat_pretrigger_xprt(ifinder);

  end generate;

  process (clock) is
  begin
    if (rising_edge(clock)) then

      vfat_pretrigger_o(0) <= vfat_pretrigger(0)(0);
      vfat_pretrigger_o(1) <= vfat_pretrigger(1)(0);
      vfat_pretrigger_o(2) <= vfat_pretrigger(2)(0);
      vfat_pretrigger_o(3) <= vfat_pretrigger(3)(0);
      vfat_pretrigger_o(4) <= vfat_pretrigger(4)(0);
      vfat_pretrigger_o(5) <= vfat_pretrigger(5)(0);
      vfat_pretrigger_o(6) <= vfat_pretrigger(6)(0);
      vfat_pretrigger_o(7) <= vfat_pretrigger(7)(0);

      vfat_pretrigger_o(8)  <= vfat_pretrigger(0)(1);
      vfat_pretrigger_o(9)  <= vfat_pretrigger(1)(1);
      vfat_pretrigger_o(10) <= vfat_pretrigger(2)(1);
      vfat_pretrigger_o(11) <= vfat_pretrigger(3)(1);
      vfat_pretrigger_o(12) <= vfat_pretrigger(4)(1);
      vfat_pretrigger_o(13) <= vfat_pretrigger(5)(1);
      vfat_pretrigger_o(14) <= vfat_pretrigger(6)(1);
      vfat_pretrigger_o(15) <= vfat_pretrigger(7)(1);

      vfat_pretrigger_o(16) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(17) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(18) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(19) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(20) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(21) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(22) <= vfat_pretrigger(7)(2);
      vfat_pretrigger_o(23) <= vfat_pretrigger(7)(2);

    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Cross Partition Deghosting
  --
  -- Need to cancel segments that appear in x-partitions and its neighbors
  --
  -- For each x-partition, and for each non null segment in a x-partition, find
  -- the best segment in the left and right partitions that is within the radius.
  -- Cancel all other segments in the radius in the real partitions. If there is a
  -- segment in the radius in both the left and right partitions, cancel both.
  -- If there is exactly one among the left and right partitions, cancel the
  -- x-partition segment. If there is none, cancel nothing.

  --------------------------------------------------------------------------------

  x_part_deghost_off : if (not (X_PRT_EN and X_DEGHOST_EDGE_DIST > 0)) generate
    all_segs_x_deghosted <= all_segs;
    all_segs_dav_deghosted <= all_segs_dav;
  end generate;

  x_part_deghost : if (X_PRT_EN and X_DEGHOST_EDGE_DIST > 0) generate
    x_prt_deghost : entity work.x_prt_deghost_qual
    generic map (
      NUM_FINDERS => NUM_FINDERS,
      RADIUS => X_DEGHOST_EDGE_DIST
      )
    port map (
      clock      => clock,
      dav_i      => all_segs_dav,
      dav_o      => all_segs_dav_deghosted,
      segs_i => all_segs,
      segs_o => all_segs_x_deghosted
      );
      
  end generate;

  --------------------------------------------------------------------------------
  -- Partition Sorting
  --
  -- Reduce the # of segments e.g. 360 to NUM_SEGMENTS.
  -- Uses a trimmed bitonic sorting network to pick the best NUM_SEGMENTS.
  --------------------------------------------------------------------------------

  segment_selector_final : entity work.segment_selector
    generic map (
      MODE        => "BITONIC",
      NUM_OUTPUTS => NUM_SEGMENTS,
      NUM_INPUTS  => all_segs_x_deghosted'length,
      SORTB       => segment_t'w,
      IGNOREB     => 0 --8+PARTITION_BITS
      )
    port map (
      clock  => clock,
      dav_i  => all_segs_dav_deghosted(0),
      dav_o  => final_segs_dav,
      segs_i => all_segs_x_deghosted,
      segs_o => final_segs
      );

  --------------------------------------------------------------------------------
  -- Segment time multiplexer to read from BRAM one at a time
  --------------------------------------------------------------------------------
  process (clock) is
  begin
    if (rising_edge(clock)) then
      -- Want to read index 0 first when new segments arrive, so phase should be 0 when final_segs_dav = 1
      bram_seg_select_phase <= to_unsigned(1, bram_seg_select_phase'length) when final_segs_dav = '1' else bram_seg_select_phase + 1; -- Set to phase=1 when DAV is high, since the current phase should be 0

      seg_info_buffer(0) <= final_segs(to_integer(bram_seg_select_phase));
      --for i in 1 to seg_info_buffer'length-1 loop
      --  seg_info_buffer(i) <= seg_info_buffer(i-1);
      --end loop;
      for i in 1 to seg_info_buffer'length-1-16 loop
        seg_info_buffer(i) <= seg_info_buffer(i-1);
      end loop;

      for i in seg_info_buffer'length-1-16+1 to seg_info_buffer'length-1 loop
        seg_info_buffer(i) <= final_clearance_segs(i-1 - (seg_info_buffer'length-16-1)); -- final_clearance_segs is fixed length of 16
      end loop;

    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Extract sbits for centroid finders from BRAM window
  --------------------------------------------------------------------------------

  window_extractor : entity work.window_extract
    port map (
      clock => clock,
      window_i => bram_out,
      wanted_strip_i => seg_info_buffer(3).strip,
      wanted_PID_i => seg_info_buffer(3).id,
      pat_sbits => centroids_in
    );
    
  --------------------------------------------------------------------------------
  -- Find centroids for each layer, then add the offsets
  --------------------------------------------------------------------------------
  
  centroid_finder_inst : entity work.centroid_finder
    port map (
      clk => clock,
      din => centroids_in,
      valid_i => (others => '1'), -- Just keeping all layers valid for now
      dout => centroids
    );
    
  offset_g : for i in 0 to 5 generate
    centroids_offset(i) <= ("000" & centroids(i)) + to_unsigned(offsets(maximum(to_integer(seg_info_buffer(5).id)-1, 0))(i), centroids_offset(i)'length); -- Need the maximum for now, since PID indexes by 1
    valid_hits(valid_hits'length-1-i) <= '0' when centroids(i) = to_unsigned(0, centroids(i)'length) else '1'; -- Flip direction, since centroids direction will be flipped
  end generate;

  --------------------------------------------------------------------------------
  -- Fitting
  --------------------------------------------------------------------------------
  -- Need to flip direction of centroids (0->5, 1->4, ...)
  fitter_inst : entity work.fit
    generic map (
      STRIP_BITS => 7
    )
    port map (
      clock => clock,
      ly0 => centroids_offset(5),
      ly1 => centroids_offset(4),
      ly2 => centroids_offset(3),
      ly3 => centroids_offset(2),
      ly4 => centroids_offset(1),
      ly5 => centroids_offset(0),
      valid_i => valid_hits,
      strip_o => strip_o,
      intercept_o => intercept_o,
      slope_o => slope_o
    );

  --------------------------------------------------------------------------------
  -- Outputs
  --------------------------------------------------------------------------------

  -- Need to convert fitter strip output coordinate to full chamber frame, since its coordinates were based only on the pattern window it saw
  patspan_adjust <= to_sfixed(to_signed(PATSPAN_LUT(maximum(0, to_integer(seg_info_buffer(seg_info_buffer'length-1).id) - 1)), 6), 6-1, 0); -- Gets the adjustment based on the size of the pattern window
  fit_strip_div2 <= to_sfixed(to_slv(strip_o), strip_o'high-1, strip_o'low-1); -- Divides the fitter strip output by 2, since it was working in 2x resolution from the centroids
  seg_strip_sfixed <= to_sfixed(signed('0'&seg_info_buffer(seg_info_buffer'length-1).strip), 8, -6); -- Convert the type, not actually doing anything to the signal here

  final_clearance_segs <= final_clearance(seg_info_buffer(seg_info_buffer'length-1 downto seg_info_buffer'length-1-16), seg_fit_list_phase);

  process (clock) is
  begin
    if rising_edge(clock) then
      -- Get segment info from seg_info_buffer
      --fit_segment.valid <= seg_info_buffer(seg_info_buffer'length-1).valid when abs(slope_o) <= (1*2) else '0'; -- 1*2 for double resolution
      fit_segment.valid <= final_clearance_segs(final_clearance_segs'length-1).valid when abs(slope_o) <= (1*2) else '0'; -- 1*2 for double resolution
      fit_segment.lc <= seg_info_buffer(seg_info_buffer'length-1).lc;
      fit_segment.id <= seg_info_buffer(seg_info_buffer'length-1).id;
      fit_segment.strip <= seg_info_buffer(seg_info_buffer'length-1).strip;
      fit_segment.partition <= seg_info_buffer(seg_info_buffer'length-1).partition;
      
      -- Get fit info from fitter output
      fit_segment.intercept <= intercept_o;
      fit_segment.slope <= to_sfixed(to_slv(slope_o), slope_o'high-1, slope_o'low-1); -- Shift decimal to the right by 1 to divide by 2, to shift from double resolution back to single
      fit_segment.fit_strip <= fit_strip_div2 + seg_strip_sfixed + patspan_adjust;
      
      seg_fit_list_phase <= seg_fit_list_phase + 1;

      dav_o             <= '1' when seg_fit_list_phase = "000" else '0';
      segment_o <= decompress_ly_count(fit_segment) when EN_HC_COMPRESS else fit_segment; -- Add 3 to LC if LC compression is enabled, and segment is valid
    end if;
  end process;

  --------------------------------------------------------------------------------
  -- Final Clearance
  -- Spatial: Checks if any segments within a BX are within A strips and B partitions, and cancels the worse one.
  -- Temporal: Checks if any segments between 2 BXs are within C strips and D partitions, and cancels the worse one. Breaks ties by picking the first one. 
  --------------------------------------------------------------------------------



--  clk40gen : if (REG_OUTPUTS) generate
--    outclk <= clock40;
--  end generate;
--  clk320 : if (not REG_OUTPUTS) generate
--    outclk <= clock;
--  end generate;

--  process (outclk) is
--  begin
--    if (rising_edge(outclk)) then
--      dav_o             <= '1' when seg_fit_list_phase = "110" else '0';
--      segments_o <= fit_segments;
--    end if;
--  end process;

end behavioral;
