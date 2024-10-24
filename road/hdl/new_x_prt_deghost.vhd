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
    N_SEGS_PRT : natural := 12;
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

    out_matrix : out array (N_SEGS_PRT-1 downto 0) of array(N_SEGS_PRT-1 downto 0) of std_logic;
    
    );
end new_x_prt_deghost;

architecture behavioral of new_x_prt_deghost is

  signal x_prt_segments : segment_list_t (N_SEGS_PRT - 1 downto 0) := (others => null_pattern);

  signal x_segment : segment_t;
  signal l_segment : segment_t;
  signal r_segment : segment_t;

  function get_dists(l_segs : segment_list_t (N_SEGS_PRT - 1 downto 0); r_segs : segment_list_t (N_SEGS_PRT - 1 downto 0)) return (array (N_SEGS_PRT-1 downto 0) of segment_list_t(N_SEGS_PRT-1 downto 0)) is
    variable out_matrix is array (N_SEGS_PRT-1 downto 0) of array (N_SEGS_PRT-1 downto 0) of std_logic := N_SEGS_PRT * ('0' * N_SEGS_PRT);
    begin
      for l_seg in l_segs loop
        l_null := (l_seg = null_pattern);

        for r_seg in r_segs loop
          r_null := (r_seg = null_pattern);

          upper_bits := l_seg(SEG_SIZE downto IDK) xor r_seg(SEG_SIZE downto IDK);
          lower_bits_diff := abs(l_seg(IDK downto IDK2) - r_seg(IDK downto IDK2));

          if (and_reduce(upper_bits) or lower_bits_diff > RADIUS) then
            out_matrix(i)(j) := '0';
          else
            out_matrix(i)(j) := '1' and (not l_null) and (not_r_null);
          end if;
        end loop;
      end loop;
      return out_matrix;
    end;

begin

  process begin
    if (rising_edge(clock)) then
      l_segs <= 
      out_matrix <= get_dists(l_segs, r_segs);
    end if;
  end process;

  -- x_prt_deghost_for : for prt_index in 0 to floor(NUM_FINDERS/2)-1 generate
  --   x_prt_segments = all_segs((2*prt_index+2)*NUM_SEGS_PER_PRT downto (2*prt_index+1)*NUM_SEGS_PER_PRT);
  --   l_prt_segments = all_segs((2*prt_index+1)*NUM_SEGS_PER_PRT downto (2*prt_index)*NUM_SEGS_PER_PRT);
  --   r_prt_segments = all_segs((2*prt_index+3)*NUM_SEGS_PER_PRT downto (2*prt_index+2)*NUM_SEGS_PER_PRT);
  -- end generate;

end behavioral;