from subfunc import *
from cocotb.triggers import RisingEdge
from constants import *

import cocotb
from cocotb.clock import Clock

from pat_unit_beh import calculate_global_layer_mask

def setup(dut):

    calculate_global_layer_mask(get_patlist_from_dut(dut))

    global LY_THRESH
    LY_THRESH = dut.THRESHOLD.value

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))


def get_segments_from_dut(dut):

    def convert_segment(segment):
        pid = segment.id.value.integer
        lyc = segment.cnt.value.integer
        strip = segment.strip.value
        seg = Segment(lyc, pid, strip=strip)
        return seg

    x = list(map(convert_segment, dut.segments_o))
    x.reverse()

    return x


def get_segment_from_dut(dut):
    lyc = int(dut.pat_o.cnt.value)
    pid = int(dut.pat_o.id.value)
    seg = Segment(lyc, pid, strip=0)
    return seg


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


def set_dut_inputs(dut, data):
    dut.ly0.value = data[0]
    dut.ly1.value = data[1]
    dut.ly2.value = data[2]
    dut.ly3.value = data[3]
    dut.ly4.value = data[4]
    dut.ly5.value = data[5]
