# Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import RisingEdge
from datadev import datadev
from pat_unit_beh import get_best_seg, calculate_global_layer_mask
from subfunc import *
import os
from cocotb_test.simulator import run
from test_common import *
from constants import *

@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)

    # set the amount of layers the muon traveled through
    ly_t = 6

    # get layer count threshold from firmware
    cnt_thresh = dut.THRESHOLD.value

    # set MAX_SPAN from firmware
    MAX_SPAN = get_max_span_from_dut(dut)

    setup(dut)

    # zero the inputs
    set_dut_inputs(dut, [0] * 6)

    # flush the buffer
    for _ in range(10):
        await RisingEdge(dut.clock)

    # setup the FIFO queuing to a fixed latency
    latency = 3
    queue = []
    for _ in range(latency):
        ly_data = datadev(ly_t, MAX_SPAN)
        queue.append(ly_data)
        set_dut_inputs(dut, ly_data)
        await RisingEdge(dut.clock)

    for _ in range(10000):

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datadev(ly_t, MAX_SPAN)
        set_dut_inputs(dut, new_data)
        queue.append(new_data)

        # sync checks with the clock
        await RisingEdge(dut.clock)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data
        data = queue.pop(0)
        sw_segment = get_best_seg(data=data, strip=0, max_span=MAX_SPAN)
        fw_segment = get_segment_from_dut(dut)

        # apply count threshold conditions to emulator pattern assignment
        # TODO: fold this into the segment finding
        if sw_segment.lc < cnt_thresh:
            sw_segment.id = 0
            sw_segment.lc = 0

        if sw_segment != fw_segment:
            print("sw=%s" % sw_segment)
            print("fw=%s" % fw_segment)

        assert sw_segment == fw_segment


def test_pat_unit():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
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
