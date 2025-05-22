# Testbench for chamber.vhd
# NOTES:
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
                       monitor_dav, setup, measure_latency)
#from get_sbits_from_root import (read_ntuple_stack, get_sbits_from_event)

#@cocotb.test() # type: ignore
#async def chamber_test_ff(dut, nloops=20):
#   await chamber_test(dut, "FF", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_5a(dut, nloops=20):
#   await chamber_test(dut, "5A", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_walking1(dut, nloops=191):
#   await chamber_test(dut, "WALKING1", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_walkingf(dut, nloops=192):
#   await chamber_test(dut, "WALKINGF", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_xprt(dut, nloops=100):
#   await chamber_test(dut, "XPRT", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_segs(dut, nloops=100):
#   await chamber_test(dut, "SEGMENTS", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_random(dut, nloops=100):
#    await chamber_test(dut, "RANDOM", nloops)
 
#@cocotb.test() # type: ignore
#async def chamber_test_deghost(dut, nloops=20):
#    await chamber_test(dut, "DEGHOST", nloops)   

#@cocotb.test() # type: ignore
#async def chamber_test_dat(dut, nloops=20):
#   await chamber_test(dut, "TEST_DAT", nloops)

#@cocotb.test() # type: ignore
#async def chamber_test_stack(dut, nloops=100):
#    await chamber_test(dut, "STACK_DAT", nloops)   

@cocotb.test() # type: ignore
async def chamber_test_stack(dut, nloops=30):
    await chamber_test(dut, "PEAKING", nloops)  
 
