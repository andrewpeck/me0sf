# Python implementation of the pat_unit.vhd behavior
import math
from typing import List

from constants import *
from subfunc import *

def shift_center(ly, max_span=37):
    """

    Patterns are defined as a +hi and -lo around a center point of a pattern.

    e.g. for a pattern 37 strips wide, there is a central strip,
    and 18 strips to the left and right of it.

    This patterns shifts from a +hi and -lo around the central strip, to an offset +hi and -lo.

    e.g. for (hi, lo) = (1, -1) and a window of 37, this will return (17,19)

    """
    center = math.floor(max_span/2)
    hi = ly.hi + center
    lo = ly.lo + center
    return (lo, hi)

def set_high_bits(lo_hi_pair):
    """Given a high bit and low bit, this function will return a bitmask with all the bits in
    between the high and low set to 1"""
    hi = lo_hi_pair[1]
    lo = lo_hi_pair[0]
    return 2**(hi-lo+1)-1 << lo

def get_ly_mask(ly_pat : patdef_t,
                max_span : int = 37) -> Mask:

    '''
    takes in a given layer pattern and returns a list of integer bit masks
    for each layer
    '''

    #for each layer, shift the provided hi and lo values for each layer from
    #pattern definition by center
    m_vals = [shift_center(ly, max_span) for ly in ly_pat.layers]

    # use the high and low indices to determine where the high bits must go for
    # each layer
    m_vec = [set_high_bits(x) for x in m_vals]
    return Mask(m_vec, ly_pat.id)

def calculate_global_layer_mask(patlist, max_span):
    """create layer masks for patterns in patlist"""
    global LAYER_MASK
    LAYER_MASK = [get_ly_mask(pat, max_span) for pat in patlist]

def mask_layer_data (data : List[int], mask) -> List[int]:
    """
    AND together a list of layer masks with a list of layers

    data is a 6 layer collection of integers

    mask is a 6 layer collection of masks

    """
    return list(map(lambda ly_dat, ly_mask: ly_dat & ly_mask , data, mask))

def calculate_centroids(masked_data : List[int]) -> List[float]:
    # print(masked_data)
    """takes in a []*6 list of pre-masked data and gives the found centroids"""
    return [find_centroid(x) for x in masked_data]

def calculate_hit_count(masked_data : List[int], light : bool = False) -> int:
    """takes in a []*6 list of pre-masked data and gives the number of hits

    this also includes "light" counting, which instead of actually counting up
    all the hits, it just looks at a subset of layers and sums a CEILed hit
    count for those layers

    the CEIL logic works as max(7, hit_count)

    only the outer layers are chosen as they are the ones that contribute most
    to the bend. This reduces the number of additions required in the firmware.

    """

    if light:
        enabled_layers = [0,5]
        return sum([min(7,count_ones(hits)) if ly in enabled_layers else 0 for (ly,hits) in enumerate(masked_data)])
    else:
        return sum([count_ones(x) for x in masked_data])

def calculate_layer_count(masked_data : List[int]) -> int:
    """takes in a []*6 list of pre-masked data and gives the layer count"""
    return sum(map(lambda x : x > 0, masked_data))

def calculate_cluster_size(data):
    cluster_size_per_layer = [max_cluster_size(x) for x in data]
    return cluster_size_per_layer

def calculate_hits(data):
    n_hits_per_layer = [count_ones(x) for x in data]
    return n_hits_per_layer

