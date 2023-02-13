import os
import plotille
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cocotb_test.simulator import run
from datagen_mux import datagen_mux
from pat_unit_mux_beh import pat_mux
from subfunc import *
from cocotb_test.simulator import run
from test_common import *

from pat_unit_beh import calculate_global_layer_mask

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


@cocotb.test()
async def pat_unit_mux_test(dut, NLOOPS=500, test="WALKING1"):

    "Test the pat_unix_mux.vhd module"

    setup(dut)

    dut.thresh.value = 4

    await RisingEdge(dut.clock)

    MAX_SPAN = get_max_span_from_dut(dut)
    THRESH = int(dut.thresh.value)
    LATENCY = int(math.ceil(dut.LATENCY.value/8.0))
    WIDTH = dut.WIDTH.value

    set_dut_inputs(dut, [0] * 6)

    # flush the pipeline for a few clocks
    for _ in range(10):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []

    # set up a fixed latency queue
    queue = []
    for _ in range(LATENCY+1):
        queue.append([0]*6)

    await RisingEdge(dut.dav_i) # align to the dav_i

    i = 0
    # loop over some number of test cases
    while i < NLOOPS:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="WALKING1":
                new_data = 6 * [0x1 << (i % 192)]
            elif test=="SEGMENTS":
                new_data = datagen_mux(n_segs=1, n_noise=0, max_span=WIDTH)
            else:
                new_data = 0*[6]
                assert "Invalid test selected"

            queue.append(new_data)

            set_dut_inputs(dut, new_data)

            i += 1

        # pop old data on dav_o
        if dut.dav_o.value == 1:

            # (1) pop old data from the head of the queue
            # (2) run the emulator on the old data

            old_data = queue.pop(0)
            sw_segments = pat_mux(partition_data=old_data,
                                  max_span=MAX_SPAN,
                                  thresh=THRESH,
                                  width=WIDTH)

            fw_segments = get_segments_from_dut(dut)

            if i > LATENCY+2:
                for j in range(WIDTH):
                    if fw_segments[j].id > 0:
                        strip_cnts.append(j)
                        id_cnts.append(fw_segments[j].id)
                    if sw_segments[j] != fw_segments[j]:
                        print(f"loop={i} (strip={j}):")
                        print(" > sw: " + str(sw_segments[j]))
                        print(" > fw: " + str(fw_segments[j]))
                        assert sw_segments[j] == fw_segments[j]

        await RisingEdge(dut.clock)

    with open("../pat_unit_mux.log", "w+") as f:

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
        os.path.join(rtl_dir, "centroid_finder.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd")]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit_mux",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_pat_unit_mux()
