# Functions, global variables, and classes used in multiple files
from itertools import islice
from math import ceil, floor
from typing import List
import math

class Config:
    hit_thresh : int = 4
    ly_thresh : int = 4
    max_span : int = 37
    width : int = 192
    deghost_pre : bool = True
    deghost_post : bool = True
    group_width : int = 8
    ghost_width : int = 1
    x_prt_en : bool = True
    en_non_pointing : bool = False
    cross_part_seg_width : int = 4
    num_outputs : int = 4
    check_ids : bool = False
    edge_distance : int = 2
    num_or : int = 2


class hi_lo_t:
    def __init__(self, hi, lo):
        self.hi = hi
        self.lo = lo

class patdef_t:
    def __init__(self, id, layer_list):
        self.id = id
        self.layers = layer_list

class Mask:
    def __init__(self, mask, id):
        self.mask = mask
        self.id = id
    def __str__(self):
        s = ["{0:b}".format(x).zfill(38) + "\n" for x in self.mask]
        return ''.join(s)

class Segment:

    def __init__(self, hc, lc, id, strip=0, partition=0, centroid=None,
                 substrip=None, bend_ang=None):
        self.hc = hc
        self.lc = lc
        self.id = id
        self.strip = strip
        self.partition = partition
        self.centroid = centroid
        self.substrip = substrip
        self.bend_ang = bend_ang
        self.update_quality()

    def reset(self):
        self.hc = 0
        self.lc = 0
        self.id = 0
        self.update_quality()

    def update_quality(self):
        """ create sortable number to compare segments"""
        hc = self.hc
        lc = self.lc
        id = self.id
        prt = self.partition
        strip = self.strip

        prt = 0 if prt is None else prt
        strip = 0 if strip is None else strip

        quality = 0
        if (hc > 0):
            quality = (lc << 23 | hc << 17) | (id << 12) | strip << 4 | prt

        self.quality=quality

    def fit(self, max_span=37):
        self.bend_ang = 0
        self.substrip = 0
        #print (self.centroid)
        if self.id !=0:
            centroids = [cent-(max_span//2+1) for cent in self.centroid]
            x = [i-2.5 for (i, cent) in enumerate(centroids) if cent !=-(max_span//2+1)] #need to improve for lc<6?
            centroids = [cent for cent in centroids if cent !=-(max_span//2+1)]
            #print (x)
            #print (centroids)
            fit = llse_fit(x, centroids)
            self.bend_ang = fit[0] #m
            self.substrip = fit[1] #b
            

    def __eq__(self, other):
        if (self.hc == 0 and other.hc == 0):
            return True

        return self.id==other.id and \
            self.hc==other.hc and self.lc==other.lc and \
            self.strip==other.strip and \
            self.quality==other.quality and \
            self.partition==other.partition
            # self.centroid==other.centroid and  \
            # self.substrip==other.substrip and \
            # self.bend_ang==other.bend_ang and \

    def __str__(self):
        if (self.id==0):
            return "n/a"

        return f"id={self.id}, hc={self.hc}, lc={self.lc}, strip={self.strip}, prt={self.partition}, quality={self.quality}"

    def __repr__(self):
        return f"Seg {self.quality}"

    def __gt__(self, other):
        if isinstance(other, Segment):
            return self.quality > other.quality

    def __lt__(self, other):
        if isinstance(other, Segment):
            return self.quality < other.quality

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

# for PATLIST initialization process
# true patlist; only used for testing pat_unit.vhd emulator
pat_straight = patdef_t(19, create_pat_ly(-0.4, 0.4))
pat_l = patdef_t(18, create_pat_ly(0.2, 0.9))
pat_r = mirror_patdef(pat_l, pat_l.id - 1)
pat_l2 = patdef_t(16, create_pat_ly(0.5, 1.2))
pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
pat_l3 = patdef_t(14, create_pat_ly(0.9, 1.7))
pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
pat_l4 = patdef_t(12, create_pat_ly(1.4, 2.3))
pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
pat_l5 = patdef_t(10, create_pat_ly(2.0, 3.0))
pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
pat_l6 = patdef_t(8, create_pat_ly(2.7, 3.8))
pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
pat_l7 = patdef_t(6, create_pat_ly(3.5, 4.7))
pat_r7 = mirror_patdef(pat_l7, pat_l7.id-1)
pat_l8 = patdef_t(4, create_pat_ly(4.3, 5.5))
pat_r8 = mirror_patdef(pat_l8, pat_l8.id-1)
pat_l9 = patdef_t(2, create_pat_ly(5.4, 7.0))
pat_r9 = mirror_patdef(pat_l9, pat_l9.id - 1)

PATLIST = (
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

PATLIST_LUT = {
    19: pat_straight,
    18: pat_l,
    17: pat_r,
    16: pat_l2,
    15: pat_r2,
    14: pat_l3,
    13: pat_r3,
    12: pat_l4,
    11: pat_r4,
    10: pat_l5,
    9: pat_r5,
    8: pat_l6,
    7: pat_r6,
    6: pat_l7,
    5: pat_r7,
    4: pat_l8,
    3: pat_r8,
    2: pat_l9,
    1: pat_r}

def count_ones(x):
    """takes in an integer and counts how many ones are in that integer's binary form"""
    cnt = 0
    while (x > 0):
        if (x&1)==1:
            cnt += 1
        x = x>>1
    return cnt

def set_bit(index, num1=0):
    """takes in an integer index to set a one within a binary number; if num1 parameter is filled
    with an integer, that is the binary number it sets the bit within"""
    num2 = 1 << index
    final_v = num1 | num2
    return final_v

def clear_bit(num, index):
    """takes in an integer num and an integer index; clears the value of the index within the binary
    version of num and returns the new num as an integer"""
    bit = 1 & (num >> index)
    return num ^ (bit << index)


def ones_bit_mask(num):
    """takes in an integer num; converts num into its binary version and returns mask of ones the
    same length as this binary version as an integer"""
    o_mask = 0
    iterable_data = bin(num)[2:]
    for m in range(len(iterable_data)):
        mask_1 = 1 << m
        o_mask = o_mask | mask_1
    return o_mask

def find_ones(data):
    """return a list with the positions of '1's in a number"""
    ones = []
    cnt = 0

    while (data > 0):
        if (data & 0x1):
            ones.append(cnt+1)
        data = data >> 1
        cnt = cnt + 1

    return ones

def find_centroid(data : int):
    """get the centroid for some given binary hitmask"""

    ones = find_ones(data)

    if len(ones)==0:
        return 0

    return (1.0 * sum(ones)) / len(ones)

def generate_combinations(nbits : int):
    return (nbits, tuple(range(2**nbits)))

def get_centroids(max_width : int):
    # set widths to current and anticipated pattern sizes
    all_widths = range(1, max_width)
    all_masks = tuple(map(generate_combinations, all_widths))

    centroids = []
    for (length,masks) in all_masks:
        y = (length, tuple(map (lambda x : (x, round(find_centroid(x))), masks)))
        centroids.append(y)

    return centroids

def llse_fit(x, y):
    x_sum = sum(x)
    y_sum = sum(y)
    n = len(x)

    products = 0
    squares = 0
    for i in range(len(x)):
        products += (n * x[i] - x_sum) * (n * y[i] - y_sum)
        squares += (n * x[i] - x_sum) ** 2
    m = 1.0 * products / squares
    b = 1.0 / n * (y_sum - m * x_sum)

    return m, b

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

Partition = List[Segment]
Chamber = List[Partition]

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def test_find_ones():
    assert find_ones(0b100) == [3]
    assert find_ones(0b111) == [1,2,3]
    assert find_ones(0b001) == [1]

def test_find_centroid():
    assert find_centroid(0b001) == 1
    assert find_centroid(0b010) == 2
    assert find_centroid(0b100) == 3
    assert find_centroid(0b101) == 2
    assert find_centroid(0b110) == 2.5
    assert find_centroid(0b111) == 2


