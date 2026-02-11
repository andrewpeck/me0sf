----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--
-- The pattern unit multiplexer time-multiplexes a pattern unit across a
-- collection of strips. An individual pattern unit looks at a single strip.
-- Because of its fully pipelined design, however, it can be time-multiplexed to
-- process a different strip in every clock cycle.
--
-- We run the logic clock at 320MHz (8x the LHC clock), so that we can process
-- eight strips with a single pattern unit block.
--
-- This pat_unit_mux module multiplexes 8 strips into each pattern unit, then
-- demultiplexes the outputs. So in the end we process 192 strips using
-- 192/8=24 pattern units, and produce 192 output segments.
--
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.pat_types.all;
use work.priority_encoder_pkg.all;

entity pat_unit_mux is
  generic(

    VERBOSE : boolean := false;

    DISABLE_PEAKING : boolean := false;

    PATLIST : patdef_array_t := patdef_array;
    WIDTH   : natural        := PRT_WIDTH;

    --DEADTIME : natural := 3;            -- deadtime in bx
    EN_HC_COMPRESS : boolean := true;

    -- Need padding for half the width of the pattern this is to handle the edges
    -- of the chamber where some virtual chamber of all zeroes exists... to be
    -- trimmed away by the compiler during optimization
    MUX_FACTOR : natural := 8
    );
  port(

    clock : in std_logic;

    ly_thresh : in ly_thresh_prt;

    dav_i : in  std_logic;
    dav_o : out std_logic := '0';

    -- synthesis translate_off
    dav_i_phase : out natural range 0 to 7 := 0;
    dav_o_phase : out natural range 0 to 7 := 0;
    -- synthesis translate_on

    ly0 : in std_logic_vector (WIDTH-1 downto 0);
    ly1 : in std_logic_vector (WIDTH-1 downto 0);
    ly2 : in std_logic_vector (WIDTH-1 downto 0);
    ly3 : in std_logic_vector (WIDTH-1 downto 0);
    ly4 : in std_logic_vector (WIDTH-1 downto 0);
    ly5 : in std_logic_vector (WIDTH-1 downto 0);

    segments_o : out pat_unit_mux_list_t (WIDTH-1 downto 0) := (others => (lc => (others => '0'), id => (others => '0'), strip => (others => '0'))); -- Initialize to all '0's (zero function does not work without a declared signal of that type)

    trigger_o : out std_logic_vector (WIDTH-1 downto 0) := (others => '0')

    );
end pat_unit_mux;

architecture behavioral of pat_unit_mux is

  function pad_layer (pad : natural; data : std_logic_vector)
    -- function to take slv + padding and pad both the left and right sides
    return std_logic_vector is
    variable pad_slv : std_logic_vector (pad-1 downto 0) := (others => '0');
  begin
    return pad_slv & data & pad_slv;
  end;

  constant NUM_SECTORS : positive := WIDTH/MUX_FACTOR;

  constant LY_SPAN : natural := get_max_span(patdef_array);
  constant LY0_SPAN : natural := get_max_span_ly(patdef_array, 0);
  constant LY1_SPAN : natural := get_max_span_ly(patdef_array, 1);
  constant LY2_SPAN : natural := get_max_span_ly(patdef_array, 2);
  constant LY3_SPAN : natural := get_max_span_ly(patdef_array, 3);
  constant LY4_SPAN : natural := get_max_span_ly(patdef_array, 4);
  constant LY5_SPAN : natural := get_max_span_ly(patdef_array, 5);
  
  constant PADDING : natural := (LY_SPAN-1)/2;
  constant PADDING_LY0 : natural := (LY0_SPAN-1)/2;
  constant PADDING_LY1 : natural := (LY1_SPAN-1)/2;
  constant PADDING_LY2 : natural := (LY2_SPAN-1)/2;
  constant PADDING_LY3 : natural := (LY3_SPAN-1)/2;
  constant PADDING_LY4 : natural := (LY4_SPAN-1)/2;
  constant PADDING_LY5 : natural := (LY5_SPAN-1)/2;

  signal ly0_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY0 downto 0);
  signal ly1_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY1 downto 0);
  signal ly2_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY2 downto 0);
  signal ly3_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY3 downto 0);
  signal ly4_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY4 downto 0);
  signal ly5_padded : std_logic_vector (WIDTH-1 + 2*PADDING_LY5 downto 0);

  signal patterns_mux : pat_unit_list_t (NUM_SECTORS-1 downto 0);
  signal segments_accumulator : pat_unit_list_t (WIDTH-1 downto 0); -- Needed to update every 320 MHz clock, so semgent_o can be stable for 8 clocks. This is needed later in chamber.vhd, for the seg_info_buffer.

  signal phase_i, patterns_mux_phase : natural range 0 to MUX_FACTOR-1;

  attribute MAX_FANOUT                       : integer;
  attribute MAX_FANOUT of patterns_mux_phase : signal is 128;


  signal pat_unit_dav : std_logic_vector(NUM_SECTORS-1 downto 0);
 
  signal segments      : pat_unit_mux_list_t (WIDTH-1 downto 0);
  
  signal peaking_segments_old : pat_unit_list_t (WIDTH-1 downto 0);
  signal peaking_segments_oldest : std_logic_vector (WIDTH-1 downto 0); -- Only need 1 bit per segment for the oldest segments, since they are only used to remember whether there was a segment in that BX
  signal trigger : std_logic_vector (WIDTH-1 downto 0);
 
