# Functions, global variables, and classes used in multiple files
from typing import List

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

    def __init__(self, lc, id, strip=None, partition=None, centroid=None,
                 substrip=None, bend_ang=None):
        self.lc = lc
        self.id = id
        self.strip = strip
        self.partition = partition
        self.centroid = centroid
        self.substrip = substrip
        self.bend_ang = bend_ang
        self.update_quality()

    def reset(self):
        self.lc = 0
        self.id = 0
        self.update_quality()

    def update_quality(self):
        """ create sortable number to compare segments"""
        lc = self.lc
        id = self.id
        prt = self.partition
        strip = self.strip

        prt = 0 if prt is None else prt
        strip = 0 if strip is None else strip

        quality = 0
        if (lc > 0):
            quality = prt  | (id << 12) | (lc << 17)
           #quality = prt | (strip << 4) | (id << 12) | (lc << 17)

        self.quality=quality

    def __eq__(self, other):
        if (self.lc == 0 and other.lc == 0):
            return True

        return self.id==other.id and self.lc==other.lc and self.strip==other.strip and \
            self.partition==other.partition and  \
            self.centroid==other.centroid and  \
            self.substrip==other.substrip and \
            self.bend_ang==other.bend_ang and \
            self.quality==other.quality

    def __str__(self):
        return f"id={self.id}, lc={self.lc}, strip={self.strip}, quality={self.quality}"

    def __repr__(self):
        return f"Seg {self.quality}"

    def __gt__(self, other):
        if isinstance(other, Segment):
            return self.quality > other.quality

    def __lt__(self, other):
        if isinstance(other, Segment):
            return self.quality < other.quality

def mirror_hi_lo(ly):
    """"helper function for mirror_patdef, mirrors the hi and lo values"""
    return hi_lo_t(ly.lo * (-1), ly.hi * (-1))

def mirror_patdef(pat, id):
    """takes in a pattern definition and an id and returns a mirrored pattern definition associated with that id"""
    assert type(pat) == patdef_t, "pat input must be of the class patdef_t"
    assert type(pat.layers[0]) == hi_lo_t, "each layer of pat must be of the class hi_lo_t"
    assert type(id) == int, "id input must be an integer"

    mirrored_ly = list(map(mirror_hi_lo, pat.layers))
    mirrored_pat = patdef_t(id, mirrored_ly)
    return mirrored_pat
    


# FIXME: take these globals out of here and bury them somewhere

# true patlist; only used for testing pat_unit.vhd emulator
pat_straight = patdef_t(
    15,
    (hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(0, 0),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1))
)
pat_l = patdef_t(
    14,
    (hi_lo_t(-1, -4),
    hi_lo_t(0, -3),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(3, 0),
    hi_lo_t(4, 1))
)
pat_r = mirror_patdef(pat_l, pat_l.id - 1)
pat_l2 = patdef_t(
    12,
    (hi_lo_t(-2, -5),
    hi_lo_t(1, -4),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(4, 1),
    hi_lo_t(5, 2))
)
pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
pat_l3 = patdef_t(
    10,
    (hi_lo_t(-5, -8),
    hi_lo_t(-4, -7),
    hi_lo_t(0, -3),
    hi_lo_t(2, -2),
    hi_lo_t(7, 4),
    hi_lo_t(8, 5))
)
pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
pat_l4 = patdef_t(
    8,
    (hi_lo_t(-5, -8),
    hi_lo_t(-4, -7),
    hi_lo_t(0, -3),
    hi_lo_t(2, -2),
    hi_lo_t(7, 4),
    hi_lo_t(8, 5))
)
pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
pat_l5 = patdef_t(
    6,
    (hi_lo_t(-8, -11),
    hi_lo_t(-5, -9),
    hi_lo_t(0, -3),
    hi_lo_t(3, 0),
    hi_lo_t(9, 5),
    hi_lo_t(11, 8))
)
pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
pat_l6 = patdef_t(
    4,
    (hi_lo_t(-11, -15),
    hi_lo_t(-9, -11),
    hi_lo_t(4, -9),
    hi_lo_t(9, 4),
    hi_lo_t(11, 9),
    hi_lo_t(15, 11))
)
pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
pat_l7 = patdef_t(
    2,
    (hi_lo_t(-10, -18),
    hi_lo_t(-6, -14),
    hi_lo_t(2, -9),
    hi_lo_t(9, 2),
    hi_lo_t(14, 6),
    hi_lo_t(18, 10))
)
pat_r7 = mirror_patdef(pat_l7, pat_l7.id - 1)

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
)

PATLIST_LUT = {
    15: pat_straight,
    14: pat_l,
    13: pat_r,
    12: pat_l2,
    11: pat_r2,
    10: pat_l3,
    9: pat_r3,
    8: pat_l4,
    7: pat_r4,
    6: pat_l5,
    5: pat_r5,
    4: pat_l6,
    3: pat_r6,
    2: pat_l7,
    1: pat_r7,
}


def count_ones(int_ones):
    """takes in an integer and counts how many ones are in that integer's binary form"""
    n_ones = 0
    iterable = bin(int_ones)[2:]
    for i in range(len(iterable)):
        if iterable[i] == "1":
            n_ones = n_ones + 1
    return n_ones


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
    """return a list with the positions of '1's in a string"""
    ones = []
    cnt = 0

    while (data > 0):
        if (data & 0x1):
            ones.append(cnt+1)
        data = data >> 1
        cnt = cnt + 1

    return ones

def test_find_ones():
    assert find_ones(0b100) == [3]
    assert find_ones(0b111) == [1,2,3]
    assert find_ones(0b001) == [1]
