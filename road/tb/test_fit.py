#!/usr/bin/env python3
import math
import os
import random

from fxpmath import Fxp

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run
import apytypes as apy

from fxpmath import Fxp

def reciprocal6(x: int, nbits: int) -> Fxp:
    lut = {
        1: 1.0,
        2: 0.5,
        3: 1.0 / 3.0,
        4: 0.25,
        5: 0.2,
        6: 1.0 / 6.0
    }
    if x not in lut:
        print(f"WARNING: invalid reciprocal6 lookup x={x}")
        return Fxp(0.0, signed=True, n_word=nbits+1, n_frac=nbits, rounding='trunc')

    return Fxp(lut[x], signed=True, n_word=nbits+1, n_frac=nbits, rounding='trunc')


def vhdl_exact_fit(ly_vals, valid_mask):   
    cnt = max(sum(valid_mask), 1)
    
    # Stage 1: raw sums x_sum, y_sum (integers)
    x_sum = sum(i for i, v in enumerate(valid_mask) if v)
    y_sum = sum(ly_vals[i] for i, v in enumerate(valid_mask) if v)
    
    # Stage 2: n_x and n_y arrays
    n_x = [cnt * i if valid_mask[i] else 0 for i in range(6)]
    n_y = [cnt * ly_vals[i] if valid_mask[i] else 0 for i in range(6)]
    
    # Stage 3: x_diff and y_diff
    x_diff = [n_x[i] - x_sum if valid_mask[i] else 0 for i in range(6)]
    y_diff = [n_y[i] - y_sum if valid_mask[i] else 0 for i in range(6)]
    
    # Stage 4: product and square arrays
    product = [x_diff[i] * y_diff[i] for i in range(6)]
    square = [x_diff[i] * x_diff[i] for i in range(6)]

    # Stage 5: product_sum and square_sum, only sum those where valid_mask=1
    square_sum = 0
    product_sum= 0
    for i in range(6):
        if valid_mask[i]:
            product_sum += product[i]
            square_sum += square[i]
    
    # Stage 6: reciprocal of square_sum (sfixed(1 downto -13))
    if square_sum == 0:
        square_recip = Fxp(0, signed=True, n_word=15, n_frac=13, rounding='trunc')
    else:
        square_recip = Fxp(1.0 / square_sum, signed=True, n_word=15, n_frac=13, rounding='trunc')

    #product_sum_fx = Fxp(product_sum, signed=True, n_word=14, n_frac=0) 
    product_sum_fx = Fxp(product_sum, signed=True, n_word=15, n_frac=0) # After doubling resolution


    # Stage 7: slope_test = product_sum * square_recip (sfixed(15 downto -13))
    slope_test = Fxp(product_sum_fx * square_recip, signed=True, n_word=29, n_frac=13, rounding='trunc')
    
    # Stage 8: slope = resize slope_test to sfixed(3 downto -6)
    slope = Fxp(slope_test, signed=True, n_word=10, n_frac=6, rounding='trunc')
    
    # Stage 9: slope_mult = slope * x_sum_fixed (sfixed(5 downto 0))
    x_sum_fx = Fxp(x_sum, signed=True, n_word=15, n_frac=7, rounding='trunc')
    slope_mult = Fxp(slope * x_sum_fx, signed=True, n_word=16, n_frac=6, rounding='trunc')
    
    # Stage 10: slope_times_x = resize slope_mult to sfixed(7 downto -7)
    slope_times_x = Fxp(slope_mult, signed=True, n_word=15, n_frac=7, rounding='trunc')
    
    # Stage 11: intercept_mult = reciprocal(cnt) * (y_sum_fx - slope_times_x)
    
    #y_sum_fx = Fxp(y_sum, signed=True, n_word=15, n_frac=7, rounding='trunc')
    y_sum_fx = Fxp(y_sum, signed=True, n_word=16, n_frac=7, rounding='trunc') # After doubling resolution
    diff_fx = y_sum_fx - slope_times_x
    recip_fx = reciprocal6(cnt, 14)
    intercept_mult = Fxp(recip_fx * diff_fx, signed=True, n_word=32, n_frac=21, rounding='trunc')

    
    # Stage 12: intercept resize to sfixed(6 downto -8)
    #intercept = Fxp(intercept_mult, signed=True, n_word=15, n_frac=8, rounding='trunc')
    intercept = Fxp(intercept_mult, signed=True, n_word=16, n_frac=8, rounding='trunc') # After doubling resolution
    
    # Stage 13: slope * 5.0 (sfixed(7 downto -12))
    slope_5x = Fxp(slope.get_val() * 5.0, signed=True, n_word=20, n_frac=12, rounding='trunc')
    
    # Stage 14: slope_5x / 2.0 resize to sfixed(6 downto -8)
    slope_2p5 = Fxp(slope_5x.get_val() / 2.0, signed=True, n_word=15, n_frac=8, rounding='trunc')
    
    # Stage 15: strip_o = slope_2p5 + intercept (sfixed(6 downto -8))
    #strip_o = Fxp(slope_2p5.get_val() + intercept.get_val(), signed=True, n_word=15, n_frac=8, rounding='trunc')
    strip_o = Fxp(slope_2p5.get_val() + intercept.get_val(), signed=True, n_word=16, n_frac=8, rounding='trunc')  # After doubling resolution

    
    # Return all fxp values if you want to inspect intermediate fixed-point numbers later
    return slope, intercept, strip_o


