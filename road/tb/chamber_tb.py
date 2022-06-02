#Testbench for chamber.vhd
import os
import random
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from numpy import partition
from datadev_mux import datadev_mux
from datadev_part import datadev_part
from subfunc import*
from cocotb_test.simulator import run
from printly_dat import printly_dat
from chamber_beh import work_chamber
from random import seed

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
async def chamber_test(dut):
    "Test the chamber.vhd module"
    group_size=8
    ghost_width=2
    discrepancy_cnt=0
    N_LAYERS=6

    MAX_SPAN = max([dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY0_SPAN.value,
                    dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY1_SPAN.value,
                    dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY2_SPAN.value,
                    dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY3_SPAN.value,
                    dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY4_SPAN.value,
                    dut.partition_gen[0].partition_inst.pat_unit_mux_inst.LY5_SPAN.value,])

    patlist = []
    for i in range(len(dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST)):
        id = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].id.value
        ly0_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly0.hi.value
        ly0_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly0.lo.value
        ly1_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly1.hi.value
        ly1_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly1.lo.value
        ly2_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly2.hi.value
        ly2_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly2.lo.value
        ly3_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly3.hi.value
        ly3_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly3.lo.value
        ly4_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly4.hi.value
        ly4_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly4.lo.value
        ly5_hi = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly5.hi.value
        ly5_lo = dut.partition_gen[0].partition_inst.pat_unit_mux_inst.PATLIST[i].ly5.lo.value
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

    #set seed
    random.seed(56)

    width=int(dut.partition_gen[0].partition_inst.pat_unit_mux_inst.WIDTH.value)
    num_partitions=int(dut.NUM_PARTITIONS.value)




    for i in range(8):
        for j in range(6):
            dut.sbits_i[i][j].value = 0


    # latency=1 #set back to 6
    queue=[]
    # for i in range(latency):
    #     await RisingEdge(dut.dav_i)
    #     chamber_data=[datadev_mux(WIDTH=width,track_num=4,nhit_hi=10,nhit_lo=3) for i in range(8)]
    #     queue.append(chamber_data)
    #     dut.sbits_i.value = chamber_data


    for j in range(1):

        print("Case %d" %  j)

        # align to the dav_i
        await RisingEdge(dut.dav_i)

        # (1) generate new random data
        # (2) push it onto the queue
        # (3) set the DUT inputs to the new data
        chamber_data=[datadev_mux(WIDTH=width,track_num=4,nhit_hi=10,nhit_lo=3) for i in range(8)]
        # chamber_data=[[0]*6]*8
        queue.append(chamber_data)

        dut.sbits_i.value = chamber_data

        #gather emulator output
        current_data=queue.pop(0)
        pat_ids=[]
        ly_cs=[]
        strips=[]
        partition_nums=[]
        print(int(dut.S0_WIDTH.value))
        print('the number of partitions is %d'%num_partitions)
        emulator_vals=work_chamber(chamber_data=current_data, patlist=patlist, NUM_PARTITIONS=num_partitions, MAX_SPAN=MAX_SPAN, WIDTH=width, group_width=int(dut.S0_WIDTH.value),ghost_width=4,NUM_VALS=int(dut.NUM_SEGMENTS))

        print(len(emulator_vals))
        print('emulator vals are: \n' +str(emulator_vals))
        for s in range(len(emulator_vals)):
            pat_ids.append(emulator_vals[s][0])
            ly_cs.append(emulator_vals[s][1])
            strips.append(emulator_vals[s][2])
            partition_nums.append(emulator_vals[s][3])

        print('Our firmware partition values are: \n')

        partition_firm=[]
        strip_firm=[]
        cnt_firm=[]
        id_firm=[]
        for i_partition in dut.segs:
            for i_strip in i_partition:
                partition_firm.append(i_strip.partition.value)
                strip_firm.append(i_strip.strip.strip.value)
                id_firm.append(i_strip.strip.pattern.id.value)
                cnt_firm.append(i_strip.strip.pattern.cnt.value)

        partition_flag=0
        strip_flag=0
        cnt_flag=0
        id_flag=0
        # for check in range(len(partition_firm)):
        #     if (partition_firm[check]!=partition_nums[check]):
        #         partition_flag=1
        #     if (strip_firm[check]!=strips[check]):
        #         strip_flag=1
        #     if (id_firm[check]!=pat_ids[check]):
        #         id_flag=1
        #     if (cnt_firm[check]!=ly_cs[check]):
        #         cnt_flag=1
        
        if (1 or partition_flag==1):
            print('Partition Numbers in Firmware Are: \n' +str(partition_firm))
            print('\n')
            print('Partition Numbers in Emulator Are: \n'+str(partition_nums))
        if (1 or strip_flag==1):
            print('Strips in Firmware Are: \n' +str(strip_firm))
            print('\n')
            print('Strips in Emulator Are: \n'+str(strips))
        if (1 or id_flag==1):
            print('Pat IDs in Firmware Are: \n' +str(id_firm))
            print('\n')
            print('Pat IDs in Emulator Are: \n'+str(pat_ids))
        if (1 or cnt_flag==1):
            print('Layer Counts in Firmware Are: \n' +str(cnt_firm))
            print('\n')
            print('Layer Counts in Emulator Are: \n'+str(ly_cs))
    

        for r in range(len(partition_nums)):
            # if (int(dut.segs_o[r].strip.strip.value)!=strips[r]):
            print('Difference in strips at index %d\n'%r)
            print('Firmware strip: %d'%int(dut.segs_o[r].strip.strip.value))
            print('Emulator strip: %d'%strips[r])

            # if (int(dut.segs_o[r].partition.value)!=partition_nums[r]):
            print('Difference in partition number at index %d\n'%r)
            print('Firmware partition number: %d'%int(dut.segs_o[r].partition.value))
            print('Emulator partition number: %d'%partition_nums[r])

            # if (int(dut.segs_o[r].strip.pattern.id.value)!=pat_ids[r]):
            print('Difference in pattern id at index %d\n'%r)
            print('Firmware pattern id: %d'%int(dut.segs_o[r].strip.pattern.id.value))
            print('Emulator pattern id: %d'%pat_ids[r])

            # if (int(dut.segs_o[r].strip.pattern.cnt.value)!=ly_cs[r]):
            print('Layer count at index %d\n'%r)
            print('Firmware layer count: %d'%int(dut.segs_o[r].strip.pattern.cnt.value))
            print('Emulator layer count: %d'%ly_cs[r])
            print('\n')
            print('\n')



