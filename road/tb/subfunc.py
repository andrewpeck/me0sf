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
    [hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(0, 0),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1)]
)
pat_l = patdef_t(
    14,
    [hi_lo_t(-1, -4),
    hi_lo_t(0, -3),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(3, 0),
    hi_lo_t(4, 1)]
)
pat_r = mirror_patdef(pat_l, pat_l.id - 1)
pat_l2 = patdef_t(
    12,
    [hi_lo_t(-2, -5),
    hi_lo_t(1, -4),
    hi_lo_t(1, -1),
    hi_lo_t(1, -1),
    hi_lo_t(4, 1),
    hi_lo_t(5, 2)]
)
pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
pat_l3 = patdef_t(
    10,
    [hi_lo_t(-5, -8),
    hi_lo_t(-4, -7),
    hi_lo_t(0, -3),
    hi_lo_t(2, -2),
    hi_lo_t(7, 4),
    hi_lo_t(8, 5)]
)
pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
pat_l4 = patdef_t(
    8,
    [hi_lo_t(-5, -8),
    hi_lo_t(-4, -7),
    hi_lo_t(0, -3),
    hi_lo_t(2, -2),
    hi_lo_t(7, 4),
    hi_lo_t(8, 5)]
)
pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
pat_l5 = patdef_t(
    6,
    [hi_lo_t(-8, -11),
    hi_lo_t(-5, -9),
    hi_lo_t(0, -3),
    hi_lo_t(3, 0),
    hi_lo_t(9, 5),
    hi_lo_t(11, 8)]
)
pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
pat_l6 = patdef_t(
    4,
    [hi_lo_t(-11, -15),
    hi_lo_t(-9, -11),
    hi_lo_t(4, -9),
    hi_lo_t(9, 4),
    hi_lo_t(11, 9),
    hi_lo_t(15, 11)]
)
pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
pat_l7 = patdef_t(
    2,
    [hi_lo_t(-10, -18),
    hi_lo_t(-6, -14),
    hi_lo_t(2, -9),
    hi_lo_t(9, 2),
    hi_lo_t(14, 6),
    hi_lo_t(18, 10)]
)
pat_r7 = mirror_patdef(pat_l7, pat_l7.id - 1)

patlist = [
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
]


def count_ones(int_ones):
    """takes in an integer and counts how many ones are in that integer's binary form"""
    assert type(int_ones) == int, "int_ones input must be an integer."
    n_ones = 0
    iterable = bin(int_ones)[2:]
    for i in range(len(iterable)):
        if iterable[i] == "1":
            n_ones = n_ones + 1
    return n_ones


def set_bit(index, num1=0):
    """takes in an integer index to set a one within a binary number; if num1 parameter is filled with an integer, that is the binary number it sets the bit within"""
    assert type(index) == int, "index input must be an integer."
    assert type(num1) == int, "num1 input must be an integer."
    num2 = 1 << index
    final_v = num1 | num2
    return final_v


def clear_bit(num, index):
    """takes in an integer num and an integer index; clears the value of the index within the binary version of num and returns the new num as an integer"""
    assert type(num) == int, "num input must be an integer."
    assert type(index) == int, "index input must be an integer."
    bit = 1 & (num >> index)
    return num ^ (bit << index)


def ones_bit_mask(num):
    """takes in an integer num; converts num into its binary version and returns mask of ones the same length as this binary version as an integer"""
    assert type(num) == int, "num input must be an integer"
    o_mask = 0
    iterable_data = bin(num)[2:]
    for m in range(len(iterable_data)):
        mask_1 = 1 << m
        o_mask = o_mask | mask_1
    return o_mask


def get_mypattern(pat_id: int, patlist: "List[patdef_t]") -> patdef_t:
    assert type(pat_id) == int, "pat_id input must be an integer"
    assert (
        type(patlist) == list
    ), "patlist input must be a list of patdef_t class values"
    assert (
        type(patlist[0]) == patdef_t
    ), "each value in patlist input must be of the class patdef_t"
    assert (
        type(patlist[0].ly0) == hi_lo_t
    ), "each patlist layer must be of the class hi_lo_t"
    assert type(patlist[0].id) == int, "each patlist id must be an integer"
    for i in range(len(patlist)):
        if patlist[i].id == pat_id:
            mypattern = patlist[i]
    return mypattern

