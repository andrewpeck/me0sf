#note: numbering the segments 0-36, layers 0-5
#assumption made: if the track width is larger than one thats because the muon hit either
#one or two extra segments immediately to the right, left or both of the incident segments--> I just gathered this in
#with the noise



import numpy as np
import math
import random

for k in range(3):

    MAX_SPAN=37
    N_LAYERS=6
    #nhits corresponds to the hits from noise COME BACK TO ME: ask andrew if this is a reasonable number of hits from noise
    nhits=random.randint(3,10)
    hit1=random.randint(0,MAX_SPAN-1)
    ly_t=random.randint(0,N_LAYERS-1)
    slope=random.uniform(-1*(MAX_SPAN-1),MAX_SPAN-1)
    data=np.zeros(N_LAYERS,MAX_SPAN)

    #points of intersection in layers
    if (ly_t==1):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
    elif (ly_t==2):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
    elif (ly_t==3):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
    elif (ly_t==4):
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=round((slope*4)+hit1)
    else:
        ly0_h=hit1
        ly1_h=round((slope*1)+hit1)
        ly2_h=round((slope*2)+hit1)
        ly3_h=round((slope*3)+hit1)
        ly4_h=round((slope*4)+hit1)
        ly5_h=round((slope*5)+hit1)

    #layer 0 array without noise
    if (ly_t==0 or ly_t==1 or ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        data[0,ly0_h]=1
    #layer 1 array without noise
    if (ly_t==1 or ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        data[1,ly1_h]=1
    #layer 2 array without noise
    if (ly_t==2 or ly_t==3 or ly_t==4 or ly_t==5):
        data[2,ly2_h]=1
    #layer 3 array without noise
    if (ly_t==3 or ly_t==4 or ly_t==5):
        data[3,ly3_h]=1
    #layer 4 array without noise
    if (ly_t==4 or ly_t==5):
        data[4,ly4_h]=1
    #layer 5 array without noise
    if (ly_t==5):
        data[5,ly5_h]=1

    #noise for all 6 layers instruction: generate a number of hits in random layer, random strip
    for ihit in range(nhits):
        strip = random.randint(0, MAX_SPAN-1)
        ly = random.randint(0, ly_t)
        data[ly,strip]=1

    #print data
    for l in range(MAX_SPAN):
        ly0_x=data[0,:]
        ly1_x=data[1,:]
        ly2_x=data[2,:]
        ly3_x=data[3,:]
        ly4_x=data[4,:]
        ly5_x=data[5,:]
        if (ly0_x[l]!=1):
            ly0_x[l]='-'
        if (ly1_x[l]!=1):
            ly1_x[l]='-'
        if (ly2_x[l]!=1):
            ly2_x[l]='-'
        if (ly3_x[l]!=1):
            ly3_x[l]='-'
        if (ly4_x[l]!=1):
            ly4_x[l]='-'
        if (ly5_x[l]!=1):
            ly5_x[l]='-'
    ly0_x=str(ly0_x)
    ly1_x=str(ly1_x)
    ly2_x=str(ly2_x)
    ly3_x=str(ly3_x)
    ly4_x=str(ly4_x)
    ly5_x=str(ly5_x)
    print("Data for cycle %d is: " % k)
    print("ly0 %s" % ly0_x)
    print("ly1 %s" % ly1_x)
    print("ly2 %s" % ly2_x)
    print("ly3 %s" % ly3_x)
    print("ly4 %s" % ly4_x)
    print("ly5 %s\n\n" % ly5_x)



# if (t_width==2):
    #     if(left_or_right==0):
    #         ly0_x[ly0_h-1]=1
    #     else:
    #         ly0_x[ly0_h+1]=1
    # elif (t_width==3):
    #     ly0_x[ly0_h-1]=1
    #     ly0_x[ly0_h+1]=1
   # oi_ly0=random.randint(-3,3)+ly0_h COME BACK TO ME (need to discuss data with andrew more)

#t_width=random.randint(1,3)
#left_or_right=random.randint(0,1)
