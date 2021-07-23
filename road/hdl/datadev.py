#Test cases for pat_unit.vhd
import math
import random
from printly_dat import printly_dat
from subfunc import set_bit
from subfunc import count_ones
from subfunc import ones_bit_mask
from subfunc import clear_bit

def datadev_b(ly_t=6,MAX_SPAN=37,nhit_lo=3,nhit_hi=10):

    N_LAYERS=6

    #nhits corresponds to the hits from noise
    nhits=random.randint(nhit_lo,nhit_hi)
    slope=random.uniform(-1*(MAX_SPAN/(N_LAYERS-1)),MAX_SPAN/(N_LAYERS-1))
    hit1=round(random.randint(17,19)-slope*2.5)
    data=[]

    #points of intersection in layers
    if (ly_t==2):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=0
        ly3_h=0
        ly4_h=0
        ly5_h=0
    elif (ly_t==3):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=0
        ly4_h=0
        ly5_h=0
    elif (ly_t==4):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=0
        ly5_h=0
    elif (ly_t==5):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=round((slope*4)+hit1)
        ly5_h=0
    else:
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=round((slope*4)+hit1)
        ly5_h=round((slope*5)+hit1)

    #setting the boundaries at threshold 0 and 36 index values
    lyx_h=[ly0_h,ly1_h,ly2_h,ly3_h,ly4_h,ly5_h]
    for z in range(len(lyx_h)):
        if (lyx_h[z]>(MAX_SPAN-1) or lyx_h[z]<0):
            lyx_h[z]=None
        else:
            lyx_h[z]=lyx_h[z]

    #layer 0 array without noise
    if (ly_t==1 or ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5 or ly_t==6):
        if(lyx_h[0] is not None):
            data.append(set_bit(lyx_h[0]))
        else:
            data.append(0)

    #layer 1 array without noise
    if (ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5 or ly_t==6):
        if(lyx_h[1] is not None):
            data.append(set_bit(lyx_h[1]))
        else:
            data.append(0)
    #layer 2 array without noise
    if (ly_t==3 or ly_t==4 or ly_t==5 or ly_t==6):
        if(lyx_h[2] is not None):
            data.append(set_bit(lyx_h[2]))
        else:
            data.append(0)
    #layer 3 array without noise
    if (ly_t==4 or ly_t==5 or ly_t==6):
        if(lyx_h[3] is not None):
            data.append(set_bit(lyx_h[3]))
        else:
            data.append(0)
    #layer 4 array without noise
    if (ly_t==5 or ly_t==6):
        if(lyx_h[4] is not None):
            data.append(set_bit(lyx_h[4]))
        else:
            data.append(0)
    #layer 5 array without noise
    if (ly_t==6):
        if(lyx_h[5] is not None):
            data.append(set_bit(lyx_h[5]))
        else:
            data.append(0)

    #noise for all 6 layers
        for ihit in range(nhits):
            strip = random.randint(0, MAX_SPAN-1)
            ly = random.randint(0, N_LAYERS-1)
            data[ly]=set_bit(strip,data[ly],MAX_SPAN)

    #get rid of 10% of data
    ones_ct=0
    iterable_data=[]
    for i in range(len(data)):
        ones_ct=ones_ct+count_ones(data[i])
        iterable_data_v=bin(data[i])[2:]
        iterable_data_v=iterable_data_v.zfill(MAX_SPAN)
        iterable_data.append(iterable_data_v)


    def return_indices(data,iterable_data):
        indices=[]
        for n in range(len(data)):
            mask=ones_bit_mask(data[n])
            check=count_ones(data[n]&mask)
            if (check>=1):
                iterable_mask=bin(mask)[2:]
                iterable_mask=iterable_mask.zfill(MAX_SPAN)
                for o in range(len(iterable_data[n])):
                    if (int(iterable_data[n][o])&int(iterable_mask[o])==1):
                        indices.append([n,o])
        return indices

    n_eliminate=round(ones_ct*.1)
    el_indices=return_indices(data,iterable_data)


    for k in range(n_eliminate):
        target=random.choice(el_indices)
        in_1=target[0]
        in_2=target[1]
        data[in_1]=clear_bit(data[in_1],in_2)

    return data
