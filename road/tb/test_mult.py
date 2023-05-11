#!/usr/bin/env python3
import os
import random
import math
import pytest

import cocotb
from cocotb_test.simulator import run
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def fit_mult(dut):
    """Test for priority encoder with randomized data on all inputs"""

    cocotb.fork(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    A = dut.WIDTH_A.value
    B = dut.WIDTH_B.value

    a_max = 2**(A - 1) - 1
    a_min = -a_max

    b_max = 2**(B - 1) - 1
    b_min = -b_max

    dut.input_a.value = 0
    dut.input_b.value = 0

    for _ in range(1000):
        a = random.randint(a_min, a_max)
        b = random.randint(b_min, b_max)
        dut.input_a.value = a
        dut.input_b.value = b
        await RisingEdge(dut.clock)
        await RisingEdge(dut.clock)
        await RisingEdge(dut.clock)
        await RisingEdge(dut.clock)
        assert dut.output.value.signed_integer == a * b
        print("a=%d, b=%d, out=%d, exp=%d" % (a, b, dut.output.value.signed_integer, a*b))


@pytest.mark.parametrize("A", [2, 4, 8, 9, 16])
@pytest.mark.parametrize("B", [2, 4, 8, 7, 13])
def test_fit(A, B):

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pipelined_mult.vhd"),
    ]

    sim = "questa"
    os.environ["SIM"] = sim

    opts = []
    if sim == "ghdl":
        opts = ["--std=08"]
    if sim == "questa":
        opts = ["-2008"]

    parameters = {}
    parameters['WIDTH_A'] = A
    parameters['WIDTH_B'] = B

    run(vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        compile_args=opts,
        toplevel="pipelined_smult",            # top level HDL
        toplevel_lang="vhdl",
        # parameters=parameters,
        gui=0)

if __name__ == "__main__":
    test_fit(8, 9)
