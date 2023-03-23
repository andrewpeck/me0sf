# Testbench for chamber.vhd
# NOTES:
#   - measure latency
#   - verify selector latency parameter

import os
import random

import cocotb
import plotille
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from chamber_beh import process_chamber
from datagen import datagen
from subfunc import *
from tb_common import *

# @cocotb.test()
# async def segments_test(dut, nloops=1000):
#     await chamber_test(dut, "SEGMENTS", nloops)

# @cocotb.test()
# async def random_test(dut, nloops=1000):
#     await chamber_test(dut, "RANDOM", nloops)

@cocotb.test()
async def walking1_test(dut, nloops=192):
    await chamber_test(dut, "WALKING1", nloops)

async def chamber_test(dut, test, nloops=512):

    '''
    Test the chamber.vhd module
    '''

    # setup the dut and extract constants from it

    setup(dut)
    cocotb.fork(monitor_dav(dut))

    await RisingEdge(dut.clock)

    MAX_SPAN = get_max_span_from_dut(dut)
    WIDTH = int(dut.partition_gen[0].partition_inst.pat_unit_mux_inst.WIDTH.value)
    LY_THRESH = int(dut.ly_thresh.value)
    HIT_THRESH = 0
    NUM_PARTITIONS = int(dut.NUM_PARTITIONS.value)
    NULL = [[0] * 6] * NUM_PARTITIONS
    LATENCY = 5
    dut.sbits_i.value = NULL

    # flush the bufers
    for _ in range(32):
        await RisingEdge(dut.clock)

    # measure latency
    for i in range(128):
        # extract latency
        dut.sbits_i.value = [[1]*6]*NUM_PARTITIONS
        await RisingEdge(dut.clock)
        if dut.segments_o[0].lc.value.is_resolvable and \
           dut.segments_o[0].lc.value.integer > 0:
            print(f"Latency={i} clocks ({i/8.0} bx)")
            break

    # flush the bufers
    dut.sbits_i.value = NULL
    for _ in range(32):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []
    partition_cnts = []

    queue = []
    for _ in range(LATENCY):
        await RisingEdge(dut.dav_i)
        chamber_data = NULL
        queue.append(chamber_data)
        dut.sbits_i.value = chamber_data

    # loop over some number of test cases
    loop = 0
    while loop < nloops:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data


            if test=="WALKING1":
                chamber_data = 8 * [6 * [1 << loop]]
            if test=="SEGMENTS":
                prt   = random.randint(0,7)
                chamber_data = NULL
                #if loop % 10 == 0:
                chamber_data[prt] = datagen(n_segs=1, n_noise=0, max_span=MAX_SPAN)
                #chamber_data = [datagen(n_segs=1, n_noise=0, max_span=MAX_SPAN)
                #for _ in range(NUM_PARTITIONS)]
            if test=="RANDOM":
                chamber_data = NULL
                for _ in range(1000):
                    prt   = random.randint(0,7)
                    ly    = random.randint(0,5)
                    strp  = random.randint(0,191)
                    chamber_data[prt][ly] |= (1 << strp)

            queue.append(chamber_data)
            dut.sbits_i.value = chamber_data

            loop += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1:

            # gather emulator output
            popped_data = queue.pop(0)

            sw_segments = process_chamber(
                chamber_data=popped_data,
                cross_part_seg_width = 0,
                hit_thresh=HIT_THRESH,
                ly_thresh=LY_THRESH,
                enable_gcl=False,
                max_span=MAX_SPAN,
                width=WIDTH,
                group_width=int(dut.S0_WIDTH.value),
                ghost_width=4,
                num_outputs=int(dut.NUM_SEGMENTS))

            fw_segments = get_segments_from_dut(dut)

            for i in range(len(fw_segments)):

                if fw_segments[i].id > 0:
                    strip_cnts.append(fw_segments[i].strip)
                    id_cnts.append(fw_segments[i].id)
                    partition_cnts.append(fw_segments[i].partition)

                err = "   "
                if sw_segments[i] != fw_segments[i]:
                    err = "ERR"
                    print(f" {err} seg {i}:")
                    print("   > sw: " + str(sw_segments[i]))
                    print("   > fw: " + str(fw_segments[i]))
                if loop > 10:
                    assert sw_segments[i] == fw_segments[i]

        await RisingEdge(dut.clock)

    with open("../log/chamber_%s.log" % test, "w+") as f:

        f.write("Strips:\n")
        f.write(plotille.hist(strip_cnts, bins=int(192/4)))

        f.write("Partitions:\n")
        f.write(plotille.hist(partition_cnts, bins=16))

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_exchange.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_merge.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_sorter.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/bitonic_sort.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "centroid_finder.vhd"),
        os.path.join(rtl_dir, "segment_selector.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "fixed_delay.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    parameters = {}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        #sim_args=["-do set NumericStdNoWarnings 1"],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_chamber()
