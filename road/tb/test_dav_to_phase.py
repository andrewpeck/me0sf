#!/usr/bin/env python3

import os

from cocotb_test.simulator import run

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random
import math
import pytest

def princ(string):
    print(string, end="")

async def gen_dav(dut):
    while True:
        dut.dav = 1
        await RisingEdge(dut.clock)
        dut.dav = 0
        for _ in range(7):
            await RisingEdge(dut.clock)

async def phase_check(dut):

    # lock on
    for _ in range(9):
        await RisingEdge(dut.clock)

    cnt = 0
    while True:
        await RisingEdge(dut.clock)

        cnt = cnt + 1

        if dut.dav.value == 1:
            cnt = 0
        if cnt == dut.MAX.value:
            cnt = 0

        expect = cnt // dut.DIV.value
        OK = "OK" if expect == dut.phase_o.value else "BAD"
        print("%d %d %s" % (dut.dav.value, dut.phase_o.value, OK))
        assert dut.phase_o.value == expect


@cocotb.test()
async def dav_to_phase_tb(dut):
    ""
    cocotb.fork(Clock(dut.clock, 20, units="ns").start())  # Create a clock
    cocotb.fork(gen_dav(dut))
    cocotb.fork(phase_check(dut))

    print("DIV=%d" % dut.DIV.value)
    print("=" * 80)

    for _ in range(40):
        await RisingEdge(dut.clock)

    #     dav = dut.dav.value
    #     phase = dut.phase_o.value

        # OK = "OK"
        # if (dut.DIV == 1):
        #     if (dav == 1 and phase != 0):
        #         assert False, "dav error with div0"
        #         OK = "BAD"

        # if (dut.DIV == 2):

        # if (dut.DIV == 4):

        # if (dut.DIV == 8):
        #     assert phase == 0

        # print("%d %d %s" % (dav, phase, OK))


@pytest.mark.parametrize("div", [1, 2, 4, 8])
def test_dav_to_phase(div):

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [os.path.join(rtl_dir, "dav_to_phase.vhd")]

    parameters = {}
    parameters["MAX"] = 8
    parameters["DIV"] = div

    os.environ["SIM"] = "ghdl"

    run(
        vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        toplevel="dav_to_phase",            # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=0
    )


if __name__ == "__main__":
    for div in [1, 2, 4, 8]:
        test_dav_to_phase(div)