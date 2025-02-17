--Pad input 2D chunk array with null vectors, so edge cases work nicely.
--For each virtual segment, make 2 std_logic_vectors of length 2*CHUNK_RADIUS+1 (in general, set to 3 for now, can generalize later but probably don't need to)
--So, need a 2D array of std_logic_vectors, with each entry corresponding to a virtual chunk
--Compare virtual strip number to real strip numbers. Only need some of LSBs.
--Add check that chunk size is a power of 2 -- otherwise, this doesn't work.
--Chunk bits = log_2(256/chunk_size) = STRIP_BITS - log_2(chunk_size); Strip_within_chunk_bits = STRIP_BITS - chunk_bits
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
    RADIUS : natural := 2;
    CHUNK_WIDTH : natural := 16
    );
  port(
    clock      : in  std_logic;

    dav_i      : in  std_logic;
    dav_o      : out std_logic;

    segs_i : in  segment_list_t (0 to NUM_FINDERS*N_SEGS_PRT - 1);
    segs_o : out segment_list_t (0 to (NUM_FINDERS+2)*(N_SEGS_PRT+2) - 1)
    );
end x_prt_deghost_v3;

architecture behavioral of x_prt_deghost_v3 is

  -- Assuming chunk size is a power of 2, then the "strip" attribute of segments can be interpreted as:
  -- strip = [chunk_number][offset_in_chunk]
  -- Since we are only comparing chunks that are -1,0,1 apart, the whole chunk_number is unecessary for the subtraction operation.
  -- Returns 6 bits, corresponding to whether the top 3 segments are in range, and the bottom 3
  -- To save resources, we can replace the whole chunk_number with only "0" or "1", reducing our space from the whole 192 strips to the local 2 chunks (2*CHUNK_SIZE)
  
  constant N_CHUNKS_PER_PRT : positive := PRT_WIDTH/CHUNK_WIDTH;
  constant N_SEGS_TOTAL : positive := NUM_FINDERS * N_SEGS_PRT;
  constant N_SEGS_PADDED_TOTAL : positive := (NUM_FINDERS+2)*(N_SEGS_PRT+2);
  constant N_X_PRTS : positive := positive(floor(real(NUM_FINDERS)/2.0));
  
  signal segs_padded : segment_list_t(0 to N_SEGS_PADDED_TOTAL-1);
  
  type range_vector_arr is array (0 to N_X_PRTS*N_CHUNKS_PER_PRT-1) of std_logic_vector (5 downto 0);
  signal range_vectors : range_vector_arr;

  -- Function to determine if which of 6 neighboring real segments are close to the virtual segment
  --   ...[][][]...   Real partition
  --     ...[]...     Virtual partition
  --   ...[][][]...   Real partition
  function get_dists(v_seg : segment_t; r_segs : segment_list_t (0 to 5)) return std_logic_vector is
    -- Bit to left append strip number of virtual and real segments
    constant append_v : std_logic_vector (5 downto 0) := "001001";
    constant append_r : std_logic_vector (5 downto 0) := "100100";
    constant chunk_bits : natural := natural(log2(real(CHUNK_WIDTH)));
    constant intra_chunk_bits : natural := strip_bits - chunk_bits;

    variable diff : signed (intra_chunk_bits-1+2 downto 0);
    variable out_bits : std_logic_vector (5 downto 0);
    variable r_null : boolean;
    
    begin
      for i in 0 to 5 loop
        r_null := true when r_segs(i).lc = 0 else false;
        
        diff := abs( ('0' & append_r(i) & signed(r_segs(i).strip(intra_chunk_bits-1 downto 0))) - ('0' & append_v(i) & signed(v_seg.strip(intra_chunk_bits-1 downto 0))) );

        if (r_null or boolean(unsigned(diff) > RADIUS)) then
          out_bits(i) := '0';
        else
          out_bits(i) := '1';
        end if;
      end loop;
      
    return out_bits;
  end function;
  
  -- Function to pad the 2D partition-chunk matrix with null segments
  function pad_segs_in(in_segs : segment_list_t (0 to N_SEGS_TOTAL-1)) return segment_list_t is
    variable out_segs : segment_list_t (0 to N_SEGS_PADDED_TOTAL-1);
    variable cur_seg : segment_t;
    begin
      for y in 0 to NUM_FINDERS+1 loop
        for x in 0 to N_SEGS_PRT+1 loop
          if (y = 0 or y = NUM_FINDERS+1 or x = 0 or x = N_SEGS_PRT+1) then
            cur_seg.lc := (others => '0');
            cur_seg.id := (others => '0');
            cur_seg.strip := (others => '0');
            cur_seg.partition := (others => '0');
          else
            cur_seg := in_segs(N_SEGS_PRT*(y-1) + (x-1));
          end if;
          out_segs((N_SEGS_PRT+2)*y + x) := cur_seg;
        end loop;
      end loop;
    return out_segs;
  end function;

begin

  segs_padded <= pad_segs_in(segs_i);
  
  x_prts : for y in 0 to N_X_PRTS-1 generate
    v_seg : for x in 0 to N_SEGS_PRT-1 generate
      signal v_seg : segment_t := segs_padded((N_SEGS_PRT+2)*(y+1) + (x+1));
      signal r_segs : segment_list_t (0 to 5);
      
      begin
        --get segs above
        r_segs (0 to 2) <= segs_padded((N_SEGS_PRT+2)*(y+1-1) + (x+1+1) to (N_SEGS_PRT+2)*(y+1-1) + (x+1-1));
        --get segs below
        r_segs (3 to 5) <= segs_padded((N_SEGS_PRT+2)*(y+1+1) + (x+1+1) to (N_SEGS_PRT+2)*(y+1+1) + (x+1-1));
        
        range_vectors(N_SEGS_PRT*y + x) <= get_dists(v_seg, r_segs);
    end generate;
  end generate;
  
  process (clock) begin
    if (rising_edge(clock)) then
      dav_o <= dav_i;
    end if;
  end process;

  -- x_prt_deghost_for : for prt_index in 0 to floor(NUM_FINDERS/2)-1 generate
  --   x_prt_segments = all_segs((2*prt_index+2)*N_SEGS_PRT downto (2*prt_index+1)*N_SEGS_PRT);
  --   l_prt_segments = all_segs((2*prt_index+1)*N_SEGS_PRT downto (2*prt_index)*N_SEGS_PRT);
  --   r_prt_segments = all_segs((2*prt_index+3)*N_SEGS_PRT downto (2*prt_index+2)*N_SEGS_PRT);
  -- end generate;

end behavioral;