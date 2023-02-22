# Testbenh for partition.vhd
import os
import random
import cocotb
from datagen import datagen
from subfunc import *
from cocotb_test.simulator import run
from partition_beh import work_partition
from cocotb.triggers import Timer
from tb_common import *
from cocotb.triggers import RisingEdge, Edge

async def monitor_dav(dut):
    await RisingEdge(dut.dav_o)
    await RisingEdge(dut.dav_o)
    while True:
        await Edge(dut.segments_o)
        await Timer(1, units="ns")
        assert dut.dav_o == 1
        await RisingEdge(dut.clock)

        for _ in range(7):
            await RisingEdge(dut.clock)
            assert dut.dav_o == 0

        await RisingEdge(dut.clock)
        assert dut.dav_o == 1

        break

@cocotb.test()
async def partition_test_segs(dut):
    await partition_test(dut, NLOOPS=2000, test="SEGMENTS")

@cocotb.test()
async def partition_test_walking(dut):
    await partition_test(dut, NLOOPS=192, test="WALKING1")

async def partition_test(dut, NLOOPS=1000, test="SEGMENTS"):

    setup(dut)
    cocotb.fork(monitor_dav(dut))

    # random.seed(56)

    THRESH = 6
    WIDTH = dut.pat_unit_mux_inst.WIDTH.value
    MAX_SPAN = get_max_span_from_dut(dut)
    LATENCY = int(math.ceil(dut.LATENCY.value/8.0))

    # initial inputs
    dut.thresh.value = THRESH
    dut.partition_i.value = 6*[0]

    for i in range(4):
        await RisingEdge(dut.dav_i)

    queue = []

    for i in range(LATENCY-1):
        queue.append([0]*6)

    # loop over some number of test cases
    i = 0
    while i < NLOOPS:

        # push new data on dav_i
        if dut.dav_i.value == 1:

            i += 1

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data
            if test=="WALKING1":
                new_data = 6 * [0x1 << (i % 192)]
            elif test=="SEGMENTS":
                new_data = datagen(n_segs=1, n_noise=0, max_span=WIDTH)
            else:
                new_data = 0*[6]
                assert "Invalid test selected"

            queue.append(new_data)
            dut.partition_i.value = new_data


        # pop old data on dav_o
        if dut.dav_o.value == 1:

            popped_data = queue.pop(0)
            sw_segments = work_partition(partition_data=popped_data,
                                         thresh=THRESH,
                                         max_span=MAX_SPAN,
                                         width=WIDTH,
                                         enable_gcl=False)

            fw_segments = get_segments_from_dut(dut)

            for j in range(len(sw_segments)):

                if i > 3 and sw_segments[j] != fw_segments[j]:
                    print(f" loop {i} seg {j}:")
                    print("   > sw: " + str(sw_segments[j]))
                    print("   > fw: " + str(fw_segments[j]))
                    assert sw_segments[j] == fw_segments[j]

        # next clock cycle
        await RisingEdge(dut.clock)


def test_partition():
    """ """
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
                    os.path.join(rtl_dir, "pat_types.vhd"),
                    os.path.join(rtl_dir, "pat_pkg.vhd"),
                    os.path.join(rtl_dir, "fixed_delay.vhd"),
                    os.path.join(rtl_dir, "patterns.vhd"),
                    os.path.join(rtl_dir, "centroid_finder.vhd"),
                    os.path.join(rtl_dir, "pat_unit.vhd"),
                    os.path.join(rtl_dir, "dav_to_phase.vhd"),
                    os.path.join(rtl_dir, "pat_unit_mux.vhd"),
                    os.path.join(rtl_dir, "partition.vhd")]

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="partition",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        gui=0)

if __name__ == "__main__":
    test_partition()