#Perform a linear fit in the same way that it is performed in fit.vhd
def fit_modified(x, y):
    filtered = [(xi, yi) for xi, yi in zip(x, y) if not math.isnan(xi) and not math.isnan(yi)]
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
    m_fixed = apy.fx(m, int_bits=4, frac_bits=4)
    b = (y_sum - m * x_sum) / n
    b_fixed = apy.fx(b, int_bits=6, frac_bits=7)
    return m_fixed, b_fixed

#Random data to feed into the fitter
def rand_y():
    rand_m = random.randint(math.floor(-37 / 6), math.floor(37 / 6))
    #rand_b = random.randint(-5, 5)
    rand_b = random.randint(-10, 10)
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


@cocotb.test()
async def fit_tb(dut, NLOOPS=10000, verbose=False):
    """Test for priority encoder with randomized data on all inputs"""

    cocotb.start_soon(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    intercept_fracb = dut.B_FRAC_BITS.value
    slope_fracb = dut.M_FRAC_BITS.value
    strip_fracb = dut.STRIP_FRAC_BITS.value

    x = range(6)  # layers 0-5, always the same

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

    # Place dummy data into the queue, to account for the latency
    for _ in range(LATENCY - 1):
        y = rand_y()
        data.append([0, 0, 0, 0, 0, 0])

    failed_fits = 0
    failed_fits_intercept = 0
    failed_fits_strip = 0
    failed_fits_slope = 0

    for iloop in range(NLOOPS):

        # Set 5 or 6 layers valid (50% chance to 0 a random layer)
        if random.randint(0, 1) == 0: # Set all 6 layers valid
            valid_layers = 2**6 - 1 
        else: # Set a random layer to 0
            valid_layers = (2**6 - 1) ^ (2**random.randint(0, 5))

        dut.valid_i.value = valid_layers

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
        
        #Create random data, potentially with invalid layers
        valid_mask = [(dut.valid_i.value.integer >> i) & 1 for i in range(6)]
        masked_data = [v if valid else float('NaN') for v, valid in zip(this_data, valid_mask)]
        m, b, key_s = vhdl_exact_fit(this_data, valid_mask)

        slope = dut.slope_o.value.signed_integer / (2**slope_fracb)
        intercept = dut.intercept_o.value.signed_integer / (2**intercept_fracb)
        key_strip = dut.strip_o.value.signed_integer / (2**strip_fracb)

        #Define the maximum allowed discrepancy between python fit and fit.vhd
        max_error_slope = 0.65
        max_error_intercept = 2.0
        max_error_strips = max_error_intercept + max_error_slope

        if abs(b - intercept) >= max_error_intercept:
            print('FIT FAILED (intercept)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_intercept += 1

        elif abs(m - slope) >= max_error_slope:
            print('FIT FAILED (slope)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_slope += 1

        elif abs(key_s - key_strip) >= max_error_strips:
            print('FIT FAILED (strip)')
            print(f"{iloop=}")
            print(masked_data)
            print(valid_mask)
            print_slope(slope, intercept, key_strip, m, b, key_s)
            failed_fits += 1
            failed_fits_strip += 1

        elif verbose == True:
            print_slope(slope, intercept, key_strip, m, b, key_s)

        if iloop % 1000 == 0:
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

    run(vhdl_sources=vhdl_sources,
        module=module,
        compile_args=opts,
        toplevel="fit",
        toplevel_lang="vhdl",
        gui=0)

if __name__ == "__main__":
    test_fit()
