from subfunc import*
patlist=[]
for i in range(len(dut.PATLIST)):
    id=dut.PATLIST[i].id.value
    ly0_hi=dut.PATLIST[i].ly0.hi.value
    ly0_lo=dut.PATLIST[i].ly0.lo.value
    ly1_hi=dut.PATLIST[i].ly1.hi.value
    ly1_lo=dut.PATLIST[i].ly1.lo.value
    ly2_hi=dut.PATLIST[i].ly2.hi.value
    ly2_lo=dut.PATLIST[i].ly2.lo.value
    ly3_hi=dut.PATLIST[i].ly3.hi.value
    ly3_lo=dut.PATLIST[i].ly3.lo.value
    ly4_hi=dut.PATLIST[i].ly4.hi.value
    ly4_lo=dut.PATLIST[i].ly4.lo.value
    ly5_hi=dut.PATLIST[i].ly5.hi.value
    ly5_lo=dut.PATLIST[i].ly5.lo.value
    pat_o=patdef_t(id,hi_lo_t(ly0_hi,ly0_lo),hi_lo_t(ly1_hi,ly1_lo),hi_lo_t(ly2_hi,ly2_lo),hi_lo_t(ly3_hi,ly3_lo),hi_lo_t(ly4_hi,ly4_lo),hi_lo_t(ly5_hi,ly5_lo))
    patlist.append(pat_o)
# pat_straight=patdef_t(dut.PATLIST[14].id.value,hi_lo_t(dut.PATLIST[14].ly0.hi.value,dut.PATLIST[14].ly0.lo.value),hi_lo_t(dut.PATLIST[14].ly1.hi.value,dut.PATLIST[14].ly1.lo.value),hi_lo_t(dut.PATLIST[14].ly2.hi.value,dut.PATLIST[14].ly2.lo.value),hi_lo_t(dut.PATLIST[14].ly3.hi.value,dut.PATLIST[14].ly3.lo.value),hi_lo_t(dut.PATLIST[14].ly4.hi.value,dut.PATLIST[14].ly4.lo.value),hi_lo_t(dut.PATLIST[14].ly5.hi.value,dut.PATLIST[14].ly5.lo.value))
# pat_l=patdef_t(dut.PATLIST[13].id.value,hi_lo_t(dut.PATLIST[13].ly0.hi.value,dut.PATLIST[13].ly0.lo.value),hi_lo_t(dut.PATLIST[13].ly1.hi.value,dut.PATLIST[13].ly1.lo.value),hi_lo_t(dut.PATLIST[13].ly2.hi.value,dut.PATLIST[13].ly2.lo.value),hi_lo_t(dut.PATLIST[13].ly3.hi.value,dut.PATLIST[13].ly3.lo.value),hi_lo_t(dut.PATLIST[13].ly4.hi.value,dut.PATLIST[13].ly4.lo.value),hi_lo_t(dut.PATLIST[13].ly5.hi.value,dut.PATLIST[13].ly5.lo.value))
# pat_r=mirror_patdef(pat_l,pat_l.id-1)
# pat_l2=patdef_t(dut.PATLIST[11].id.value,hi_lo_t(dut.PATLIST[11].ly0.hi.value,dut.PATLIST[11].ly0.lo.value),hi_lo_t(dut.PATLIST[11].ly1.hi.value,dut.PATLIST[11].ly1.lo.value),hi_lo_t(dut.PATLIST[11].ly2.hi.value,dut.PATLIST[11].ly2.lo.value),hi_lo_t(dut.PATLIST[11].ly3.hi.value,dut.PATLIST[11].ly3.lo.value),hi_lo_t(dut.PATLIST[11].ly4.hi.value,dut.PATLIST[11].ly4.lo.value),hi_lo_t(dut.PATLIST[11].ly5.hi.value,dut.PATLIST[11].ly5.lo.value))
# pat_r2=mirror_patdef(pat_l2,pat_l2.id-1)
# pat_l3=patdef_t(dut.PATLIST[9].id.value,hi_lo_t(dut.PATLIST[9].ly0.hi.value,dut.PATLIST[9].ly0.lo.value),hi_lo_t(dut.PATLIST[9].ly1.hi.value,dut.PATLIST[9].ly1.lo.value),hi_lo_t(dut.PATLIST[9].ly2.hi.value,dut.PATLIST[9].ly2.lo.value),hi_lo_t(dut.PATLIST[9].ly3.hi.value,dut.PATLIST[9].ly3.lo.value),hi_lo_t(dut.PATLIST[9].ly4.hi.value,dut.PATLIST[9].ly4.lo.value),hi_lo_t(dut.PATLIST[9].ly5.hi.value,dut.PATLIST[9].ly5.lo.value))
# pat_r3=mirror_patdef(pat_l3,pat_l3.id-1)
# pat_l4=patdef_t(dut.PATLIST[7].id.value,hi_lo_t(dut.PATLIST[7].ly0.hi.value,dut.PATLIST[7].ly0.lo.value),hi_lo_t(dut.PATLIST[7].ly1.hi.value,dut.PATLIST[7].ly1.lo.value),hi_lo_t(dut.PATLIST[7].ly2.hi.value,dut.PATLIST[7].ly2.lo.value),hi_lo_t(dut.PATLIST[7].ly3.hi.value,dut.PATLIST[7].ly3.lo.value),hi_lo_t(dut.PATLIST[7].ly4.hi.value,dut.PATLIST[7].ly4.lo.value),hi_lo_t(dut.PATLIST[7].ly5.hi.value,dut.PATLIST[7].ly5.lo.value))
# pat_r4=mirror_patdef(pat_l4,pat_l4.id-1)
# pat_l5=patdef_t(dut.PATLIST[5].id.value,hi_lo_t(dut.PATLIST[5].ly0.hi.value,dut.PATLIST[5].ly0.lo.value),hi_lo_t(dut.PATLIST[5].ly1.hi.value,dut.PATLIST[5].ly1.lo.value),hi_lo_t(dut.PATLIST[5].ly2.hi.value,dut.PATLIST[5].ly2.lo.value),hi_lo_t(dut.PATLIST[5].ly3.hi.value,dut.PATLIST[5].ly3.lo.value),hi_lo_t(dut.PATLIST[5].ly4.hi.value,dut.PATLIST[5].ly4.lo.value),hi_lo_t(dut.PATLIST[5].ly5.hi.value,dut.PATLIST[5].ly5.lo.value))
# pat_r5=mirror_patdef(pat_l5,pat_l5.id-1)
# pat_l6=patdef_t(dut.PATLIST[3].id.value,hi_lo_t(dut.PATLIST[3].ly0.hi.value,dut.PATLIST[3].ly0.lo.value),hi_lo_t(dut.PATLIST[3].ly1.hi.value,dut.PATLIST[3].ly1.lo.value),hi_lo_t(dut.PATLIST[3].ly2.hi.value,dut.PATLIST[3].ly2.lo.value),hi_lo_t(dut.PATLIST[3].ly3.hi.value,dut.PATLIST[3].ly3.lo.value),hi_lo_t(dut.PATLIST[3].ly4.hi.value,dut.PATLIST[3].ly4.lo.value),hi_lo_t(dut.PATLIST[3].ly5.hi.value,dut.PATLIST[3].ly5.lo.value))
# pat_r6=mirror_patdef(pat_l6,pat_l6.id-1)
# pat_l7=patdef_t(dut.PATLIST[1].id.value,hi_lo_t(dut.PATLIST[1].ly0.hi.value,dut.PATLIST[1].ly0.lo.value),hi_lo_t(dut.PATLIST[1].ly1.hi.value,dut.PATLIST[1].ly1.lo.value),hi_lo_t(dut.PATLIST[1].ly2.hi.value,dut.PATLIST[1].ly2.lo.value),hi_lo_t(dut.PATLIST[1].ly3.hi.value,dut.PATLIST[1].ly3.lo.value),hi_lo_t(dut.PATLIST[1].ly4.hi.value,dut.PATLIST[1].ly4.lo.value),hi_lo_t(dut.PATLIST[1].ly5.hi.value,dut.PATLIST[1].ly5.lo.value))
# pat_r7=mirror_patdef(pat_l7,pat_l7.id-1)

