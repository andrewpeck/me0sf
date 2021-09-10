#!/usr/bin/env python3

import os

from cocotb_test.simulator import run

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random

# import math
# import pytest
# from cocotb.triggers import Timer
# from cocotb.triggers import Event
# from cocotb.triggers import FallingEdge

# from https://github.com/cocotb/cocotb/blob/master/tests/test_cases/test_discovery/test_discovery.py
# @cocotb.test()
# async def recursive_discover(dut):
#     """Discover absolutely everything in the DUT"""
#     def _discover(obj):
#         for thing in obj:
#             dut._log.info("Found %s (%s)", thing._name, type(thing))
#             _discover(thing)
#     _discover(dut)

#  good example:
#  https://github.com/alexforencich/verilog-ethernet/blob/master/tb/ptp_clock_cdc/test_ptp_clock_cdc.py


def fit_modified(x, y):

    x_sum = sum(x)
    y_sum = sum(y)
    n = len(x)

    products = 0
    squares = 0
    for i in range(len(x)):
        products += (n*x[i]-x_sum)*(n*y[i]-y_sum)
        squares += (n*x[i]-x_sum)**2

    m = 1.0*products / squares
    b = 1.0/n * (y_sum - m * x_sum)

    return m, b


@cocotb.test()
async def fit_tb(dut):
    """Test for priority encoder with randomized data on all inputs"""

    cocotb.fork(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    data = [
        [1, 1, 1, 1, 1, 1],
        [0, 1, 2, 3, 4, 5],
        [0, 1, 2, 4, 5, 6],
        [0, 1, 3, 4, 5, 6]
        ]

    for i in range(1000):
        data.append([random.randint(-15, 15), random.randint(-15, 15),
                     random.randint(-15, 15), random.randint(-15, 15),
                     random.randint(-15, 15), random.randint(-15, 15)])

    intercept_fracb = dut.B_FRAC_BITS.value
    slope_fracb = dut.M_FRAC_BITS.value

    x = range(6)
    for y in data:

        dut.ly0 = y[0]
        dut.ly1 = y[1]
        dut.ly2 = y[2]
        dut.ly3 = y[3]
        dut.ly4 = y[4]
        dut.ly5 = y[5]

        dut.valid = 0x3f

        for i in range(11):
            await RisingEdge(dut.clock)  # Synchronize with the clock

        m, b = fit_modified(x, y)

        slope = dut.slope_o.value.signed_integer / (2**slope_fracb-1)
        intercept = dut.intercept_o.value.signed_integer / (2**intercept_fracb-1)

        print("found y=%f x + %f" % (slope, intercept))
        print("expec y=%f x + %f" % (m, b))

        max_error_strips_per_layer = 0.2
        max_error_strips = 0.5

        if (m > 0 and slope > 0):
            assert (abs(m-slope) < max_error_strips_per_layer),  "Slope error"
        if (b > 0 and intercept > 0):
            assert (abs(b-intercept) < max_error_strips), "Intercept error"


def test_fit():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, f"fit.vhd")
    ]

    run(
        vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        compile_args=["-2008"],
        toplevel="fit",            # top level HDL
        toplevel_lang="vhdl",
        # parameters=parameters,
        gui=0
    )


if __name__ == "__main__":
    test_fit()
