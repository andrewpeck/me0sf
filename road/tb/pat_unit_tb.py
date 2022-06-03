# Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datadev import datadev
from printly_dat import printly_dat
from pat_unit_beh import process_pat
from subfunc import *
import os
from cocotb_test.simulator import run


async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i.value = 1
        await RisingEdge(dut.clock)
        dut.dav_i.value = 0
        for _ in range(7):
            await RisingEdge(dut.clock)


def get_patlist_from_dut(dut):
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
    return patlist


@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)
    # set the amount of layers the muon traveled through
    ly_t = 6
    # set layer count threshold from firmware
    cnt_thresh = dut.THRESHOLD.value
    # set MAX_SPAN from firmware
    ly_spans = [
        dut.LY0_SPAN.value,
        dut.LY1_SPAN.value,
        dut.LY2_SPAN.value,
        dut.LY3_SPAN.value,
        dut.LY4_SPAN.value,
        dut.LY5_SPAN.value,
    ]
    MAX_SPAN = max(ly_spans)
    # set patlist from firmware
    patlist = get_patlist_from_dut(dut)
    agreement_ct = 0
    i = 0
    id_disagreement = 0
    lc_disagreement = 0
    disagreement_vec_id = []
    disagreement_vec_lc = []
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())
    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))
    dut.dav_i.value = 0
    dut.ly0.value = 0
    dut.ly1.value = 0
    dut.ly2.value = 0
    dut.ly3.value = 0
    dut.ly4.value = 0
    dut.ly5.value = 0
    for j in range(10):
        await RisingEdge(dut.clock)

    # setup the FIFO queuing to a fixed latency
    latency = 3
    queue = []
    for _ in range(latency):

        ly_data = datadev(ly_t, MAX_SPAN)
        queue.append(ly_data)
        dut.ly0.value = ly_data[0]
        dut.ly1.value = ly_data[1]
        dut.ly2.value = ly_data[2]
        dut.ly3.value = ly_data[3]
        dut.ly4.value = ly_data[4]
        dut.ly5.value = ly_data[5]
        # align to the dav_i
        await RisingEdge(
            dut.clock
        )  # FIXME:try this out and then align with dav_i eventually

    for k in range(1000):
        dut.dav_i.value = 1

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datadev(ly_t, MAX_SPAN)
        dut.ly0.value = new_data[0]
        dut.ly1.value = new_data[1]
        dut.ly2.value = new_data[2]
        dut.ly3.value = new_data[3]
        dut.ly4.value = new_data[4]
        dut.ly5.value = new_data[5]
        queue.append(new_data)

        # sync checks with the clock
        await RisingEdge(dut.clock)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data
        [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x] = queue.pop(0)
        [pat_id, ly_c] = process_pat(
            patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN
        )

        # generate visual data from old data in queue
        print("Testcase %d Original Data:" % i)
        printly_dat(data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x], MAX_SPAN=MAX_SPAN)

        for m in range(len(patlist)):
            if patlist[m].id == pat_id:
                mask_v = get_ly_mask(patlist[m], MAX_SPAN)
                print("Emulator Pattern Assignment:")
                printly_dat(
                    data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x],
                    mask=mask_v,
                    MAX_SPAN=MAX_SPAN,
                )
                print("\n")

        # apply count threshold conditions to emulator pattern assignment
        if ly_c < cnt_thresh:
            pat_id = 0
            ly_c = 0

        for n in range(len(patlist)):
            if patlist[n].id == dut.pat_o.id.value:
                mask_v = get_ly_mask(patlist[n], MAX_SPAN)
                print("Pat_unit Pattern Assignment:")
                printly_dat(
                    data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x],
                    mask=mask_v,
                    MAX_SPAN=MAX_SPAN,
                )
                print("\n")
            if (n == len(patlist) - 1) and (patlist[n].id != dut.pat_o.id.value):
                print("Pat_unit ID not in Patlist")

        print("Emulator Pat ID: %d" % pat_id)
        print("Pat_unit Pat ID: %d" % dut.pat_o.id.value)
        print("\n")
        print("Emulator Layer Count: %d" % ly_c)
        print("Pat_unit Layer Count: %d" % dut.pat_o.cnt.value)
        print("\n")
        if pat_id != dut.pat_o.id.value:
            id_disagreement += 1
            disagreement_vec_id.append(i)
        if ly_c != dut.pat_o.cnt.value:
            lc_disagreement += 1
            disagreement_vec_lc.append(i)
        # keep a count for how many testcases pass the layer count threshold
        if (
            ly_c > cnt_thresh
            and dut.pat_o.cnt.value == ly_c
            and dut.pat_o.id.value == pat_id
        ):
            agreement_ct += 1

        print("In %d Testcases...\n" % (i + 1))
        print("%d Disagreements in ID" % id_disagreement)
        print("Testcase Indexes of ID Disagreements: " + str(disagreement_vec_id))
        print("\n\n")
        print("%d Disagreements in Layer Count" % lc_disagreement)
        print(
            "Testcase Indexes of Layer Count disagreements: " + str(disagreement_vec_lc)
        )
        print("\n\n")
        print("Amount of Agreements above the Layer Count: %d" % agreement_ct)
        print("\n")
        i += 1
        # await RisingEdge(dut.clock)

    for z in range(1000):
        await RisingEdge(dut.clock)


def test_pat_unit():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_pat_unit()
