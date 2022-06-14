# Python implementation of the pat_unit.vhd behavior
from subfunc import *
from constants import *

def get_ly_mask(ly_pat, MAX_SPAN=37):
    """takes in a given layer pattern and returns a list of integer bit masks for each layer"""
    assert (
        type(ly_pat) == patdef_t
    ), "ly_pat input must be defined in the patdef_t class"
    assert (
        type(ly_pat.ly0) == hi_lo_t
    ), "each layer of ly_pat must be of the class hi_lo_t"
    assert type(ly_pat.id) == int, "ly_pat's id must be an integer"
    assert type(MAX_SPAN) == int, "MAX_SPAN input must be an integer"
    m_vec = []
    center = round(MAX_SPAN / 2)
    m_vals = []
    #create list of pattern layers
    ly_list = [ly_pat.ly0, ly_pat.ly1, ly_pat.ly2, ly_pat.ly3, ly_pat.ly4, ly_pat.ly5] 
    #for each layer, shift the provided hi and lo values for each layer from pattern definition by center
    for layer in ly_list: 
        hi = layer.hi + center
        lo = layer.lo + center
        m_vals.append([lo, hi])
    # use the high and low indices to determine where the high bits must go for each layer
    for i in range(len(m_vals)):
        high_bits = 0
        # keep setting high bits from the low index to the high index; leave all else as low bits
        for index in range(m_vals[i][0], m_vals[i][1] + 1):
            val = 1 << index
            high_bits = high_bits | val
        m_vec.append(high_bits)
    return m_vec

def test_get_ly_mask():
    """ test function for get_ly_mask """
    assert get_ly_mask(pat_straight) ==[0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1000000000000000000, 0b11100000000000000000, 0b11100000000000000000]
    assert get_ly_mask(pat_l) ==[0b111100000000000000, 0b1111000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000000, 0b11110000000000000000000]
    assert get_ly_mask(pat_r) == [0b11110000000000000000000, 0b1111000000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b1111000000000000000, 0b111100000000000000]
    assert get_ly_mask(pat_l2) == [0b11110000000000000, 0b11111100000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11110000000000000000000, 0b111100000000000000000000] 
    assert get_ly_mask(pat_r2) == [0b111100000000000000000000, 0b11111100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b111100000000000000, 0b11110000000000000]
    assert get_ly_mask(pat_l3) == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000, 0b111100000000000000000000000]
    assert get_ly_mask(pat_r3) == [0b111100000000000000000000000, 0b11110000000000000000000000, 0b1111000000000000000000, 0b111110000000000000000, 0b111100000000000, 0b11110000000000]
    assert get_ly_mask(pat_l4) == [0b11110000000000, 0b111100000000000, 0b1111000000000000000, 0b111110000000000000000, 0b11110000000000000000000000,
 0b111100000000000000000000000] 

def get_lc_id(patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN):
    """takes in patlist and the data from each layer to determine the layer count that would be obtained from the data overlaying any mask; returns id and layer count for each mask"""
    corr_pat_id = []
    pats_m = []
    for w in range(len(patlist)):
        pats_m.append(get_ly_mask(patlist[w], MAX_SPAN))
    lc_vec_x = []
    lc_id_vec = []
    data = [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x]

    # and the layer data with the respective mask layer to determine how many hits are in each layer
    for v in range(len(patlist)):
        ly_hits = [] 
        for i in range(N_LAYERS):
            ly_hits.append(data[i] & pats_m[v][i])
 
        # count the hits in each layer and store in ly_ones
        ly_ones = []
        for ly in ly_hits:
            ly_ones.append(count_ones(ly))
 
        # assign a layer count of 1 for at least 1 hit in a mask for a given layer, else assign layer count of 0
        layer_count = []
        for j in range(len(ly_ones)):
            if ly_ones[j] >= 1:
                layer_count.append(1)
            else:
                layer_count.append(0)

        # total up layer counts for each layer to get pattern's total layer count
        lc_vec_x.append(sum(layer_count))

    #add layer id to corr_pat_id
    for i in range(len(patlist)):
        corr_pat_id.append(patlist[i].id)

    # match the correct pattern id to its total layer count
    for p in range(len(patlist)):
        lc_id_vec.append([lc_vec_x[p], corr_pat_id[p]])

    return lc_id_vec

