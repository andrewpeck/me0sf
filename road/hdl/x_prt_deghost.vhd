library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

entity x_prt_deghost is
  generic(
    NUM_FINDERS : integer := 15;
    NUM_SEGS_PER_PRT : natural := 12;
    EDGE_DIST : natural := 2
    );
  port(
    clock      : in  std_logic;

    dav_i      : in  std_logic;
    dav_o      : out std_logic;

    segments_i : in  segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0);
    --segments_o : out segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0)
    vector_o : out std_logic_vector(NUM_SEGS_PER_PRT-1 downto 0)
    );
end x_prt_deghost;

architecture behavioral of x_prt_deghost is

  constant NUM_X_PRT : integer := integer(floor(real(NUM_FINDERS)/2.0));

  signal x_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);
  signal l_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);
  signal r_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);

  signal x_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal l_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal r_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  
  signal in_radius_vector_l : std_logic_vector(NUM_SEGS_PER_PRT-1 downto 0);
  signal in_radius_vector_r : std_logic_vector(NUM_SEGS_PER_PRT-1 downto 0);
  
  signal best_index_l : natural;
  signal best_index_r : natural;
  
  type seg_exists_t is array (0 to NUM_X_PRT-1, 0 to NUM_SEGS_PER_PRT) of boolean;
  signal x_seg_exists : seg_exists_t;
  
  
  --Function to reduce resources of subtraction of 8 bit integers (strips numbers)
  --Returns true if left and right seg are both non-null and within EDGE_DIST
  function are_segs_in_range(l_seg : segment_t; r_seg : segment_t) return boolean is
    variable out_bool : boolean;
    
    variable upper_bits_xor : std_logic_vector (STRIP_BITS-1 downto 2);

    variable lower_bits_diff : unsigned (2 downto 0);

    begin
      -- Check if either segment is null
      if l_seg.lc = 0 or r_seg.lc = 0 then
        return false;
      end if;

      for i in STRIP_BITS-1 downto 2 loop
          upper_bits_xor(i) := l_seg.strip(i) xor r_seg.strip(i);
      end loop;
      --report("UPPER BITS XOR: "&integer'image(to_integer(unsigned(upper_bits_xor))));
         
      lower_bits_diff := unsigned(abs(signed(unsigned('0'&l_seg.strip(1 downto 0))) - signed(unsigned('0'&r_seg.strip(1 downto 0)))));
      --report "LOWER BITS DIFF: "&integer'image(to_integer(lower_bits_diff)) severity note;

      out_bool := false when (or_reduce(upper_bits_xor) = '1') or (lower_bits_diff(1 downto 0) > EDGE_DIST) else true;
      
      return out_bool;
    end;

begin
  -- set masks to all 1's
  x_prt_mask <= (others => '1');
  l_prt_mask <= (others => '1');
  r_prt_mask <= (others => '1');

  -- deghost each virtual partition in parallel
  -- x_prt_deghost_for : for prt_index in 0 to NUM_X_PRT-1 generate
  x_prt_deghost_for : for prt_index in 0 to 0 generate -- temporarily checking only prt for testing
    l_prt_segments <= segments_i((2*prt_index+1)*NUM_SEGS_PER_PRT-1 downto (2*prt_index)*NUM_SEGS_PER_PRT);
    x_prt_segments <= segments_i((2*prt_index+2)*NUM_SEGS_PER_PRT-1 downto (2*prt_index+1)*NUM_SEGS_PER_PRT);
    r_prt_segments <= segments_i((2*prt_index+3)*NUM_SEGS_PER_PRT-1 downto (2*prt_index+2)*NUM_SEGS_PER_PRT);

    -- deghost each segment in a given virtual partition
    x_prt_seg_for : for x_segment_index in 0 to 0 generate -- NUM_SEGS_PER_PRT-1 generate
      x_seg_exists(prt_index, x_segment_index) <= True when x_prt_segments(x_segment_index).lc /= 0 else False; --make sure segment is not null
      
     -- best_index_l <= NUM_SEGS_PER_PRT;
      in_radius_finder_l : for l_segment_index in 0 to NUM_SEGS_PER_PRT-1 generate
        --in_radius_vector_l(l_segment_index) <= '1' when (x_seg_exists(prt_index, x_segment_index) and l_prt_segments(l_segment_index).lc > 0 and abs(signed(unsigned(l_prt_segments(l_segment_index).strip) - unsigned(x_prt_segments(x_segment_index).strip))) <= EDGE_DIST) else '0';    
        in_radius_vector_l(l_segment_index) <= '1' when are_segs_in_range(l_prt_segments(l_segment_index), x_prt_segments(x_segment_index)) else '0';                       
      end generate;
    
      --best_index_r <= NUM_SEGS_PER_PRT;
      in_radius_finder_r : for r_segment_index in 0 to NUM_SEGS_PER_PRT-1 generate
        in_radius_vector_r(r_segment_index) <= '1' when (x_seg_exists(prt_index, x_segment_index) and r_prt_segments(r_segment_index).lc > 0 and abs(signed(unsigned(r_prt_segments(r_segment_index).strip) - unsigned(x_prt_segments(x_segment_index).strip))) <= EDGE_DIST) else '0';
      end generate;
      
  vector_o <= in_radius_vector_l;
    
--    deghost_final_choice : if (best_index_l /= NUM_SEGS_PER_PRT and best_index_r /= NUM_SEGS_PER_PRT) generate
--      l_prt_mask(best_index_l) <= '0';
--      r_prt_mask(best_index_r) <= '0';
--    elsif (best_index_l /= NUM_SEGS_PER_PRT or best_index_r /= NUM_SEGS_PER_PRT) generate
--      x_prt_mask(x_segment_index) <= '0';
--      end generate;
      
    end generate;
  end generate;

end behavioral;
