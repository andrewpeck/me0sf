import os
import random
import csv
import cocotb
from cocotb.triggers import RisingEdge
#from cocotb.triggers import Timer
from cocotb.clock import Clock
from datadev_mux import datadev_mux
from pat_unit_mux_beh import pat_mux
from subfunc import*
from cocotb_test.simulator import run
from printly_dat import printly_dat


async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i <= 1
        await RisingEdge(dut.clock)
        dut.dav_i <= 0
        for _ in range(7):
            await RisingEdge(dut.clock)


@cocotb.test()
async def pat_unit_mux_test(dut):
    "Test the pat_unix_mux.vhd module"

    # random.seed(56)
    disagreements_id = 0
    agreements_id = 0
    disagreement_indices_cnt = []
    disagreements_cnt = 0
    agreements_cnt = 0
    disagreement_indices_strip = []
    disagreements_strip = 0
    agreements_strip = 0
    total_disagreements = 0
    total_agreements = 0

    MAX_SPAN = max([dut.LY0_SPAN.value,
                    dut.LY1_SPAN.value,
                    dut.LY2_SPAN.value,
                    dut.LY3_SPAN.value,
                    dut.LY4_SPAN.value,
                    dut.LY5_SPAN.value,])

    # set patlist from firmware
    patlist = []
    for i in range(len(dut.PATLIST)):
        id = dut.PATLIST[i].id.value
        ly0_hi = dut.PATLIST[i].ly0.hi.value
        ly0_lo = dut.PATLIST[i].ly0.lo.value
        ly1_hi = dut.PATLIST[i].ly1.hi.value
        ly1_lo = dut.PATLIST[i].ly1.lo.value
        ly2_hi = dut.PATLIST[i].ly2.hi.value
        ly2_lo = dut.PATLIST[i].ly2.lo.value
        ly3_hi = dut.PATLIST[i].ly3.hi.value
        ly3_lo = dut.PATLIST[i].ly3.lo.value
        ly4_hi = dut.PATLIST[i].ly4.hi.value
        ly4_lo = dut.PATLIST[i].ly4.lo.value
        ly5_hi = dut.PATLIST[i].ly5.hi.value
        ly5_lo = dut.PATLIST[i].ly5.lo.value
        pat_o = patdef_t(
            id,
            hi_lo_t(ly0_hi, ly0_lo),
            hi_lo_t(ly1_hi, ly1_lo),
            hi_lo_t(ly2_hi, ly2_lo),
            hi_lo_t(ly3_hi, ly3_lo),
            hi_lo_t(ly4_hi, ly4_lo),
            hi_lo_t(ly5_hi, ly5_lo),
        )
        patlist.append(pat_o)

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))

    dut.ly0 <= 0
    dut.ly1 <= 0
    dut.ly2 <= 0
    dut.ly3 <= 0
    dut.ly4 <= 0
    dut.ly5 <= 0

    hit = 1 << 0
    [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x] = [hit]*6

    # datadev CHANGE ME AFTER WE FIX THE DATA SHIFT PROBLEM
    # [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev_mux(dut.WIDTH.value)
    # rewrite id and cnt discrepancies files at the start of each test bench run

    titles_iddiscrepancies = ['Testcase #', 'Strip',
                              'Parsed Data', 'Pat_unit_mux ID', 'Emulator ID']
    titles_cntdiscrepancies = ['Testcase #', 'Strip', 'Parsed Data',
                               'Pat_unit_mux CNT', 'Pat_unit_mux ID', 'Emulator CNT', 'Emulator ID']

    with open('../discrepancies_id.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(titles_iddiscrepancies)
        csv_file.close()

    with open('../discrepancies_cnt.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(titles_cntdiscrepancies)
        csv_file.close()

    # flush the pipeline for a few clocks
    for _ in range(10):
        await RisingEdge(dut.clock)

    # loop over some number of test cases
    for j in range(1000):

        # align to the dav_i
        while True:
            await RisingEdge(dut.clock)
            if dut.dav_i == 1:
                break

        print("Testcase %d:" % j)

        dut.ly0 <= ly0_x
        dut.ly1 <= ly1_x
        dut.ly2 <= ly2_x
        dut.ly3 <= ly3_x
        dut.ly4 <= ly4_x
        dut.ly5 <= ly5_x

        # keep the data high for 8 clock cycles, since we
        # are running on a 320MHz clock but the data is valid for 25ns
        for i in range(8):
            await RisingEdge(dut.clock)

        dut.ly0 <= 0
        dut.ly1 <= 0
        dut.ly2 <= 0
        dut.ly3 <= 0
        dut.ly4 <= 0
        dut.ly5 <= 0

        await RisingEdge(dut.clock)
        # pat_unit_inputs = [[], [], [], [], [], []]
        # for a in range(dut.WIDTH.value):
        #     pat_unit_inputs[0].append(dut.patgen[a].pat_unit_inst.ly0.value)
        #     pat_unit_inputs[1].append(dut.patgen[a].pat_unit_inst.ly1.value)
        #     pat_unit_inputs[2].append(dut.patgen[a].pat_unit_inst.ly2.value)
        #     pat_unit_inputs[3].append(dut.patgen[a].pat_unit_inst.ly3.value)
        #     pat_unit_inputs[4].append(dut.patgen[a].pat_unit_inst.ly4.value)
        #     pat_unit_inputs[5].append(dut.patgen[a].pat_unit_inst.ly5.value)

        [patterns, strips_data] = pat_mux(chamber_data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x],
                                          patlist=patlist,
                                          MAX_SPAN=MAX_SPAN,
                                          WIDTH=dut.WIDTH.value)
        print('\n\n')
        printly_dat(data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x], MAX_SPAN=dut.WIDTH.value)

        # wait for a few clocks for the data to go through the pipeline
        latency = 6
        for _ in range(latency-2):
            await RisingEdge(dut.clock)

        pat_dat_id_b = []
        pat_dat_id_t = []
        pat_dat_cnt_b = []
        pat_dat_cnt_t = []
        disagreement_id_vals_t = []
        disagreement_cnt_vals_t = []
        disagreement_id_vals_b = []
        disagreement_cnt_vals_b = []
        disagreement_indices_id = []
        # print warning if the data doesn't match
        emulator_vals = []
        hardware_vals = []

        # for a in range(dut.WIDTH.value):
        #   for b in range(6):
        #       if (int(pat_unit_inputs[b][a]) != strips_data[a][b]):
        #           print("Discrepancy in ly%d data at strip %d"%(b,a))
        #           print("Pat_unit_mux data: "+str(pat_unit_inputs[b][a]))
        #           print("Emulator data:     " +str(bin(strips_data[a][b])[2:].zfill(MAX_SPAN)))
        #   emulator_vals.append([bin(strips_data[a][0])[2:].zfill(MAX_SPAN), bin(strips_data[a][1])[2:].zfill(MAX_SPAN), bin(strips_data[a][2])[2:].zfill(MAX_SPAN), bin(strips_data[a][3])[2:].zfill(MAX_SPAN), bin(strips_data[a][4])[2:].zfill(MAX_SPAN), bin(strips_data[a][5])[2:].zfill(MAX_SPAN)])
        #   hardware_vals.append([, str(dut.patgen[a].pat_unit_inst.ly1.value), str(dut.patgen[a].pat_unit_inst.ly2.value), str(dut.patgen[a].pat_unit_inst.ly3.value), str(dut.patgen[a].pat_unit_inst.ly4.value), str(dut.patgen[a].pat_unit_inst.ly5.value)])
        #   print('\n\n')
        # print("These are the values:")
        # print('Hardware Values:')
        # print(hardware_vals)
        # print('\n\n')
        # print("Emulator Values:")
        # print(emulator_vals)

        for i in range(len(patterns)):

            patid = dut.strips_o[i].pattern.id.value
            cnt = dut.strips_o[i].pattern.cnt.value
            strip = dut.strips_o[i].strip.value

            if (patterns[i][0] != int(str(patid), 2)):
                disagreement_indices_id.append(strip)
                disagreement_id_vals_t.append(int(str(patid), 2))
                disagreement_id_vals_b.append(patterns[i][0])
                disagreements_id += 1
            else:
                agreements_id += 1

            if (patterns[i][1] != int(str(cnt), 2)):
                disagreement_indices_cnt.append(strip)
                disagreement_cnt_vals_t.append(int(str(cnt), 2))
                disagreement_cnt_vals_b.append(patterns[i][1])
                disagreements_cnt += 1
            else:
                agreements_cnt += 1

            pat_dat_id_b.append(patterns[i][0])
            pat_dat_id_t.append(int(str(patid), 2))
            pat_dat_cnt_b.append(patterns[i][1])
            pat_dat_cnt_t.append(int(str(cnt), 2))

        total_disagreements = total_disagreements + disagreements_id + disagreements_cnt
        total_agreements = total_agreements + agreements_id + agreements_cnt

        print("In %d testcases..." % j)
        print("Pat_unit_mux's Pattern ID's:\n" + str(pat_dat_id_t))
        print("\nEmulator's Pattern ID's:\n" + str(pat_dat_id_b))
        print('\n\n')
        print("Pat_unit_mux's Layer Counts:\n" + str(pat_dat_cnt_t))
        print("\nEmulator's Layer Counts:\n" + str(pat_dat_cnt_b))
        print('\n\n')
        print("Total disagreements: %d" % total_disagreements)
        print("Total agreements: %d" % total_agreements)
        print('\n\n')
        print("Total disagreements from Pattern ID: %d" % disagreements_id)
        print("Disagreement Indices from Pattern ID: " + str(disagreement_indices_id))
        print('\n\n')
        print("Total disagreements from Layer Count: %d"%disagreements_cnt)
        print("Disagreement Indices from  Layer Count: "+str(disagreement_indices_cnt))
        print('\n\n\n\n')

        # id_discrepancies_towrite=[]
        # cnt_discrepancies_towrite=[]
        # for p in range(len(disagreement_indices_id)):
        #     parsed_data=parse_chamber_dat(strip=disagreement_indices_id[p],chamber_data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x],WIDTH=dut.WIDTH.value,MAX_SPAN=MAX_SPAN)
        #     p_unit_mux_id=pat_dat_id_t[disagreement_indices_id[p]]
        #     emulator_id=pat_dat_id_b[disagreement_indices_id[p]]
        #     id_discrepancies_towrite.append([j,disagreement_indices_id[p],parsed_data,p_unit_mux_id,emulator_id])
        # for l in range(len(disagreement_indices_cnt)):
        #     parsed_data=parse_chamber_dat(strip=disagreement_indices_cnt[l],chamber_data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x],WIDTH=dut.WIDTH.value,MAX_SPAN=MAX_SPAN)
        #     p_unit_mux_cnt=pat_dat_cnt_t[disagreement_indices_cnt[l]]
        #     emulator_cnt=pat_dat_cnt_b[disagreement_indices_cnt[l]]
        #     p_unit_mux_id=pat_dat_id_t[disagreement_indices_cnt[l]]
        #     emulator_id=pat_dat_id_b[disagreement_indices_cnt[l]]
        #     cnt_discrepancies_towrite.append([j,disagreement_indices_cnt[l],parsed_data,p_unit_mux_cnt,p_unit_mux_id,emulator_cnt,emulator_id])
        # with open('../discrepancies_id.csv', 'a') as csv_file:
        #     csv_writer = csv.writer(csv_file)
        #     for i in range(len(id_discrepancies_towrite)):
        #         csv_writer.writerow(id_discrepancies_towrite[i])
        #     csv_file.close()
        # with open('../discrepancies_cnt.csv', 'a') as csv_file:
        #     csv_writer=csv.writer(csv_file)
        #     for j in range(len(cnt_discrepancies_towrite)):
        #         csv_writer.writerow(cnt_discrepancies_towrite[j])
        #     csv_file.close()
        # disagreement_indices_id=[]
        # pat_dat_id_b=[]
        # pat_dat_id_t=[]
        # pat_dat_cnt_b=[]
        # pat_dat_cnt_t=[]
        # datadev CHANGE ME AFTER WE FIX THE DATA SHIFT PROBLEM
        # [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev_mux(dut.WIDTH.value)

    for _ in range(1000):
        await RisingEdge(dut.clock)


def test_pat_unit_mux_1():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd")]

    parameters = {}
    parameters['MUX_FACTOR'] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit_mux",   # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=0
    )


if __name__ == "__main__":
    test_pat_unit_mux_1()
