# Testbenh for partition.vhd
import os
import random
from math import ceil

import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from datagen import datagen
from partition_beh import process_partition
from subfunc import *
from tb_common import *

@cocotb.test() # type: ignore
async def partition_test_5A(dut):
    await partition_test(dut, NLOOPS=20, test="5A")

@cocotb.test() # type: ignore
async def partition_test_FF(dut):
    await partition_test(dut, NLOOPS=20, test="FF")

@cocotb.test() # type: ignore
async def partition_test_walking1(dut):
    await partition_test(dut, NLOOPS=192, test="WALKING1")

@cocotb.test() # type: ignore
async def partition_test_walkingf(dut):
    await partition_test(dut, NLOOPS=192, test="WALKINGF")

@cocotb.test() # type: ignore
async def partition_test_random(dut):
    await partition_test(dut, NLOOPS=2000, test="RANDOM")

@cocotb.test() # type: ignore
async def partition_test_segs(dut):
    await partition_test(dut, NLOOPS=2000, test="SEGMENTS")


async def partition_test(dut, NLOOPS=1000, test="SEGMENTS"):

    setup(dut)
    cocotb.start_soon(monitor_dav(dut))

    # random.seed(56)

    config = Config()
    config.width = 192
    config.max_span = get_max_span_from_dut(dut)
    config.width = dut.pat_unit_mux_inst.WIDTH.value
    config.group_width = dut.S0_WIDTH.value
    config.deghost_pre = dut.DEGHOST_PRE.value
    config.deghost_post = dut.DEGHOST_POST.value

    # initial inputs
    dut.ly_thresh.value = config.ly_thresh
    dut.partition_i.value = [0 for _ in range(6)]

    # flush the buffers
    for i in range(128):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []

    queue = []

    # measure latency
    meas_latency=1
    for i in range(128):
        # extract latency
        dut.partition_i.value = [1 for _ in range(6)]
        await RisingEdge(dut.clock)
        if dut.segments_o[0].lc.value.is_resolvable and \
           dut.segments_o[0].lc.value.integer >= config.ly_thresh:
            meas_latency = i/8.0
            print(f"Latency={i} clocks ({meas_latency} bx)")
            break

    LATENCY = ceil(meas_latency)

    # flush the buffers
    dut.partition_i.value = [0 for _ in range(6)]
    for i in range(128):
        await RisingEdge(dut.clock)

    for i in range(LATENCY):
        queue.append([0]*6)

    # loop over some number of test cases
    i = 0
    while i < NLOOPS:

        # push new data on dav_i
        if dut.dav_i_phase.value == 7:

            i += 1

            # (1) generate new data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="WALKING1":
                hits = [(0x1 << (i % 192)) for _ in range(6)]

            elif test=="WALKINGF":
                hits = [(2**192-1) & (0xffff << (i % 192)) for _ in range(6)]

            elif test=="5A":
                if i % 2 == 0:
                    hits = [0x555555555555555555555555555555555555555555555555 for _ in range(6)]
                else:
                    hits = [0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa for _ in range(6)]

            elif test=="FF":
                if i % 2 == 0:
                    hits = [0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF for _ in range(6)]
                else:
                    hits = [0x000000000000000000000000000000000000000000000000 for _ in range(6)]

            elif test=="SEGMENTS":
                hits = datagen(n_segs=4, n_noise=8, max_span=config.width)

            elif test=="RANDOM":
                hits = [0]*6
                for _ in range(400):
                    ly = random.randint(0,5)
                    strp = random.randint(0,191)
                    clust = 2**(random.randint(0,7))-1
                    hits[ly] |= clust << strp
                for ly in range(6):
                    hits[ly] &= 2**192-1
                
            else:
                hits = [0 for _ in range(6)]
                raise Exception("Invalid test selected")


            queue.append(hits)
            dut.partition_i.value = hits


        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:

            popped_data = queue.pop(0)

            sw_segments = process_partition(partition_data=popped_data,
                                            partition=dut.PARTITION_NUM.value,
                                            config=config)

            fw_segments = get_segments_from_dut(dut)

            for j in range(len(sw_segments)):

                if fw_segments[j].id > 0:
                    strip_cnts.append(j)
                    id_cnts.append(fw_segments[j].id)

                if i > 3 and sw_segments[j] != fw_segments[j]:
                    print(f" loop {i} seg {j}:")
                    print("   > sw: " + str(sw_segments[j]))
                    print("   > fw: " + str(fw_segments[j]))
                    assert sw_segments[j] == fw_segments[j]

        # next clock cycle
        await RisingEdge(dut.clock)

    filename = "../log/partition_%s.log" % test
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:

        f.write("Strips:\n")
        f.write(plotille.hist(strip_cnts, bins=int(192/4)))

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


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
                    os.path.join(rtl_dir, "hit_count.vhd"),
                    os.path.join(rtl_dir, "pat_unit.vhd"),
                    os.path.join(rtl_dir, "dav_to_phase.vhd"),
                    os.path.join(rtl_dir, "deadzone.vhd"),
                    os.path.join(rtl_dir, "pat_unit_mux.vhd"),
                    os.path.join(rtl_dir, "deghost.vhd"),
                    os.path.join(rtl_dir, "partition.vhd")]

    # disable DEADTIME in the test bench since it is not emulated in the software
    parameters = {"DEADTIME": 0}

    os.environ["SIM"] = "questa"
    #os.environ["COCOTB_RESULTS_FILE"] = f"../log/{module}.xml"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        parameters=parameters,
        toplevel="partition",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-do", "set NumericStdNoWarnings 1;"],
        gui=0)

if __name__ == "__main__":
    test_partition()