begin

  --------------------------------------------------------------------------------
  -- Asserts
  --------------------------------------------------------------------------------

  assert WIDTH mod MUX_FACTOR = 0
    report "pat_unit_mux WIDTH must be divisible by MUX_FACTOR"
    severity error;

  --------------------------------------------------------------------------------
  -- DAV Monitor (for sim)
  --------------------------------------------------------------------------------

  -- synthesis translate_off
  dav_to_phase_i_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_i, phase_o => dav_i_phase);
  dav_to_phase_o_mon : entity work.dav_to_phase
    generic map (DIV => 1)
    port map (clock  => clock, dav => dav_o, phase_o => dav_o_phase);
  -- synthesis translate_on

  --------------------------------------------------------------------------------
  -- Padding
  --
  -- pad the edges of the chamber with zeroes so that strips at the edges
  -- can still do pattern finding using the normal machanism
  --------------------------------------------------------------------------------

  ly0_padded <= pad_layer(PADDING_LY0, ly0);
  ly1_padded <= pad_layer(PADDING_LY1, ly1);
  ly2_padded <= pad_layer(PADDING_LY2, ly2);
  ly3_padded <= pad_layer(PADDING_LY3, ly3);
  ly4_padded <= pad_layer(PADDING_LY4, ly4);
  ly5_padded <= pad_layer(PADDING_LY5, ly5);

  --------------------------------------------------------------------------------
  -- Pattern Units Input Mux
  --
  -- for some # of strips, e.g. 192 ... we divide it into different sectors of
  -- width=MUX_FACTOR
  --
  -- so in this case we divide into 24 sectors of 8 wide each
  --
  -- we loop over those 24 sectors and mux together the inputs / outputs
  --------------------------------------------------------------------------------

  dav_to_phase_i_inst : entity work.dav_to_phase
    generic map (DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => dav_i, phase_o => phase_i);

  patgen : for I in 0 to NUM_SECTORS-1 generate

    signal ly0_unit : std_logic_vector (LY0_SPAN-1 downto 0) := (others => '0');
    signal ly1_unit : std_logic_vector (LY1_SPAN-1 downto 0) := (others => '0');
    signal ly2_unit : std_logic_vector (LY2_SPAN-1 downto 0) := (others => '0');
    signal ly3_unit : std_logic_vector (LY3_SPAN-1 downto 0) := (others => '0');
    signal ly4_unit : std_logic_vector (LY4_SPAN-1 downto 0) := (others => '0');
    signal ly5_unit : std_logic_vector (LY5_SPAN-1 downto 0) := (others => '0');
    --signal ly0_unit, ly1_unit, ly2_unit, ly3_unit, ly4_unit, ly5_unit
    --  : std_logic_vector (LY_SPAN - 1 downto 0) := (others => '0');

    signal lyx_unit_dav : std_logic := '0';

  begin

    process (clock) is
    begin
      if (rising_edge(clock)) then

        ly0_unit <= ly0_padded (I+phase_i*NUM_SECTORS+PADDING_LY0*2 downto I+phase_i*NUM_SECTORS);
        ly1_unit <= ly1_padded (I+phase_i*NUM_SECTORS+PADDING_LY1*2 downto I+phase_i*NUM_SECTORS);
        ly2_unit <= ly2_padded (I+phase_i*NUM_SECTORS+PADDING_LY2*2 downto I+phase_i*NUM_SECTORS);
        ly3_unit <= ly3_padded (I+phase_i*NUM_SECTORS+PADDING_LY3*2 downto I+phase_i*NUM_SECTORS);
        ly4_unit <= ly4_padded (I+phase_i*NUM_SECTORS+PADDING_LY4*2 downto I+phase_i*NUM_SECTORS);
        ly5_unit <= ly5_padded (I+phase_i*NUM_SECTORS+PADDING_LY5*2 downto I+phase_i*NUM_SECTORS);

        lyx_unit_dav <= dav_i;

      end if;
    end process;

    pat_unit_inst : entity work.pat_unit
      generic map (VERBOSE => verbose, EN_HC_COMPRESS => EN_HC_COMPRESS)
      port map (

        clock => clock,

        ly_thresh => ly_thresh,

        dav_i => lyx_unit_dav,
        bx_0_i => lyx_unit_dav,
        ly0   => ly0_unit,
        ly1   => ly1_unit,
        ly2   => ly2_unit,
        ly3   => ly3_unit,
        ly4   => ly4_unit,
        ly5   => ly5_unit,

        dav_o => pat_unit_dav(I),
        pat_o => patterns_mux(I)
      );
        
  end generate;

  --------------------------------------------------------------------------------
  -- Pattern Units Outputs Demux
  --------------------------------------------------------------------------------

  dav_to_phase_o_inst : entity work.dav_to_phase
    generic map (DIV => 8/MUX_FACTOR)
    port map (clock  => clock, dav => pat_unit_dav(0), phase_o => patterns_mux_phase);

  process (clock) is
  begin
    if (rising_edge(clock)) then

      --------------------------------------------------------------------------------
      -- Peak finding logic
      --------------------------------------------------------------------------------
      --
      -- A problem that was quickly discovered in developing the segment finding
      -- algorithms was that due to the poor timing resolution of the GEM
      -- chamber, not all hits arrive in a single clock cycle.
      --
      -- To account for this, pulse stretching is used to make each S-bit hit
      -- last for e.g. 3 clock cycles.
      --
      -- A problem in this approach though is that the pattern unit will fire on
      -- the early hits, which e.g. may only have 4 layers, while the remaining
      -- 2 layers can come in across the next two clock cycles.
      --
      -- To prevent this "early-firing" phenomena, a simple mechanism "peaking"
      -- mechanism is used.
      --
      -- This works by buffering the found segments for a single clock cycle,
      -- and waiting until a time bin where the quality of the found pattern
      -- decreases, then doing a 1 clock cycle lookback and using the segments
      -- found in the /previous/ clock cycle.
      --
      --
      -- so for example say the hits are coming in out of time... with pulse
      -- extension=3
      --
      -- bx N we have 4 layers
      -- bx N+1 we have 6 layers
      -- bx N+2 we have 6 layers
      -- bx N + 3 we have 2 layers
      --
      -- we'd know from the transition of 6->2 layers that we gathered all of
      -- the hits, so in this case we use BX N+2 as the actual segment
      --
      --
      --                   ─────┬───┬───┬───┬─────────────────────────────────────────
      -- segments               │ 5 │ 6 │ 5 │
      --   lyc             ─────┴───┴───┴───┴─────────────────────────────────────────
      --
      --                   ─────────┬───┬───┬───┬─────────────────────────────────────
      -- segments_last              │ 5 │ 6 │ 5 │
      --   lyc             ─────────┴───┴───┴───┴─────────────────────────────────────
      --
      --                                ┌───┐
      -- segments <        ─────────────┘   └─────────────────────────────────────────
      -- segments_last
      --
      --                   ──────────────┬───┬────────────────────────────────────────
      -- segments_o                      │ 6 │
      --   lyc             ──────────────┴───┴────────────────────────────────────────
      --
      --------------------------------------------------------------------------------
      
      --TODO: Add dav for peaking

      -- Store segments as they come out of the pat_units @ 320 MHz
      for I in 0 to NUM_SECTORS-1 loop
        segments_accumulator(I+patterns_mux_phase*NUM_SECTORS) <= patterns_mux(I);
      end loop;

      -- Assign output strips (constant)
      for I in segments_o'range loop
        segments_o(I).strip <= to_unsigned(I, STRIP_BITS);
      end loop;
      
      if not DISABLE_PEAKING then          
        -- Peaking operates at BX frequency (40 MHz); Peaking logic is not very complex, so probably not worth to keep it multiplexed and reuse logic, since this would require multiplexing inputs/outputs
        if patterns_mux_phase = 0 then --segments_accumulator is fully updated for the BX, so can now do the peaking step
          for I in segments_accumulator'range loop
            -- If we are triggered, then definitely output the old segment, and reset trigger
            if trigger(I) = '1' then
             segments_o(I).lc <= peaking_segments_old(I).lc;
             segments_o(I).id <= peaking_segments_old(I).id;
             trigger(I) <= '0';
            -- Otherwise, if we have seen a segment in the last BX
            elsif peaking_segments_oldest(I) = '0' and peaking_segments_old(I).lc > 0 then
            -- And we no longer see a segment, then output the segment we saw 
              if segments_accumulator(I).lc = 0 then
                segments_o(I).lc <= peaking_segments_old(I).lc;
                segments_o(I).id <= peaking_segments_old(I).id;
            -- And we still see the segment, then trigger to output in the next BX
              else
                segments_o(I).lc <= to_unsigned(0, LC_BITS);
                trigger(I) <= '1';
              end if;
            -- Otherwise, nothing to output right now
            else
              segments_o(I).lc <= to_unsigned(0, LC_BITS);
            end if;
            
            -- Update segments (old and oldest)
            peaking_segments_oldest(I) <= '1' when peaking_segments_old(I).lc > 0 else '0';
            peaking_segments_old(I) <= segments_accumulator(I);
         end loop;   
        end if; -- 40 MHz clock
      else -- End peaking
        for I in segments_o'range loop
        -- Assign segments_o at 40 MHz
          segments_o(I).lc <= segments_accumulator(I).lc when patterns_mux_phase = 0;
          segments_o(I).id <= segments_accumulator(I).id when patterns_mux_phase = 0;
        end loop;
      end if; -- End no peaking

      dav_o <= '1' when patterns_mux_phase = 0 else '0';
      
    end if;  -- rising_edge(clock)

  end process;

end behavioral;
