import os
from math import ceil

import cocotb
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from subfunc import Config
from tb_common import (get_max_span_from_dut, get_segments_from_dut,
                       monitor_dav, setup, measure_latency)
from get_sbits_from_root import (read_ntuple_stack, get_sbits_from_event)
from convert_tracks_to_sbits import *

@cocotb.test() # type: ignore
async def chamber_test_ff(dut, nloops=20):
   await chamber_test(dut, "FF", nloops)

async def chamber_test(dut, test, nloops=512, verbose=True):

    '''
    Test the chamber.vhd module
    '''
    # Read in ROOT file for sbit data
    sbit_root = read_ntuple_stack("00001199.root")

    # Read in ROOT file for tracks
    track_root = read_stack_tracks("stack_testdata_tracks.root")

    # setup the dut and extract constants from it

    setup(dut)

    cocotb.start_soon(monitor_dav(dut))

    await RisingEdge(dut.clock)
     
    config = Config()

    config.skip_centroids = True
    config.x_prt_en = dut.X_PRT_EN.value
    config.en_non_pointing = dut.EN_NON_POINTING.value
    config.max_span = get_max_span_from_dut(dut)
    config.width = dut.partition_gen[0].partition_gen_real.partition_inst.pat_unit_mux_inst.WIDTH.value
    config.deghost_pre = dut.partition_gen[0].partition_gen_real.partition_inst.DEGHOST_PRE.value
    config.deghost_post = dut.partition_gen[0].partition_gen_real.partition_inst.DEGHOST_POST.value
    config.group_width = dut.partition_gen[0].partition_gen_real.partition_inst.S0_WIDTH.value
    config.num_outputs= dut.NUM_SEGMENTS.value
    config.ly_thresh_eta = [4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4]
    config.ly_thresh_patid = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    config.cross_part_seg_width = dut.X_DEGHOST_EDGE_DIST.value # set to zero to disable until implmented in fw

    en_hc_compress = True #this is a generic, so need to set it here and in top level in FW

    NUM_PARTITIONS = 8
    NULL = lambda : [[0 for _ in range(6)] for _ in range(8)]
    dut.sbits_i.value = NULL()

    dut.ly_thresh_i.value = [[max(eta_thresh, id_thresh) for id_thresh in config.ly_thresh_patid] for eta_thresh in config.ly_thresh_eta]

    # flush the buffers
    for _ in range(256):
        await RisingEdge(dut.clock)

    # measure latency by putting some s-bits on a strip and waiting to see the output
    # subtract 3 to account for lc compression
    checkfn = lambda : dut.segments_o[0].lc.value.is_resolvable and \
        dut.segments_o[0].lc.value.integer >= config.ly_thresh_patid[dut.segments_o[0].id.value.integer - 1] - 3*(en_hc_compress)

    def setfn(dut, x):
        dut.sbits_i.value = [[x for _ in range(6)] for _ in range(NUM_PARTITIONS)]

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
                print(f"{loop}=")

            # (1) generate new random data
            # (2) push it onto the queue
            # (3) set the DUT inputs to the new data

            if test=="TRACKS":
                chamber_data = get_sbits_from_event(sbit_root[loop])

            queue.append(loop)
            dut.sbits_i.value = chamber_data
            loop += 1

        # pop old data on dav_o
        if dut.dav_o_phase.value == 0:

            # Get track output
            popped_iteration = queue.pop(0)

            track = track_root[popped_iteration]
            track_hits_prt_list, track_hits_strip_list = get_sbits_from_track(track)
            track_prt = track_hits_prt_list[3]
            track_strip = track_hits_strip_list[3]

            if (popped_iteration != 0):
                same = True
                params = ("trackInterceptX", "trackInterceptY", "trackSlopeX", "trackSlopeY")
                for param in params:
                    if last_track[param] != track[param]:
                        same = False
            else:
                same = False

            last_track = track

            # Get FW output
            fw_segments = get_segments_from_dut(dut)

            #Add 3 to the FW segments' layer count, to account for LC compression
            if (en_hc_compress):
                for segment in fw_segments:
                    if (segment.lc > 0):
                        segment.lc += 3
                        segment.update_quality()

            if verbose:
                print(f'{loop}=')
                for i in range(len(fw_segments)):
                    print("  > fw: " + str(fw_segments[i]))
                    print("  > track: Prt: " + str(track_prt) + " Strip: " + str(track_strip))

            err = "   "
            if loop > LATENCY+2:
                # Check if FW returned nothing, but SW returned something
                if (fw_segments[0].id == 0 and not same):
                    print(popped_iteration)
                    err = "ERR"
                    print(f" {err} seg {i}:")
                    print("   > track: Prt: " + str(track_prt) + " Strip: " + str(track_strip))
                    print("   > fw: No segments")
                    assert False
                # Check if FW returned something, but SW returned nothing
                elif (fw_segments[0].id != 0 and same):
                    print(popped_iteration)
                    err = "ERR"
                    print(f" {err} seg {i}:")
                    print("   > track: No segments")
                    print("   > fw: Prt: " + str(fw_segments[0].partition) + " Strip: " + str(fw_segments[0].strip))
                # Check if both FW and SW returned something, they are similar segments
                elif abs(track_strip - fw_segments[0].strip) > 10 or abs(track_prt - fw_segments[0].partition) > 3:
                    print(popped_iteration)
                    err = "ERR"
                    print(f" {err} seg {i}:")
                    print("   > track: Prt: " + str(track_prt) + " Strip: " + str(track_strip))
                    print("   > fw: Prt: " + str(fw_segments[0].partition) + " Strip: " + str(fw_segments[0].strip))
                    assert False

        await RisingEdge(dut.clock)

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
        os.path.join(rtl_dir, "x_prt_deghost_qual.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber_pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    parameters = {"DISABLE_PEAKING": True, "X_DEGHOST_EDGE_DIST" : 2}

    os.environ["SIM"] = "questa"
    
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
