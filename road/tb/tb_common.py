import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Edge, RisingEdge, Timer
from cocotb_test.simulator import run

from constants import *
from pat_unit_beh import calculate_global_layer_mask
from subfunc import *


def setup(dut, max_span=37):

    calculate_global_layer_mask(get_patlist_from_dut(dut), max_span)

    # set layer count threshold
    dut.ly_thresh_i.value = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.start_soon(generate_dav(dut))

def get_segments_from_dut(dut):

    def convert_segment(segment):
        lyc = segment.lc.value.integer
        pid = segment.id.value.integer
        if hasattr(segment, "strip"):
            strip = segment.strip.value.integer
        else:
            strip = 0
        if hasattr(segment, "partition"):
            partition = segment.partition.value.integer
        else:
            partition = 0
        seg = Segment(lc=lyc, id=pid, strip=strip, partition=partition)
        return seg

    segs = [convert_segment(x) for x in dut.segments_o]
    segs.reverse()

    return segs

async def measure_latency(dut, checkfn, setfn):

    #--------------------------------------------------------------------------------
    # Measure Latency
    #--------------------------------------------------------------------------------

    meas_latency=-1

    # align to the dav input
    await RisingEdge(dut.dav_i)
    for _ in range(8):
        await RisingEdge(dut.clock)

    # turn on the input for 1 clock cycle, then turn off
    setfn(dut, 1)
    for _ in range(8):
        await RisingEdge(dut.clock)
    setfn(dut, 0)

    # extract latency
    for i in range(128):
        await RisingEdge(dut.clock)
        if checkfn():
            meas_latency = i/8.0 + 3 # add magic number?? to account for the 1 bx latency to turn on and off above
            print(f"Latency={i} clocks ({meas_latency} bx)")
            break

    assert meas_latency != -1, \
        print("Couldn't measure pat_unit_mux latency. Never saw a pattern!")

    return meas_latency


def get_segment_from_pat_unit(dut):
    lc = int(dut.pat_o.lc.value)
    id = int(dut.pat_o.id.value)
    seg = Segment(lc=lc, id=id, strip=0, partition=0)
    return seg


async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i.value = 1
        #dut.clock40.value = 1
        await RisingEdge(dut.clock)
        dut.dav_i.value = 0
        #dut.clock40.value = 0
        for _ in range(7):
            await RisingEdge(dut.clock)

async def monitor_dav(dut):
    await RisingEdge(dut.dav_o)
    await RisingEdge(dut.dav_o)
    await RisingEdge(dut.dav_o)
    while True:
        await Edge(dut.segments_o)
        await Timer(1, units="ns")
        assert dut.dav_o == 1
        await RisingEdge(dut.clock)

        for i in range(7):
            await RisingEdge(dut.clock)
            assert dut.dav_o == 0, print(f"dav=1 in cycle {i}")

        await RisingEdge(dut.clock)
        assert dut.dav_o == 1

        break

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
            [hi_lo_t(ly0_hi, ly0_lo),
             hi_lo_t(ly1_hi, ly1_lo),
             hi_lo_t(ly2_hi, ly2_lo),
             hi_lo_t(ly3_hi, ly3_lo),
             hi_lo_t(ly4_hi, ly4_lo),
             hi_lo_t(ly5_hi, ly5_lo)])
        patlist.append(pat_o)
    return patlist


def get_max_span_from_dut(dut):
    ly_spans = [dut.LY0_SPAN.value,
                dut.LY1_SPAN.value,
                dut.LY2_SPAN.value,
                dut.LY3_SPAN.value,
                dut.LY4_SPAN.value,
                dut.LY5_SPAN.value]
    return max(ly_spans)


def set_dut_inputs(dut, data):
    dut.ly0.value = data[0]
    dut.ly1.value = data[1]
    dut.ly2.value = data[2]
    dut.ly3.value = data[3]
    dut.ly4.value = data[4]
    dut.ly5.value = data[5]