def pat_unit(data,
             strip : int = 0,
             ly_thresh : int = 4,
             partition : int = -1,
             input_max_span : int = 37,
             num_or : int = 2,
             light_hit_count : bool = True,
             verbose : bool = False,
             skip_centroids : bool = True):

    # construct the dynamic_patlist (we do not use default PATLIST anymore)
    # for robustness concern, other codes might use PATLIST, so we kept the default PATLIST in subfunc
    # however, this could cause inconsistent issue, becareful! OR find a way to modify PATLIST
    global LAYER_MASK

    if LAYER_MASK is None:

        factor = num_or / 2
        pat_straight = patdef_t(19, create_pat_ly(-0.4 / factor, 0.4 / factor))
        pat_l = patdef_t(18, create_pat_ly(0.2 / factor, 0.9 / factor))
        pat_r = mirror_patdef(pat_l, pat_l.id - 1)
        pat_l2 = patdef_t(16, create_pat_ly(0.5 / factor, 1.2 / factor))
        pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
        pat_l3 = patdef_t(14, create_pat_ly(0.9 / factor, 1.7 / factor))
        pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
        pat_l4 = patdef_t(12, create_pat_ly(1.4 / factor, 2.3 / factor))
        pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
        pat_l5 = patdef_t(10, create_pat_ly(2.0 / factor, 3.0 / factor))
        pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
        pat_l6 = patdef_t(8, create_pat_ly(2.7 / factor, 3.8 / factor))
        pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
        pat_l7 = patdef_t(6, create_pat_ly(3.5 / factor, 4.7 / factor))
        pat_r7 = mirror_patdef(pat_l7, pat_l7.id-1)
        pat_l8 = patdef_t(4, create_pat_ly(4.3 / factor, 5.5 / factor))
        pat_r8 = mirror_patdef(pat_l8, pat_l8.id-1)
        pat_l9 = patdef_t(2, create_pat_ly(5.4 / factor, 7.0 / factor))
        pat_r9 = mirror_patdef(pat_l9, pat_l9.id - 1)

        dynamic_patlist = (
            pat_straight,
            pat_l,
            pat_r,
            pat_l2,
            pat_r2,
            pat_l3,
            pat_r3,
            pat_l4,
            pat_r4,
            pat_l5,
            pat_r5,
            pat_l6,
            pat_r6,
            pat_l7,
            pat_r7,
            pat_l8,
            pat_r8,
            pat_l9,
            pat_r9)

        # first make the PATLIST appropriate
        calculate_global_layer_mask(dynamic_patlist, input_max_span)

    """
    takes in sample data for each layer and returns best segment

    processing pipeline is

    (1) take in 6 layers of raw data
    (2) for the X (~16) patterns available, AND together the raw data with the respective pattern masks
    (3) count the # of hits in each pattern
    (4) calculate the centroids for each pattern
    (5) process segments
    (6) choose the max of all patterns
    (7) apply a layer threshold
    """

    # (2)
    # and the layer data with the respective layer mask to
    # determine how many hits are in each layer
    # this yields a map object that can be iterated over to get,
    #    for each of the N patterns, the masked []*6 layer data
    masked_data = [mask_layer_data(x.mask, data) for x in LAYER_MASK]

    # (3) count # of hits
    hcs = [calculate_hit_count(x, light_hit_count) for x in masked_data]
    lcs = [calculate_layer_count(x) for x in masked_data]
    pids = [x.id for x in LAYER_MASK]

    # (4) process centroids
    if skip_centroids:
        centroids = [[0 for _ in range(6)] for _ in range(len(masked_data))]
    else:
        centroids = [calculate_centroids(x) for x in masked_data]

    # (5) process segments
    seg_list = [Segment(lc=lc,
                        hc=hc,
                        id=pid,
                        partition=partition,
                        strip=strip,
                        centroid=centroid)
                for (hc, lc, pid, centroid) in
                zip(hcs, lcs, pids, centroids)]

    # (6) choose the max of all patterns
    best = max(seg_list) # type: ignore

    # (7) remove segments with multiple noisy layers or multiple large clusters
    cluster_size_max_limit = 3
    n_hits_max_limit = 6
    cluster_size_counts = calculate_cluster_size(data)
    n_hits_counts = calculate_hits(data)
    n_layers_large_clusters = 0
    n_layers_large_hits = 0
    for l in cluster_size_counts:
        if l > cluster_size_max_limit:
            n_layers_large_clusters += 1
    for l in n_hits_counts:
        if l > n_hits_max_limit:
            n_layers_large_hits += 1
    if n_layers_large_hits > 1:
        best.reset()
    if n_layers_large_clusters > 1:
        best.reset()
    #elif n_layers_large_clusters == 1:
    #    ly_thresh += 1

    # (8) apply a layer threshold
    if (partition % 2 != 0):
        ly_thresh += 1
    ly_thresh = min(ly_thresh, 6)
    if (best.lc < ly_thresh):
        best.reset()

    # (9) remove very wide segments
    if (best.id <= 10):
        best.reset()

    best.partition=partition

    # debug output
    if verbose:
        for ly in range(6):
            for bit in range(37):
                print(0x1 & (data[ly] >> bit), end="")
            print("\n", end="")
        print("\n", end="")

        for (i,id) in enumerate(masked_data):
            print(f"id={i+1}")
            for ly in range(6):
                for bit in range(37):
                    print(0x1 & (id[ly] >> bit), end="")
                print("\n", end="")
            print("\n", end="")

        for seg in seg_list:
            print(seg)


    best.hc=0
    best.update_quality()

    return best

################################################################################
# Tests
################################################################################

def test_pat_unit():
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]).id == 19
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]).lc == 6
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000]).id == 19
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000]).lc == 6
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).id == 18
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).lc == 5
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).id == 0
    assert pat_unit(strip=0, partition=0, ly_thresh=4, data=[0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).lc == 0

def test_get_ly_mask():
    """ test function for get_ly_mask """
    assert get_ly_mask(pat_straight).mask == [0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000]
    assert get_ly_mask(pat_l).mask == [0b1111000000000000000, 0b1110000000000000000,0b1100000000000000000,0b11000000000000000000,0b111000000000000000000, 0b1111000000000000000000]
    assert get_ly_mask(pat_r).mask == [0b1111000000000000000000, 0b111000000000000000000, 0b11000000000000000000, 0b1100000000000000000, 0b1110000000000000000, 0b1111000000000000000]
