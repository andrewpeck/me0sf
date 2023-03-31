# Testbench for pat_unit.vhd
import os
import random
from typing import List

import cocotb
import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from constants import *
from datagen import datagen
from pat_unit_beh import pat_unit
from subfunc import *
from tb_common import *


async def monitor_dav(dut, latency):

    # wait for the first edge to start monitoring
    await RisingEdge(dut.dav_o)

    while True:
        await RisingEdge(dut.dav_i)
        for i in range(latency+1):
            assert dut.dav_o.value == 0, f"Is the latency setting wrong? found dav when we didn't expect it in clock {i} latency={latency}"
            await RisingEdge(dut.clock)
        assert dut.dav_o.value == 1, f"Is the latency setting wrong? did not find dav w/ latency={latency}"

@cocotb.test() # type: ignore
async def pat_unit_test_segments(dut):
    await pat_unit_test(dut, test="SEGMENTS")

@cocotb.test() # type: ignore
async def pat_unit_test_noise(dut):
    await pat_unit_test(dut, test="NOISE")

async def pat_unit_test(dut, test="SEGMENTS"):

    random.seed(56)

    # constants
    LY_CNT = 6
    N_NOISE = 1
    LY_THRESH = 4
    HIT_THRESH = 0
    LATENCY = dut.LATENCY.value

    # set layer count threshold
    dut.ly_thresh.value = LY_THRESH

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

    if test=="SEGMENTS": 
        get_data = lambda : datagen(LY_CNT, N_NOISE, max_span=MAX_SPAN)
    elif test=="NOISE":

        def get_data() -> List[int]:
            hits = [0 for _ in range(6)]
            num_hits = random.randint(0,50)
            for _ in range(num_hits):
                ly = random.randint(0,5)
                strp = random.randint(0,37)
                clust = 2**(random.randint(0,3))-1
                hits[ly] |= clust << strp
            hits = [x & 2**37-1 for x in hits]
            return hits
    else:
        raise Exception(f"Unknown test {test}")

    for _ in range(LATENCY):
        ly_data = get_data()
        queue.append(ly_data)
        set_dut_inputs(dut, ly_data)
        await RisingEdge(dut.clock)

    id_cnts = []
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
        sw_segment = pat_unit(data=data, strip=0,
                              hit_thresh=HIT_THRESH,
                              ly_thresh=LY_THRESH,
                              partition=0)
        fw_segment = get_segment_from_dut(dut)

        # apply count threshold conditions to emulator pattern assignment
        # TODO: fold this into the segment finding
        if sw_segment.lc < LY_THRESH:
            sw_segment.id = 0
            sw_segment.lc = 0

        if sw_segment != fw_segment:
            print(f"loop={i}")
            print("> sw = %s" % sw_segment)
            print("> fw = %s" % fw_segment)

        id_cnts.append(fw_segment.id)

        assert sw_segment == fw_segment

    filename = "../log/pat_unit_%s.log" % test
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


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
        os.path.join(rtl_dir, "pat_unit.vhd")]

    parameters = {}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0)


if __name__ == "__main__":
    test_pat_unit()
