#Testbench for pat_unit.vhd
import random
import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock
from datadev import datadev
from printly_dat import printly_dat
from pat_unit_beh import process_pat
from subfunc import*

@cocotb.test()
async def pat_unit_test(dut):
    random.seed(56)
    cnt_thresh=dut.THRESHOLD
    ly_t=6
    ly_spans=[int(dut.LY0_SPAN),int(dut.LY1_SPAN),int(dut.LY2_SPAN),int(dut.LY3_SPAN),int(dut.LY4_SPAN),int(dut.LY5_SPAN)]
    MAX_SPAN=max(ly_spans)
    agreement_ct=0
    i=0
    id_disagreement=0
    lc_disagreement=0
    lc_disagreement_cnt_t=0
    id_disagreement_cnt_t=0
    disagreement_vec_id=[]
    disagreement_vec_lc=[]
    cnt_thresh_idd=[]
    cnt_thresh_lcd=[]
    [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev(ly_t,MAX_SPAN)
    print('Testcase %d Original Data:' %i)
    printly_dat(data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x])
    ly0_x=ly0_x
    ly1_x=ly1_x
    ly2_x=ly2_x
    ly4_x=ly4_x
    ly5_x=ly5_x
    c=Clock(dut.clock,12,'ns')
    cocotb.fork(c.start())
    dut.dav_i<=0
    dut.ly0<=0
    dut.ly1<=0
    dut.ly2<=0
    dut.ly3<=0
    dut.ly4<=0
    dut.ly5<=0
    for j in range(10):
        await RisingEdge(dut.clock)
    for k in range(1001):
        await RisingEdge(dut.clock)
        dut.dav_i<=1
        dut.ly0<=ly0_x
        dut.ly1<=ly1_x
        dut.ly2<=ly2_x
        dut.ly3<=ly3_x
        dut.ly4<=ly4_x
        dut.ly5<=ly5_x
        [pat_id,ly_c]=process_pat(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN)
        for m in range(len(patlist)):
            if (patlist[m].id==pat_id):
                mask_v=get_ly_mask(patlist[m])
                print('Emulator Pattern Assignment:')
                printly_dat(data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x],mask=mask_v)
                print('\n')
        if (ly_c<cnt_thresh):
            pat_id=0
            ly_c=0
        await Timer(37,units='ns')
        for n in range(len(patlist)):
            if (patlist[n].id==dut.pat_o.id.value):
                mask_v=get_ly_mask(patlist[n])
                print('Pat_unit Pattern Assignment:')
                printly_dat(data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x],mask=mask_v)
                print('\n')
        print("Emulator Pat ID: %d" %pat_id)
        print("Pat_unit Pat ID: %d" %dut.pat_o.id.value)
        print('\n')
        print("Emulator Layer Count: %d" %ly_c)
        print("Pat_unit Layer Count: %d" %dut.pat_o.cnt.value)
        print('\n')
        if (pat_id!=dut.pat_o.id.value):
            id_disagreement=id_disagreement+1
            disagreement_vec_id.append(i)
        if (ly_c!=dut.pat_o.cnt.value):
            lc_disagreement=lc_disagreement+1
            disagreement_vec_lc.append(i)
        if (ly_c<cnt_thresh and dut.pat_o.id.value!=pat_id):
            id_disagreement_cnt_t=id_disagreement_cnt_t+1
            cnt_thresh_idd.append(i)
        if (ly_c<cnt_thresh and dut.pat_o.cnt.value!=ly_c):
            lc_disagreement_cnt_t=lc_disagreement_cnt_t+1
            cnt_thresh_lcd.append(i)
        if (ly_c>cnt_thresh and dut.pat_o.cnt.value==ly_c and dut.pat_o.id.value==pat_id):
            agreement_ct=agreement_ct+1
        id_dis=set(disagreement_vec_id)
        ct_dis=set(disagreement_vec_lc)
        id_dis_cntt=set(cnt_thresh_idd)
        ct_dis_cntt=set(cnt_thresh_lcd)
        true_id_dset=id_dis.difference(id_dis_cntt)
        true_lc_dset=ct_dis.difference(ct_dis_cntt)
        dut.dav_i<=0
        dut.ly0<=0
        dut.ly1<=0
        dut.ly2<=0
        dut.ly3<=0
        dut.ly4<=0
        dut.ly5<=0
        true_dis_id=id_disagreement-id_disagreement_cnt_t
        true_dis_lc=lc_disagreement-lc_disagreement_cnt_t
        print("In %d Testcases...\n" %i)
        print('%d Disagreements in ID' %id_disagreement)
        print('Indexes of ID disagreements: ' + str(disagreement_vec_id))
        print('\n\n')
        print('%d Disagreements in Layer Count' %lc_disagreement)
        print('Indexes of Layer Count disagreements: ' + str(disagreement_vec_lc))
        print('\n\n')
        print('%d ID disagreements from CNT_THRESH' %id_disagreement_cnt_t)
        print('%d Layer Count disagreements from CNT_THRESH' %lc_disagreement_cnt_t)
        print('\n\n')
        print(str(true_dis_id) + ' true disagreements in ID\n' + str(true_dis_lc) + ' true disagreements in Layer Count')
        print('Indexes of ID disagreements not caused by CNT_THRESH: '+str(true_id_dset))
        print('Indexes of Layer Count Disagreement not caused by CNT_THRESH: '+str(true_lc_dset))
        print('\n')
        print('The amount of agreements above the layer count is: %d' %agreement_ct)
        print('\n')
        i+=1
        [ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x]=datadev(ly_t,MAX_SPAN)
        print('Testcase %d Original Data:' %i)
        printly_dat(data=[ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x])
        for l in range(10):
            await RisingEdge(dut.clock)
    for z in range(1000):
        await RisingEdge(dut.clock)
