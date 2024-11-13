library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

entity new_x_prt_deghost is
  generic(
    NUM_FINDERS : integer := 15;
    EDGE_DIST : natural := 2
    );
  port(
    clock      : in  std_logic;

    -- dav_i      : in  std_logic;
    -- dav_o      : out std_logic;

    -- segments_i : in  segment_list_t (NUM_FINDERS * N_SEGS_PRT - 1 downto 0);
    -- segments_o : out segment_list_t (NUM_FINDERS * N_SEGS_PRT - 1 downto 0)
    l_segs_i : in segment_list_t (N_SEGS_PRT-1 downto 0);
    r_segs_i : in segment_list_t (N_SEGS_PRT-1 downto 0);

    out_matrix : out dist_matrix
    
    );
end new_x_prt_deghost;

architecture behavioral of new_x_prt_deghost is

  signal x_prt_segments : segment_list_t (N_SEGS_PRT - 1 downto 0) := (others => null_pattern);

  signal x_segment : segment_t;
  signal l_segment : segment_t;
  signal r_segment : segment_t;

  function get_dists(l_segs : segment_list_t (N_SEGS_PRT - 1 downto 0); r_segs : segment_list_t (N_SEGS_PRT - 1 downto 0)) return dist_matrix is
    variable out_matrix : dist_matrix;
    variable l_seg : segment_t;
    variable r_seg : segment_t;
    
    variable l_null : std_logic;
    variable r_null : std_logic;
    
    variable upper_bits : std_logic_vector (STRIP_BITS-1 downto 2);
    variable lower_bit : std_logic_vector (STRIP_BITS-1 downto 2);

    variable lower_bits_diff : signed (2 downto 0);

    constant RADIUS : unsigned (1 downto 0) := unsigned(2);
    begin
      for i in 0 to N_SEGS_PRT-1 loop
        l_seg := l_segs(i);
        l_null := std_logic(l_seg.lc = 0);

        for j in 0 to N_SEGS_PRT-1 loop
          r_seg := r_segs(j);
          r_null := std_logic(r_seg.lc = 0);
          
          for k in STRIP_BITS downto 2 loop
            upper_bits(k) := l_seg.strip(k) xor r_seg.strip(k);
          end loop;
         
          lower_bits_diff := abs(signed(unsigned(l_seg.strip(1 downto 0))) - signed(unsigned(r_seg.strip(1 downto 0))));

          if (boolean(and_reduce(upper_bits)) or boolean(lower_bits_diff > signed(RADIUS))) then
            out_matrix(i)(j) := '0';
          else
            out_matrix(i)(j) := '1' and (not l_null) and (not r_null);
          end if;
        end loop;
      end loop;
      return out_matrix;
    end;

begin

  process begin
    if (rising_edge(clock)) then
      out_matrix <= get_dists(l_segs_i, r_segs_i);
    end if;
  end process;

  -- x_prt_deghost_for : for prt_index in 0 to floor(NUM_FINDERS/2)-1 generate
  --   x_prt_segments = all_segs((2*prt_index+2)*N_SEGS_PRT downto (2*prt_index+1)*N_SEGS_PRT);
  --   l_prt_segments = all_segs((2*prt_index+1)*N_SEGS_PRT downto (2*prt_index)*N_SEGS_PRT);
  --   r_prt_segments = all_segs((2*prt_index+3)*N_SEGS_PRT downto (2*prt_index+2)*N_SEGS_PRT);
  -- end generate;

end behavioral;