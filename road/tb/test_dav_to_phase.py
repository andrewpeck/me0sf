#!/usr/bin/env python3

import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run


async def gen_dav(dut):
    "Generates a DAV signal every 8 clock cycles"
    while True:
        dut.dav.value = 1
        await RisingEdge(dut.clock)
        dut.dav.value = 0
        for _ in range(7):
            await RisingEdge(dut.clock)

async def phase_check(dut):

    "Check that the phase is as expected by monitoring the DAV signal."

    div = dut.DIV.value
    dly = dut.DLY.value
    max = dut.MAX.value
    cnt = 0

    # lock on
    for _ in range(16):

        await RisingEdge(dut.clock)

        if dut.dav == 1:
            cnt = 0
        elif cnt == max-1:
            cnt = 0
        else:
            cnt = cnt + 1

    while True:

        expect = ((cnt + dly) % 8)
        phase = dut.phase_o.value

        OK = "OK" if expect == phase else "BAD"
        print("DIV=%d DLY=%d CNT=%d, DAV=%d PHASE=%d (expect=%d) %s" % \
              (div, dly, cnt, dut.dav.value, phase, expect, OK))
        assert dut.phase_o.value == expect

        if cnt == max-1:
            cnt = 0
        else:
            cnt = cnt + 1

        await RisingEdge(dut.clock)



@cocotb.test()
async def dav_to_phase_test(dut):

    cocotb.start_soon(Clock(dut.clock, 20, units="ns").start())  # Create a clock
    cocotb.start_soon(gen_dav(dut))
    cocotb.start_soon(phase_check(dut))

    print("DIV=%d" % dut.DIV.value)
    print("=" * 80)

    for _ in range(128):
        await RisingEdge(dut.clock)

#@pytest.mark.parametrize("div", [1, 2, 4, 8])
#@pytest.mark.parametrize("dly", [0, 1, 4])
def test_dav_to_phase(div, dly):

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]
    print(f'{module=}')

    vhdl_sources = [os.path.join(rtl_dir, "dav_to_phase.vhd")]

    parameters = {}
    parameters["MAX"] = 8
    parameters["DIV"] = div
    parameters["DLY"] = dly

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        toplevel="dav_to_phase",            # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=0)


if __name__ == "__main__":
    # for dly in [0, 1, 4, 7]:
    #     for div in [1, 2, 4, 8]:
    #     #for div in [1]:
    #         test_dav_to_phase(div, dly)
    test_dav_to_phase(div=1, dly=0)
