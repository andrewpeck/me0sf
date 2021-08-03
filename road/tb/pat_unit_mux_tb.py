import random
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.triggers import Timer
from cocotb.clock import Clock
from datadev import datadev
from subfunc import*

@cocotb.test()
#NOTE: ONLY USING THIS STYLE FOR NOW TO GET A MEASURE OF LATENCY AND TO SEE WHEN I NEED TO GATHER DATA; WILL USE PYTEST.MARK.PARAMETERIZE LATER
async def pat_unit_mux_test(dut):
    random.seed(56)
    ly_t=6
    ly_spans = [
        dut.LY0_SPAN.value,
        dut.LY1_SPAN.value,
        dut.LY2_SPAN.value,
        dut.LY3_SPAN.value,
        dut.LY4_SPAN.value,
        dut.LY5_SPAN.value,
    ]
    MAX_SPAN = max(ly_spans)
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())
    dut.ly0<=0
    dut.ly1<=0
    dut.ly2<=0
    dut.ly3<=0
    dut.ly4<=0
    dut.ly5<=0
    [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev(ly_t,MAX_SPAN)
    for i in range(10):
        await RisingEdge(dut.clock)
    for j in range(1000):
        await RisingEdge(dut.clock)
        dut.dav_i <= 1
        dut.ly0 <= ly0_x
        dut.ly1 <= ly1_x
        dut.ly2 <= ly2_x
        dut.ly3 <= ly3_x
        dut.ly4 <= ly4_x
        dut.ly5 <= ly5_x
        #insert data acquisition and comparison here
        dut.dav_i <= 0
        dut.ly0 <= 0
        dut.ly1 <= 0
        dut.ly2 <= 0
        dut.ly3 <= 0
        dut.ly4 <= 0
        dut.ly5 <= 0
        #insert comments on the data found
        for l in range(10):
            await RisingEdge(dut.clock)
    for z in range(1000):
        await RisingEdge(dut.clock)