#keep me
# pat_straight=patdef_t(dut.PATLIST(14).id.value,hi_lo_t(dut.PATLIST(14).ly0.hi.value,dut.PATLIST(14).ly0.lo.value),hi_lo_t(dut.PATLIST(14).ly1.hi.value,dut.PATLIST(14).ly1.lo.value),hi_lo_t(dut.PATLIST(14).ly2.hi.value,dut.PATLIST(14).ly2.lo.value),hi_lo_t(dut.PATLIST(14).ly3.hi.value,dut.PATLIST(14).ly3.lo.value),hi_lo_t(dut.PATLIST(14).ly4.hi.value,dut.PATLIST(14).ly4.lo.value),hi_lo_t(dut.PATLIST(14).ly5.hi.value,dut.PATLIST(14).ly5.lo.value))
# pat_l=patdef_t(dut.PATLIST(13).id.value,hi_lo_t(dut.PATLIST(13).ly0.hi.value,dut.PATLIST(13).ly0.lo.value),hi_lo_t(dut.PATLIST(13).ly1.hi.value,dut.PATLIST(13).ly1.lo.value),hi_lo_t(dut.PATLIST(13).ly2.hi.value,dut.PATLIST(13).ly2.lo.value),hi_lo_t(dut.PATLIST(13).ly3.hi.value,dut.PATLIST(13).ly3.lo.value),hi_lo_t(dut.PATLIST(13).ly4.hi.value,dut.PATLIST(13).ly4.lo.value),hi_lo_t(dut.PATLIST(13).ly5.hi.value,dut.PATLIST(13).ly5.lo.value))
# pat_r=mirror_patdef(pat_l,pat_l.id-1)
# pat_l2=patdef_t(dut.PATLIST(11).id.value,hi_lo_t(dut.PATLIST(11).ly0.hi.value,dut.PATLIST(11).ly0.lo.value),hi_lo_t(dut.PATLIST(11).ly1.hi.value,dut.PATLIST(11).ly1.lo.value),hi_lo_t(dut.PATLIST(11).ly2.hi.value,dut.PATLIST(11).ly2.lo.value),hi_lo_t(dut.PATLIST(11).ly3.hi.value,dut.PATLIST(11).ly3.lo.value),hi_lo_t(dut.PATLIST(11).ly4.hi.value,dut.PATLIST(11).ly4.lo.value),hi_lo_t(dut.PATLIST(11).ly5.hi.value,dut.PATLIST(11).ly5.lo.value))
# pat_r2=mirror_patdef(pat_l2,pat_l2.id-1)
# pat_l3=patdef_t(dut.PATLIST(9).id.value,hi_lo_t(dut.PATLIST(9).ly0.hi.value,dut.PATLIST(9).ly0.lo.value),hi_lo_t(dut.PATLIST(9).ly1.hi.value,dut.PATLIST(9).ly1.lo.value),hi_lo_t(dut.PATLIST(9).ly2.hi.value,dut.PATLIST(9).ly2.lo.value),hi_lo_t(dut.PATLIST(9).ly3.hi.value,dut.PATLIST(9).ly3.lo.value),hi_lo_t(dut.PATLIST(9).ly4.hi.value,dut.PATLIST(9).ly4.lo.value),hi_lo_t(dut.PATLIST(9).ly5.hi.value,dut.PATLIST(9).ly5.lo.value))
# pat_r3=mirror_patdef(pat_l3,pat_l3.id-1)
# pat_l4=patdef_t(dut.PATLIST(7).id.value,hi_lo_t(dut.PATLIST(7).ly0.hi.value,dut.PATLIST(7).ly0.lo.value),hi_lo_t(dut.PATLIST(7).ly1.hi.value,dut.PATLIST(7).ly1.lo.value),hi_lo_t(dut.PATLIST(7).ly2.hi.value,dut.PATLIST(7).ly2.lo.value),hi_lo_t(dut.PATLIST(7).ly3.hi.value,dut.PATLIST(7).ly3.lo.value),hi_lo_t(dut.PATLIST(7).ly4.hi.value,dut.PATLIST(7).ly4.lo.value),hi_lo_t(dut.PATLIST(7).ly5.hi.value,dut.PATLIST(7).ly5.lo.value))
# pat_r4=mirror_patdef(pat_l4,pat_l4.id-1)
# pat_l5=patdef_t(dut.PATLIST(5).id.value,hi_lo_t(dut.PATLIST(5).ly0.hi.value,dut.PATLIST(5).ly0.lo.value),hi_lo_t(dut.PATLIST(5).ly1.hi.value,dut.PATLIST(5).ly1.lo.value),hi_lo_t(dut.PATLIST(5).ly2.hi.value,dut.PATLIST(5).ly2.lo.value),hi_lo_t(dut.PATLIST(5).ly3.hi.value,dut.PATLIST(5).ly3.lo.value),hi_lo_t(dut.PATLIST(5).ly4.hi.value,dut.PATLIST(5).ly4.lo.value),hi_lo_t(dut.PATLIST(5).ly5.hi.value,dut.PATLIST(5).ly5.lo.value))
# pat_r5=mirror_patdef(pat_l5,pat_l5.id-1)
# pat_l6=patdef_t(dut.PATLIST(3).id.value,hi_lo_t(dut.PATLIST(3).ly0.hi.value,dut.PATLIST(3).ly0.lo.value),hi_lo_t(dut.PATLIST(3).ly1.hi.value,dut.PATLIST(3).ly1.lo.value),hi_lo_t(dut.PATLIST(3).ly2.hi.value,dut.PATLIST(3).ly2.lo.value),hi_lo_t(dut.PATLIST(3).ly3.hi.value,dut.PATLIST(3).ly3.lo.value),hi_lo_t(dut.PATLIST(3).ly4.hi.value,dut.PATLIST(3).ly4.lo.value),hi_lo_t(dut.PATLIST(3).ly5.hi.value,dut.PATLIST(3).ly5.lo.value))
# pat_r6=mirror_patdef(pat_l6,pat_l6.id-1)
# pat_l7=patdef_t(dut.PATLIST(1).id.value,hi_lo_t(dut.PATLIST(1).ly0.hi.value,dut.PATLIST(1).ly0.lo.value),hi_lo_t(dut.PATLIST(1).ly1.hi.value,dut.PATLIST(1).ly1.lo.value),hi_lo_t(dut.PATLIST(1).ly2.hi.value,dut.PATLIST(1).ly2.lo.value),hi_lo_t(dut.PATLIST(1).ly3.hi.value,dut.PATLIST(1).ly3.lo.value),hi_lo_t(dut.PATLIST(1).ly4.hi.value,dut.PATLIST(1).ly4.lo.value),hi_lo_t(dut.PATLIST(1).ly5.hi.value,dut.PATLIST(1).ly5.lo.value))
# pat_r7=mirror_patdef(pat_l7,pat_l7.id-1)