import os
from math import ceil

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (get_segments_from_dut, generate_dav, monitor_dav, measure_latency)

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
    cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=20):
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)

    NUM_PARTITIONS = 8

    checkfn = lambda : True

    def setfn(dut, x):
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
    LATENCY = 50  #arbitrary value for now, just want to flush everything

    # flush the buffers
    setfn(dut, 0)

    for _ in range(LATENCY*8+1):
        await RisingEdge(dut.clock)

    for _ in range(LATENCY-1):
        await RisingEdge(dut.dav_i)

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
                NUM_FINDERS = 15
                NUM_SEGS_PER_PRT = 12

                segments_data = NUM_FINDERS*NUM_SEGS_PER_PRT*['0'*(4+5+8+4)]
                
                PRT = 0
                SEG_NUM = 0
                #[LC PID STRIP PRT]
                #[0000 00000 00000000 0000]
                #[4 bits 5 bits 8 bits 4 bits]
                segments_data[NUM_SEGS_PER_PRT*PRT + SEG_NUM] = format(4, '04b') + format(17, '05b') + format(0, '08b') + format(PRT, '04b')
                segments_data[NUM_SEGS_PER_PRT*1 + 0] = format(4, '04b') + format(17, '05b') + format(3, '08b') + format(1, '04b')
                segments_data[NUM_SEGS_PER_PRT*PRT + 4] = format(4, '04b') + format(17, '05b') + format(2, '08b') + format(PRT, '04b')


      
            else:
                raise Exception("Test not found")

            for i in range (15*12):
                dut.segments_i[i].lc.value = int(segments_data[i][0:4], 2)
                dut.segments_i[i].id.value = int(segments_data[i][4:9], 2)
                dut.segments_i[i].strip.value = int(segments_data[i][9:17], 2)
                dut.segments_i[i].partition.value = int(segments_data[i][17:21], 2)

            loop += 1

        # pop old data on dav_o
        if dut.dav_i.value == 1 and loop > 10:
            fw_vector = dut.vector_o
            for i in range(NUM_SEGS_PER_PRT):
                #print(dut.x_prt_segments[i].lc.value.integer)
                print(dut.in_radius_vector_l[i].value)

            if verbose:
                print(f'{loop=}')
                for i in range(len(fw_vector)):
                    print("  > fw: " + str(fw_vector[i]))

        await RisingEdge(dut.clock)

def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "x_prt_deghost.vhd")]

    parameters = {"NUM_SEGS_PER_PRT" : 12}

    os.environ["SIM"] = "questa"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="x_prt_deghost",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_chamber()
