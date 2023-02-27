----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity segment_selector is
  generic(
    MODE        : string  := "BITONIC";
    NUM_INPUTS  : natural := 32;
    NUM_OUTPUTS : natural := 32;
    SORTB       : natural := 1
    );
  port(
    clock  : in  std_logic;
    dav_i  : in  std_logic;
    dav_o  : out std_logic;
    segs_i : in  segment_list_t (NUM_INPUTS-1 downto 0);
    segs_o : out segment_list_t (NUM_OUTPUTS-1 downto 0)
    );
end segment_selector;

architecture behavioral of segment_selector is

  function next_power_of_two (size : natural) return natural is
  begin
    return 2**integer(ceil(log2(real(size))));
  end;
  constant CLOG_WIDTH : natural := next_power_of_two(NUM_INPUTS);
  constant BITS       : natural := segment_t'w;

begin

  BITONIC_GEN : if (MODE = "BITONIC") generate

    subtype cand_i_array_t is
      std_logic_vector(CLOG_WIDTH*BITS-1 downto 0);
    subtype cand_o_array_t is
      std_logic_vector(NUM_OUTPUTS*BITS-1 downto 0);

    signal segs_i_slv : cand_i_array_t := (others => '0');
    signal segs_o_slv : cand_o_array_t;
    signal dav_i_r : std_logic := '0';
    signal dav_o_r : std_logic := '0';
  begin

    assert NUM_INPUTS >= NUM_OUTPUTS
      report "Width of segment selector must be >= # of inputs" severity error;

    -- assert false report "BITS = " & integer'image(BITS) severity note;
    -- assert false report "CLOG_WIDTH = " & integer'image(CLOG_WIDTH) severity note;
    -- assert false report "NUM_INPUTS = " & integer'image(NUM_INPUTS) severity note;
    -- assert false report "NUM_OUTPUTS = " & integer'image(NUM_OUTPUTS) severity note;

    process (clock) is
    begin
      if (rising_edge(clock)) then
        dav_i_r <= dav_i;
        dav_o   <= dav_o_r;
      end if;
    end process;

    inloop : for I in 0 to NUM_INPUTS-1 generate
      constant bithi : natural := (I+1)*BITS;
      constant bitlo : natural := I*BITS;
      signal sl      : std_logic_vector (bithi-bitlo - 1 downto 0);
    begin
      process (clock) is
      begin
        if (rising_edge(clock)) then
          segs_i_slv(bithi-1 downto bitlo) <= convert(segs_i(I), sl);
        end if;
      end process;
    end generate;

    -- Select a subset of outputs from the sorter
    outloop : for I in 0 to NUM_OUTPUTS-1 generate
    begin
      process (clock) is
      begin
        if (rising_edge(clock)) then
          segs_o(I) <= convert(segs_o_slv((I+1)*BITS-1 downto I*BITS), segs_o(I));
        end if;
      end process;
    end generate;

    bitonic_sort_inst : entity work.bitonic_sort
      generic map (
        INPUTS               => CLOG_WIDTH,
        OUTPUTS              => NUM_OUTPUTS,
        DATA_BITS            => BITS,
        KEY_BITS             => SORTB,
        META_BITS            => 1,
        PIPELINE_STAGE_AFTER => 1,
        ADD_INPUT_REGISTERS  => true,
        ADD_OUTPUT_REGISTERS => true
        )
      port map (
        clock     => clock,
        reset     => '0',
        data_i    => segs_i_slv,
        data_o    => segs_o_slv,
        meta_i(0) => dav_i_r,
        meta_o(0) => dav_o_r
        );

  end generate;

  PRIORITY_GEN : if (MODE = "PRIORITY") generate

    -- inloop : for I in 0 to NUM_INPUTS-1 generate
    --   constant bithi : natural := (I+1)*BITS;
    --   constant bitlo : natural := I*BITS;
    -- begin
    --   segs_i_slv(bithi-1 downto bitlo) <= to_slv(segs_i(I));
    -- end generate;

    -- -- Select a subset of outputs from the sorter
    -- outloop : for I in 0 to NUM_OUTPUTS-1 generate
    -- begin
    --   segs_o(I) <=
    --     to_segment(segs_o_slv((I+1)*BITS-1 downto I*BITS));
    -- end generate;

    -- priority_encoder_inst : entity work.priority_encoder
    --   generic map (
    --     WIDTH      => NUM_PATTERNS,
    --     REG_INPUT  => true,
    --     REG_OUTPUT => true,
    --     REG_STAGES => 0,
    --     DAT_BITS   => PATTERN_LENGTH,
    --     QLT_BITS   => 1+CNT_BITS+PID_BITS,
    --     ADR_BITS_o => integer(ceil(log2(real(NUM_PATTERNS))))
    --     )
    --   port map (
    --     clock => clock,
    --     dav_i => cand_dav,
    --     dat_i => cand_slv,
    --     dav_o => best_dav,
    --     dat_o => best_slv,
    --     adr_o => open
    --     );

  end generate;

end behavioral;
