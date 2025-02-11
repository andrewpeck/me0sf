--Pad input 2D chunk array with null vectors on the left and right, so edge cases work nicely.
--For each virtual segment, make 2 std_logic_vectors of length 2*CHUNK_RADIUS+1 (in general, set to 3 for now, can generalize later but probably don't need to)
--So, need a 2D array of std_logic_vectors, with each entry corresponding to a virtual chunk
--If virtual chunk is near border, put 0's in missing chunks
--Compare virtual strip number to real strip numbers. Only need some of LSBs.
--Add check that chunk size is a power of 2 -- otherwise, this doesn't work.
--Chunk bits = log_2(256/chunk_size) = STRIP_BITS - log_2(chunk_size); Strip_within_chunk_bits = STRIP_BITS - chunk_bits
--If chunks being compared are not equal, need to left-append 0 to left chunk and 1 to right chunk (if 1 away; if 2 away, left append 00 and 10, then 00 and 11 if 3 away...)
--Realistically, only comparing up to 1 chunk away. Can generalize later.
--Or both vectors together. If only 1 true, kill virtual. If both true, kill both real.
--To kill segments, make a 2D std_logic array (array of std_logic_vector) to mask. If killing, set 0. Else, set 1. And this with 2D chunk array.

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

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
    EDGE_DIST : natural := 2
    );
  port(
    clock      : in  std_logic;

    dav_i      : in  std_logic;
    dav_o      : out std_logic;

    -- segments_i : in  segment_list_t (NUM_FINDERS * N_SEGS_PRT - 1 downto 0);
    -- segments_o : out segment_list_t (NUM_FINDERS * N_SEGS_PRT - 1 downto 0)
    v_seg_i : in segment_t;
    r_segs_i : in segment_list_t (5 downto 0); -- 12 segs in

--    out_matrix : out dist_matrix
    out_bits : out std_logic_vector(5 downto 0)
    );
end x_prt_deghost_v3;

architecture behavioral of x_prt_deghost_v3 is

  -- Assuming chunk size is a power of 2, then the "strip" attribute of segments can be interpreted as:
  -- strip = [chunk_number][offset_in_chunk]
  -- Since we are only comparing chunks that are -1,0,1 apart, the whole chunk_number is unecessary for the subtraction operation.
  -- Returns 6 bits, corresponding to whether the top 3 segments are in range, and the bottom 3
  -- To save resources, we can replace the whole chunk_number with only "0" or "1", reducing our space from the whole 192 strips to the local 2 chunks (2*CHUNK_SIZE)

  function get_dists(v_seg : segment_t; r_segs : segment_list_t (5 downto 0)) return std_logic_vector is
    variable out_bits : std_logic_vector (5 downto 0);
    
    variable r_null : boolean;

    -- TODO: Check signed size to make sure overflow doesn't happen, just put numbers down for now
    variable diff : signed (6 downto 0);

    -- Bit to left append strip number of virtual and real segments
    constant append_v : std_logic_vector (5 downto 0) := "001001";
    constant append_r : std_logic_vector (5 downto 0) := "100100";

    constant RADIUS : unsigned (1 downto 0) := "10";
    constant temp : signed (20 downto 0) := (others => '0');
    
    begin
      for i in 0 to 5 loop
        r_null := true when r_segs(i).lc = 0 else false;
        
        diff := abs( ('0' & append_r(i) & signed(r_segs(i).strip(4 downto 0))) - ('0' & append_v(i) & signed(v_seg.strip(4 downto 0))) );

        if (r_null or boolean(unsigned(diff) > RADIUS)) then
          out_bits(i) := '0';
        else
          out_bits(i) := '1';
        end if;
      end loop;
      
      return out_bits;
    end function;

begin

  process (clock) begin
    if (rising_edge(clock)) then
      out_bits <= get_dists(v_seg_i, r_segs_i);
      dav_o <= dav_i;
    end if;
  end process;

  -- x_prt_deghost_for : for prt_index in 0 to floor(NUM_FINDERS/2)-1 generate
  --   x_prt_segments = all_segs((2*prt_index+2)*N_SEGS_PRT downto (2*prt_index+1)*N_SEGS_PRT);
  --   l_prt_segments = all_segs((2*prt_index+1)*N_SEGS_PRT downto (2*prt_index)*N_SEGS_PRT);
  --   r_prt_segments = all_segs((2*prt_index+3)*N_SEGS_PRT downto (2*prt_index+2)*N_SEGS_PRT);
  -- end generate;

end behavioral;
