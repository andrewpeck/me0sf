import os
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from cocotb_test.simulator import run
from datadev_mux import datadev_mux
from pat_unit_mux_beh import pat_mux
from subfunc import *


async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i.value = 1
        await RisingEdge(dut.clock)
        dut.dav_i.value = 0
        for _ in range(7):
            await RisingEdge(dut.clock)


def get_patlist_from_dut(dut):

    """set patlist from firmware"""

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
async def pat_unit_mux_test(dut):
    "Test the pat_unix_mux.vhd module"

    disagreements_id = 0
    agreements_id = 0
    # disagreement_indices_cnt = []
    disagreements_cnt = 0
    agreements_cnt = 0
    # disagreement_indices_strip = []
    # disagreements_strip = 0
    # agreements_strip = 0
    total_disagreements = 0
    total_agreements = 0

    MAX_SPAN = max(
        [
            dut.LY0_SPAN.value,
            dut.LY1_SPAN.value,
            dut.LY2_SPAN.value,
            dut.LY3_SPAN.value,
            dut.LY4_SPAN.value,
            dut.LY5_SPAN.value,
        ]
    )

    patlist = get_patlist_from_dut(dut)

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))

    set_layer_hits(dut, [0] * 6)

    # flush the pipeline for a few clocks
    for _ in range(10):
        await RisingEdge(dut.clock)

    # set up a fixed latency queue
    latency = 2
    width = dut.WIDTH.value
    queue = []

    for _ in range(latency):

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        ly_data = datadev_mux(width)
        queue.append(ly_data)

        set_layer_hits(dut, ly_data)

    # loop over some number of test cases
    NLOOPS = 1000
    for j in range(NLOOPS):

        if j % 100 == 0:
            print("%d loops completed..." % j)

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datadev_mux(width)
        queue.append(new_data)

        set_layer_hits(dut, new_data)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data

        patterns = pat_mux(
            chamber_data=queue.pop(0),
            patlist=patlist,
            MAX_SPAN=MAX_SPAN,
            WIDTH=dut.WIDTH.value,
        )

        # def princ(astring):
        #     print(astring, end="")

        for (i, pattern) in enumerate(patterns):

            # readout pat_unit_mux outputs from the simulator
            patid = dut.strips_o[i].pattern.id.value.integer
            cnt = dut.strips_o[i].pattern.cnt.value.integer
            # strip = dut.strips_o[i].strip.value

            if pattern[0] != patid:
                # disagreement_indices_id.append(strip)
                # disagreement_id_vals_t.append(patid)
                # disagreement_id_vals_b.append(pattern[0])
                disagreements_id += 1
            else:
                agreements_id += 1

            if pattern[1] != cnt:
                # disagreement_indices_cnt.append(strip)
                # disagreement_cnt_vals_t.append(cnt)
                # disagreement_cnt_vals_b.append(pattern[1])
                disagreements_cnt += 1
            else:
                agreements_cnt += 1

            # pat_dat_id_b.append(pattern[0])
            # pat_dat_id_t.append(patid)
            # pat_dat_cnt_b.append(pattern[1])
            # pat_dat_cnt_t.append(cnt)

        total_disagreements += disagreements_id + disagreements_cnt
        total_agreements += agreements_id + agreements_cnt

    print("In %d testcases..." % NLOOPS)
    print("Total disagreements: %d" % total_disagreements)
    # print('\n\n')
    print("Total disagreements from Pattern ID: %d" % disagreements_id)
    # print("Disagreement Indices from Pattern ID: " + str(disagreement_indices_id))
    # print('\n\n')
    print("Total disagreements from Layer Count: %d" % disagreements_cnt)
    # print("Disagreement Indices from  Layer Count: "+str(disagreement_indices_cnt))
    # print('\n\n\n\n')
    assert total_disagreements == 0


def test_pat_unit_mux():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="pat_unit_mux",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args = ['-do "set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_pat_unit_mux()
