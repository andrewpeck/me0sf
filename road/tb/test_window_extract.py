import os
from functools import reduce

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (generate_dav)

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
   # cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def extract_test_center(dut, nloops=10):
   await extract_test(dut, "CENTER", nloops) 

async def extract_test(dut, test, nloops=512, verbose=True):
    pat_hi_los = dut.patdef_array.value.reverse # List of hi_lo pairs for patterns, should index 16: straight pattern, but need to check TODO
    
    setup(dut)

    for _ in range(16):
        await RisingEdge(dut.clock)

    sbits_q = [[0 for _ in range(6)]]
    strip_q = [0]
    pid_q = [17]

    # loop over some number of test cases
    loop = 0
    for loop in range(nloops):
        if verbose:
            print(f"{loop=}")

        #sbits_q.append([2**18 for _ in range(6)]) # Straight segment centered on strip 0
        sbits_q.append([(1+2+4+8+16+32), (2**7+2**8+2**9+2**10), (2**14+2**15+2**16), 0, 0, 0])
        strip_q.append(0)
        pid_q.append(1)

        if test=="CENTER":

            sbit_window = sbits_q.pop(0)
            strip = strip_q.pop(0)
            pid = pid_q.pop(0)
            
            if verbose:
                print(f"{sbit_window=}")
                print(f"{strip=}")
                print(f"{pid=}")

            dut.window_i.value = sbit_window
            dut.wanted_strip_i.value = strip
            dut.wanted_PID_i.value = pid
        else:
            raise Exception("Test not found")

        await RisingEdge(dut.clock)

        # Extract bits with SW to check for correctness
        pat = pat_hi_los[pid-1] # Subtract 1 from PID since the values index by 1 for now
        los_list = [pat.ly0.lo.signed_integer, pat.ly1.lo.signed_integer, pat.ly2.lo.signed_integer, pat.ly3.lo.signed_integer, pat.ly4.lo.signed_integer, pat.ly5.lo.signed_integer] # List of los for patterns
        sw_bits = [0 for _ in range(6)]
        for ly in range(6):
            center = (strip % 12) + 18 # Indexes from right, by 0
            left_index = center - los_list[ly]
            mask = reduce(lambda x, y : x | y, [2**(left_index-i) for i in range(6)]) # Take 6 bits, starting from left_index bit and going right
            sw_bits[ly] = mask & sbit_window[ly]

        print(sw_bits)

        # Read updated internal signals and output

        # pat_sbits = dut.pat_sbits.value
        center = dut.center_position.value.integer
        ly_offsets = [v.signed_integer for v in dut.ly_offsets.value]
        pat_sbits = dut.pat_sbits.value

        if verbose:
            print(f"{center=}")
            print(f"{ly_offsets=}")
            print(f"{pat_sbits=}")

        if verbose:
            print(f"{loop=}")

def test_extract():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "window_extract.vhd")]

    os.environ["SIM"] = "questa"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="window_extract",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters={},
        gui=0)

if __name__ == "__main__":
    test_extract()
