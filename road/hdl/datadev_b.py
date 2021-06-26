#Test cases for pat_unit_beh


import numpy as np
import math
import random




def datadev(MAX_SPAN=37,nhit_lo=3,nhit_hi=10):

    N_LAYERS=6
    #nhits corresponds to the hits from noise
    nhits=random.randint(nhit_lo,nhit_hi)
    hit1=random.randint(0,MAX_SPAN-1)
    ly_t=random.randint(0,N_LAYERS-1)
    slope=random.uniform(-1*(MAX_SPAN-1),MAX_SPAN-1)
    data=np.zeros((N_LAYERS,MAX_SPAN), dtype=int)

    #points of intersection in layers
    if (ly_t==1):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=0
        ly3_h=0
        ly4_h=0
        ly5_h=0
    elif (ly_t==2):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=0
        ly4_h=0
        ly5_h=0
    elif (ly_t==3):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=0
        ly5_h=0
    elif (ly_t==4):
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
            lyx_h[z]=[]
        else:
            lyx_h[z]=lyx_h[z]

    #layer 0 array without noise
    if (ly_t==0 or ly_t==1 or ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        if(lyx_h[0]!=[]):
            data[0,lyx_h[0]]=1
        else:
            data[0,lyx_h[0]]=[]
    #layer 1 array without noise
    if (ly_t==1 or ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        if(lyx_h[1]!=[]):
            data[1,lyx_h[1]]=1
        else:
            data[1,lyx_h[1]]=[]
    #layer 2 array without noise
    if (ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        if(lyx_h[2]!=[]):
            data[2,lyx_h[2]]=1
        else:
            data[2,lyx_h[2]]=[]
    #layer 3 array without noise
    if (ly_t==3 or ly_t==4 or ly_t==5):
        if(lyx_h[3]!=[]):
            data[3,lyx_h[3]]=1
        else:
            data[3,lyx_h[3]]=[]
    #layer 4 array without noise
    if (ly_t==4 or ly_t==5):
        if(lyx_h[4]!=[]):
            data[4,lyx_h[4]]=1
        else:
            data[4,lyx_h[4]]=[]
    #layer 5 array without noise
    if (ly_t==5):
        if(lyx_h[5]!=[]):
            data[5,lyx_h[5]]=1
        else:
            data[5,lyx_h[5]]=[]

    #noise for all 6 layers instruction: generate a number of hits in random layer, random strip
    for ihit in range(nhits):
        strip = random.randint(0, MAX_SPAN-1)
        ly = random.randint(0, ly_t)
        data[ly,strip]=1

    #get rid of 10% of data
    def count_ones(ones_arr):
        n_ones=0
        for j in range(N_LAYERS):
            for i in range(len(ones_arr[j])):
                if (ones_arr[j,i]==1):
                    n_ones=n_ones+1
        return n_ones;

    def return_indices(ones_arr):
        indices=[]
        for m in range(N_LAYERS):
            for n in range(len(ones_arr[m])):
                if (ones_arr[m,n]==1):
                    indices.append([m,n])
        return indices


    n_eliminate=round(count_ones(data)*.1)
    b=return_indices(data)

    for k in range(n_eliminate):
        el_rc=random.choice(b)
        el_rc1=el_rc[0]
        el_rc2=el_rc[1]
        data[el_rc1,el_rc2]=0



    return data



