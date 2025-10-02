import os
from functools import reduce
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from tb_common import (generate_dav)

def setup(dut):
    c = Clock(dut.clock, 12, "ns")
    cocotb.start_soon(c.start())
   # cocotb.start_soon(generate_dav(dut))

@cocotb.test() # type: ignore
async def extract_test_random(dut, nloops=10000):
   await extract_test(dut, "RANDOM", nloops) 

#@cocotb.test() # type: ignore
#async def extract_test_custom(dut, nloops=10):
#   await extract_test(dut, "CUSTOM", nloops)

async def extract_test(dut, test, nloops=512, verbose=True):
    pat_los = [[eval("pat.ly"+str(j)+".lo.value", {}, {"pat" : pat}) for j in range(6)] for pat in dut.patlist] # Need to use eval since the FW has the pattern values stored as 6 signals labeled "ly0", "ly1", ...
    pat_los.reverse() # Reverse the list so index 16 is the straight pattern
    pat_his = [[eval("pat.ly"+str(j)+".hi.value", {}, {"pat" : pat}) for j in range(6)] for pat in dut.patlist]
    pat_his.reverse()

    pat_sbit_sizes = [[hi-lo+1 for hi, lo in zip(hi_lys, lo_lys)] for hi_lys, lo_lys in zip(pat_his, pat_los)]


    setup(dut)
    random.seed(1337)

    for _ in range(16):
        await RisingEdge(dut.clock)

    sbits_q = [[0 for _ in range(6)] for _ in range(2)]
    strip_q = [0, 0]
    pid_q = [17, 17]

    # loop over some number of test cases
    loop = 0
    for loop in range(nloops):
        if verbose:
            print("\n"+f"{loop=}")

        # Generate input data, and decide on which strip and PID to use
        if test=="RANDOM":
            sbit_window = [random.randint(0, 2**48-1) for _ in range(6)]
            sbits_q.append(sbit_window)

            strip = random.randint(0, 47) # Should be 0, 191
            strip_q.append(strip)

            pid = random.randint(1, 17)
            pid_q.append(pid)
        elif test=="CUSTOM":

            #sbit_window = [2**18 for _ in range(6)] # Straight segment centered on strip 0

            sbit_window = [(1+2+4+8+16+32), (2**7+2**8+2**9+2**10), (2**14+2**15+2**16), 0, 0, 0] if loop == 5 else [0 for _ in range(6)]# Matches widest pattern for lys 0,1,2 at rightmost sbits
            sbits_q.append(sbit_window)

            strip = 0
            strip_q.append(strip)

            pid = 3 if loop == 5 else 17
            pid_q.append(pid)
        else:
            raise Exception("Test not found")
        
        # Set FW values
        dut.window_i.value = sbit_window
        dut.wanted_strip_i.value = strip
        dut.wanted_PID_i.value = pid

        # Wait a clock
        await RisingEdge(dut.clock)

        # Get input values from previous clock, to find the expected output in SW
        sbit_window = sbits_q.pop(0)
        strip = strip_q.pop(0)
        pid = pid_q.pop(0)

        if verbose:
            print("sbit_window:")
            for i in range(6):
                print(format(sbit_window[i], "048b"))
            print(f"{strip=}")
            print(f"{pid=}")

        # Get patlist sizes and los
        pat_los = [[eval("pat.ly"+str(j)+".lo.value", {}, {"pat" : pat}) for j in range(6)] for pat in dut.patlist] # Need to use eval since the FW has the pattern values stored as 6 signals labeled "ly0", "ly1", ...
        pat_los.reverse() # Reverse the list so index 16 is the straight pattern
        pat_his = [[eval("pat.ly"+str(j)+".hi.value", {}, {"pat" : pat}) for j in range(6)] for pat in dut.patlist]
        pat_his.reverse()
    
        pat_sbit_sizes = [[hi-lo+1 for hi, lo in zip(hi_lys, lo_lys)] for hi_lys, lo_lys in zip(pat_his, pat_los)]

        # Extract bits with SW
        los_ly_list = pat_los[pid-1] # Subtract 1 from PID since the values index by 1 for now
        sw_bits = [0 for _ in range(6)]
        center = (strip % 12) + 18 # Indexes from right, by 0
        print("CENTER IN WINDOW: " + str(center))
        for ly in range(6):
            left_index = center - los_ly_list[ly]
            size = pat_sbit_sizes[pid-1][ly]
            mask = reduce(lambda x, y : x | y, [2**(left_index-i) for i in range(size)]) # Take SIZE bits, starting from left_index bit and going right
            sbits_not_zero_padded = format(mask & sbit_window[ly], "048b")[(47-left_index):(47-left_index+size)] # Apply mask and extract only the relevant bits
            sw_bits[ly] = "0"*(6-size) + sbits_not_zero_padded

        print(f"{sw_bits=}")
        # Find centroids in SW
        sw_centroids = []
        for sbit_ly in sw_bits:
            vals = [i if bit == '1' else 0 for i, bit in enumerate(sbit_ly[::-1])] # Iterate over bitstring from right to left
            num_ones = sum([1 if i == '1' else 0 for i in sbit_ly])
            sw_centroids.append(round(2/num_ones*sum(vals)+2) if '1' in sbit_ly else "NO HITS")

        # Find offsets in SW
        pat_his = [[eval("pat.ly"+str(j)+".hi.value", {}, {"pat" : pat}) for j in range(6)] for pat in dut.PATLIST] # Need to use eval since the FW has the pattern values stored as 6 signals labeled "ly0", "ly1", ...
        pat_his.reverse() # Reverse the list so index 16 is the straight pattern

        pat_offsets = []
        for pat_his_ly in pat_his:
            hi_max = max(pat_his_ly)
            pat_offsets.append([2*(hi_max-ly_hi) for ly_hi in pat_his_ly]) # Factor 2 for double resolution

        sw_centers = [int(sw_centroids[i] + pat_offsets[pid-1][i]) if sw_centroids[i] != "NO HITS" else "NO HITS" for i in range(6)]
        fw_centers = [v.value.integer for v in dut.centroids_offset]

        #print("FW OFFSETS: " + str([[j.value for j in i] for i in dut.offsets]))
        #print("SW OFFSETS: " + str(pat_offsets))
        #print("PID IN: " + str(dut.wanted_PID_i.value.integer))
        #print("PID BUFFER: " + str([v.value.integer if v.value.is_resolvable else "U" for v in dut.pid_buffer]))

        print(f"{sw_centroids=}")
        print(f"{sw_centers=}")
        print(f"{fw_centers=}")

        if loop > 2:
            for ly in range(6):
                assert sw_centers[ly] == fw_centers[ly] or sw_centers[ly] == "NO HITS"

        if verbose:
            print(f"{loop=}"+"\n")

def test_window_centroid():

    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "window_extract.vhd"),
        os.path.join(rtl_dir, "centroid_finder.vhd"),
        os.path.join(tests_dir, "window_centroid_combine.vhd")]

    os.environ["SIM"] = "questa"
    
    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="window_centroid",  # top level HDL
        toplevel_lang="vhdl",
        sim_args=["-suppress", "14408", "-do", "set NumericStdNoWarnings 1;"],
        parameters={},
        gui=0)

if __name__ == "__main__":
    test_window_centroid()
