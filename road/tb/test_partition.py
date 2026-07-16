# Testbenh for partition.vhd
import os
import random
from math import ceil

import plotille
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner, VHDL

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

    setup_pat_unit(dut)
    #cocotb.start_soon(monitor_dav(dut))

    # random.seed(56)

    config = Config()
    config.initialize_patlist(get_patlist_from_dut(dut))
    config.width = 192
    config.skip_centroids = True
    config.width = dut.pat_unit_mux_inst.WIDTH.value
    config.group_width = dut.S0_WIDTH.value
    config.deghost_pre = dut.DEGHOST_PRE.value
    config.deghost_post = dut.DEGHOST_POST.value
    config.start_tst_manager()

    # initial inputs
    en_hc_compress = True if dut.EN_HC_COMPRESS.value == 1 else False
    dut.ly_thresh.value = [thresh-4 for thresh in config.ly_thresh_patid] if en_hc_compress else config.ly_thresh_patid # Since HC compression happens at a higher level in FW, need to take care of it here

    dut.partition_i.value = [0 for _ in range(6)]

    # flush the buffers
    for i in range(128):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []

    queue = []

    #--------------------------------------------------------------------------------
    # Measure latency
    #--------------------------------------------------------------------------------
    checkfn = lambda : dut.segments_o[0].valid.value.is_resolvable and dut.segments_o[0].valid.value == 1

    def setfn(dut, x):
        dut.partition_i.value = [x for _ in range(6)]

    meas_latency = await measure_latency(dut, checkfn, setfn)

    LATENCY = ceil(meas_latency)-4

    #--------------------------------------------------------------------------------
    # Event Loop
    #--------------------------------------------------------------------------------

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
        if dut.dav_o.value == 1:

            popped_data = queue.pop(0)

            sw_segments = process_partition(partition_data=popped_data,
                                            partition=dut.PARTITION_NUM.value,
                                            config=config,
                                            partition_bx_data = [[0]*192]*6)

            fw_segments = get_segments_from_dut(dut)

            for j in range(max([len(fw_segments), len(sw_segments)])):

                if fw_segments[j].id > 0:
                    strip_cnts.append(j)
                    id_cnts.append(fw_segments[j].id)

                    if en_hc_compress:
                        fw_segments[j].lc += 3
                        fw_segments[j].update_quality()

                if i > 3 and sw_segments[j] != fw_segments[j]:
                    print(f" loop {i} seg {j}:")
                    print("   > sw: " + str(sw_segments[j]))
                    print("   > fw: " + str(fw_segments[j]))
                    assert sw_segments[j] == fw_segments[j]

        # next clock cycle
        await RisingEdge(dut.clock)

#    filename = "../log/partition_%s.log" % test
#    os.makedirs(os.path.dirname(filename), exist_ok=True)
#    with open(filename, "w+", encoding="utf-8") as f:
#
#        f.write("Strips:\n")
#        f.write(plotille.hist(strip_cnts, bins=int(192/4)))
#
#        f.write("\nIDs:\n")
#        f.write(plotille.hist(id_cnts, bins=16))


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
                    os.path.join(rtl_dir, "pat_unit_mux.vhd"),
                    os.path.join(rtl_dir, "deghost.vhd"),
                    os.path.join(rtl_dir, "partition.vhd")]

    # disable DEADTIME in the test bench since it is not emulated in the software
    parameters = {"DISABLE_PEAKING": True, "NUM_SEGMENTS": 8, "S0_WIDTH" : 16}

    sim = os.getenv("SIM", "questa")
    runner = get_runner(sim)

    runner.build(
        sources = vhdl_sources,
        parameters = parameters,
        build_args = [VHDL("-2008")],
        hdl_toplevel = "partition",
        always = True
    )

    speedup_args = ["-no_autoacc"]

    runner.test(
        hdl_toplevel="partition",
        test_module="test_partition",
        test_args = ["-noautoldlibpath"] + speedup_args,
        pre_cmd = ["set NumericStdNoWarnings 1;"],
        gui = 0
    )

if __name__ == "__main__":
    test_partition()
