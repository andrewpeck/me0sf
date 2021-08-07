#Data devlopment for the pat_unit_mux.vhd
import random
from subfunc import*
from datadev import datadev
from printly_dat import printly_dat

def datadev_mux(WIDTH=192,nhit_lo=3,nhit_hi=10):
    """takes a given chamber width and a range of hits to generate a random number of tracks for populating data throughout layers"""
    ly_t=random.randint(1,6)
    print("ly_t is %d"%ly_t)
    track_num=random.randint(1,10)
    N_LAYERS=6
    data_store=[0,0,0,0,0,0]
    for i in range(track_num):
        data=datadev(ly_t=ly_t,MAX_SPAN=WIDTH,nhit_lo=nhit_lo,nhit_hi=nhit_hi)
        for j in range(N_LAYERS):
            data_store[j]=(data_store[j]|data[j])
    data_out=data_store
    return data_out
for i in range(1000):
    data=datadev_mux()
    print(data)
    printly_dat(data=data,MAX_SPAN=192)


