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

library xpm;
use xpm.vcomponents.all;

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
    wanted_strip : in unsigned (STRIP_BITS-1 downto 0);
    wanted_prt : in unsigned (PARTITION_BITS-1 downto 0);
    bram_o   : out sbit_window_t
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
  std_logic_vector (192+18*2-1 downto 0);
type padded_data_t is array (0 to 14) of padded_prt_t;
type padded_prts_t is array (0 to 5) of
  std_logic_vector(192*8-1 downto 0);
type padded_prts_arr_t is array (0 to 1) of padded_prts_t;

signal padded_sbits : padded_data_t := (others => (others => (others => '0')));
signal padded_prts_arr : padded_prts_arr_t;

signal bx_addr_a : unsigned (3 downto 0) := to_unsigned(((SBIT_PHASE+7) / 8)*15, 4); -- Set to 15 if SBIT_PHASE is nonzero, so it will increment to 0
signal bx_addr_b : unsigned (3 downto 0) := to_unsigned(15-LATENCY40, 4);
signal copy_addr_a : unsigned (1 downto 0) := to_unsigned(3 - (SBIT_PHASE / 2), 2); -- Initialize to 2 so it will be 0 at first write
signal full_addr_a : std_logic_vector (5 downto 0);
signal full_addr_b : std_logic_vector (10 downto 0) := (others => '0');
signal wanted_bram_from_strip : std_logic_vector (1 downto 0) := "00";
signal wanted_word_from_strip : std_logic_vector (1 downto 0) := "00";
signal wanted_prt_reg : std_logic_vector (PARTITION_BITS-1 downto 0) := "0000";
signal real_cross_select : std_logic;

type window_real_cross_t is array (0 to 1) of sbit_window_t;
signal bram_o_real_cross : window_real_cross_t;

signal global_phase : unsigned (2 downto 0) := to_unsigned(0, 3); 

-- Function to reorganize data from array of partitions to slv. Also takes the lower 192 bits (from 192+36 bits) in each layer, in order to create the shifted copies.
function to_slv(arr : padded_data_t) return padded_prts_arr_t is
  variable slv_arr : padded_prts_arr_t;
  variable prt_2 : integer;
begin
  for prt in 0 to arr'length-1 loop -- Partitions
    prt_2 := prt/integer(2);
    for ly in arr(0)'range loop -- Layers
      slv_arr(prt mod 2)(ly)(192*(prt_2+1)-1 downto 192*prt_2) := arr(prt)(ly)(191 downto 0);
    end loop;
  end loop;

  -- Set "dummy" 16th partition to 0s
  for ly in 0 to 6-1 loop
    slv_arr(1)(ly)(192*(7+1)-1 downto 192*7) := (others => '0');
  end loop;

  return slv_arr;
end function;

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
   
  -- The BRAM macro only allows for 5 bits to select within a word (i.e factor of 32 difference between WIDTH_A and WIDTH_B). Ideally, we would have 6 (4 bits partition + 2 bits copies). So, we need to split the partitions. This is done by splitting the real and cross partitions, as this method is most consistent with the rest of the Segment Finder.

  -- It is significantly simpler to create 16 partitions, where partition 16 is a "dummy" and just set to all 0s. It is possible to use less BRAM space by only using 15 partitions. This would require the window size to be changed from 48 -> 45. However, the (4 bits partition)(2 bits word) to select within a single word would need to be mixed in a convoluted way. 
  partition_bram_gen : for prt_I in 0 to 1 generate
    layer_bram_gen : for ly_I in 0 to 6-1 generate
    begin
          xpm_memory_sdpram_inst_real_prt : xpm_memory_sdpram
            generic map (
               ADDR_WIDTH_A => 6,               -- (4 bits for BX)(2 bits for copies)
               ADDR_WIDTH_B => 11,               -- (4 bits BX)(2 bits copies)(3 bits partition)(2 bits word)
               BYTE_WRITE_WIDTH_A => 192*8,        -- DECIMAL
               CLOCKING_MODE => "independent_clock", -- String
               MEMORY_PRIMITIVE => "block",      -- String
               MEMORY_SIZE => 192*16*8*4,      -- Strips x BXs x Copies x Partitions = 98,304 bits ~= 12.3 kB
            --   RAM_DECOMP => "auto",            -- String
               READ_DATA_WIDTH_B => 48,         -- DECIMAL
               READ_LATENCY_B => 1,             -- DECIMAL
               SIM_ASSERT_CHK => 1,             -- DECIMAL; 0=disable simulation messages, 1=enable simulation messages
               USE_EMBEDDED_CONSTRAINT => 0,    -- DECIMAL
               USE_MEM_INIT => 0,               -- DECIMAL
               USE_MEM_INIT_MMI => 0,           -- DECIMAL
               WAKEUP_TIME => "disable_sleep",  -- String
               WRITE_DATA_WIDTH_A => 192*8,        -- DECIMAL
               WRITE_MODE_B => "no_change",     -- String
               WRITE_PROTECT => 0               -- DECIMAL
            )
            port map (
               doutb => bram_o_real_cross(prt_I)(ly_I),
               addra => full_addr_a,
               addrb => full_addr_b,
               clka => write_clock,
               clkb => clock320,
               dina => padded_prts_arr(prt_I)(ly_I),
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
full_addr_b <= std_logic_vector(bx_addr_b) & wanted_bram_from_strip & wanted_prt_reg(wanted_prt_reg'high downto 1) & wanted_word_from_strip; -- Drop the LSB of wanted_prt, as it is used in the real or cross partition selection

padded_prts_arr <= to_slv(padded_sbits); -- Organize data to be input to the BRAM. Just wiring, no logic here.

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

    real_cross_select <= wanted_prt_reg(0);
    wanted_prt_reg <= std_logic_vector(wanted_prt);
    wanted_word_from_strip <= std_logic_vector(to_unsigned(to_integer(wanted_strip) / 48, wanted_word_from_strip'length));
    wanted_bram_from_strip <= std_logic_vector(to_unsigned((to_integer(wanted_strip) / 12) mod 4, wanted_bram_from_strip'length));

    bram_o <= bram_o_real_cross(0) when real_cross_select = '0' else bram_o_real_cross(1);
  end if;
end process;

end Behavioral;
