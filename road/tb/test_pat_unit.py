# Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import RisingEdge
from datagen import datagen
from pat_unit_beh import pat_unit
from subfunc import *
import os
from cocotb_test.simulator import run
from tb_common import *
from constants import *

async def monitor_dav(dut, latency):
    for _ in range(8):
        await RisingEdge(dut.clock)

    while True:
        await RisingEdge(dut.dav_i)
        for _ in range(latency+1):
            assert dut.dav_o.value == 0
            await RisingEdge(dut.clock)
        assert dut.dav_o.value == 1

@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)

    # constants
    LY_CNT = 6
    N_NOISE = 0
    CNT_THRESH = 4
    LATENCY = dut.LATENCY.value

    # set layer count threshold
    dut.thresh.value = CNT_THRESH

    # set MAX_SPAN from firmware
    # should be a number approx 37
    MAX_SPAN = get_max_span_from_dut(dut)

    setup(dut)

    cocotb.fork(monitor_dav(dut,LATENCY))

    # zero the inputs
    set_dut_inputs(dut, [0] * 6)

    # flush the pipeline
    for _ in range(10):
        await RisingEdge(dut.clock)

    # setup the FIFO queuing to a fixed latency

    queue = []

    get_data = lambda : datagen(LY_CNT, N_NOISE, max_span=MAX_SPAN)

    for _ in range(LATENCY):
        ly_data = get_data()
        queue.append(ly_data)
        set_dut_inputs(dut, ly_data)
        await RisingEdge(dut.clock)

    for i in range(10000):

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = get_data()

        set_dut_inputs(dut, new_data)
        queue.append(new_data)

        # sync checks with the clock
        await RisingEdge(dut.clock)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data
        data = queue.pop(0)
        sw_segment = pat_unit(data=data, strip=0, ly_thresh=CNT_THRESH, partition=0)
        fw_segment = get_segment_from_dut(dut)

        # apply count threshold conditions to emulator pattern assignment
        # TODO: fold this into the segment finding
        if sw_segment.lc < CNT_THRESH:
            sw_segment.id = 0
            sw_segment.lc = 0

        if sw_segment != fw_segment:
            print(f"loop={i}")
            print("> sw = %s" % sw_segment)
            print("> fw = %s" % fw_segment)

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
