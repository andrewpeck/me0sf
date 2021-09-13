#!/usr/bin/env python3

import os

from cocotb_test.simulator import run

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random
import math

import matplotlib.pyplot as plt

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


def rand_y():

    rand_m = random.randint(math.floor(-37/6), math.floor(37/6))
    rand_b = random.randint(-5, 5)

    return [
        math.floor(rand_m * (0 - 2.5) + rand_b + random.randint(-1, 1)),
        math.floor(rand_m * (1 - 2.5) + rand_b + random.randint(-1, 1)),
        math.floor(rand_m * (2 - 2.5) + rand_b + random.randint(-1, 1)),
        math.floor(rand_m * (3 - 2.5) + rand_b + random.randint(-1, 1)),
        math.floor(rand_m * (4 - 2.5) + rand_b + random.randint(-1, 1)),
        math.floor(rand_m * (5 - 2.5) + rand_b + random.randint(-1, 1))]

    # return [random.randint(-15, 15),
    #         random.randint(-15, 15),
    #         random.randint(-15, 15),
    #         random.randint(-15, 15),
    #         random.randint(-15, 15),
    #         random.randint(-15, 15)]
    #return [1, 2, 3, 4, 5, 6]


def print_slope(slope, intercept, m, b):
    key_s = m*2.5 + b
    key_strip = slope*2.5 + b
    print("found y=%.3f x + %f (s=%f)" % (slope, intercept, key_strip))
    print("expec y=%.3f x + %f (s=%f)" % (m, b, key_s))
    print("\n")

@cocotb.test()
async def fit_tb(dut):
    """Test for priority encoder with randomized data on all inputs"""

    cocotb.fork(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    intercept_fracb = dut.B_FRAC_BITS.value
    slope_fracb = dut.M_FRAC_BITS.value

    x = range(6)  # layers 0-5, always the same

    dut.valid_i = 0x3f

    # flush the pipeline
    dut.ly0 = 1
    dut.ly1 = 2
    dut.ly2 = 3
    dut.ly3 = 4
    dut.ly4 = 5
    dut.ly5 = 6

    LATENCY = dut.N_STAGES.value+1

    for i in range(LATENCY):
        await RisingEdge(dut.clock)

    data = []

    itests = 0


    for i in range(LATENCY-1):

        y = rand_y()

        # plot line
        # plt.plot(x, y)
        # plt.show()

        data.append(y)

        dut.ly0 = y[0]
        dut.ly1 = y[1]
        dut.ly2 = y[2]
        dut.ly3 = y[3]
        dut.ly4 = y[4]
        dut.ly5 = y[5]

        await RisingEdge(dut.clock)  # Synchronize with the clock

    for i in range(10000):

        y = rand_y()

        dut.ly0 = y[0]
        dut.ly1 = y[1]
        dut.ly2 = y[2]
        dut.ly3 = y[3]
        dut.ly4 = y[4]
        dut.ly5 = y[5]

        data.append(y)

        await RisingEdge(dut.clock)  # Synchronize with the clock

        this_data = data.pop(0)
        m, b = fit_modified(x, this_data)

        # sfixed --> float
        slope = dut.slope_o.value.signed_integer / \
            (2**slope_fracb-1)

        intercept = dut.intercept_o.value.signed_integer / \
            (2**intercept_fracb-1)

        max_error_strips_per_layer = 0.5
        max_error_strips = 0.75

        # slope = round(slope, 1)
        # intercept = round(intercept, 1)
        # m = round(m, 1)
        # b = round(b, 1)

        #if (round(slope, 1) != round(m, 1) or round(intercept, 2) != round(b, 1)):

        # if (slope != m or intercept != b):
        #print_slope(slope, intercept, m, b)

        key_s = m*2.5 + b
        key_strip = slope*2.5 + b

        # print(this_data)

        assert (abs(m-slope) < max_error_strips_per_layer), print_slope(slope, intercept, m, b)
        assert (abs(key_s - key_strip) < max_error_strips), print_slope(slope, intercept, m, b)
        #assert (abs(b-intercept) < max_error_strips), print_slope(slope, intercept, m, b)

        itests += 1

    print("================================================================================")
    print("%d fits tested" % itests)
    print("================================================================================")


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