def test_chamber_1():
    tests_dir = os.path.abspath(os.path.dirname(__file__))
    rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', 'hdl'))
    module = os.path.splitext(os.path.basename(__file__))[0]

    vhdl_sources = [
        os.path.join(rtl_dir, "priority_encoder/hdl/priority_encoder.vhd"),
        os.path.join(rtl_dir, "pat_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort_pkg.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/poc_bitonic_sort.vhd"),
        os.path.join(rtl_dir, "bitonic_sort/bitonic_sort.vhd"),
        os.path.join(rtl_dir, "patterns.vhd"),
        os.path.join(rtl_dir, "segment_selector.vhd"),
        os.path.join(rtl_dir, "pat_unit.vhd"),
        os.path.join(rtl_dir, "dav_to_phase.vhd"),
        os.path.join(rtl_dir, "pat_unit_mux.vhd"),
        os.path.join(rtl_dir, "partition.vhd"),
        os.path.join(rtl_dir, "chamber.vhd")]

    parameters = {}
    parameters['MUX_FACTOR'] = 8

    os.environ["SIM"] = "questa"

    run(
        vhdl_sources=vhdl_sources,
        module=module,       # name of cocotb test module
        compile_args=["-2008"],
        toplevel="chamber",   # top level HDL
        toplevel_lang="vhdl",
        parameters=parameters,
        gui=0
    )


if __name__ == "__main__":
    test_chamber_1()

