# Testbench for pat_unit.vhd
import os
import random

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb_test.simulator import run

from constants import *
from subfunc import *
from tb_common import *


@cocotb.test() # type: ignore
async def bram_rand(dut):
    await bram_base(dut, "RANDOM", 50)

#@cocotb.test() # type: ignore
#async def bram_unique(dut):
#   await bram_base(dut, "UNIQUE", 5000)

#@cocotb.test() # type: ignore
#async def bram_walking1(dut):
#    await bram_base(dut, "WALKING1", 17300)

#@cocotb.test() # type: ignore
#async def bram_manual(dut):
#    await bram_base(dut, "MANUAL", 20)

async def bram_base(dut, test, nloops, verbose=False):
    # Check test validity
    if test not in ("RANDOM", "UNIQUE", "WALKING1", "MANUAL"):
        raise Exception("Invalid test type")
    
    LATENCY320 = dut.LATENCY320.value
    SBIT_PHASE = dut.SBIT_PHASE.value    

    # Set random seed, arbitrary
    random.seed(1337)

    # Start clock
    c320 = Clock(dut.clock320, 9, "ns")
    cocotb.start_soon(c320.start())

    if verbose:
        print("Starting value of copy reg A state: " + str(dut.copy_addr_a.value))

    # Need to have all 0's for initialized values read in first BX
    # Offset of 3 @ 320MHz + 1 BX (=N latency setting)
    q = [[[0 for _ in range(6)] for _ in range(15)] for _ in range(LATENCY320 + 10)]
    # Strip and partition queues must be offset, as addresses are registered from strip but not from partition
    # Constant offset of 3 BX, comes from pipelining address computation + 1 from BRAM interal read + 1 from output signal assignment
    strip_q = [0]*3
    prt_q = [0]*3

    # Wait one clock to start, to allow sbits to be set at next clock
    await RisingEdge(dut.clock320)

    # Wait for PHASE cycles
    for _ in range(SBIT_PHASE):
        await RisingEdge(dut.clock320)

 
    for i in range(nloops):
        # Generate input sbits
        if test == "RANDOM":
            vals = [[random.randint(0, 2**192-1) for _ in range(6)] for _ in range(15)]
        if test == "UNIQUE":
            vals = [[i*j*k for j in range(6)] for k in range(15)]
        elif test == "WALKING1":
            in_ly = (i//192) % 6
            in_prt = (i//(192*6)) % 15
            vals = [[0 for j in range(6)] for k in range(15)]
            vals[in_prt][in_ly] = 2**(i%192)
        elif test == "MANUAL":
            vals = [[i*k for j in range(6)] for k in range(15)]

        dut.sbits_i.value = vals
        q += [vals for _ in range(8)]

        # Check if output matches input (wait N BXs for latency)
        for j in range(8):

            # Determine which strip and partition to look at
            if test == "RANDOM" or test == "UNIQUE":
                strip = random.randint(0, 191)
                prt = random.randint(0, 14)
            elif test == "WALKING1":
                adjust_offset = 1 if j == 0 else 0
                strip = max(i-1-adjust_offset-(LATENCY320//8), 0) % 192
                prt = max(i-1-adjust_offset-(LATENCY320//8), 0)//(192*6) % 15
            elif test == "MANUAL":
                strip = i % 192
                prt = 1

            # Add read addr to FIFO
            strip_q.append(strip)
            prt_q.append(prt)

            # Apply to FW and step clock320
            dut.wanted_strip.value = strip
            dut.wanted_prt.value = prt
            await RisingEdge(dut.clock320)

            # Check that new out data matches corresponding input data
            strip = strip_q.pop(0)
            prt = prt_q.pop(0)
            if verbose:
                print(f"Strip: {strip}, Partition: {prt}")

            # Format data out from FW
            out_data = [ly.value.binstr for ly in dut.my_out]

            # Format data in from FIFO
            a = q.pop(0)
            in_data_offset = a[prt]
            in_data_formatted = ["0"*18 + bin(x)[2:].zfill(192) + "0"*18 for x in in_data_offset] if isinstance(in_data_offset[0], int) else ['U'*(192+36) for _ in range(6)]
            word_from_strip = strip // 48
            copy_from_strip = (strip // 12) % 4
            start_i = 48*word_from_strip + 12*copy_from_strip
            end_i = start_i + 48
            in_data_word = [x[192+36-end_i:192+36-start_i] for x in in_data_formatted]

            # Display info for debugging
            if verbose:
                print(f"In Data:\n{in_data_word}")
                print(f"Out data:\n{out_data}")
    
                print(f"A BX addr: {dut.bx_addr_a.value}")
                print(f"B BX addr: {dut.bx_addr_b.value}")
                print(f"Wanted BRAM from strip: {dut.wanted_bram_from_strip.value}")
                print(f"Wanted prt_reg: {dut.wanted_prt_reg.value}")

            # Assert data in == data out
            try:
                # If 'U' in out_data, in startup state so skip
                if i >= (LATENCY320 // 8) + 2:
                    assert in_data_word == out_data
            except:
                print(a)
                print(f"Partition: {prt}")
                assert False

    # Need this to get back to the starting phase, since we waited PHASE+1 clocks in the very beginning
    for _ in range(7-SBIT_PHASE):
        await RisingEdge(dut.clock320)

import pytest


phases = [0, 1, 2, 3, 4, 5, 6, 7]
latencies = [i for i in range(115)]

# Run for each phase setting, for each latency setting
parameters = []
for p in phases:
    for l in latencies:
        parameters.append({"LATENCY320" : l, "SBIT_PHASE" : p})


@pytest.mark.parametrize("parameters", parameters)
def test_bram(parameters):
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "../../../xpm_VCOMP.vhd"),
        os.path.join(rtl_dir, "sbit_bram.vhd")]

    verilog_sources = [os.path.join(rtl_dir, "../../../xpm_memory.sv")]

    #parameters = {"LATENCY320" : latency, "SBIT_PHASE" : phase}

    os.environ["SIM"] = "questa"
   
    run(vhdl_sources=vhdl_sources,
        verilog_sources=verilog_sources,
        module=module,  # name of cocotb test module
        vhdl_compile_args=["-2008"],
        toplevel="sbit_bram",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        sim_args=["-t", "ps", "-voptargs=\"-access=rw+/.\""], #voptargs arg might speed up sim
        parameters=parameters,
        sim_build = "sim_build/" + "_".join(("{}={}".format(*i) for i in parameters.items())),
        gui=0)

if __name__ == "__main__":
    phases = [7]
    latencies = [114]
    
    # Run for each phase setting, for each latency setting
    parameters = []
    for p in phases:
        for l in latencies:
            parameters.append({"LATENCY320" : l, "SBIT_PHASE" : p})
    test_bram(parameters[0])


