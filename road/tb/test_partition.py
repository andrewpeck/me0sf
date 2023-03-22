# Testbenh for partition.vhd
import os
import random

import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from datagen import datagen
from partition_beh import process_partition
from subfunc import *
from tb_common import *

@cocotb.test()
async def partition_test_walking(dut):
    await partition_test(dut, NLOOPS=192, test="WALKING1")

@cocotb.test()
async def partition_test_segs(dut):
    await partition_test(dut, NLOOPS=2000, test="SEGMENTS")

@cocotb.test()
async def partition_test_random(dut):
    await partition_test(dut, NLOOPS=2000, test="RANDOM")

async def partition_test(dut, NLOOPS=1000, test="SEGMENTS"):

    setup(dut)
    cocotb.fork(monitor_dav(dut))

    # random.seed(56)

    LY_THRESH = 6
    HIT_THRESH = 0
    WIDTH = dut.pat_unit_mux_inst.WIDTH.value
    GROUP_WIDTH = dut.S0_WIDTH.value
    MAX_SPAN = get_max_span_from_dut(dut)
    LATENCY = int(math.ceil(dut.LATENCY.value/8.0))

    # initial inputs
    dut.ly_thresh.value = LY_THRESH
    dut.partition_i.value = 6*[0]

    for i in range(4):
        await RisingEdge(dut.dav_i)

    strip_cnts = []
    id_cnts = []

    queue = []

    for i in range(LATENCY-1):
        queue.append([0]*6)

    # loop over some number of test cases
    i = 0
    while i < NLOOPS:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            i += 1

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data
            if test=="WALKING1":
                hits = 6 * [0x1 << (i % 192)]
            elif test=="SEGMENTS":
                hits = datagen(n_segs=4, n_noise=8, max_span=WIDTH)
            elif test=="RANDOM":
                hits = [0]*6
                for _ in range(30):
                    ly = random.randint(0,5)
                    strp = random.randint(0,37)
                    clust = 2**(random.randint(0,3))-1
                    hits[ly] |= clust << strp
                
            else:
                hits = 0*[6]
                assert "Invalid test selected"

            queue.append(hits)
            dut.partition_i.value = hits


        # pop old data on dav_o
        if dut.dav_o.value == 1:

            popped_data = queue.pop(0)

            sw_segments = process_partition(
                partition_data=popped_data,
                ly_thresh=LY_THRESH,
                hit_thresh=HIT_THRESH,
                max_span=MAX_SPAN,
                width=WIDTH,
                group_width=GROUP_WIDTH,
                enable_gcl=False)

            fw_segments = get_segments_from_dut(dut)

            for j in range(len(sw_segments)):

                if fw_segments[j].id > 0:
                    strip_cnts.append(j)
                    id_cnts.append(fw_segments[j].id)

                if i > 3 and sw_segments[j] != fw_segments[j]:
                    print(f" loop {i} seg {j}:")
                    print("   > sw: " + str(sw_segments[j]))
                    print("   > fw: " + str(fw_segments[j]))
                    assert sw_segments[j] == fw_segments[j]

        # next clock cycle
        await RisingEdge(dut.clock)

    with open("../log/partition_%s.log" % test, "w+") as f:

        f.write("Strips:\n")
        f.write(plotille.hist(strip_cnts, bins=int(192/4)))

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


def test_partition():
    """ """
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
                    os.path.join(rtl_dir, "pat_types.vhd"),
                    os.path.join(rtl_dir, "pat_pkg.vhd"),
                    os.path.join(rtl_dir, "fixed_delay.vhd"),
                    os.path.join(rtl_dir, "patterns.vhd"),
                    os.path.join(rtl_dir, "centroid_finder.vhd"),
                    os.path.join(rtl_dir, "pat_unit.vhd"),
                    os.path.join(rtl_dir, "dav_to_phase.vhd"),
                    os.path.join(rtl_dir, "pat_unit_mux.vhd"),
                    os.path.join(rtl_dir, "partition.vhd")]

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="partition",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        gui=0)

if __name__ == "__main__":
    test_partition()
