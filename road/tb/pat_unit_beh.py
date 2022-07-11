# Python implementation of the pat_unit.vhd behavior
from subfunc import *
from constants import *

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

def get_ly_mask(ly_pat, max_span=37):
    """takes in a given layer pattern and returns a list of integer bit masks for each layer"""
    #for each layer, shift the provided hi and lo values for each layer from pattern definition by center
    m_vals = [shift_center(ly, max_span) for ly in ly_pat.layers]
    # use the high and low indices to determine where the high bits must go for each layer
    m_vec = list(map(set_high_bits, m_vals))
    return Mask(m_vec, ly_pat.id)

def calculate_global_layer_mask(patlist):
    """create layer masks for patterns in patlist"""
    global LAYER_MASK
    LAYER_MASK = [get_ly_mask(pat) for pat in patlist]
    
calculate_global_layer_mask(PATLIST)

def mask_layer_data (data, mask):
    """
    AND together a list of layer masks with a list of layers

    data is a 6 layer collection of integers

    mask is a 6 layer collection of masks

    """
    return list(map(lambda ly_dat, ly_mask: ly_dat & ly_mask , data, mask))

def calculate_centroids(masked_data):
    """takes in a []*6 list of pre-masked data and gives the found centroids"""
    return list(map(find_centroid, masked_data))

def calculate_layer_count(masked_data):
    """takes in a []*6 list of pre-masked data and gives the layer count"""
    return sum(map(lambda x : x > 0, masked_data))

def get_seg(lc_id_pair, strip):
    """creates segment object for a given pair of layer count and pattern id"""
    seg = Segment(lc_id_pair[0], lc_id_pair[1], strip)
    return seg

def find_best_seg(data, strip=None, max_span=37, ly_thresh=LY_THRESH, partition=-1):
    """
    takes in sample data for each layer and returns best segment

    processing pipeline is

    (1) take in 6 layers of raw data
    (2) for the X (~16) patterns available, AND together the raw data with the respective pattern masks
    (3) count the # of hits in each pattern
    (4) calculate the centroids for each pattern
    (5) choose the max of all patterns
    (6) apply a layer threshold
    """

    # and the layer data with the respective layer mask to
    # determine how many hits are in each layer
    # this yields a map object that can be iterated over to get,
    #    for each of the N patterns, the masked []*6 layer data
    # (2)
    masked_data = map(lambda mask : mask_layer_data(mask.mask, data), LAYER_MASK)

    # (3)
    lycs = map(lambda pattern_data : calculate_layer_count(pattern_data), masked_data)
    pids = map(lambda mask : mask.id, LAYER_MASK);
    lycs_pids = zip(lycs, pids)

    # (4)

    seg_list = map(lambda lyc_pid : get_seg(lyc_pid, strip), lycs_pids)

    # (5) choose the max of all patterns
    best = max(seg_list)

    # (6) apply a layer threshold
    if (best.lc < ly_thresh):
        best.reset()

    best.partition=partition

    return best

################################################################################
# Tests
################################################################################

def test_find_best_seg():
    assert find_best_seg([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 37).id == 15
    assert find_best_seg([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 37).lc == 6
    assert find_best_seg([0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000], 37).id == 15
    assert find_best_seg([0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000], 37).lc == 5
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 6
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 5
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert find_best_seg([0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 4
    assert find_best_seg([0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 0
    assert find_best_seg([0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 0
    assert find_best_seg([0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 0
    assert find_best_seg([0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 0

def test_get_ly_mask():
    """ test function for get_ly_mask """
    assert get_ly_mask(pat_straight).mask == [0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1000000000000000000, 0b11100000000000000000, 0b11100000000000000000]
    assert get_ly_mask(pat_l).mask == [0b111100000000000000, 0b1111000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000000, 0b11110000000000000000000]
    assert get_ly_mask(pat_r).mask == [0b11110000000000000000000, 0b1111000000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000, 0b111100000000000000]
    assert get_ly_mask(pat_l2).mask == [0b11110000000000000, 0b11111100000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11110000000000000000000, 0b111100000000000000000000]
    assert get_ly_mask(pat_r2).mask == [0b111100000000000000000000, 0b11111100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b111100000000000000, 0b11110000000000000]
    assert get_ly_mask(pat_l3).mask == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000, 0b111100000000000000000000000]
    assert get_ly_mask(pat_r3).mask == [0b111100000000000000000000000, 0b11110000000000000000000000, 0b1111000000000000000000, 0b111110000000000000000, 0b111100000000000, 0b11110000000000]
    assert get_ly_mask(pat_l4).mask == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000, 0b111100000000000000000000000]
