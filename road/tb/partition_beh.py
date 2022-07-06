""" Emulator that processes a single partition (6 layers x 192 strips) and returns a collection of segments"""
import numpy as np
from pat_unit_mux_beh import pat_mux
#from datadev_mux import datadev_mux
from subfunc import *

def compare_ghosts(seg, comp_list):
    """takes in a segment and a list of segments to ensure that there aren't copies of the same data (ID value identical) or mirrors (ID value +2 or -2 from each other)"""
    comp_list = [x for x in comp_list if x.id != 0]
    if len(comp_list) != 0:
        for i in range(len(comp_list)):
            if seg.id == 0 and seg.lc == 0:
                break
            if (
                seg.id == comp_list[i].id
                or seg.id + 2 == comp_list[i].id
                or seg.id - 2 == comp_list[i].id
            ):
                seg.id = 0
                seg.lc = 0
    return seg

def partition_filtering(pat_mux_dat, group_width=8, ghost_width=4, WIDTH=37):
    """takes in pat_unit_mux_data and performs edge cancellation"""
    for group in range(round((WIDTH - 1) / group_width)):
        lo_index = int(group + group_width - (ghost_width / 2))  # maybe check this first if there's discrepancies
        hi_index = lo_index + (ghost_width)
        for j in range(lo_index, hi_index): 
            pat_mux_dat[j] = compare_ghosts(pat_mux_dat[j], pat_mux_dat[(j + 1):hi_index])
    return pat_mux_dat

def work_partition(partition_data, MAX_SPAN=37, WIDTH=192, group_width=8, ghost_width=4):
    """takes in pat_unit_mux_data, a group size, and a ghost width to return a smaller data set, using ghost edge cancellation
    and segment quality filtering

    NOTE: ghost width denotes the width where we can likely see copies of the same segment in the data"""
    #perform edge cancellation on pat_unit_mux_data
    pat_mux_dat = np.array(partition_filtering(pat_mux(partition_data, MAX_SPAN, WIDTH), group_width, ghost_width, WIDTH))

    #divide partition into 24 pieces and take best segment from each piece
    final_dat = list(map(max, pat_mux_dat.reshape(WIDTH//group_width, group_width)))
    return final_dat
