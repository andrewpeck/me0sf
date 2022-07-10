# Testbenh for partition.vhd
import os
import random
import cocotb
import event_display as disp
from datadev_mux import datadev_mux
from subfunc import *
from cocotb_test.simulator import run
from partition_beh import work_partition
from test_common import *

@cocotb.test()
async def partition_test(
    dut, group_size=8, ghost_width=2, discrepancy_cnt=0, N_LAYERS=6
):
    """Test the partition.vhd module"""

    # random.seed(56)

    WIDTH = dut.pat_unit_mux_inst.WIDTH.value

    setup(dut)

    # set MAX_SPAN from firmware
    MAX_SPAN = get_max_span_from_dut(dut)

    for i in range(6):
        dut.partition_i[i].value = 0
        dut.neighbor_i[i].value = 0

    for i in range(4):
        await RisingEdge(dut.dav_i)

    # set up a fixed latency queue
    latency = 2  # FIXME: input the actual latency value; not an exact clock cycle --> 1 dav or 8 clock cycles from the dav_i await above

    queue = []

    for j in range(latency):

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        chamber_data = [0]*6

        queue.append(chamber_data)

        for i in range(6):
            dut.partition_i[i].value = chamber_data[i]

    for j in range(1000):

        print("loop %d" % j)

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datadev_mux(WIDTH=WIDTH, track_num=4, nhit_hi=4, nhit_lo=3)

        queue.append(new_data)

        dut.partition_i.value = new_data

        # set neighbor_i to 0 for now
        # dut.neighbor_i.value = [0]*6

        # latency equals 9 clock cycles

        # gather emulator output
        popped_data = queue.pop(0)

        sw_segments = work_partition(
            partition_data=popped_data, max_span=MAX_SPAN, width=WIDTH, enable_gcl=False
        )
        fw_segments = get_segments_from_dut(dut)

        for i in range(len(sw_segments)):

            # disp.event_display(hits=popped_data, fits=None, pats=None, width=WIDTH, max_span=MAX_SPAN)

            if True or sw_segments[i] != fw_segments[i]:
                print(f" seg {i}:")
                print("   > sw: " + str(sw_segments[i]))
                print("   > fw: " + str(fw_segments[i]))
            assert sw_segments[i] == fw_segments[i]


def test_partition():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "centroid_finding.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="partition",  # top level HDL
        toplevel_lang="vhdl",
        sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_partition()
