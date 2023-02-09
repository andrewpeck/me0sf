# Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import RisingEdge
from datagen import datagen
from pat_unit_beh import find_best_seg, calculate_global_layer_mask
from subfunc import *
import os
from cocotb_test.simulator import run
from test_common import *
from constants import *

@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)

    # constants
    LY_CNT = 6
    N_NOISE = 0
    CNT_THRESH = 4

    # set layer count threshold
    dut.thresh.value = CNT_THRESH

    # set MAX_SPAN from firmware
    # should be a number approx 37
    MAX_SPAN = get_max_span_from_dut(dut)

    setup(dut)

    # zero the inputs
    set_dut_inputs(dut, [0] * 6)

    # flush the pipeline
    for _ in range(10):
        await RisingEdge(dut.clock)

    # setup the FIFO queuing to a fixed latency
    LATENCY = 3
    queue = []
    for _ in range(LATENCY):
        ly_data = datagen(LY_CNT, N_NOISE, max_span=MAX_SPAN)
        queue.append(ly_data)
        set_dut_inputs(dut, ly_data)
        await RisingEdge(dut.clock)

    for i in range(10000):

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datagen(LY_CNT, N_NOISE, max_span=MAX_SPAN)

        set_dut_inputs(dut, new_data)
        queue.append(new_data)

        # sync checks with the clock
        await RisingEdge(dut.clock)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data
        data = queue.pop(0)
        sw_segment = find_best_seg(data=data, strip=0, max_span=MAX_SPAN)
        fw_segment = get_segment_from_dut(dut)

        # apply count threshold conditions to emulator pattern assignment
        # TODO: fold this into the segment finding
        if sw_segment.lc < CNT_THRESH:
            sw_segment.id = 0
            sw_segment.lc = 0

        if sw_segment != fw_segment:
            print(f"loop={i}")
            print("> sw=%s" % sw_segment)
            print("> fw=%s" % fw_segment)

        assert sw_segment == fw_segment


def test_pat_unit():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "centroid_finder.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_pat_unit()
