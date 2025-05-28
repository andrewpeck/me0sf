#!/usr/bin/env python3
import math
import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run
from fixedpoint import FixedPoint

def fit_modified(x, y):
    filtered = [(xi, yi) for xi, yi in zip(x, y) if not math.isnan(xi) and not math.isnan(yi)]

    if not filtered:
        return float('nan'), float('nan')  # No valid data

    x_valid, y_valid = zip(*filtered)
    x_sum = sum(x_valid)
    y_sum = sum(y_valid)
    n = len(x_valid)

    products = 0
    squares = 0
    for i in range(n):
        xi = x_valid[i]
        yi = y_valid[i]
        products += (n * xi - x_sum) * (n * yi - y_sum)
        squares += (n * xi - x_sum) ** 2

    m = products / squares
    b = (y_sum - m * x_sum) / n

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

    #dut.valid_i.value = 0x3F

    # flush the pipeline
    dut.ly0.value = 1
    dut.ly1.value = 2
    dut.ly2.value = 3
    dut.ly3.value = 4
    dut.ly4.value = 5
    dut.ly5.value = 6

    LATENCY = dut.N_STAGES.value + 3 # Number of clock cycles that code takes to run

    for _ in range(LATENCY):
        await RisingEdge(dut.clock)

    data = []

    for _ in range(LATENCY - 1):
        y = rand_y()
        data.append(y)

        (dut.ly0.value, dut.ly1.value, dut.ly2.value, dut.ly3.value, dut.ly4.value, dut.ly5.value) = y

        await RisingEdge(dut.clock)
    failed_fits = 0
    failed_fits_intercept = 0
    failed_fits_strip = 0
    failed_fits_slope = 0

    for iloop in range(NLOOPS):

        valid_layers = sorted(random.sample(range(6), random.randint(5, 6)))
        dut.valid_i.value = sum(1 << i for i in valid_layers)

        y = rand_y()

        dut.ly0.value = y[0]
        dut.ly1.value = y[1]
        dut.ly2.value = y[2]
        dut.ly3.value = y[3]
        dut.ly4.value = y[4]
        dut.ly5.value = y[5]

        data.append(y)

        m, b = fit_modified(x, y)
        await RisingEdge(dut.clock)  # Synchronize with the clock

        this_data = data.pop(0)

        valid_mask = [(dut.valid_i.value.integer >> i) & 1 for i in range(6)]
        masked_data = [v if valid else float('NaN') for v, valid in zip(this_data, valid_mask)]
        masked_x = [v if valid else float('NaN') for v, valid in zip(x, valid_mask)]
        #m, b = fit_modified(x, this_data)
        m, b = fit_modified(masked_x, masked_data)

        slope = dut.slope_o.value.signed_integer / (2**slope_fracb - 1)
        intercept = dut.intercept_o.value.signed_integer / (2**intercept_fracb - 1)
        key_strip = dut.strip_o.value.signed_integer / (2**strip_fracb - 1)

        #max_error_slope = 0.5
        #max_error_intercept = 1.4
        key_s = m * 2.5 + b
        max_error_slope = 0.8
        max_error_intercept = 5
        max_error_strips = max_error_intercept + max_error_slope

        #errors = [
        #    abs(b - intercept) >= max_error_intercept,
        #    abs(m - slope) >= max_error_slope,
        #    abs(key_s - key_strip) >= max_error_strips
        #]

        if abs(b - intercept) >= max_error_intercept:
            print('FIT FAILED (intercept)')
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_intercept += 1
        elif abs(m - slope) >= max_error_slope:
            print('FIT FAILED (slope)')
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_slope += 1
        elif abs(key_s - key_strip) >= max_error_strips:
            print('FIT FAILED (strip)')
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_strip += 1

        if iloop % 1000 == 0:
        ##if iloop < 100:
            print("%d fits tested" % iloop)
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)

    print("="*80)
    print("%d fits tested" % NLOOPS)
    print("="*80)
    print("%d fits failed" % failed_fits)
    print("%d slope fits failed" % failed_fits_slope)
    print("%d intercept fits failed" % failed_fits_intercept)
    print("%d strip fits failed" % failed_fits_strip)


def test_fit():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]
    
    vhdl_sources = [os.path.join(rtl_dir, "reciprocal.vhd"),
                    os.path.join(rtl_dir, "pipelined_mult.vhd"),
                    os.path.join(rtl_dir, "pipelined_mult_check.vhd"),
                    os.path.join(rtl_dir, "fit.vhd")]


    sim = "questa"
    os.environ["SIM"] = sim

    opts = []
    if sim == "ghdl":
        opts = ["--std=08"]
    if sim == "questa":
        opts = ["-2008"]
    if sim == "xsim":
        opts = ["-2008"]


    run(vhdl_sources=vhdl_sources,
        module=module,
        compile_args=opts,
        toplevel="fit",
        toplevel_lang="vhdl",
        gui=0)


if __name__ == "__main__":
    test_fit()