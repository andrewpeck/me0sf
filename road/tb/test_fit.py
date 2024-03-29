#!/usr/bin/env python3
import math
import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run


def fit_modified(x, y):

    x_sum = sum(x)
    y_sum = sum(y)
    n = len(x)

    products = 0
    squares = 0
    for i in range(len(x)):
        products += (n * x[i] - x_sum) * (n * y[i] - y_sum)
        squares += (n * x[i] - x_sum) ** 2

    m = 1.0 * products / squares
    b = 1.0 / n * (y_sum - m * x_sum)

    return m, b


def rand_y():

    rand_m = random.randint(math.floor(-37 / 6), math.floor(37 / 6))
    rand_b = random.randint(-5, 5)

    return [math.floor(rand_m * (0 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (1 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (2 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (3 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (4 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (5 - 2.5) + rand_b + random.randint(-1, 1))]

def print_slope(slope, intercept, key_strip, m, b, key_s):
    print("found y=%.3f x + %f (s=%f)" % (slope, intercept, key_strip))
    print("expec y=%.3f x + %f (s=%f)" % (m, b, key_s))
    print("\n")


@cocotb.test() # type: ignore
async def fit_tb(dut, NLOOPS=10000):
    """Test for priority encoder with randomized data on all inputs"""

    cocotb.start_soon(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    intercept_fracb = dut.B_FRAC_BITS.value
    slope_fracb = dut.M_FRAC_BITS.value
    strip_fracb = dut.STRIP_FRAC_BITS.value

    x = range(6)  # layers 0-5, always the same

    dut.valid_i.value = 0x3F

    # flush the pipeline
    dut.ly0.value = 1
    dut.ly1.value = 2
    dut.ly2.value = 3
    dut.ly3.value = 4
    dut.ly4.value = 5
    dut.ly5.value = 6

    LATENCY = dut.N_STAGES.value + 1

    for _ in range(LATENCY):
        await RisingEdge(dut.clock)

    data = []

    for _ in range(LATENCY - 1):

        y = rand_y()
        data.append(y)

        # plot line
        # plt.plot(x, y)
        # plt.show()

        (dut.ly0.value, dut.ly1.value, dut.ly2.value, dut.ly3.value, dut.ly4.value, dut.ly5.value) = y

        await RisingEdge(dut.clock)

    for iloop in range(NLOOPS):

        y = rand_y()

        dut.ly0.value = y[0]
        dut.ly1.value = y[1]
        dut.ly2.value = y[2]
        dut.ly3.value = y[3]
        dut.ly4.value = y[4]
        dut.ly5.value = y[5]

        data.append(y)

        await RisingEdge(dut.clock)  # Synchronize with the clock

        this_data = data.pop(0)
        m, b = fit_modified(x, this_data)

        # sfixed --> float
        slope = dut.slope_o.value.signed_integer / (2**slope_fracb - 1)

        intercept = dut.intercept_o.value.signed_integer / (2**intercept_fracb - 1)

        key_strip = dut.strip_o.value.signed_integer / (2**strip_fracb - 1)

        max_error_strips_per_layer = 0.2
        max_error_strips = 0.5
        max_error_intercept = 0.5

        # slope = round(slope, 1)
        # intercept = round(intercept, 1)
        # m = round(m, 1)
        # b = round(b, 1)

        # if (slope != m or intercept != b):
        #    print_slope(slope, intercept, m, b)

        key_s = m * 2.5 + b

        # print(this_data)
        # print_slope(slope, intercept, m, b)
        # print_slope(slope, intercept, key_strip, m, b, key_s)

        assert abs(b - intercept) < max_error_intercept, \
            print_slope(slope, intercept, key_strip, m, b, key_s)
        assert abs(m - slope) < max_error_strips_per_layer, \
            print_slope(slope, intercept, key_strip, m, b, key_s)
        assert abs(key_s - key_strip) < max_error_strips, \
            print_slope(slope, intercept, key_strip, m, b, key_s)

        if iloop % 1000 == 0:
            print("%d fits tested" % iloop)

    print("="*80)
    print("%d fits tested" % NLOOPS)
    print("="*80)


def test_fit():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [os.path.join(rtl_dir, "reciprocal.vhd"),
                    os.path.join(rtl_dir, "pipelined_mult.vhd"),
                    os.path.join(rtl_dir, "fit.vhd")]

    sim = "questa"
    os.environ["SIM"] = sim

    opts = []
    if sim == "ghdl":
        opts = ["--std=08"]
    if sim == "questa":
        opts = ["-2008"]

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=opts,
        toplevel="fit",  # top level HDL
        toplevel_lang="vhdl",
        # parameters=parameters,
        gui=0)


if __name__ == "__main__":
    test_fit()
