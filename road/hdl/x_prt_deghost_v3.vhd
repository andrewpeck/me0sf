--Pad input 2D chunk array with null vectors, so edge cases work nicely. Only need to pad left and right sides (not top or bottom), as x-partitions are between real partitions.
--For each virtual segment, make a std_logic_vector ("range vector") of length 2*CHUNK_RADIUS+1 (set to 6 bits for now, can generalize later but probably don't need to)
--Create 2D array of range vectors, each corresponding to a virtual chunk. Each bit represent whether the virtual segment in that chunk is close to a real segment in a neighboring chunk.
--Real   [0][1][2] <--- Bits 0-2 of the RV
--Virtual    [] <--- RV for this chunk
--Real   [3][4][5] <--- Bits 3-5 of the RV
--Compare virtual strip number to real strip numbers. Only need some of LSBs, since chunk is known.
--Add check that chunk size is a power of 2 -- otherwise, this doesn't work.
--If chunks being compared are not equal, need to left-append 0 to left chunk and 1 to right chunk
--Or both vectors together. If only 1 true, kill virtual. If both true, kill both real.
--To kill segments, make a 2D std_logic array (array of std_logic_vector) to mask. If killing, set 0. Else, set 1. And this with 2D chunk array.

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use ieee.math_real.log2;
use ieee.math_real.floor;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

-- Each [] represents a "chunk" from intra-partition deghosting. Each chunk contains either one segment, or none (lc=0).
-- A chunk is represented by a segment.
--   ...[][][]...   Real partition
--     ...[]...     Virtual partition
--   ...[][][]...   Real partition
--
-- Each virtual segment is compared to chunks offset by -1,0,1 in the neighboring (real) partitions.

entity x_prt_deghost_v3 is
  generic(
    NUM_FINDERS : integer := 15;
    RADIUS : natural := 2
    );
  port(
    clock      : in  std_logic;

    dav_i      : in  std_logic;
    dav_o      : out std_logic;

    segs_i : in  segment_list_t (0 to NUM_FINDERS*N_SEGS_PRT - 1);
    segs_o : out segment_list_t (0 to NUM_FINDERS*N_SEGS_PRT - 1)
    );
end x_prt_deghost_v3;

architecture behavioral of x_prt_deghost_v3 is

  -- Assuming chunk size is a power of 2, then the "strip" attribute of segments can be interpreted as:
  -- strip = [chunk_number][offset_in_chunk]
  -- Since we are only comparing chunks that are -1,0,1 apart, the whole chunk_number is unecessary for the subtraction operation.
  -- Returns 6 bits, corresponding to whether the top 3 segments are in range, and the bottom 3
  -- To save resources, we can replace the whole chunk_number with only "0" or "1", reducing our space from the whole 192 strips to the local 2 chunks (2*CHUNK_SIZE)
  
  constant N_SEGS_TOTAL : positive := NUM_FINDERS * N_SEGS_PRT;
  constant N_SEGS_PADDED_TOTAL : positive := (NUM_FINDERS)*(N_SEGS_PRT+2);
  constant N_X_PRTS : positive := positive(floor(real(NUM_FINDERS)/2.0));
  
  signal segs_padded : segment_list_t(0 to N_SEGS_PADDED_TOTAL-1);
  
  type range_vector_arr is array (0 to N_X_PRTS*N_SEGS_PRT-1) of std_logic_vector (0 to 5);
  type range_vector_padded_arr is array (0 to (N_X_PRTS+2)*(N_SEGS_PRT+2)-1) of std_logic_vector (0 to 5);
  signal range_vectors : range_vector_arr;
  signal range_vectors_padded : range_vector_padded_arr;
  
  signal mask : std_logic_vector (0 to NUM_FINDERS*N_SEGS_PRT - 1);
  signal segs_masked : segment_list_t (0 to NUM_FINDERS*N_SEGS_PRT - 1);
  
  -- Function to pad the 2D partition-chunk matrix with null segments
  function pad_segs_in(in_segs : segment_list_t (0 to N_SEGS_TOTAL-1)) return segment_list_t is
    variable out_segs : segment_list_t (0 to N_SEGS_PADDED_TOTAL-1);
    variable cur_seg : segment_t;
    begin
      for y in 0 to NUM_FINDERS-1 loop
        for x in 0 to N_SEGS_PRT+1 loop
          if (x = 0 or x = N_SEGS_PRT+1) then
            cur_seg.lc := (others => '0');
            cur_seg.id := (others => '0');
            cur_seg.strip := (others => '0');
            cur_seg.partition := (others => '0');
          else
            cur_seg := in_segs(N_SEGS_PRT*y + (x-1));
          end if;
          out_segs((N_SEGS_PRT+2)*y + x) := cur_seg;
        end loop;
      end loop;
    return out_segs;
  end function;
  
  -- Function to pad the 2D range vector matrix with null range vectors ("000000")
  function pad_RV(in_RV : range_vector_arr) return range_vector_padded_arr is
    variable out_RV : range_vector_padded_arr;
    begin
      for y in 0 to N_X_PRTS+2-1 loop
        for x in 0 to N_SEGS_PRT+2-1 loop
          out_RV((N_SEGS_PRT+2)*y + x) := (others => '0') when (y = 0 or y = N_X_PRTS+1 or x = 0 or x = N_SEGS_PRT+1) else in_RV(N_SEGS_PRT*(y-1) + (x-1));
        end loop;
      end loop;
    return out_RV;
  end function;

  -- Function to determine if which of 6 neighboring real segments are close to the virtual segment
  --   ...[][][]...   Real partition
  --     ...[]...     Virtual partition
  --   ...[][][]...   Real partition
  function get_dists(v_seg : segment_t; r_segs : segment_list_t (0 to 5)) return std_logic_vector is
    -- Bit to left append strip number of virtual and real segments
    constant append_v : std_logic_vector (0 to 5) := "100100";
    constant append_r : std_logic_vector (0 to 5) := "001001";
    constant chunk_bits : natural := natural(log2(real(PRT_WIDTH/N_SEGS_PRT)));
    constant intra_chunk_bits : natural := strip_bits - chunk_bits;

    variable diff : signed (intra_chunk_bits-1+2 downto 0);
    variable r_null : boolean;
    variable v_null : boolean;
    
    variable out_bits : std_logic_vector (0 to 5);
    
  begin
    v_null := true when v_seg.lc = 0 else false;
    for i in 0 to 5 loop
      r_null := true when r_segs(i).lc = 0 else false;
      
      diff := abs( ('0' & append_r(i) & signed(r_segs(i).strip(intra_chunk_bits-1 downto 0))) - ('0' & append_v(i) & signed(v_seg.strip(intra_chunk_bits-1 downto 0))) );

      out_bits(i) := '0' when v_null or r_null or boolean(unsigned(diff) > RADIUS) else '1';
    end loop;
      
    return out_bits;
  end function;
  
  function get_mask(range_vectors : range_vector_padded_arr) return std_logic_vector is
  
    type range_vector_or_arr is array (0 to (N_X_PRTS+2)*(N_SEGS_PRT+2)-1) of std_logic_vector(0 to 1); 
    variable range_vectors_or : range_vector_or_arr;
    
    variable range_vectors_s2 : range_vector_arr;
    variable v_kill_bits : std_logic_vector (0 to 5);
    
    variable mask : std_logic_vector (0 to NUM_FINDERS*N_SEGS_PRT - 1);
  
  begin
    for i in 0 to (N_X_PRTS+2)*(N_SEGS_PRT+2)-1 loop
      range_vectors_or(i)(0) := or_reduce(range_vectors(i)(0 to 2));
      range_vectors_or(i)(1) := or_reduce(range_vectors(i)(3 to 5));
    end loop;
    --Kill real segment ghosts
    for y in 0 to NUM_FINDERS-N_X_PRTS-1 loop
      for x in 0 to N_SEGS_PRT-1 loop
        v_kill_bits(0) := range_vectors(y*(N_SEGS_PRT+2) + x)(5) and range_vectors_or(y*(N_SEGS_PRT+2) + x)(0);
        v_kill_bits(1) := range_vectors(y*(N_SEGS_PRT+2) + x + 1)(4) and range_vectors_or(y*(N_SEGS_PRT+2) + x + 1)(0);
        v_kill_bits(2) := range_vectors(y*(N_SEGS_PRT+2) + x + 2)(3) and range_vectors_or(y*(N_SEGS_PRT+2) + x + 2)(0);
        
        v_kill_bits(3) := range_vectors((y+1)*(N_SEGS_PRT+2) + x)(2) and range_vectors_or((y+1)*(N_SEGS_PRT+2) + x)(1);
        v_kill_bits(4) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(1) and range_vectors_or((y+1)*(N_SEGS_PRT+2) + x + 1)(1);
        v_kill_bits(5) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 2)(0) and range_vectors_or((y+1)*(N_SEGS_PRT+2) + x + 2)(1);
        
        mask(2*y*N_SEGS_PRT + x) := '0' when or_reduce(v_kill_bits) else '1';
      end loop;
    end loop;
    
    --Update range vectors
    for y in 0 to N_X_PRTS-1 loop
      for x in 0 to N_SEGS_PRT-1 loop
        range_vectors_s2(y*N_SEGS_PRT + x)(0) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(0) and mask(2*y*N_SEGS_PRT + x - 1) when x/=0 else '0';
        range_vectors_s2(y*N_SEGS_PRT + x)(1) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(1) and mask(2*y*N_SEGS_PRT + x);
        range_vectors_s2(y*N_SEGS_PRT + x)(2) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(2) and mask(2*y*N_SEGS_PRT + x + 1) when x/=N_SEGS_PRT-1 else '0';
        
        range_vectors_s2(y*N_SEGS_PRT + x)(3) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(3) and mask(2*(y+1)*N_SEGS_PRT + x - 1) when x/=0 else '0';
        range_vectors_s2(y*N_SEGS_PRT + x)(4) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(4) and mask(2*(y+1)*N_SEGS_PRT + x);
        range_vectors_s2(y*N_SEGS_PRT + x)(5) := range_vectors((y+1)*(N_SEGS_PRT+2) + x + 1)(5) and mask(2*(y+1)*N_SEGS_PRT + x + 1) when x/=N_SEGS_PRT-1 else '0';
        
      end loop;
    end loop;
    
    --Kill virtual ghosts
    for y in 0 to N_X_PRTS-1 loop
      for x in 0 to N_SEGS_PRT-1 loop
        --If not in range of any real segs, keep. Otherwise, kill.
        mask((2*y+1)*N_SEGS_PRT + x) := not or_reduce(range_vectors_s2(y*N_SEGS_PRT+x));  
      end loop;
    end loop;
    
    return mask;
  end function;

