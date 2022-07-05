# Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datadev import datadev
from pat_unit_beh import get_best_seg, calculate_global_layer_mask
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

def set_dut_inputs(dut, data):
    dut.ly0.value = data[0]
    dut.ly1.value = data[1]
    dut.ly2.value = data[2]
    dut.ly3.value = data[3]
    dut.ly4.value = data[4]
    dut.ly5.value = data[5]

def get_segment_from_dut(dut):
    lyc = int(dut.pat_o.cnt.value)
    pid =  int(dut.pat_o.id.value)
    seg = Segment(lyc, pid, strip=0)
    return seg

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
            [
                hi_lo_t(ly0_hi, ly0_lo),
                hi_lo_t(ly1_hi, ly1_lo),
                hi_lo_t(ly2_hi, ly2_lo),
                hi_lo_t(ly3_hi, ly3_lo),
                hi_lo_t(ly4_hi, ly4_lo),
                hi_lo_t(ly5_hi, ly5_lo),
            ],
        )
        patlist.append(pat_o)
    return patlist

def get_max_span_from_dut(dut):
    ly_spans = [
        dut.LY0_SPAN.value,
        dut.LY1_SPAN.value,
        dut.LY2_SPAN.value,
        dut.LY3_SPAN.value,
        dut.LY4_SPAN.value,
        dut.LY5_SPAN.value,
    ]
    return max(ly_spans)

@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)

    # set the amount of layers the muon traveled through
    ly_t = 6

    # get layer count threshold from firmware
    cnt_thresh = dut.THRESHOLD.value

    # set MAX_SPAN from firmware
    MAX_SPAN=get_max_span_from_dut(dut)

    # get patlist from firmware
    patlist = get_patlist_from_dut(dut)
    calculate_global_layer_mask(patlist)

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))

    # zero the inputs
    set_dut_inputs(dut, [0] * 6)

    # flush the buffer
    for _ in range(10):
        await RisingEdge(dut.clock)

    # setup the FIFO queuing to a fixed latency
    latency = 3
    queue = []
    for _ in range(latency):
        ly_data = datadev(ly_t, MAX_SPAN)
        queue.append(ly_data)
        set_dut_inputs(dut, ly_data)
        await RisingEdge(dut.clock)

    for _ in range(10000):

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        new_data = datadev(ly_t, MAX_SPAN)
        set_dut_inputs(dut, new_data)
        queue.append(new_data)

        # sync checks with the clock
        await RisingEdge(dut.clock)

        # (1) pop old data from the head of the queue
        # (2) run the emulator on the old data
        data = queue.pop(0)
        sw_segment = get_best_seg(data=data, strip=0, MAX_SPAN=MAX_SPAN)
        fw_segment = get_segment_from_dut(dut)

        # apply count threshold conditions to emulator pattern assignment
        # TODO: fold this into the segment finding
        if sw_segment.lc < cnt_thresh:
            sw_segment.id = 0
            sw_segment.lc = 0

        if (sw_segment != fw_segment):
            print("sw=%s" % sw_segment)
            print("fw=%s" % fw_segment)

        assert sw_segment == fw_segment

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
