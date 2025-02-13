import os
from math import ceil
from random import seed, randint

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (get_segments_from_dut, generate_dav, monitor_dav, measure_latency)

CHUNK_WIDTH = 16
RADIUS = 3

class seg:
    def __init__ (self, lc, strip, pid, part):
        self.lc = lc
        self.strip = strip
        self.pid = pid
        self.part = part

def input_fw(dut, segs):
    dut.v_seg_i.lc.value = segs[0].lc
    dut.v_seg_i.strip.value = segs[0].strip
    dut.v_seg_i.id.value = segs[0].pid
    dut.v_seg_i.partition.value = segs[0].part

    for i in range(1, 7):
        dut.r_segs_i[i-1].lc.value = segs[i].lc
        dut.r_segs_i[i-1].strip.value = segs[i].strip
        dut.r_segs_i[i-1].id.value = segs[i].pid
        dut.r_segs_i[i-1].partition.value = segs[i].part

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
    cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=20000): 
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)
    seed(12708142)
    await RisingEdge(dut.clock)

    NUM_PARTITIONS = 8

    checkfn = lambda : dut.out_bits.value.is_resolvable and dut.out_bits.value.integer > 0
    
    def setfn(dut, x):
       input_fw(dut, [seg(x,0,0,0) for _ in range(7)])

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
                NUM_FINDERS = 15
                NUM_SEGS_PER_PRT = 12
                
                v_seg_strip = randint(CHUNK_WIDTH, 192-CHUNK_WIDTH+1)
                v_chunk = v_seg_strip//CHUNK_WIDTH

                segments_data = [seg(4, v_seg_strip, 0, 0), seg(4, (v_chunk-1)*CHUNK_WIDTH + randint(0, CHUNK_WIDTH-1), 0, 0), seg(4, v_chunk*CHUNK_WIDTH + randint(0, CHUNK_WIDTH-1), 0, 0), seg(4, (v_chunk+1)*CHUNK_WIDTH + randint(0, CHUNK_WIDTH-1), 0, 0), seg(4, (v_chunk-1)*CHUNK_WIDTH + randint(0, CHUNK_WIDTH-1), 0, 0), seg(4, v_chunk*CHUNK_WIDTH+randint(0, CHUNK_WIDTH-1), 0, 0), seg(4, (v_chunk+1)*CHUNK_WIDTH + randint(0, CHUNK_WIDTH-1), 0, 0)]
                for my_seg in segments_data:
                    print(my_seg.strip) 

                # segments_data = [seg(4, 17, 0, 0), seg(4, 16, 0, 0), seg(4, 19, 0, 0), seg(0, 0, 0, 0), seg(0, 16, 0, 0), seg(4, 17, 0, 0), seg(4, 32, 0, 0)]
                # Should give 010011 
      
            else:
                raise Exception("Test not found")
            queue.append(segments_data)
            input_fw(dut, segments_data)
            loop += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1 and loop > LATENCY:
            sw_segs = queue.pop(0)
            out_str = ""
            for i in range(1, 7):
                if (sw_segs[i].lc > 0 and abs(sw_segs[i].strip - sw_segs[0].strip) <= RADIUS):
                    out_str += "1"
                else:
                    out_str += "0"

            print("FW: " + str(dut.out_bits.value))
            print("SW: " + out_str[::-1])
            print("\n")
            assert str(dut.out_bits.value) == out_str[::-1]

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
