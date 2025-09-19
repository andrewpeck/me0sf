----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 07/18/2025 04:34:38 PM
-- Design Name: 
-- Module Name: sbit_bram - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------


use work.pat_types.all;
use work.pat_pkg.all;

--use this on machine with Vivado and XPM library available
--library xpm;
--use xpm.vcomponents.xpm_memory_sdpram;

--use this on machine without Vivado available (needs XPM BRAM files included in HDL sources)
use work.vcomponents.all;

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity sbit_bram is
  generic (
    LATENCY320 : integer := 0; --LATENCY320 + BX_ADDR_PHASE_WRITE MUST BE [0, 114], INCLUSIVE
    SBIT_PHASE : integer := 0  --MUST BE [0, 7], INCLUSIVE
  );
  port (
    clock320 : in  std_logic;
    sbits_i  : in  chamber_w_virtual_t;
    wanted_strip : in std_logic_vector (STRIP_BITS-1 downto 0);
    wanted_prt : in std_logic_vector (PARTITION_BITS-1 downto 0);
    my_out   : out sbit_window_t
    );
end sbit_bram;

architecture Behavioral of sbit_bram is

constant BX_ADDR_PHASE_READ : integer := (LATENCY320 + SBIT_PHASE + 7) mod 8;
constant LATENCY40 : integer := (LATENCY320 + SBIT_PHASE + 7) / 8; --Add 7 so with 1 latency, start at -1 BX
constant COPY_ADDR_PHASE : integer := (SBIT_PHASE + 1) mod 2;
constant PADDED_PHASE : integer := SBIT_PHASE mod 2;

constant NUM_BRAMS : integer := 4;
constant WINDOW_SIZE : integer := 48;

signal write_clock : std_logic := to_unsigned(COPY_ADDR_PHASE, 1)(0);

type padded_prt_t is array (0 to 5) of
  std_logic_vector (191+18*2 downto 0);
type padded_data_t is array (0 to 14) of padded_prt_t;

signal padded_sbits : padded_data_t := (others => (others => (others => '0')));

signal bx_addr_a : unsigned (3 downto 0) := to_unsigned(((SBIT_PHASE+7) / 8)*15, 4); -- Set to 15 if SBIT_PHASE is nonzero, so it will increment to 0
signal bx_addr_b : unsigned (3 downto 0) := to_unsigned(15-LATENCY40, 4);
signal copy_addr_a : unsigned (1 downto 0) := to_unsigned(3 - (SBIT_PHASE / 2), 2); -- Initialize to 2 so it will be 0 at first write
signal full_addr_a : std_logic_vector (5 downto 0);
signal full_addr_b : std_logic_vector (7 downto 0) := (others => '0');
signal wanted_bram_from_strip : std_logic_vector (1 downto 0) := "00";
signal wanted_word_from_strip : std_logic_vector (1 downto 0) := "00";
signal wanted_prt_reg, wanted_prt_reg2 : std_logic_vector (PARTITION_BITS-1 downto 0) := "0000";

signal global_phase : unsigned (2 downto 0) := to_unsigned(0, 3);

type bram_o_chamber_t is array (0 to 14) of sbit_window_t;
    
signal bram_o : bram_o_chamber_t;

