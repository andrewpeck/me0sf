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
                       monitor_dav, setup, measure_latency)

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=100):
   await chamber_test(dut, "SEGMENTS", nloops) 

async def chamber_test(dut, test, nloops=512, verbose=True):
    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)

    NUM_PARTITIONS = 8
    NULL = lambda : [[0 for _ in range(6)] for _ in range(8)]
    dut.sbits_i.value = NULL()

    # flush the buffers
    for _ in range(256):
        await RisingEdge(dut.clock)

    # measure latency by putting some s-bits on a strip and waiting to see the output
    checkfn = lambda : dut.segments_o[0].lc.value.is_resolvable and dut.segments_o[0].lc.value.integer > 0

    def setfn(dut, x):
        dut.segments_i.value = [[x for _ in range(6)] for _ in range(NUM_PARTITIONS)]

    meas_latency = await measure_latency(dut, checkfn, setfn)

    LATENCY = ceil(meas_latency)-1

    # flush the buffers
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

            if test=="SEGMENTS":

                segments_data = NULL()

                NUM_FINDERS = 15
                NUM_SEGS_PER_PRT = 12

                PRT = 0
                SEG_NUM = 0
                segments_data[NUM_FINDERS*PRT + SEG_NUM] = (2**192-1) & (2**26)
      

            else:
                segments_data = NULL()

            queue.append(segments_data)
            dut.segments_i.value = segments_data
            loop += 1

        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:

            # gather emulator output
            popped_data = queue.pop(0)

            temp_zeros = [[[0]*192]*6]*8
            sw_segments = process_chamber(chamber_data=popped_data,
                                          config=config, chamber_bx_data=temp_zeros)

            fw_segments = get_segments_from_dut(dut)

            #Add 3 to the FW segments' layer count, to account for LC compression
            if (en_hc_compress):
                for segment in fw_segments:
                    if (segment.lc > 0):
                        segment.lc += 3
                        segment.update_quality()

            if verbose:
                print(f'{loop=}')
                for i in range(len(fw_segments)):
                    print("  > fw: " + str(fw_segments[i]))
                    print("  > sw: " + str(sw_segments[i]))

            for i in range(max((len(sw_segments), len(fw_segments)))):

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
        os.path.join(rtl_dir, "hit_count.vhd"),
        os.path.join(rtl_dir, "segment_selector.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "fixed_delay.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "deghost.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber_pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    #parameters = {"PULSE_EXTEND": 1, "DEADTIME": 0, "DISABLE_PEAKING": True}
    parameters = {"DISABLE_PEAKING": True}

    os.environ["SIM"] = "questa"
    #os.environ["COCOTB_RESULTS_FILE"] = f"../log/{module}.xml"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_chamber()
