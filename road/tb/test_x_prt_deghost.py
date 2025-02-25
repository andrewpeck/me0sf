import os
from math import ceil
from random import seed, randint

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (get_segments_from_dut, generate_dav, monitor_dav, measure_latency)
from subfunc import Segment
from chamber_beh import cross_partition_cancellation 

CHUNK_WIDTH = 16
RADIUS = 2

NUM_FINDERS = 15
NUM_SEGS_PER_PRT = 12

def input_fw(dut, segs):
    for i,my_seg in enumerate(segs):
        dut.segs_i[i].lc.value = my_seg.lc
        dut.segs_i[i].strip.value = my_seg.strip
        dut.segs_i[i].id.value = my_seg.id
        dut.segs_i[i].partition.value = my_seg.partition

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
    cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=10000): 
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)
    seed(12708142)
    await RisingEdge(dut.clock)

    checkfn = lambda : dut.range_vectors[0].value.is_resolvable #and dut.out_bits.value.integer > 0
    
    def setfn(dut, x):
       input_fw(dut, [Segment(lc=x,id=0) for _ in range(NUM_FINDERS*NUM_SEGS_PER_PRT)])
 
    setfn(dut, 0)
    
    # flush the buffers
    for _ in range(10):
        await RisingEdge(dut.clock)

    meas_latency = await measure_latency(dut, checkfn, setfn)
    LATENCY = ceil(meas_latency)-2
 
    # flush the buffers
    setfn(dut, 0)

    for _ in range(LATENCY):
        await RisingEdge(dut.clock)

    # loop over some number of test cases
    loop = 0
    queue = []
    while loop < nloops:
        
        # push new data on dav_i
        if dut.dav_i.value == 1:

            if verbose:
                print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="SEGMENTS":
                segments_data = []
                for prt in range(NUM_FINDERS):
                    for chunk in range(NUM_SEGS_PER_PRT):
                        strip = randint(chunk*CHUNK_WIDTH, (chunk+1)*CHUNK_WIDTH - 1)
                        segments_data.append(Segment(lc=4, strip=strip, id=15, partition=prt))
            else:
                raise Exception("Test not found")
            queue.append(segments_data)
            input_fw(dut, segments_data)
            loop += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1 and loop > LATENCY:
            sw_segs = queue.pop(0)
            sw_segs_2d = [[sw_segs[y*NUM_SEGS_PER_PRT+x] for x in range(NUM_SEGS_PER_PRT)] for y in range(NUM_FINDERS)]
            cancelled_sw_segs_2d = cross_partition_cancellation(sw_segs_2d, RADIUS)
            
            print("\n")

            orig_segs_1d = [my_seg.strip for my_seg in sw_segs]
            print("Original segs:")
            for i in range(NUM_FINDERS):
                print(str(orig_segs_1d[NUM_SEGS_PER_PRT*i:NUM_SEGS_PER_PRT*(i+1)]))

           # pad_segs_1d = [my_seg.strip.value.integer for my_seg in dut.segs_padded]
           # print("Padded segs:")
           # for i in range(NUM_FINDERS):
           #     print(str(pad_segs_1d[(NUM_SEGS_PER_PRT+2)*i:(NUM_SEGS_PER_PRT+2)*(i+1)]))

            range_vectors_1d = [my_range.value for my_range in dut.range_vectors]
            print("Range vectors:")
            for i in range(NUM_FINDERS//2):
                print(str(range_vectors_1d[NUM_SEGS_PER_PRT*i:NUM_SEGS_PER_PRT*(i+1)]))

            mask_1d = [val.value for val in dut.mask]
            print("Mask:")
            for i in range(NUM_FINDERS):
                print(str(mask_1d[NUM_SEGS_PER_PRT*i:NUM_SEGS_PER_PRT*(i+1)]))

            segs_o = [my_seg.lc.value.integer for my_seg in dut.segs_o]
            print("Segs out:")
            for i in range(NUM_FINDERS):
                print(str(segs_o[NUM_SEGS_PER_PRT*i:NUM_SEGS_PER_PRT*(i+1)]))

            print("\nSW x-prt-deghosted segs:")
            for i in range(NUM_FINDERS):
                print([seg.lc for seg in cancelled_sw_segs_2d[i]])

            print("\n")
            for y in range(NUM_FINDERS):
                for x in range(NUM_SEGS_PER_PRT):
                    assert(cancelled_sw_segs_2d[y][x].lc == segs_o[y*NUM_SEGS_PER_PRT+x])

        await RisingEdge(dut.clock)

def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "x_prt_deghost_v3.vhd")]

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="x_prt_deghost_v3",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters={"RADIUS": RADIUS, "CHUNK_WIDTH": CHUNK_WIDTH},
        gui=0)

if __name__ == "__main__":
    test_chamber()