begin

  -- Domain checks
  assert LATENCY320 >= 0 and LATENCY320 <= 114
   report "Latency320 for sbit BRAM must be in [0, 114], inclusive."
   severity failure;
  assert SBIT_PHASE >= 0 and SBIT_PHASE <= 7
    report "SBIT_PHASE must be in [0, 7], inclusive."
    severity failure;
  assert SBIT_PHASE /= 7 or LATENCY320 /= 114
    report "SBIT_PHASE cannot be 7 if LATENCY320 = 114."
    severity failure;
    
  partition_bram_gen : for prt_I in 0 to 15-1 generate
    layer_bram_gen : for ly_I in 0 to 6-1 generate
    begin
          xpm_memory_sdpram_inst0 : xpm_memory_sdpram
            generic map (
               ADDR_WIDTH_A => 6,               -- (4 bits for BX)(4 bits for partition)(2 bits for copies)
               ADDR_WIDTH_B => 8,               -- (4 bits BX)(4 bits partition)(2 bits copies)(2 bits word)
               BYTE_WRITE_WIDTH_A => 192,        -- DECIMAL
               CLOCKING_MODE => "independent_clock", -- String
               MEMORY_PRIMITIVE => "block",      -- String
               MEMORY_SIZE => 12288,             -- DECIMAL
            --   RAM_DECOMP => "auto",            -- String
               READ_DATA_WIDTH_B => 48,         -- DECIMAL
               READ_LATENCY_B => 1,             -- DECIMAL
               SIM_ASSERT_CHK => 1,             -- DECIMAL; 0=disable simulation messages, 1=enable simulation messages
               USE_EMBEDDED_CONSTRAINT => 0,    -- DECIMAL
               USE_MEM_INIT => 0,               -- DECIMAL
               USE_MEM_INIT_MMI => 0,           -- DECIMAL
               WAKEUP_TIME => "disable_sleep",  -- String
               WRITE_DATA_WIDTH_A => 192,        -- DECIMAL
               WRITE_MODE_B => "no_change",     -- String
               WRITE_PROTECT => 0               -- DECIMAL
            )
            port map (
               doutb => bram_o(prt_I)(ly_I),
               addra => full_addr_a,
               addrb => full_addr_b,
               clka => write_clock,
               clkb => clock320,
               --dina => padded_sbits(prt_I)(ly_I)(padded_sbits(prt_I)(ly_I)'length-1 downto 36),
              dina => padded_sbits(prt_I)(ly_I)(padded_sbits(prt_I)(ly_I)'length-1-36 downto 0),
               ena => '1',
               enb => '1',
               regceb => '1',                 -- 1-bit input: Clock Enable for the last register stage on the output data path.
               rstb => '0',                     -- 1-bit input: Reset signal for the final port B output register stage. Synchronously resets output port
                                                 -- doutb to the value specified by parameter READ_RESET_VALUE_B.
               sleep => '0',
               injectsbiterra => '0',
               injectdbiterra => '0',
               wea => "1"                        -- WRITE_DATA_WIDTH_A/BYTE_WRITE_WIDTH_A-bit input: Write enable vector for port A input data port dina. 1
                                                 -- bit wide when word-wide writes are used. In byte-wide write configurations, each bit controls the writing
                                                 -- one byte of dina to address addra. For example, to synchronously write only bits [15-8] of dina when
                                                 -- WRITE_DATA_WIDTH_A is 32, wea would be 4'b0010.
            );
    end generate;
  end generate;

full_addr_a <= std_logic_vector(bx_addr_a) & std_logic_vector(copy_addr_a);
full_addr_b <= std_logic_vector(bx_addr_b) & wanted_bram_from_strip & wanted_word_from_strip;

process (clock320) begin
  if (rising_edge(clock320)) then

    -- Derive the write clock from the 320MHz clock, with phase depending on the phase of the incoming sbits
    write_clock <= not write_clock;

    -- Move BX addresses at 40 MHz, depending on phases
    global_phase <= global_phase + 1;
    if global_phase = ((7 + SBIT_PHASE) mod 8) then
      bx_addr_a <= bx_addr_a + 1;
    end if;
    if global_phase = BX_ADDR_PHASE_READ then
      bx_addr_b <= bx_addr_b + 1;
    end if;

    -- Shift sbits and move copy address at phases (0,2,4,6) or (1,3,5,7), depending on when the sbits to write arrive
    if global_phase(0) = to_unsigned(PADDED_PHASE, 1)(0) then
       for i in 0 to 14 loop
        for j in 0 to 5 loop
          copy_addr_a <= copy_addr_a + 1;
          if copy_addr_a = 3 then
            padded_sbits(i)(j) <= "000000000000000000" & sbits_i(i)(j) & "000000000000000000";
          else
            --padded_sbits(i)(j) <= padded_sbits(i)(j)(padded_sbits(i)(j)'length-1-12 downto 0) & "000000000000";
            padded_sbits(i)(j) <= "000000000000" & padded_sbits(i)(j)(padded_sbits(i)(j)'length-1 downto 12);
          end if;
        end loop;
      end loop;     
    end if;    

    wanted_prt_reg2 <= wanted_prt;
    wanted_prt_reg <= wanted_prt_reg2;
    wanted_word_from_strip <= std_logic_vector(to_unsigned(to_integer(unsigned(wanted_strip)) / 48, wanted_word_from_strip'length));
    wanted_bram_from_strip <= std_logic_vector(to_unsigned((to_integer(unsigned(wanted_strip)) / 12) mod 4, wanted_bram_from_strip'length));
    my_out <= bram_o(to_integer(unsigned(wanted_prt_reg)));
   end if;
end process;

end Behavioral;
