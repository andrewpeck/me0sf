import os
import random
import csv
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datadev_mux import datadev_mux
from pat_unit_mux_beh import pat_mux
from subfunc import*
from cocotb_test.simulator import run
from printly_dat import printly_dat
from partition_beh import work_partition

async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i <= 1
        await RisingEdge(dut.clock)
        dut.dav_i <= 0
        for _ in range(7):
            await RisingEdge(dut.clock)

@cocotb.test()
async def partition_test(dut):
    "Test the partition.vhd module"
    group_size=8
    ghost_width=2

    #FIXME: find a way to set the MAX_SPAN from firmware; for now use var assignment
    MAX_SPAN=37

    # MAX_SPAN = max([dut.LY0_SPAN.value,
    #                 dut.LY1_SPAN.value,
    #                 dut.LY2_SPAN.value,
    #                 dut.LY3_SPAN.value,
    #                 dut.LY4_SPAN.value,
    #                 dut.LY5_SPAN.value,])

    # FIXME: find a way to set patlist from firmware; for now use subfunc def
    # patlist = []
    # for i in range(len(dut.PATLIST)):
    #     id = dut.PATLIST[i].id.value
    #     ly0_hi = dut.PATLIST[i].ly0.hi.value
    #     ly0_lo = dut.PATLIST[i].ly0.lo.value
    #     ly1_hi = dut.PATLIST[i].ly1.hi.value
    #     ly1_lo = dut.PATLIST[i].ly1.lo.value
    #     ly2_hi = dut.PATLIST[i].ly2.hi.value
    #     ly2_lo = dut.PATLIST[i].ly2.lo.value
    #     ly3_hi = dut.PATLIST[i].ly3.hi.value
    #     ly3_lo = dut.PATLIST[i].ly3.lo.value
    #     ly4_hi = dut.PATLIST[i].ly4.hi.value
    #     ly4_lo = dut.PATLIST[i].ly4.lo.value
    #     ly5_hi = dut.PATLIST[i].ly5.hi.value
    #     ly5_lo = dut.PATLIST[i].ly5.lo.value
    #     pat_o = patdef_t(
    #         id,
    #         hi_lo_t(ly0_hi, ly0_lo),
    #         hi_lo_t(ly1_hi, ly1_lo),
    #         hi_lo_t(ly2_hi, ly2_lo),
    #         hi_lo_t(ly3_hi, ly3_lo),
    #         hi_lo_t(ly4_hi, ly4_lo),
    #         hi_lo_t(ly5_hi, ly5_lo),
    #     )
    #     patlist.append(pat_o)

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))


    for j in range(5):
        [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev_mux(WIDTH=dut.PRT_WIDTH.value)
        dut.lyor[0] <= ly0_x
        dut.lyor[1] <= ly1_x
        dut.lyor[2] <= ly2_x
        dut.lyor[3] <= ly3_x
        dut.lyor[4] <= ly4_x
        dut.lyor[5] <= ly5_x

        #set up emulator check
        [patterns, strips_data]=pat_mux(chamber_data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x],patlist=patlist,MAX_SPAN=MAX_SPAN,WIDTH=dut.WIDTH.value)
        best_vals=work_partition(pat_mux_dat=patterns,group_size=group_size,ghost_width=ghost_width)



def test_partition_1():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd")]

    parameters = {}
    parameters['MUX_FACTOR'] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        compile_args=["-2008"],
        toplevel="partition",   # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=1
    )


if __name__ == "__main__":
    test_partition_1()