def test_get_lc_id():
    """ test function for get_lc_id """
    assert get_lc_id(patlist, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 37) == [[6, 15], [4, 14], [4, 13], [3, 12], [3, 11], [2, 10], [2, 9], [2, 8], [2, 7], [2, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 37) == [[5, 15], [4, 14], [4, 13], [3, 12], [4, 11], [2, 10], [1, 9], [2, 8], [1, 7], [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == [[4, 15], [6, 14], [3, 13], [5, 12], [3, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == [[3, 15], [5, 14], [2, 13], [4, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == [[2, 15], [4, 14], [1, 13], [3, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == [[1, 15], [3, 14], [1, 13], [2, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]
    assert get_lc_id(patlist, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == [[0, 15], [2, 14], [2, 13], [2, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]

def priority_encoder(lc_id_vec):
    """
    receives a list of layer counts and ids from each mask and the layer data
    to determine which pattern is the best fit, based on the highest layer
    count; returns the id of this best pattern; if the layer count is the same
    for two patterns, the pattern higher id will be returned

    """
    max_lc = 0
    max_id = 0
    s_list = []

    # find the highest layer count and save its index r
    for r in range(len(lc_id_vec)):
        if lc_id_vec[r][0] >= max_lc:
            max_lc = lc_id_vec[r][0]

    # check if any other patterns have the same layer count as the max layer count and save these values to s_list
    for s in range(len(lc_id_vec)):
        if lc_id_vec[s][0] == max_lc:
            s_list.append(lc_id_vec[s])

    # check which id value in slist has the highest pattern id; save the index as the best pattern index
    for t in range(len(s_list)):
        if s_list[t][1] > max_id:
            max_id = s_list[t][1]
            b_pat_index = t

    # choose the highest layer count and pattern id from s_list
    [b_lc, b_id] = s_list[b_pat_index]
    b_lc = int(b_lc)
    b_id = int(b_id)
    return b_lc, b_id

def test_priority_encoder():
    assert priority_encoder([[6, 15], [4, 14], [4, 13], [3, 12], [3, 11], [2, 10], [2, 9], [2, 8], [2, 7], [2, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]) == (6, 15)
    assert priority_encoder([[5, 15], [4, 14], [4, 13], [3, 12], [4, 11], [2, 10], [1, 9], [2, 8], [1, 7], [1, 6], [1, 5], [1, 4], [1, 3], [1, 2], [1, 1]]) == (5, 15)
    assert priority_encoder([[4, 15], [6, 14], [3, 13], [5, 12], [3, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [2, 5], [1, 4], [1, 3], [1, 2], [1, 1]]) == (6, 14)
    assert priority_encoder([[3, 15], [5, 14], [2, 13], [4, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]) == (5, 14)
    assert priority_encoder([[2, 15], [4, 14], [1, 13], [3, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]) == (4, 14)
    assert priority_encoder([[1, 15], [3, 14], [1, 13], [2, 12], [1, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]) == (3, 14)
    assert priority_encoder([[0, 15], [2, 14], [2, 13], [2, 12], [2, 11], [1, 10], [2, 9], [1, 8], [2, 7], [1, 6], [1, 5], [1, 4], [1, 3], [2, 2], [1, 1]]) == (2, 14) 


def process_pat(patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN=37):

    """
    takes in a list of patterns and sample data for each layer to generate a
    layer count and id for the pattern that best matches the data. Returns best id, layer count
    """

    lc_id_vec = get_lc_id(patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN)

    [ly_c, pat_id] = priority_encoder(lc_id_vec)
    if ly_c == 0:
        pat_id = 0
    return pat_id, ly_c

def test_process_pat():
    assert process_pat(patlist, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 37) == (15, 6)
    assert process_pat(patlist, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 37) == (15, 5)
    assert process_pat(patlist, 0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == (14, 6)
    assert process_pat(patlist, 0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == (14, 5)
    assert process_pat(patlist, 0b100000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == (14, 4)
    assert process_pat(patlist, 0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == (14, 3)
    assert process_pat(patlist, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 37 ) == (14, 2)
