# TODO: test the deadzone logic

import os
from math import ceil

import cocotb
import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from datagen import datagen
from pat_unit_mux_beh import pat_mux
from subfunc import *
from tb_common import *


def set_layer_hits(dut, hits):

    """
    Take a collection of 6 layers, each of which is an integer bitmask of
    hits and set the DUT inputs
    """

    dut.ly0.value = hits[0]
    dut.ly1.value = hits[1]
    dut.ly2.value = hits[2]
    dut.ly3.value = hits[3]
    dut.ly4.value = hits[4]
    dut.ly5.value = hits[5]


@cocotb.test() # type: ignore
async def pat_unit_mux_walking(dut):
    await pat_unit_mux_test(dut, NLOOPS=192, test="WALKING1")

@cocotb.test() # type: ignore
async def pat_unit_mux_segments(dut):
    await pat_unit_mux_test(dut, NLOOPS=1000, test="SEGMENTS")

@cocotb.test() # type: ignore
async def pat_unit_mux_5s(dut):
    await pat_unit_mux_test(dut, NLOOPS=20, test="5A")

@cocotb.test() # type: ignore
async def pat_unit_mux_ff(dut):
    await pat_unit_mux_test(dut, NLOOPS=20, test="FF")

async def pat_unit_mux_test(dut, NLOOPS=500, test="WALKING1"):

    "Test the pat_unix_mux.vhd module"

    #--------------------------------------------------------------------------------
    # Setup and Flush the Pipeline
    #--------------------------------------------------------------------------------

    setup(dut)
    cocotb.start_soon(monitor_dav(dut))

    set_dut_inputs(dut, [0 for _ in range(6)])

    for _ in range(64):
        await RisingEdge(dut.clock)

    #--------------------------------------------------------------------------------
    # Configuration
    #--------------------------------------------------------------------------------

    config = Config()
    config.skip_centroids = True
    config.max_span=get_max_span_from_dut(dut)
    config.ly_thresh=6
    config.width=dut.WIDTH.value
    dut.ly_thresh.value = config.ly_thresh

    #--------------------------------------------------------------------------------
    # Measure Latency
    #--------------------------------------------------------------------------------

    meas_latency=-1

    # align to the dav input
    await RisingEdge(dut.dav_i)
    for _ in range(8):
        await RisingEdge(dut.clock)
    set_dut_inputs(dut, [1 for _ in range(6)])

    for i in range(128):
        # extract latency
        await RisingEdge(dut.clock)
        if dut.segments_o[0].lc.value.is_resolvable and \
           dut.segments_o[0].lc.value.integer > 0:
            meas_latency = i/8.0
            print(f"Latency={i} clocks ({meas_latency} bx)")
            break

    assert meas_latency != -1, print("Couldn't measure pat_unit_mux latency. Never saw a pattern!")

    LATENCY = ceil(meas_latency)

    set_dut_inputs(dut, [0 for _ in range(6)])

    #--------------------------------------------------------------------------------
    # Setup a fixed latency queue
    #--------------------------------------------------------------------------------

    # flush the pipeline for a few clocks
    for _ in range(32):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []

    queue = []
    for _ in range(LATENCY):
        queue.append([0 for _ in range(6)])

    await RisingEdge(dut.dav_i) # align to the dav_i

    #--------------------------------------------------------------------------------
    # Event Loop
    #--------------------------------------------------------------------------------

    i = 0
    while i < NLOOPS:

        # push new data on dav_i
        if dut.dav_i_phase.value == 7:

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="WALKING1":
                new_data = [0x1 << (i % 192) for _ in range(6)]
            elif test=="5A":
                if i % 2 == 0:
                    new_data = [0x555555555555555555555555555555555555555555555555 for _ in range(6)]
                else:
                    new_data = [0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for _ in range(6)]
            elif test=="FF":
                if i % 2 == 0:
                    new_data = [0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF for _ in range(6)]
                else:
                    new_data = [0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for _ in range(6)]
            elif test=="SEGMENTS":
                new_data = datagen(n_segs=2, n_noise=10, max_span=config.width)
            else:
                new_data = 0*[6]
                raise Exception("Invalid test selected")

            queue.append(new_data)

            set_dut_inputs(dut, new_data)

            i += 1

        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:


            # (1) pop old data from the head of the queue
            # (2) run the emulator on the old data

            old_data = queue.pop(0)
            sw_segments = pat_mux(partition_data=old_data,
                                  partition=0,
                                  config=config)

            fw_segments = get_segments_from_dut(dut)

            if i > LATENCY+2:
                for j in range(config.width):
                    if fw_segments[j].id > 0:
                        strip_cnts.append(j)
                        id_cnts.append(fw_segments[j].id)
                    if sw_segments[j] != fw_segments[j]:
                        print(f"loop={i} (strip={j}):")
                        print(" > sw: " + str(sw_segments[j]))
                        print(" > fw: " + str(fw_segments[j]))
                        assert sw_segments[j] == fw_segments[j]

        await RisingEdge(dut.clock)

    filename = "../log/pat_unit_mux_%s.log" % test
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:

        f.write("Strips:\n")
        f.write(plotille.hist(strip_cnts, bins=int(192/4)))

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


def test_pat_unit_mux():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "hit_count.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "deadzone.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd")]

    parameters = {}
    parameters["MUX_FACTOR"] = 8
    parameters["DEADTIME"]   = 0

    os.environ["SIM"] = "questa"
    #os.environ["COCOTB_RESULTS_FILE"] = f"../log/{module}.xml"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit_mux",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-do", "set NumericStdNoWarnings 1;"],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_pat_unit_mux()
