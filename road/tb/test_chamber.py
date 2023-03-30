# Testbench for chamber.vhd
# NOTES:
#   - measure latency
#   - verify selector latency parameter
#   - add cross partition tester
#   - check the outputs of the partitions before chamber sorting ?

import os
import random
from math import ceil

import cocotb
import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from chamber_beh import process_chamber
from datagen import datagen
from subfunc import Config
from tb_common import (get_max_span_from_dut, get_segments_from_dut,
                       monitor_dav, setup)

@cocotb.test()
async def chamber_test_ff(dut, nloops=20):
    await chamber_test(dut, "FF", nloops)

@cocotb.test()
async def chamber_test_5a(dut, nloops=20):
    await chamber_test(dut, "5A", nloops)

@cocotb.test()
async def chamber_test_walking1(dut, nloops=192*2):
    await chamber_test(dut, "WALKING1", nloops)

@cocotb.test()
async def chamber_test_walkingf(dut, nloops=192*2):
    await chamber_test(dut, "WALKINGF", nloops)

@cocotb.test()
async def chamber_test_xprt(dut, nloops=1000):
    await chamber_test(dut, "XPRT", nloops)

@cocotb.test()
async def chamber_test_segs(dut, nloops=1000):
    await chamber_test(dut, "SEGMENTS", nloops)

@cocotb.test()
async def chamber_test_random(dut, nloops=100):
    await chamber_test(dut, "RANDOM", nloops)

