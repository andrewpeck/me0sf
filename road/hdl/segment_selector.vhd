----------------------------------------------------------------------------------
-- CMS Muon Endcap
-- GEM Collaboration
-- ME0 Segment Finder Firmware
-- A. Peck, A. Datta, C. Grubb, J. Chismar
----------------------------------------------------------------------------------
-- Description:
--
-- The "segment selector" is simply a wrapper than instantiates a bitonic
-- sorter. It converts between the segment_t type into the std_logic_vectors
-- required by the bitonic sorter. It also has optional INPUT and OUTPUT
-- registers that can be configured by generics.
--
-- NUM_OUTPUTS can be set to a number less than NUM_INPUTS and it will operate
-- as a funnel and output only the best NUM_OUTPUTs segments.
--
-- SORTB and IGNOREB configure the # of bits that are used as sorting keys.
-- From the datafield, the sorting key is DATA(SORTB-1 downto IGNOREB).
--
----------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_types.all;
use work.pat_pkg.all;
use work.patterns.all;

entity segment_selector is
  generic(
    MODE        : string  := "BITONIC";
    NUM_INPUTS  : natural := 32;
    NUM_OUTPUTS : natural := 32;
    SORTB       : natural := 1;
    IGNOREB     : natural := 0;
    REG_INPUTS  : boolean := true;
    REG_OUTPUTS : boolean := true
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

    --------------------------------------------------------------------------------
    -- Input / Output Registers
    --------------------------------------------------------------------------------

    process (clock, dav_i) is
    begin
      if (not REG_INPUTS or rising_edge(clock)) then
        dav_i_r <= dav_i;
      end if;
    end process;

    process (clock, dav_o_r) is
    begin
      if (not REG_OUTPUTS or rising_edge(clock)) then
        dav_o   <= dav_o_r;
      end if;
    end process;

    inloop : for I in 0 to NUM_INPUTS-1 generate
      constant bithi : natural := (I+1)*BITS;
      constant bitlo : natural := I*BITS;
      signal sl      : std_logic_vector (bithi-bitlo - 1 downto 0);
    begin
      process (clock, segs_i) is
      begin
        if (not REG_INPUTS or rising_edge(clock)) then
          segs_i_slv(bithi-1 downto bitlo) <= convert(segs_i(I), sl);
        end if;
      end process;
    end generate;

    -- Select a subset of outputs from the sorter
    outloop : for I in 0 to NUM_OUTPUTS-1 generate
    begin
      process (clock, segs_o_slv) is
      begin
        if (not REG_OUTPUTS or rising_edge(clock)) then
          segs_o(I) <= convert(segs_o_slv((I+1)*BITS-1 downto I*BITS), segs_o(I));
        end if;
      end process;
    end generate;

    --------------------------------------------------------------------------------
    -- Sorter
    --------------------------------------------------------------------------------

    assert SORTB <= BITS report "Sort bits must be <= bits"
                    & " DATA_BITS=" & integer'image(BITS)
                    & " KEY_BITS=" & integer'image(SORTB)
                    severity error;

    bitonic_sort_inst : entity work.bitonic_sort
      generic map (
        INPUTS               => CLOG_WIDTH,
        OUTPUTS              => NUM_OUTPUTS,
        DATA_BITS            => BITS,
        KEY_BITS             => SORTB,
        IGNORE_BITS          => IGNOREB,
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

end behavioral;
