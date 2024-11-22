import os
from math import ceil

import cocotb
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (get_segments_from_dut, monitor_dav, setup, measure_latency)

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=100):
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)

    NUM_PARTITIONS = 8
    NULL = lambda : [[0 for _ in range(6)] for _ in range(8)]
    dut.sbits_i.value = NULL()

    # flush the buffers
    for _ in range(256):
        await RisingEdge(dut.clock)

    # measure latency by putting some s-bits on a strip and waiting to see the output
    checkfn = lambda : dut.segments_o[0].lc.value.is_resolvable and dut.segments_o[0].lc.value.integer > 0

    def setfn(dut, x):
        dut.segments_i.value = [[x for _ in range(6)] for _ in range(NUM_PARTITIONS)]

    meas_latency = await measure_latency(dut, checkfn, setfn)

    LATENCY = ceil(meas_latency)-1

    # flush the buffers
    dut.sbits_i.value = NULL()
    for _ in range(LATENCY*8+1):
        await RisingEdge(dut.clock)

    for _ in range(LATENCY-1):
        await RisingEdge(dut.dav_i)

    # loop over some number of test cases
    loop = 0
    while loop < nloops:

        # push new data on dav_i
        if dut.dav_i_phase.value == 7:

            if verbose:
                print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="SEGMENTS":

                segments_data = NUM_FINDERS*NUM_SEGS_PER_PRT*[0]

                NUM_FINDERS = 15
                NUM_SEGS_PER_PRT = 12

                PRT = 0
                SEG_NUM = 0
                #[LC PID STRIP PRT]
                #[0000 00000 00000000 0000]
                #[4 bits 5 bits 8 bits 4 bits]
                segments_data[NUM_FINDERS*PRT + SEG_NUM] = int(format(4, '04b') + format(17, '05b') + format(0, '08b') + format(PRT, '04b'), 2)
      
            else:
                segments_data = NULL()

            dut.segments_i.value = segments_data
            loop += 1

        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:
            fw_segments = get_segments_from_dut(dut)

            if verbose:
                print(f'{loop=}')
                for i in range(len(fw_segments)):
                    print("  > fw: " + str(fw_segments[i]))

        await RisingEdge(dut.clock)

def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "x_prt_deghost.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd")]

    os.environ["SIM"] = "questa"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        gui=0)

if __name__ == "__main__":
    test_chamber()