begin
  --Zero pad 2d segment array on left and right
  segs_padded <= pad_segs_in(segs_i);
  
  --Get range vectors for each virtual chunk
  x_prts : for y in 0 to N_X_PRTS-1 generate
    v_seg : for x in 0 to N_SEGS_PRT-1 generate
      signal v_seg : segment_t;
      signal r_segs : segment_list_t (0 to 5);
      
      begin
        --get virtual segment
        v_seg <= segs_padded((N_SEGS_PRT+2)*(2*y+1) + (x+1));
        --get segs above
        r_segs (0 to 2) <= segs_padded((N_SEGS_PRT+2)*(2*y+1-1) + (x+1-1) to (N_SEGS_PRT+2)*(2*y+1-1) + (x+1+1));
        --get segs below
        r_segs (3 to 5) <= segs_padded((N_SEGS_PRT+2)*(2*y+1+1) + (x+1-1) to (N_SEGS_PRT+2)*(2*y+1+1) + (x+1+1));

        range_vectors(N_SEGS_PRT*y + x) <= get_dists(v_seg, r_segs);
    end generate;
  end generate;
  
  range_vectors_padded <= pad_RV(range_vectors);
  
  --Mask
  mask <= get_mask(range_vectors_padded);
  part_masking : for y in 0 to NUM_FINDERS-1 generate
    seg_masking : for x in 0 to N_SEGS_PRT-1 generate
      segs_masked(y*N_SEGS_PRT + x).id <= segs_i(y*N_SEGS_PRT + x).id;
      segs_masked(y*N_SEGS_PRT + x).partition <= segs_i(y*N_SEGS_PRT + x).partition;
      segs_masked(y*N_SEGS_PRT + x).strip <= segs_i(y*N_SEGS_PRT + x).strip;
      segs_masked(y*N_SEGS_PRT + x).lc <= segs_i(y*N_SEGS_PRT + x).lc when (mask(y*N_SEGS_PRT + x) = '1') else "000";
    end generate;
  end generate;
  
  process (clock) begin
    if (rising_edge(clock)) then
      dav_o <= dav_i;
      segs_o <= segs_masked;
    end if;
  end process;

end behavioral;
