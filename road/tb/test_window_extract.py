import os

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

        sbits_q.append([2**18 for _ in range(6)]) # Straight segment centered on strip 0
        strip_q.append(loop)
        pid_q.append(10)

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
