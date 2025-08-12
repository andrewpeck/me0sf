# Testbench for pat_unit.vhd
import os
import random
from typing import List

import cocotb
import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from constants import *
from datagen import datagen
from pat_unit_beh import pat_unit
from subfunc import *
from tb_common import *


@cocotb.test() # type: ignore
async def bram_0(dut):
    await bram_base(dut)

async def bram_base(dut):

    random.seed(1337)

    c40 = Clock(dut.clock40, 72, "ns")
    c160 = Clock(dut.clock160, 18, "ns")
    c320 = Clock(dut.clock320, 9, "ns")
    cocotb.start_soon(c40.start())
    cocotb.start_soon(c160.start())
    cocotb.start_soon(c320.start())

    # Need to have all 0's for initialized values read in first BX
    # Offset of 3 @ 320MHz + 1 BX (=N latency setting)
    q = [[['U' for _ in range(6)] for _ in range(15)] for _ in range(2)] + [[[0 for _ in range(6)] for _ in range(15)] for _ in range(11)]
    # Strip and partition queues must be offset, as addresses are registered from strip but not from partition
    # Constant offset of 3 BX, comes from pipelining address computation + 1 from BRAM interal read + 1 from output signal assignment
    strip_q = [0]*4
    prt_q = [0]*4

    for i in range(0, 10000):
        # Generate input sbits
        temp_val = i
        vals = [[i*j*k for j in range(6)] for k in range(15)]
        dut.sbits_i.value = vals
        q += [vals for _ in range(8)]
        
        # Check if output matches input (wait N BXs for latency)
        for j in range(8):
            strip = random.randint(0, 191)
            prt = random.randint(0, 14)
            #strip = (i*40) % 191
            #strip = 0 if i < 10 else 80
            #prt = 1 if i < 10 else 10
            strip_q.append(strip)
            prt_q.append(prt)
            #print(f"bram_out val: {dut.bram_o.value}")
            dut.wanted_strip.value = strip
            dut.wanted_prt.value = prt
            await RisingEdge(dut.clock320)
            
            strip = strip_q.pop(0)
            prt = prt_q.pop(0)
            print(f"Strip: {strip}, Partition: {prt}")

            out_data = []
            for ly in range(6):
                out_data.append(dut.my_out.value[(ly*48):(ly*48+47)].binstr)

            print("In Data:")
            a = q.pop(0)
            in_data_offset = a[prt]
            in_data_formatted = ["0"*18 + bin(x)[2:].zfill(192) + "0"*18 for x in in_data_offset] if isinstance(in_data_offset[0], int) else ['U'*(192+36) for _ in range(6)]
            word_from_strip = strip // 48
            copy_from_strip = (strip // 12) % 4
            start_i = 48*word_from_strip + 12*copy_from_strip
            end_i = start_i + 48
            in_data_word = [x[192+36-end_i:192+36-start_i] for x in in_data_formatted]
            print(in_data_word)

            print("Out data:")
            print(out_data)

            print(f"A BX addr: {dut.bx_addr_a.value}")
            print(f"B BX addr: {dut.bx_addr_b.value}")
            print(f"Wanted BRAM from strip: {dut.wanted_bram_from_strip.value}")
            print(f"Wanted prt_reg: {dut.wanted_prt_reg.value}")

            try:
                assert in_data_word == out_data
            except:
                print(a)
                print(f"Partition: {prt}")
                assert False

def test_bram():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "../../../xpm_VCOMP.vhd"),
        os.path.join(rtl_dir, "sbit_bram.vhd")]

    verilog_sources = [os.path.join(rtl_dir, "../../../xpm_memory.sv")]

    parameters = {}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        verilog_sources=verilog_sources,
        module=module,  # name of cocotb test module
        vhdl_compile_args=["-2008"],
        toplevel="sbit_bram",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        sim_args=["-t", "ps"],
        parameters=parameters,
        gui=0)


if __name__ == "__main__":
    test_bram()
