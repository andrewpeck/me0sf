import os
from math import ceil

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (generate_dav, monitor_dav, measure_latency)

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
    cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=400):
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)

    NUM_PARTITIONS = 8

    checkfn = lambda : True

    def setfn(dut, x):
        return
        for i in range(15*12):
            dut.segments_i[i].lc.value.integer = x
            dut.segments_i[i].id.value.integer = 0
            dut.segments_i[i].strip.value.integer = 0
            dut.segments_i[i].partition.value.integer = 0

    setfn(dut, 0)

    # flush the buffers
    for _ in range(256):
        await RisingEdge(dut.clock)

    meas_latency = await measure_latency(dut, checkfn, setfn)

    # LATENCY = ceil(meas_latency)-1
    LATENCY = 2  #arbitrary value for now, just want to flush everything

    # flush the buffers
    setfn(dut, 0)

    for _ in range(LATENCY*8+1):
        await RisingEdge(dut.clock)

    for _ in range(LATENCY-1):
        await RisingEdge(dut.dav_i)

    segments_queue = []

    #for lc_l in range(2**3):
    #    for strip_l in range(2**8):
    #        for lc_r in range(2**3):
    #            for strip_r in range(2**8):
    #                segments_queue.append(({"LC" : lc_l, "STRIP" : strip_l}, {"LC" : lc_r, "STRIP" : strip_r}))
    for strip_l in range(192):
        for strip_r in range(192):
            segments_queue.append(({"LC" : 1, "STRIP" : strip_l}, {"LC" : 1, "STRIP" : strip_r}))

    # loop over some number of test cases
    loop = 0
    while loop < nloops:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            if verbose:
                print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="SEGMENTS":

                seg_l, seg_r = segments_queue.pop(0)
                
                if verbose:
                    print(f"Left segment LC: {seg_l["LC"]}")
                    print(f"Left segment strip: {seg_l["STRIP"]}")
                    print(f"Right segment LC: {seg_r["LC"]}")
                    print(f"Right segment strip: {seg_r["STRIP"]}")

                dut.seg_l_i.lc.value = seg_l["LC"]
                dut.seg_l_i.strip.value = seg_l["STRIP"]
                dut.seg_r_i.lc.value = seg_r["LC"]
                dut.seg_r_i.strip.value = seg_r["STRIP"]

            else:
                raise Exception("Test not found")

            loop += 1

        # pop old data on dav_o
        if dut.dav_i.value == 1:
            compress_o = dut.bool_o_compress.value
            uncompress_o = dut.bool_o_uncompress.value

            if verbose:
                print(f'{loop=}')
                print(f"Compressed: {compress_o}")
                print(f"Uncompressed: {uncompress_o}")

           # assert compress_o == uncompress_o

        await RisingEdge(dut.clock)

def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "subtract_tester.vhd")]

    #parameters = {"NUM_SEGS_PER_PRT" : 12}

    os.environ["SIM"] = "questa"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="subtract_tester",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters={},
        gui=0)

if __name__ == "__main__":
    test_chamber()