async def chamber_test(dut, test, nloops=512, verbose=False):

    '''
    Test the chamber.vhd module
    '''

    random.seed(56) # chloe's favorite number

    # setup the dut and extract constants from it
    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)

    config = Config()

    config.x_prt_en = dut.X_PRT_EN.value
    config.en_non_pointing = dut.EN_NON_POINTING.value
    config.max_span = get_max_span_from_dut(dut)
    config.width = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.WIDTH.value
    config.deghost_pre = dut.partition_gen[0].partition_inst.DEGHOST_PRE.value
    config.deghost_post = dut.partition_gen[0].partition_inst.DEGHOST_POST.value
    config.group_width = dut.partition_gen[0].partition_inst.S0_WIDTH.value
    config.num_outputs= dut.NUM_SEGMENTS
    config.ly_thresh = 6
    config.hit_thresh = 0 # set to zero to disable until implmented in fw
    config.cross_part_seg_width = 0 # set to zero to disable until implmented in fw

    NUM_PARTITIONS = 8
    NULL = lambda : [[0 for _ in range(6)] for _ in range(8)]
    dut.sbits_i.value = NULL()

    dut.ly_thresh.value = config.ly_thresh

    # flush the bufers
    for _ in range(256):
        await RisingEdge(dut.clock)

    # measure latency
    meas_latency=-1
    for i in range(128):
        # extract latency
        dut.sbits_i.value = [[1 for _ in range(6)] for _ in range(NUM_PARTITIONS)]
        await RisingEdge(dut.clock)
        if dut.segments_o[0].lc.value.is_resolvable and \
           dut.segments_o[0].lc.value.integer >= config.ly_thresh:
            meas_latency = i/8.0
            print(f"Latency={i} clocks ({meas_latency} bx)")
            break

    LATENCY = ceil(meas_latency)

    # flush the bufers
    dut.sbits_i.value = NULL()
    for _ in range(LATENCY*8+1):
        await RisingEdge(dut.clock)

    strip_cnts = []
    id_cnts = []
    partition_cnts = []

    queue = []
    for _ in range(LATENCY-1):
        await RisingEdge(dut.dav_i)
        queue.append(NULL())

    # loop over some number of test cases
    istrip = 0
    iprt = 0
    loop = 0
    while loop < nloops:

        # push new data on dav_i
        if dut.dav_i_phase.value == 7:

            if verbose:
                print(f"{loop=}")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="WALKING1" or test=="WALKINGF":

                if istrip == 191:
                    istrip = 0
                    if iprt == 7:
                        iprt = 0
                    else:
                        iprt += 1
                else:
                    istrip += 1

                dat = 0x1 if test=="WALKING1" else 0xffff
                chamber_data=NULL()
                chamber_data[iprt] = [(2**192-1) & (dat << istrip) for _ in range(6)]

            elif test=="SEGMENTS":
                prt   = random.randint(0,7)
                chamber_data = NULL()
                chamber_data = [datagen(n_segs=2, n_noise=8, max_span=config.max_span)
                                for _ in range(NUM_PARTITIONS)]

            elif test=="FF":
                if loop % 2 == 0:
                    chamber_data = [[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF for _ in range(6)] for _ in range(8)]
                else:
                    chamber_data = [[0x000000000000000000000000000000000000000000000000 for _ in range(6)] for _ in range(8)]

            elif test=="XPRT":

                prt   = random.randint(0,6)
                strp  = random.randint(0,191)

                # feed in a cross-partition segment
                chamber_data=NULL()
                chamber_data[prt+0][0] |= (1 << strp)
                chamber_data[prt+0][1] |= (1 << strp)
                chamber_data[prt+0][2] |= (1 << strp)
                chamber_data[prt+1][3] |= (1 << strp)
                chamber_data[prt+1][4] |= (1 << strp)
                chamber_data[prt+1][5] |= (1 << strp)

            elif test=="5A":
                if loop % 2 == 0:
                    chamber_data = [[0x555555555555555555555555555555555555555555555555 for _ in range(6)] for _ in range(8)]
                else:
                    chamber_data = [[0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA for _ in range(6)] for _ in range(8)]

            elif test=="RANDOM":

                chamber_data = NULL()

                num_hits = random.randint(0,1000)

                for _ in range(num_hits):
                    prt   = random.randint(0,7)
                    ly    = random.randint(0,5)
                    strp  = random.randint(0,191)
                    chamber_data[prt][ly] |= (1 << strp)

                for prt in range(8):
                    for ly in range(6):
                        chamber_data[prt][ly] &= 2**192-1

                # chamber_data = [[0,0,0,0,0,0],
                #                 [0,0,0,0,0,0],
                #                 [0,0,0,0,0,0],
                #                 [0,0,0,0,0,0],
                #                 [24038801780916083168769940586170856529853459044767744, 393854372280306332493332304728065653894960221539015196672, 197695011464233716551040219415442138429244291613734731776, 784637740307541833018438133678121907990633486120280145920, 3139317115463798414685423611272489066807669546084909449221, 2298743311304495757759654983174502303995534521288364032],
                #                 #[(0xffff << 44) for _ in range(6)],
                #                 [0,0,0,0,0,0],
                #                 [0,0,0,0,0,0],
                #                 [0,0,0,0,0,0],]
            else:
                chamber_data = NULL()

            queue.append(chamber_data)
            dut.sbits_i.value = chamber_data

            loop += 1

        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:

            # gather emulator output
            popped_data = queue.pop(0)

            sw_segments = process_chamber(
                chamber_data=popped_data,
                config=config)

            fw_segments = get_segments_from_dut(dut)

            if verbose:
                print(f'{loop=}')
                for i in range(len(fw_segments)):
                    print("  > fw: " + str(fw_segments[i]))
                    print("  > sw: " + str(sw_segments[i]))

            for i in range(len(fw_segments)):

                if fw_segments[i].id > 0:
                    strip_cnts.append(fw_segments[i].strip)
                    id_cnts.append(fw_segments[i].id)
                    partition_cnts.append(fw_segments[i].partition)

                err = "   "
                if loop > LATENCY+2:
                    if sw_segments[i] != fw_segments[i]:
                        err = "ERR"
                        print(f" {err} seg {i}:")
                        print("   > sw: " + str(sw_segments[i]))
                        print("   > fw: " + str(fw_segments[i]))

                    assert sw_segments[i] == fw_segments[i]

        await RisingEdge(dut.clock)

    filename = "../log/chamber_%s.log" % test
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:

        f.write("Strips:\n")
        f.write(plotille.hist(strip_cnts, bins=int(192/4)))

        f.write("\nPartitions:\n")
        f.write(plotille.hist(partition_cnts, bins=16))

        f.write("\nIDs:\n")
        f.write(plotille.hist(id_cnts, bins=16))


def test_chamber():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_exchange.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_merge.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/kawazome/bitonic_sorter.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/bitonic_sort.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "centroid_finder.vhd"),
        os.path.join(rtl_dir, "segment_selector.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "fixed_delay.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "deghost.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    parameters = {}

    os.environ["SIM"] = "questa"
    os.environ["COCOTB_RESULTS_FILE"] = f"../log/{module}.xml"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-do", "set NumericStdNoWarnings 1;"],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_chamber()
