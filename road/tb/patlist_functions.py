from math import ceil, floor

class patdef_t:
    def __init__(self, id, layer_list):
        self.id = id
        self.layers = layer_list

class hi_lo_t:
    def __init__(self, hi, lo):
        self.hi = hi
        self.lo = lo

def mirror_hi_lo(ly : hi_lo_t):
    """"helper function for mirror_patdef, mirrors the hi and lo values"""
    return hi_lo_t(ly.lo * (-1), ly.hi * (-1))

def mirror_patdef(pat : patdef_t, id : int):
    """takes in a pattern definition and an id and returns a mirrored pattern definition associated with that id"""
    assert type(pat) == patdef_t, "pat input must be of the class patdef_t"
    assert type(pat.layers[0]) == hi_lo_t, "each layer of pat must be of the class hi_lo_t"
    assert type(id) == int, "id input must be an integer"

    mirrored_ly = list(map(mirror_hi_lo, pat.layers))
    mirrored_pat = patdef_t(id, mirrored_ly)
    return mirrored_pat
    

def create_pat_ly(lower : float, upper : float):

    """
    takes in two boundary slopes and returns a list of hi lo pairs for each
    layer to use when creating patterns
    """

    layer_list = [hi_lo_t(-1,-1)]*6

    for i in range(6):

        if i < 3:
            hi = lower*(i-2.5)
            lo = upper*(i-2.5)
        else:
            hi = upper*(i-2.5)
            lo = lower*(i-2.5)

        if abs(hi) < 0.1:
            hi = 0
        if abs(lo) < 0.1:
            lo = 0 

        layer_list[i] = hi_lo_t(ceil(hi), floor(lo))

    return layer_list

# Moved this from pat_unit_beh to save time on checks
# Default patlist
# construct the dynamic_patlist (we do not use default PATLIST anymore)
# for robustness concern, other codes might use PATLIST, so we kept the default PATLIST in subfunc
# however, this could cause inconsistent issue, becareful! OR find a way to modify PATLIST
num_or = 2
factor = num_or / 2

pat_straight = patdef_t(17, create_pat_ly(-0.4 / factor, 0.4 / factor))
pat_l = patdef_t(16, create_pat_ly(0.2 / factor, 0.9 / factor))
pat_r = mirror_patdef(pat_l, pat_l.id - 1)
pat_l2 = patdef_t(14, create_pat_ly(0.9 / factor, 1.7 / factor))
pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
pat_l3 = patdef_t(12, create_pat_ly(1.4 / factor, 2.3 / factor))
pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
pat_l4 = patdef_t(10, create_pat_ly(2.0 / factor, 3.0 / factor))
pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
pat_l5 = patdef_t(8, create_pat_ly(2.7 / factor, 3.8 / factor))
pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
pat_l6 = patdef_t(6, create_pat_ly(3.5 / factor, 4.7 / factor))
pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
pat_l7 = patdef_t(4, create_pat_ly(4.3 / factor, 5.5 / factor))
pat_r7 = mirror_patdef(pat_l7, pat_l7.id - 1)
pat_l8 = patdef_t(2, create_pat_ly(5.4 / factor, 7.0 / factor))
pat_r8 = mirror_patdef(pat_l8, pat_l8.id - 1)

DEFAULT_PATLIST = (
    pat_r8,
    pat_l8, 
    pat_r7,
    pat_l7,
    pat_r6,
    pat_l6,
    pat_r5,
    pat_l5,
    pat_r4,
    pat_l4,
    pat_r3,
    pat_l3,
    pat_r2,
    pat_l2,
    pat_r,
    pat_l,
    pat_straight)
