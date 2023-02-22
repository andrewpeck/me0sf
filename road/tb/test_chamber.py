# Testbench for chamber.vhd
import os
import random
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datagen import datagen
from subfunc import *
from cocotb_test.simulator import run
from chamber_beh import process_chamber
from tb_common import *


@cocotb.test()
async def chamber_test(dut, NLOOPS=100):

    """Test the chamber.vhd module"""

    # set MAX_SPAN from firmware
    setup(dut)

    await RisingEdge(dut.clock)

    MAX_SPAN = get_max_span_from_dut(dut)
    WIDTH = int(dut.partition_gen[0].partition_inst.pat_unit_mux_inst.WIDTH.value)
    THRESH = int(dut.thresh.value)
    NUM_PARTITIONS = int(dut.NUM_PARTITIONS.value)
    NULL = [[0] * 6] * 8
    LATENCY = 4

    for _ in range(10):
        await RisingEdge(dut.clock)

    dut.sbits_i.value = NULL

    queue = []
    for _ in range(LATENCY):
        await RisingEdge(dut.dav_i)
        chamber_data = NULL
        queue.append(chamber_data)
        dut.sbits_i.value = chamber_data

    fn_datagen = lambda: datagen(n_segs=1, n_noise=10, max_span=MAX_SPAN)

    # loop over some number of test cases
    loop = 0
    while loop < NLOOPS:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if loop % 10 == 0:
                chamber_data = [fn_datagen() for _ in range(NUM_PARTITIONS)]
            else:
                chamber_data = NULL

            queue.append(chamber_data)
            dut.sbits_i.value = chamber_data

            loop += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1:

            # gather emulator output
            popped_data = queue.pop(0)

            sw_segments = process_chamber(
                chamber_data=popped_data,
                thresh=THRESH,
                max_span=MAX_SPAN,
                width=WIDTH,
                group_width=int(dut.S0_WIDTH.value),
                ghost_width=4,
                num_outputs=int(dut.NUM_SEGMENTS),
            )

            fw_segments = get_segments_from_dut(dut)

            # print(sw_segments[0])
            # print(fw_segments)

            for i in range(len(sw_segments)):

                if sw_segments[i] != fw_segments[i]:
                    print(f" seg {i}:")
                    print("   > sw: " + str(sw_segments[i]))
                    print("   > fw: " + str(fw_segments[i]))
                    # assert sw_segments[i] == fw_segments[i]

        # align to the dav_i
        await RisingEdge(dut.clock)


def test_chamber_1():
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
        os.path.join(rtl_dir, "chamber.vhd"),
    ]

    parameters = {}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        #sim_args=['-do "set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0)


if __name__ == "__main__":
    test_chamber_1()
