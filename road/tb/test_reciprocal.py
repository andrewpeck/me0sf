import os

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.runner import get_runner, VHDL

from test_fit import reciprocal, fx

@cocotb.test()
async def reciprocal_tb(dut, NLOOPS=20, verbose=False):
    cocotb.start_soon(Clock(dut.clock, 20, units="ns").start())  # Create a clock

    dut.v_in.value = 1

    for _ in range(15):
        await RisingEdge(dut.clock)

    fail_array = []

    for i in range(2, 630+1+1):
        dut.v_in.value = i
        await RisingEdge(dut.clock)
        fw_val = dut.v_out.value.signed_integer / 2**13
        sw_val = fx(reciprocal(i-1), 13)
        print(f"FW value: {fw_val}")
        print(f"SW value: {sw_val}")
        print(f"Input value: {i-1}")
        if fw_val != sw_val:
            fail_array.append(i-1)

    print(f"Failed values: {fail_array}")

#Include all the paths and run the test
def test_reciprocal():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]
    
    vhdl_sources = [os.path.join(rtl_dir, "reciprocal.vhd"),
                    os.path.join(rtl_dir, "recip_test.vhd")]

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
        hdl_toplevel = "recip_test",
        always = True
    )

    runner.test(
        hdl_toplevel="recip_test",
        test_module="test_reciprocal",
        test_args=["-noautoldlibpath", "-no_autoacc"],
        pre_cmd = ["set NumericStdNoWarnings 1;"],
        gui = 0
    )

if __name__ == "__main__":
    test_reciprocal()
