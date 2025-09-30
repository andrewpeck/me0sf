use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity window_centroid is
  port(
    clock             : in  std_logic;
    window_i         : in  sbit_window_t;
    wanted_strip_i : in unsigned (STRIP_BITS-1 downto 0);
    wanted_PID_i   : in unsigned (PID_BITS-1 downto 0);
    
    centroids_offset  : out centroids_offset_t
    );
    
end window_centroid;

architecture behavioral of window_centroid is

    constant buffer_size : integer := 2;
    type strip_buffer_t is array (0 to BUFFER_SIZE-1) of unsigned(STRIP_BITS-1 downto 0);
    type pid_buffer_t is array (0 to BUFFER_SIZE-1) of unsigned(PID_BITS-1 downto 0);

    signal strip_buffer : strip_buffer_t;
    signal pid_buffer : pid_buffer_t;

----------------------------
  -- Centroids
  --------------------------------------------------------------------------------
    
  signal centroids_in : pat_sbits_t;
  signal centroids : centroids_t;
  -- Temporarily commenting out this for testing, bring back later
  --signal centroids_offset : centroids_offset_t; 
  
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
        -- Have to do this monstrosity since the ly0, ly1, ... values in the patlist are currently implemented as separately named signals
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

begin

  --------------------------------------------------------------------------------
  -- Extract sbits for centroid finders from BRAM window
  --------------------------------------------------------------------------------

  window_extractor : entity work.window_extract
    port map (
      clock => clock,
      window_i => window_i,
      wanted_strip_i => wanted_strip,
      wanted_PID_i => wanted_PID_i,
      pat_sbits => centroids_in
    );
    
  --------------------------------------------------------------------------------
  -- Find centroids for each layer, then add the offsets
  --------------------------------------------------------------------------------
  
  centroid_finder_i : entity work.centroid_finder
    port map (
      clk => clock,
      din => centroids_in,
      valid_i => (others => '1'), -- Just keeping all layers valid for now
      dout => centroids
    );
    
  offset_g : for i in 0 to 5 generate
    centroids_offset(i) <= ("000" & centroids(I)) + to_unsigned(offsets(to_integer(pid_buffer(1))-1)(i), centroids_offset(i)'length);
  end generate;

  strip_buffer(0) <= wanted_strip_i;
  pid_buffer(0) <= wanted_PID_i;

  process (clock) is
    if (rising_edge(clock)) then
      for i in 1 to BUFFER_SIZE-1 loop
        strip_buffer(i) <= strip_buffer(i-1);
        pid_buffer(i) <= pid_buffer(i-1);
      end loop;
    end if;
  end process;

end behavioral;
