# Testbenh for partition.vhd
import os
import random
import csv
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from numpy import partition
from datadev_mux import datadev_mux
from subfunc import *
from cocotb_test.simulator import run
from printly_dat import printly_dat
from partition_beh import work_partition
import time
from cocotb.triggers import Timer
from pat_unit_mux_beh import pat_mux


async def generate_dav(dut):
    "Generates a dav signal every 8th clock cycle"
    while True:
        dut.dav_i.value = 1
        await RisingEdge(dut.clock)
        dut.dav_i.value = 0
        for _ in range(7):
            await RisingEdge(dut.clock)


random.seed(56)


@cocotb.test()
async def partition_test(dut):
    "Test the partition.vhd module"
    group_size = 8
    ghost_width = 2
    discrepancy_cnt = 0
    N_LAYERS = 6

    MAX_SPAN = max(
        [
            dut.pat_unit_mux_inst.LY0_SPAN.value,
            dut.pat_unit_mux_inst.LY1_SPAN.value,
            dut.pat_unit_mux_inst.LY2_SPAN.value,
            dut.pat_unit_mux_inst.LY3_SPAN.value,
            dut.pat_unit_mux_inst.LY4_SPAN.value,
            dut.pat_unit_mux_inst.LY5_SPAN.value,
        ]
    )

    patlist = []
    for i in range(len(dut.pat_unit_mux_inst.PATLIST)):
        id = dut.pat_unit_mux_inst.PATLIST[i].id.value
        ly0_hi = dut.pat_unit_mux_inst.PATLIST[i].ly0.hi.value
        ly0_lo = dut.pat_unit_mux_inst.PATLIST[i].ly0.lo.value
        ly1_hi = dut.pat_unit_mux_inst.PATLIST[i].ly1.hi.value
        ly1_lo = dut.pat_unit_mux_inst.PATLIST[i].ly1.lo.value
        ly2_hi = dut.pat_unit_mux_inst.PATLIST[i].ly2.hi.value
        ly2_lo = dut.pat_unit_mux_inst.PATLIST[i].ly2.lo.value
        ly3_hi = dut.pat_unit_mux_inst.PATLIST[i].ly3.hi.value
        ly3_lo = dut.pat_unit_mux_inst.PATLIST[i].ly3.lo.value
        ly4_hi = dut.pat_unit_mux_inst.PATLIST[i].ly4.hi.value
        ly4_lo = dut.pat_unit_mux_inst.PATLIST[i].ly4.lo.value
        ly5_hi = dut.pat_unit_mux_inst.PATLIST[i].ly5.hi.value
        ly5_lo = dut.pat_unit_mux_inst.PATLIST[i].ly5.lo.value
        pat_o = patdef_t(
            id,
            hi_lo_t(ly0_hi, ly0_lo),
            hi_lo_t(ly1_hi, ly1_lo),
            hi_lo_t(ly2_hi, ly2_lo),
            hi_lo_t(ly3_hi, ly3_lo),
            hi_lo_t(ly4_hi, ly4_lo),
            hi_lo_t(ly5_hi, ly5_lo),
        )
        patlist.append(pat_o)

    # start the clock
    c = Clock(dut.clock, 12, "ns")
    cocotb.fork(c.start())

    # start the dav signal (high every 8th clock cycle)
    cocotb.fork(generate_dav(dut))

    for i in range(6):
        dut.partition_i[i].value = 0
        dut.neighbor_i[i].value = 0

    # expected_partition=dut.PARTITION_NUM
    for i in range(4):
        await RisingEdge(dut.dav_i)

    # set up a fixed latency queue
    latency = 2  # FIXME: input the actual latency value; not an exact clock cycle --> 1 dav or 8 clock cycles from the dav_i await above
    queue = []

    bad_strips = []
    bad_patterns = []
    bad_lyc = []
    partition_num = 0
    for j in range(latency):

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # if (j==1):
        chamber_data = datadev_mux(
            WIDTH=dut.pat_unit_mux_inst.WIDTH.value, track_num=4, nhit_hi=10, nhit_lo=3
        )
        # else:
        #     chamber_data = [0,0,0,0,0,0]

        queue.append(chamber_data)

        for i in range(6):
            dut.partition_i[i].value = chamber_data[i]

    for j in range(1000):

        print("Case %d" % j)

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data

        #     if (j==2):
        new_data = datadev_mux(
            WIDTH=dut.pat_unit_mux_inst.WIDTH.value, track_num=4, nhit_hi=10, nhit_lo=3
        )
        #     else:
        # new_data = [0,0,0,0,0,0]

        queue.append(new_data)

        for i in range(6):
            dut.partition_i[i].value = new_data[i]

        # set neighbor_i to 0 for now
        dut.neighbor_i[0].value = 0
        dut.neighbor_i[1].value = 0
        dut.neighbor_i[2].value = 0
        dut.neighbor_i[3].value = 0
        dut.neighbor_i[4].value = 0
        dut.neighbor_i[5].value = 0

        # latency equals 9 clock cycles

        # gather emulator output
        current_data = queue.pop(0)
        emulator_dat = work_partition(
            chamber_data=current_data,
            patlist=patlist,
            MAX_SPAN=MAX_SPAN,
            WIDTH=dut.pat_unit_mux_inst.WIDTH.value,
        )
        print("\n\n")
        printly_dat(data=current_data, MAX_SPAN=dut.pat_unit_mux_inst.WIDTH.value)
        print("\n\n")

        # set up the comparisons
        # list of [pat_id, ly_c, strip]

        for r in range(len(dut.segments_o)):

            # print ("segment %d" % r)

            firmware_id = dut.segments_o[r].strip.pattern.id.value
            emulator_id = emulator_dat[r][0]

            firmware_cnt = dut.segments_o[r].strip.pattern.cnt.value
            emulator_cnt = emulator_dat[r][1]

            firmware_strip = dut.segments_o[r].strip.strip.value
            emulator_strip = emulator_dat[r][2]

            # if (int(firmware_cnt) > 0):
            #     print('Case #%d'%j)
            #     print("=============================----------------------------------------------------")
            #     print("=============================----------------------------------------------------")
            # compare the partition id/cnt/strips
            if firmware_id != emulator_id:
                bad_patterns.append([j, r])
                print(
                    "  > emulator id = %d, simulator_id = %d"
                    % (emulator_id, firmware_id)
                )
            if firmware_cnt != emulator_cnt:
                bad_lyc.append([j, r])
                print(
                    "  > emulator cnt = %d, simulator_cnt = %d"
                    % (emulator_cnt, firmware_cnt)
                )
            if firmware_strip != emulator_strip:
                bad_strips.append([j, r])
                print(
                    "  > emulator strip = %d, simulator_strip = %d"
                    % (emulator_strip, firmware_strip)
                )

            if dut.segments_o[r].strip.pattern.id.value != emulator_dat[r][0]:
                bad_patterns.append([j, r])

            if dut.segments_o[r].strip.pattern.cnt.value != emulator_dat[r][1]:
                bad_lyc.append([j, r])

        if j == 2:  # check once that the PARTITION_NUM is the correct value
            for i in range(len(dut.segments_o)):
                assert partition_num == dut.segments_o[i].partition.value

        print("We have %d strip discrepancies" % (len(bad_strips)))
        print(bad_strips)
        print("\n\n")
        print("We have %d pattern discrepancies" % (len(bad_patterns)))
        print(bad_patterns)
        print("\n\n")
        print("We have %d lyc discrepancies" % (len(bad_lyc)))
        print(bad_lyc)
        print("\n\n")
        assert len(bad_strips) + len(bad_patterns) + (len(bad_lyc)) == 0, "Oh no"


def test_partition_1():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, "..", "hdl"))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
    ]

    parameters = {}
    parameters["MUX_FACTOR"] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,  # name of cocotb test module
        compile_args=["-2008"],
        toplevel="partition",  # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=0,
    )


if __name__ == "__main__":
    test_partition_1()
