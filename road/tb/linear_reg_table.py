from subfunc import*
import itertools
from linearreg import*
# def generate_lookupt(patlist=patlist):
#     """generates the different testcases for the linear regression lookup table"""
#     pat_width=[]
#     pat_comb=[]
#     for i in range(2): #change back to len(patlist)
#         pat_width.append([patlist[i].id,patlist[i].ly0.hi-patlist[i].ly0.lo+1,patlist[i].ly1.hi-patlist[i].ly1.lo+1,patlist[i].ly2.hi-patlist[i].ly2.lo+1,patlist[i].ly3.hi-patlist[i].ly3.lo+1,patlist[i].ly4.hi-patlist[i].ly4.lo+1,patlist[i].ly5.hi-patlist[i].ly5.lo+1])
#     for j in range(len(pat_width)):
#         temp_list=pat_width[j][1:]
#         for k in range(len(temp_list)):
#             temp_list[k]=[l for l in range(2**temp_list[k])]
#             #temp_list[k]=[bin(l)[2:].zfill(temp_list[k]) for l in range(2**temp_list[k])] #might not really need this binary version
#         pat_comb.append([pat_width[j][0],temp_list])
#     return pat_comb

# pat_comb=generate_lookupt()
# print(pat_comb)
# all_comb=[]
# for i in range(len(pat_comb)):
#     hold=list(itertools.product(*pat_comb[i][1]))
#     hold=[list(x) for x in hold]
#     all_comb.append([pat_comb[i][0],hold])
all_widths=[1,3,4,5,6,8,9,12,14]
def generate_all_comb(width=all_widths):
    all_comb=[]
    for i in range(len(width)):
        temp_list=[l for l in range(2**width[i])]
        all_comb.append(temp_list)
    return all_comb
all_comb=generate_all_comb()
print(all_comb)


#first dimension should be length, 2nd dimension is hit pattern; value stored is what centroid you have

def generate_centroid_lut(all_comb):
    hold_all=[]
    for o in range(len(all_comb)):
        hold_some=[]
        for p in range(len(all_comb[o])):
            hold_some.append(find_centroid(all_comb[o]))
        hold_all.append(hold_some)
    return hold_all

print(generate_centroid_lut(all_comb))




