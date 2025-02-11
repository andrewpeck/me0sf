import os
from math import ceil

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (get_segments_from_dut, generate_dav, monitor_dav, measure_latency)

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
async def chamber_test_ff(dut, nloops=20): 
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)
 
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

                segments_data = [seg(4, 17, 0, 0), seg(4, 16, 0, 0), seg(4, 19, 0, 0), seg(0, 0, 0, 0), seg(0, 16, 0, 0), seg(4, 17, 0, 0), seg(4, 32, 0, 0)]

                # segments_data = NUM_FINDERS*NUM_SEGS_PER_PRT*['0'*(4+5+8+4)]
                
                PRT = 0
                SEG_NUM = 0
                #[LC PID STRIP PRT]
                #[0000 00000 00000000 0000]
                #[4 bits 5 bits 8 bits 4 bits]
                # segments_data[NUM_SEGS_PER_PRT*PRT + SEG_NUM] = format(4, '04b') + format(17, '05b') + format(0, '08b') + format(PRT, '04b')
                # segments_data[NUM_SEGS_PER_PRT*1 + 0] = format(4, '04b') + format(17, '05b') + format(3, '08b') + format(1, '04b')
                # segments_data[NUM_SEGS_PER_PRT*PRT + 4] = format(4, '04b') + format(17, '05b') + format(2, '08b') + format(PRT, '04b')


      
            else:
                raise Exception("Test not found")

            input_fw(dut, segments_data)
            loop += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1 and loop > LATENCY:
            fw_vector = dut.out_bits
            print(dut.out_bits.value)
            print("\n")

         #   if verbose:
         #       print(f'{loop=}')
         #       for i in range(len(fw_vector)):
         #           print("  > fw: " + str(fw_vector[i]))

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

    #parameters = {"NUM_SEGS_PER_PRT" : 12}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="x_prt_deghost_v3",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters={},
        gui=0)

if __name__ == "__main__":
    test_chamber()
