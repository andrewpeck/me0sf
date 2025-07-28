# Testbench for pat_unit.vhd
import os
import random
from typing import List

import cocotb
import plotille
from cocotb.triggers import RisingEdge
from cocotb_test.simulator import run

from constants import *
from datagen import datagen
from pat_unit_beh import pat_unit
from subfunc import *
from tb_common import *


@cocotb.test() # type: ignore
async def bram_0(dut):
    await bram_base(dut)   

async def bram_base(dut):

    c40 = Clock(dut.clock, 72, "ns")
    c160 = Clock(dut.clock, 18, "ns")
    c320 = Clock(dut.clock, 9, "ns")
    cocotb.start_soon(c40.start())
    cocotb.start_soon(c160.start())
    cocotb.start_soon(c320.start())

    dut.sbits_i.value = [[[0 for _ in range(192)] for _ in range(6)] for _ in range(15)]

    dut.wanted_strip.value = 0
    dut.wanted_prt.value = 0

    for i in range(100):
        print(dut.my_out.value)


def test_bram():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "pat_types.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "sbit_bram.vhd")]

    parameters = {}

    os.environ["SIM"] = "questa"

    run(vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="sbit_bram",  # top level HDL
        toplevel_lang="vhdl",
        # sim_args=["-do", '"set NumericStdNoWarnings 1;"'],
        parameters=parameters,
        gui=0)


if __name__ == "__main__":
    test_bram()
