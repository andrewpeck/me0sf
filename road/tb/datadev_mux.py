# Data development for the pat_unit_mux.vhd
import random
from subfunc import *
from datadev import datadev
from printly_dat import printly_dat


def datadev_mux(WIDTH=192, track_num=4, nhit_lo=3, nhit_hi=10):
    """takes a given chamber width and a range of hits to generate a random number of tracks for populating data throughout layers"""
    assert type(WIDTH) == int, "WIDTH input must be an integer"
    assert type(track_num) == int, "track_num input must be an integer"
    assert type(nhit_lo) == int, "nhit_lo input must be an integer"
    assert type(nhit_hi) == int, "nhit_hi input must be an integer"
    N_LAYERS = 6
    # create space for 6 layers of data
    data_store = [0, 0, 0, 0, 0, 0]
    # create tracks with datadev(); overlay hits from multiple muon tracks onto strip data
    for i in range(track_num):
        # vary the number of layers for each muon track
        ly_t = 6
        data = datadev(ly_t=ly_t, MAX_SPAN=WIDTH, nhit_lo=nhit_lo, nhit_hi=nhit_hi)
        for j in range(N_LAYERS):
            # ADD track data onto existing layer data
            data_store[j] = data_store[j] | data[j]
    data_out = data_store
    return data_out
