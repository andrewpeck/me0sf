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

  signal x_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);
  signal l_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);
  signal r_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);

  signal x_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal l_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal r_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');

  signal x_segment : segment_t;
  signal l_segment : segment_t;
  signal r_segment : segment_t;
  
  signal in_radius_vector_l : std_logic_vector(NUM_SEGS_PER_PRT-1 downto 0);
  signal in_radius_vector_r : std_logic_vector(NUM_SEGS_PER_PRT-1 downto 0);
  
  signal best_index_l : natural;
  signal best_index_r : natural;
  
  signal is_seg_in_radius : boolean;
  signal x_seg_exists : boolean;

begin
  -- set masks to all 1's
  x_prt_mask <= (others => '1');
  l_prt_mask <= (others => '1');
  r_prt_mask <= (others => '1');

  -- deghost each virtual partition in parallel
  x_prt_deghost_for : for prt_index in 0 to integer(floor(real(NUM_FINDERS)/2.0))-1 generate
    l_prt_segments <= segments_i((2*prt_index+1)*NUM_SEGS_PER_PRT-1 downto (2*prt_index)*NUM_SEGS_PER_PRT);
    x_prt_segments <= segments_i((2*prt_index+2)*NUM_SEGS_PER_PRT-1 downto (2*prt_index+1)*NUM_SEGS_PER_PRT);
    r_prt_segments <= segments_i((2*prt_index+3)*NUM_SEGS_PER_PRT-1 downto (2*prt_index+2)*NUM_SEGS_PER_PRT);

    -- deghost each segment in a given virtual partition
    x_prt_seg_for : for x_segment_index in 0 to NUM_SEGS_PER_PRT-1 generate
      x_segment <= x_prt_segments(x_segment_index);
      
      --x_seg_exists <= True when x_segment.lc /= 0 else False; --make sure segment is not null
      
     -- best_index_l <= NUM_SEGS_PER_PRT;
      in_radius_finder_l : for l_segment_index in 0 to NUM_SEGS_PER_PRT-1 generate
        l_segment <= l_prt_segments(l_segment_index);
        in_radius_vector_l(l_segment_index) <= '1' when (x_seg_exists and abs(signed(unsigned(l_segment.strip) - unsigned(x_segment.strip))) <= EDGE_DIST) else '0';
      end generate;
    
      --best_index_r <= NUM_SEGS_PER_PRT;
      in_radius_finder_r : for r_segment_index in 0 to NUM_SEGS_PER_PRT-1 generate
        r_segment <= r_prt_segments(r_segment_index);
        in_radius_vector_r(r_segment_index) <= '1' when (x_seg_exists and abs(signed(unsigned(r_segment.strip) - unsigned(x_segment.strip))) <= EDGE_DIST) else '0';
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