async def chamber_test(dut, test, nloops=512, verbose=True):

    '''
    Test the chamber.vhd module
    '''
    #random.seed(56) # chloe's favorite number

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
    config.cross_part_seg_width = dut.X_DEGHOST_EDGE_DIST.value # set to zero to disable x-partition deghosting
    config.disable_peaking = False

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

    LATENCY = ceil(meas_latency)-1    -1 #Peaking introduced this, need to investigate...

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

            if test=="WALKING1" or test=="WALKINGF":

                iprt = random.randint(0,7)

                if istrip == 191:
                    istrip = 0
                else:
                    istrip += 1

                dat = 0x1 if test=="WALKING1" else 0xffff

                chamber_data=NULL()
                chamber_data[iprt] = [(2**192-1) & (dat << istrip) for _ in range(6)]

            elif test=="SEGMENTS":
                chamber_data = [datagen(n_segs=2, n_noise=8, max_span=config.max_span)
                                for _ in range(NUM_PARTITIONS)]

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

            elif test=="FF" or test=="5A":

                chamber_data = NULL()

                iprt = (loop % 16) // 2

                if loop % 2 == 0:
                    if (test=="FF"):
                        dat = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    if (test=="5A"):
                        dat = 0x555555555555555555555555555555555555555555555555
                else:
                    if (test=="FF"):
                        dat = 0x000000000000000000000000000000000000000000000000
                    if (test=="5A"):
                        dat = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

                chamber_data[iprt] = [dat for _ in range(6)]

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
            elif test=="DEGHOST":

                chamber_data = NULL()

                #chamber_data[3] = [(2**192-1) & (2**184) for _ in range(6)]
                #The following creates a ghost
                # chamber_data[3][0] = (2**192-1) & (2**15)
                # chamber_data[3][1] = (2**192-1) & (2**15)
                # chamber_data[3][2] = (2**192-1) & (2**14)
                # chamber_data[3][4] = (2**192-1) & (2**17)
                # chamber_data[3][5] = (2**192-1) & (2**18)

                # chamber_data[1][0] = (2**192-1) & (2**10)
                # chamber_data[1][1] = (2**192-1) & (2**10)
                # chamber_data[0][2] = (2**192-1) & (2**10)
                # chamber_data[0][3] = (2**192-1) & (2**10)
                # chamber_data[0][4] = (2**192-1) & (2**12)
                # chamber_data[0][5] = (2**192-1) & (2**12)

                chamber_data[1][0] = (2**192-1) & (2**26)
                chamber_data[1][1] = (2**192-1) & (2**26)
                chamber_data[1][2] = (2**192-1) & (2**26)
                chamber_data[1][3] = (2**192-1) & (2**26)
                chamber_data[1][4] = (2**192-1) & (2**26)
                chamber_data[1][5] = (2**192-1) & (2**26)
            
            elif test=="TEST_DAT":

                #chamber_data = [[120527522816, 34493956200, 17179873280, 290816, 234881252, 30064771072], [67108864, 537395212, 2147487778, 25769803776, 103079739392, 266240], [12289, 34361573376, 92274688, 2684354688, 51759810560, 271581184], [256, 68920830080, 1073741824, 117473280, 553648128, 120259088640], [1711292416, 268468864, 15032389632, 129390215168, 17179869184, 103079215104], [2149580800, 1075839104, 38117867584, 3892314112, 1006637088, 163577856], [1073750017, 268566528, 3087007744, 234897408, 1835008, 4324329474], [6553600, 126648320, 16891912, 1610612736, 12885168128, 103146323996]]
                #chamber_data = [[15535702016, 805306368, 57998835840, 9663676416, 68853760016, 0], [57344, 393472, 98635776, 234881280, 536870912, 112742899712], [2149580832, 5398069248, 12398364672, 1811939328, 6190809088, 3758096384], [151126044, 3221225612, 2, 4294967822, 68719476800, 8589934592], [335544320, 3670036, 69236352, 2147485760, 3145728, 0], [1077940224, 117440512, 34360656900, 6442452992, 34762915856, 2149580800], [2156333056, 7405568, 25166344, 134234112, 805306368, 120309415968], [552600576, 26230800, 786944, 4152, 68719477120, 2621440]]
                zeros = [0]*6
                chamber_data = [zeros, zeros, zeros, [41484288, 1310720, 393440, 917536, 16973968, 17182064696], [34359738370, 16, 393228, 2097600, 50399232, 939982976], zeros, zeros, zeros] 
                
            elif test=="STACK_DAT":
                if (loop == 0):
                    if (os.path.exists("00001199.root")):
                        i_file_path = "00001199.root"
                    elif (os.path.exists("../00001199.root")):
                        i_file_path = "../00001199.root"
                    else:
                        raise Exception("Root file not found")

                    events = read_ntuple_stack(i_file_path)

                if (loop < len(events)):
                    event = events[loop]
                else:
                    print("Reached end of stack data file for given nloops. Repeating last entry.")
                    event = events[-1]

                chamber_data = get_sbits_from_event(event)
                
            
            elif test=="PEAKING":
                zeros = [0]*6
                if (loop < 10):
                    chamber_data = [[1]*6] + [zeros for _ in range(7)]
                else:
                    chamber_data = [zeros for _ in range(8)]
            else:
                chamber_data = NULL()

            queue.append(chamber_data)
            dut.sbits_i.value = chamber_data
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
                print(f'{loop}=')
                for i in range(len(fw_segments)):
                    print("  > fw: " + str(fw_segments[i]))
                    print("  > sw: " + str(sw_segments[i]))

            for i in range(max((len(sw_segments), len(fw_segments)))):

                if fw_segments[i].id > 0:
                    strip_cnts.append(fw_segments[i].strip)
                    id_cnts.append(fw_segments[i].id)
                    partition_cnts.append(fw_segments[i].partition)

                err = "   "
                if True:#loop > LATENCY+2:
                    if sw_segments[i] != fw_segments[i]:
                        print(popped_data)
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
        os.path.join(rtl_dir, "x_prt_deghost_qual.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber_pulse_extension.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    #parameters = {"PULSE_EXTEND": 1, "DEADTIME": 0, "DISABLE_PEAKING": True}
    parameters = {"DISABLE_PEAKING": False, "X_DEGHOST_EDGE_DIST" : 2}

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
