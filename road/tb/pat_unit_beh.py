# Python implementation of the pat_unit.vhd behavior
from subfunc import *
from constants import *

def shift_center(ly, MAX_SPAN=37):
    """helper function that shifts center of hi and lo values"""
    center = round(MAX_SPAN/2)
    hi = ly.hi + center
    lo = ly.lo + center
    return [lo, hi]

def get_ly_mask(ly_pat, MAX_SPAN=37):
    """takes in a given layer pattern and returns a list of integer bit masks for each layer"""
    assert (
        type(ly_pat) == patdef_t
    ), "ly_pat input must be defined in the patdef_t class"
    assert (
        type(ly_pat.layers[0]) == hi_lo_t
    ), "each layer of ly_pat must be of the class hi_lo_t"
    assert type(ly_pat.id) == int, "ly_pat's id must be an integer"
    assert type(MAX_SPAN) == int, "MAX_SPAN input must be an integer"
    m_vec = []
    #for each layer, shift the provided hi and lo values for each layer from pattern definition by center
    m_vals = list(map(shift_center, ly_pat.layers))    
    # use the high and low indices to determine where the high bits must go for each layer
    for i in range(len(m_vals)):
        high_bits = 0
        # keep setting high bits from the low index to the high index; leave all else as low bits
        for index in range(m_vals[i][0], m_vals[i][1] + 1):
            val = 1 << index
            high_bits = high_bits | val
        m_vec.append(high_bits)
    mask_vec = Mask(m_vec, ly_pat.id)
    return mask_vec

def test_get_ly_mask():
    """ test function for get_ly_mask """
    assert get_ly_mask(pat_straight).mask ==[0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1000000000000000000, 0b11100000000000000000, 0b11100000000000000000]
    assert get_ly_mask(pat_l).mask ==[0b111100000000000000, 0b1111000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000000, 0b11110000000000000000000]
    assert get_ly_mask(pat_r).mask == [0b11110000000000000000000, 0b1111000000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000, 0b111100000000000000]
    assert get_ly_mask(pat_l2).mask == [0b11110000000000000, 0b11111100000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11110000000000000000000, 0b111100000000000000000000] 
    assert get_ly_mask(pat_r2).mask == [0b111100000000000000000000, 0b11111100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b111100000000000000, 0b11110000000000000]
    assert get_ly_mask(pat_l3).mask == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000, 0b111100000000000000000000000]
    assert get_ly_mask(pat_r3).mask == [0b111100000000000000000000000, 0b11110000000000000000000000, 0b1111000000000000000000, 0b111110000000000000000, 0b111100000000000, 0b11110000000000]
    assert get_ly_mask(pat_l4).mask == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000, 0b111100000000000000000000000] 

def return_layer_mask():
    """create layer masks for patterns in patlist"""
    global LAYER_MASK
    LAYER_MASK = list(map(get_ly_mask, patlist))
    
return_layer_mask()

def get_lc(ones):
    """assigns a layer count of 1 for at least 1 hit in a mask for a given layer, else assign layer count of 0"""
    if ones >= 1:
        return 1
    else:
        return 0

def create_lc_id_pair(lc, mask):
    """creates pair of layer count and pattern id"""
    return [lc, mask.id]

def get_lc_id(data, MAX_SPAN=37):
    """takes in the data (list of each layer's data) to determine the layer count that would be obtained from the data overlaying any mask; returns id and layer count for each mask"""
    lc_vec_x = []
    # and the layer data with the respective layer mask to determine how many hits are in each layer
    for v in range(len(LAYER_MASK)):
        ly_hits = [] 
        for i in range(N_LAYERS):
            ly_hits.append(data[i] & LAYER_MASK[v].mask[i])
 
        # count the hits in each layer and store in ly_ones
        ly_ones = list(map(count_ones, ly_hits))
        # assign a layer count for each layer
        layer_count = list(map(get_lc, ly_ones))
        # total up layer counts for each layer to get pattern's total layer count
        lc_vec_x.append(sum(layer_count))

    # return list of corresponding total layer counts and pattern ids 
    return list(map(create_lc_id_pair, lc_vec_x, LAYER_MASK))

def test_get_lc_id():
    """ test function for get_lc_id """
    assert get_lc_id([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 37) == [[6, 15], [4, 14], [4, 13], [3, 12], [3, 11], [2, 10], [2, 9], [2, 8], [2, 7], [2, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000], 37) == [[5, 15], [4, 14], [4, 13], [3, 12], [4, 11], [2, 10], [1, 9], [2, 8], [1, 7], [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ) == [[4, 15], [6, 14], [3, 13], [5, 12], [3, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ) == [[3, 15], [5, 14], [2, 13], [4, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ) == [[2, 15], [4, 14], [1, 13], [3, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ) == [[1, 15], [3, 14], [1, 13], [2, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id([0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ) == [[0, 15], [2, 14], [2, 13], [2, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]

def get_seg(lc_id_pair, strip):
    """creates segment object for a given pair of layer count and pattern id"""
    seg = Segment(lc_id_pair[0], lc_id_pair[1], strip)
    seg.get_quality()
    return seg

def process_pat(data, strip=None, MAX_SPAN=37):
    """takes in sample data for each layer and returns best segment"""

    lc_id_vec = get_lc_id(data, MAX_SPAN)
    seg_list = [get_seg(lc_id_pair, strip) for lc_id_pair in lc_id_vec]

    return max(seg_list)

def test_process_pat():
    assert process_pat([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 37).id == 15
    assert process_pat([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 37).lc == 6 
    assert process_pat([0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000], 37).id == 15
    assert process_pat([0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000], 37).lc == 5
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 6
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 5
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert process_pat([0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 4
    assert process_pat([0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert process_pat([0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 3
    assert process_pat([0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).id == 14
    assert process_pat([0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000], 37 ).lc == 2