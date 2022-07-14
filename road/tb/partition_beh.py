""" Emulator that processes a single partition (6 layers x 192 strips) and returns a collection of segments"""
from itertools import islice
from pat_unit_mux_beh import pat_mux
from subfunc import *
import numpy as np

def compare_ghosts(seg, comp_list):
    """takes in a segment and a list of segments to ensure that there aren't copies of the same data (ID value identical) or mirrors (ID value +2 or -2 from each other)"""
    comp_list = [x for x in comp_list if x.id != 0 ]
    if len(comp_list) != 0:
        for i in range(len(comp_list)):
            if seg.id == 0 and seg.lc == 0:
                break
            if (
                seg.id == comp_list[i].id
                or seg.id + 2 == comp_list[i].id
                or seg.id - 2 == comp_list[i].id
            ):
                seg.reset()
    return seg

def test_compare_ghosts():
    seg_list = [Segment(6, 15), Segment(6, 12), Segment(6,5)]
    seg1 = Segment(6, 15)
    seg2 = Segment(6, 10)
    seg3 = Segment(6, 7)
    #check for reset with copy, ID+2, ID-2
    assert compare_ghosts(seg1, seg_list).id == 0
    assert compare_ghosts(seg2, seg_list).id == 0
    assert compare_ghosts(seg3, seg_list).id == 0

def cancel_edges(pat_mux_dat, group_width=8, ghost_width=4, width=192):

    """takes in pat_unit_mux_data, finds edges of groups w/given group width, and performs edge
    cancellation by checking ghosts around each edge within given ghost width"""

    for edge in range((width // group_width)-1):
        lo_index = group_width*(edge+1) - (ghost_width//2)
        hi_index = lo_index + ghost_width
        for j in range(lo_index, hi_index): 
            pat_mux_dat[j] = compare_ghosts(pat_mux_dat[j], pat_mux_dat[(j + 1):hi_index])
    return pat_mux_dat

def test_cancel_edges():
    seg_list1 = []
    for i in range(24):
        seg_list1.append(Segment(6, 15)) 
    cancelled1 = cancel_edges(seg_list1, 8, 4, 24)
    #check first edge is cancelled correctly
    assert cancelled1[6].id == 0
    assert cancelled1[7].id == 0
    assert cancelled1[8].id == 0
    assert cancelled1[9].id == 15
    #check second edge is cancelled correctly 
    assert cancelled1[14].id == 0 
    assert cancelled1[15].id == 0
    assert cancelled1[16].id == 0
    assert cancelled1[17].id == 15
    seg_list2 = [Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 14),Segment(6, 11), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15),Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15), Segment(6, 15)]
    cancelled2 = cancel_edges(seg_list2, 8, 4, 24)
    #check only 6th segment is cancelled in first edge
    assert cancelled2[6].id == 0
    assert cancelled2[7].id == 14
    assert cancelled2[8].id == 11

def work_partition(partition_data, max_span=37, width=192, group_width=8, ghost_width=4, enable_gcl=True, partition=0):

    """

    takes in partition data, a group size, and a ghost width to return a smaller data set, using
    ghost edge cancellation and segment quality filtering

    NOTE: ghost width denotes the width where we can likely see copies of the same segment in the
    data

    steps: process partition data with pat_mux, perfom edge cancellations, divide partition into
    pieces, take best segment from each piece

    """

    segments = pat_mux(partition_data, max_span, width, partition=partition)

    if (enable_gcl):
        segments = cancel_edges(partition_data, group_width, ghost_width, width)

    #divide partition into pieces and take best segment from each piece

    def chunk(it, size):
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    chunked = chunk(segments, group_width)

    #final_dat = list(map(max, chunked, group_width))
    final_dat = list(map(max, np.array(segments).reshape(width//group_width, group_width)))

    return final_dat

def test_work_partition():
    data = [0b1, 0b1, 0b1, 0b1, 0b1, 0b1]
    part = work_partition(data)
    assert part[0].id == 15
    assert part[0].lc == 6
    assert part[1].id == 0
    assert part[1].lc == 0
