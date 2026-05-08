#!/usr/bin/env python3
import math
import numpy as np
import random
import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner, VHDL

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from fit_func import reciprocal, reciprocal6, vhdl_exact_fit, fx
from subfunc import llse_fit

def rand_y():
    rand_m = random.randint(math.floor(-37 / 6), math.floor(37 / 6))
    rand_b = random.randint(-10, 10)
    vals = [math.floor(rand_m * (0 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (1 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (2 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (3 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (4 - 2.5) + rand_b + random.randint(-1, 1)),
            math.floor(rand_m * (5 - 2.5) + rand_b + random.randint(-1, 1))]
    shift_vals = [val - min(min(vals), 0) for val in vals] # Ensure all values are positive
    return shift_vals

def print_slope(slope, intercept, key_strip, m, b, key_s):
    print("found y=%.3f x + %f (s=%f)" % (slope, intercept, key_strip))
    print("expec y=%.3f x + %f (s=%f)" % (m, b, key_s))
    print("\n")


@cocotb.test()
async def fit_tb(dut, NLOOPS=10000, verbose=False):
    """Test for priority encoder with randomized data on all inputs"""

    random.seed(1802148680)

    cocotb.start_soon(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    intercept_fracb = dut.B_FRAC_BITS.value
    slope_fracb = dut.M_FRAC_BITS.value
    strip_fracb = dut.STRIP_FRAC_BITS.value

    # flush the pipeline
    dut.ly0.value = 1
    dut.ly1.value = 2
    dut.ly2.value = 3
    dut.ly3.value = 4
    dut.ly4.value = 5
    dut.ly5.value = 6

    dut.valid_i.value = 0

    LATENCY = dut.N_STAGES.value # Number of clock cycles that it takes to run, as specified in fit.vhd (13 cycles)

    for _ in range(LATENCY):
        await RisingEdge(dut.clock)
    data = []
    valid_vector=[]

    # Place dummy data into the queue, to account for the latency
    for _ in range(LATENCY - 1):
        y = rand_y()
        data.append([0, 0, 0, 0, 0, 0])
        valid_vector.append(0)

    failed_fits = 0
    failed_fits_intercept = 0
    failed_fits_strip = 0
    failed_fits_slope = 0

    true_slopes = []
    slope_diffs = []

    true_strips = []
    strip_diffs = [] 

    for iloop in range(NLOOPS):
        if random.randint(0, 1) == 0: # Set all 6 layers valid
            valid_layers = 2**6 - 1 
        else: # Set a random layer to 0
            valid_layers = (2**6 - 1) ^ (2**random.randint(0, 5))
            valid_layers = valid_layers ^ (2**random.randint(0, 5))

        y = rand_y()

        dut.ly0.value = y[0]
        dut.ly1.value = y[1]
        dut.ly2.value = y[2]
        dut.ly3.value = y[3]
        dut.ly4.value = y[4]
        dut.ly5.value = y[5]
        dut.valid_i.value = valid_layers

        data.append(y)
        valid_vector.append(valid_layers)
        
        await RisingEdge(dut.clock)  # Synchronize with the clock
        v = valid_vector.pop(0)
        valid_mask = [(v >> i) & 1 for i in range(6)]

        this_data = data.pop(0)

        masked_data = [v if valid else float('NaN') for v, valid in zip(this_data, valid_mask)]
        m, b, key_s = vhdl_exact_fit(this_data, valid_mask)

        x = [i for (i, valid) in enumerate(valid_mask) if valid != 0] #need to improve for lc<6?

        if len(x) > 0:
            mllse, bllse, msellse = llse_fit(x, [v for v,valid in zip(this_data, valid_mask) if valid != 0])
            slope_diffs.append(m - mllse)
            strip_diffs.append(mllse*2.5 + bllse - key_s)
            true_slopes.append(mllse)
            true_strips.append(mllse*2.5 + bllse)

        slope = dut.slope_o.value.signed_integer / (2**slope_fracb)
        intercept = dut.intercept_o.value.signed_integer / (2**intercept_fracb)
        key_strip = dut.strip_o.value.signed_integer / (2**strip_fracb)
        
        #Define the maximum allowed discrepancy between python fit and fit.vhd
        max_error_slope = 0 #0.65
        max_error_intercept = 0 #2.0
        max_error_strips = max_error_intercept + max_error_slope

        if abs(b - intercept) > max_error_intercept:
            print('FIT FAILED (intercept)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_intercept += 1

        elif abs(m - slope) > max_error_slope:
            print('FIT FAILED (slope)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_slope += 1

        elif abs(key_s - key_strip) > max_error_strips:
            print('FIT FAILED (strip)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_strip += 1

        elif verbose == True:
            print_slope(slope, intercept, key_strip, m, b, key_s)

        if iloop % 500 == 0:
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


    print(f"Average slope error = {np.mean([abs(s) for s in slope_diffs])}")
    print(f"Average strip error = {np.mean([abs(s) for s in strip_diffs])}")

    plt.scatter(true_slopes, [abs(s) for s in slope_diffs], marker='.')
    plt.xlabel("LLSE Slope")
    plt.ylabel("Fit Error")
    plt.savefig("slope_plot.pdf")

    plt.clf()

    plt.scatter(true_strips, [abs(s) for s in strip_diffs], marker='.')
    plt.xlabel("LLSE Strip")
    plt.ylabel("Fit Error")
    plt.savefig("strip_plot.pdf")


#Include all the paths and run the test
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
    if sim == "xsim":
        opts = ["-2008"]

    sim_config = os.getenv("SIM", "questa")
    runner = get_runner(sim_config)

    runner.build(
        sources = vhdl_sources,
        build_args = [VHDL("-2008")],
        hdl_toplevel = "fit",
        always = True
    )

    runner.test(
        hdl_toplevel="fit",
        test_module="test_fit",
        test_args=["-noautoldlibpath", "-no_autoacc"],
        pre_cmd = ["set NumericStdNoWarnings 1;"],
        gui = 0
    )

#    run(vhdl_sources=vhdl_sources,
#        module=module,
#        compile_args=opts,
#        sim_args=["-noautoldlibpath"],
#        toplevel="fit",
#        toplevel_lang="vhdl",
#        gui=0)

if __name__ == "__main__":
    test_fit()
