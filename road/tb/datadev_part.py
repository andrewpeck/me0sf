from datadev_mux import datadev_mux
from printly_dat import printly_dat

def datadev_part(num_partitions=8,WIDTH=192, track_num=4, nhit_lo=3, nhit_hi=10):
    dataout=datadev_mux(WIDTH=(WIDTH*num_partitions),track_num=track_num,nhit_lo=nhit_lo,nhit_hi=nhit_hi)
    return dataout
