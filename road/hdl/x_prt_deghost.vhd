library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

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

    -- dav_i      : in  std_logic;
    -- dav_o      : out std_logic;

    segments_i : in  segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0);
    segments_o : out segment_list_t (NUM_FINDERS * NUM_SEGS_PER_PRT - 1 downto 0)
    );
end x_prt_deghost;

architecture behavioral of x_prt_deghost is

  signal x_prt_segments : segment_list_t (NUM_SEGS_PER_PRT - 1 downto 0) := (others => null_pattern);

  signal x_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal l_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');
  signal r_prt_mask : std_logic_vector(NUM_SEGS_PER_PRT - 1 downto 0) := (others => '1');

  signal x_segment : segment_t;
  signal l_segment : segment_t;
  signal r_segment : segment_t;

begin
  -- set masks to all 1's
  x_prt_mask <= (others => '1');
  l_prt_mask <= (others => '1');
  r_prt_mask <= (others => '1');

  -- deghost each virtual partition in parallel
  x_prt_deghost_for : for prt_index in 0 to floor(NUM_FINDERS/2)-1 generate
    x_prt_segments = all_segs((2*prt_index+2)*NUM_SEGS_PER_PRT downto (2*prt_index+1)*NUM_SEGS_PER_PRT);
    l_prt_segments = all_segs((2*prt_index+1)*NUM_SEGS_PER_PRT downto (2*prt_index)*NUM_SEGS_PER_PRT);
    r_prt_segments = all_segs((2*prt_index+3)*NUM_SEGS_PER_PRT downto (2*prt_index+2)*NUM_SEGS_PER_PRT);

    -- deghost each segment in a given virtual partition
    x_prt_seg_for : for x_segment_index in 0 to NUM_SEGS_PER_PRT generate
      x_segment <= x_prt_segments(x_segment_index);

      if (x_segment /= 0) then -- make sure segment is not null
        best_index_l = NUM_SEGS_PER_PRT;

        l_seg_for : for l_segment_index in 0 to NUM_SEGS_PER_PRT generate
          l_segment = l_prt_segments(l_segment_index);
          if (abs(l_segment.strip - x_segment.strip) <= EDGE_DIST and best_index_l /= NUM_SEGS_PER_PRT) then -- if within distance to x_seg and we have already found another seg, zero the old seg
            l_prt_mask(l_segment_index) <= 0;
          end if;
        end generate;

        r_seg_for : for r_segment_index in 0 to NUM_SEGS_PER_PRT generate
          r_segment = r_prt_segments(r_segment_index);
          if (abs(r_segment.strip - x_segment.strip) <= EDGE_DIST and best_index_r /= NUM_SEGS_PER_PRT) then -- if within distance to x_seg and we have already found another seg, zero the old seg
            r_prt_mask(r_segment_index) <= 0;
          end if;
        end generate;

        if (best_index_l /= NUM_SEGS_PER_PRT and best_index_r /= NUM_SEGS_PER_PRT) then
          l_prt_mask(best_index_l) <= 0;
          r_prt_mask(best_index_r) <= 0;
        else if (best_index_l /= NUM_SEGS_PER_PRT or best_index_r /= NUM_SEGS_PER_PRT) then
          x_prt_mask(x_segment_index) <= 0;
        end if;
      end if;
    end generate;
  end generate;

end behavioral;