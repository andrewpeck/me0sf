# Testbench for chamber.vhd
import os
import random
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datadev_mux import datadev_mux
from subfunc import *
from cocotb_test.simulator import run
from chamber_beh import process_chamber
from test_common import *

@cocotb.test()
async def chamber_test(dut, group_size = 8, ghost_width = 2, discrepancy_cnt = 0, N_LAYERS = 6):

    """Test the chamber.vhd module"""

    # set MAX_SPAN from firmware
    MAX_SPAN = get_max_span_from_dut(dut)

    setup(dut)

    # set seed
    random.seed(56)

    width = int(dut.partition_gen[0].partition_inst.pat_unit_mux_inst.WIDTH.value)
    num_partitions = int(dut.NUM_PARTITIONS.value)

    dut.sbits_i.value = [[0]*6]*8

    queue = []
    LATENCY=8
    for _ in range(LATENCY):
        await RisingEdge(dut.dav_i)
        chamber_data=[[0]*6]*8
        queue.append(chamber_data)
        dut.sbits_i.value = chamber_data

    for j in range(1):

        print("Case %d" % j)

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        chamber_data = [datadev_mux(WIDTH=width, track_num=4, nhit_hi=10, nhit_lo=3) for _ in range(8)]
        queue.append(chamber_data)
        dut.sbits_i.value = chamber_data

        # gather emulator output
        popped_data = queue.pop(0)

        sw_segments = process_chamber(
            chamber_data=popped_data,
            max_span=MAX_SPAN,
            width=width,
            group_width=int(dut.S0_WIDTH.value),
            ghost_width=4,
            num_outputs=int(dut.NUM_SEGMENTS)
        )

        fw_segments = get_segments_from_dut(dut)

        # print(sw_segments[0])
        # print(fw_segments)

        for i in range(len(sw_segments)):

            # disp.event_display(hits=popped_data, fits=None, pats=None, width=WIDTH, max_span=MAX_SPAN)

            if True or sw_segments[i] != fw_segments[i]:
                print(f" seg {i}:")
                print("   > sw: " + str(sw_segments[i]))
                print("   > fw: " + str(fw_segments[i]))
            assert sw_segments[i] == fw_segments[i]



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
        os.path.join(rtl_dir, "bitonic_sort/bitonic_sort.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "centroid_finding.vhd"),
        os.path.join(rtl_dir, "segment_selector.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "chamber.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_chamber_1()
