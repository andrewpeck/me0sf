library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.pat_pkg.all;
use work.patterns.all;
use work.priority_encoder_pkg.all;

entity segment_selector is
  generic(
    MODE        : string  := "BITONIC";
    NUM_INPUTS  : natural := 32;
    NUM_OUTPUTS : natural := 32
    );
  port(

    clock : in std_logic;

    pats_i : in  pat_list_t (NUM_INPUTS-1 downto 0);
    pats_o : out pat_list_t (NUM_OUTPUTS-1 downto 0);

    sump : out std_logic

    );
end segment_selector;

architecture behavioral of segment_selector is

  function next_power_of_two (size : natural) return natural is
  begin
    return 2**integer(ceil(log2(real(size))));
  end;

  constant CLOG_WIDTH : natural := next_power_of_two(NUM_INPUTS);

  subtype cand_i_array_t is
    std_logic_vector(CLOG_WIDTH*PATTERN_LENGTH-1 downto 0);
  subtype cand_o_array_t is
    std_logic_vector(NUM_OUTPUTS*PATTERN_LENGTH-1 downto 0);

  signal pats_i_slv : cand_i_array_t;
  signal pats_o_slv : cand_o_array_t;

begin

  BITONIC_GEN : if (MODE = "BITONIC") generate
    assert NUM_INPUTS >= NUM_OUTPUTS
      report "Width of segment selector must be >= # of inputs" severity error;

    assert false report "CLOG_WIDTH = " & integer'image(CLOG_WIDTH) severity note;
    assert false report "NUM_INPUTS = " & integer'image(NUM_INPUTS) severity note;
    assert false report "NUM_OUTPUTS = " & integer'image(NUM_OUTPUTS) severity note;

    inloop : for I in 0 to CLOG_WIDTH-1 generate
    begin

      in_assign : if (I < NUM_INPUTS) generate
        pats_i_slv((I+1)*PATTERN_LENGTH-1 downto I*PATTERN_LENGTH)
          <= to_slv(pats_i(I));
      end generate;

      null_assign : if (I >= NUM_INPUTS) generate
        pats_i_slv((I+1)*PATTERN_LENGTH-1 downto I*PATTERN_LENGTH)
          <= to_slv(null_pattern);
      end generate;

    end generate;

    -- Select a subset of outputs from the sorter
    outloop : for I in 0 to NUM_OUTPUTS-1 generate
    begin
      pats_o(I) <=
        to_pattern(pats_o_slv((I+1)*PATTERN_LENGTH-1 downto I*PATTERN_LENGTH));
    end generate;

    bitonic_sort_inst : entity work.bitonic_sort
      generic map (
        INPUTS               => CLOG_WIDTH,
        OUTPUTS              => NUM_OUTPUTS,
        DATA_BITS            => PATTERN_LENGTH,
        KEY_BITS             => PATTERN_LENGTH - null_pattern.hash'length,
        META_BITS            => 0,
        PIPELINE_STAGE_AFTER => 2,
        ADD_INPUT_REGISTERS  => false,
        ADD_OUTPUT_REGISTERS => true
        )
      port map (
        clock  => clock,
        reset  => '0',
        data_i => pats_i_slv,
        data_o => pats_o_slv,
        meta_i => (others => '0'),
        meta_o => open
        );

    sump <= '0';
  end generate;

  PRIORITY_GEN : if (MODE = "PRIORITY") generate
  end generate;

end behavioral;
