# Python implementation of the pat_unit.vhd behavior

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
    center = round(max_span/2)
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

def calculate_global_layer_mask(patlist):
    """create layer masks for patterns in patlist"""
    global LAYER_MASK
    LAYER_MASK = [get_ly_mask(pat) for pat in patlist]

# FIXME: ugh this is not nice
calculate_global_layer_mask(PATLIST)

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
        hcs = [min(7,count_ones(hits)) if ly in enabled_layers else 0 for (ly,hits) in enumerate(masked_data)]
        hc = sum(hcs)
        return hc
    else:
        return sum([count_ones(x) for x in masked_data])

def calculate_layer_count(masked_data : List[int]) -> int:
    """takes in a []*6 list of pre-masked data and gives the layer count"""
    return sum(map(lambda x : x > 0, masked_data))

def pat_unit(data,
             strip : int = 0,
             ly_thresh : int = 4,
             partition : int = -1,
             light_hit_count : bool = True,
             verbose : bool = False):

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

    # (7) apply a layer threshold
    if (best.lc < ly_thresh):
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
