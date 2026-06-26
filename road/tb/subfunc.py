# Functions, global variables, and classes used in multiple files

from patlist_functions import *
from fit_func import reciprocal6, reciprocal, fx, vhdl_exact_fit

from itertools import islice
from math import ceil, floor
from typing import List
import math
import numpy as np

LAYER_MASK = None

class Peaking_Manager:
    def __init__(self):
        self.segs = [[[None for _ in range(192)] for _ in range(15)] for _ in range(2)]
        self.trigger = np.zeros((15,192), dtype=bool) # partition, strip
        self.delays = np.zeros((15,192), dtype=np.int16) # partition, strip

        #self.three_seq_LUT ={(1, 1, 1): 0, (1, 1, 0): -1, (1, 0, 0): -1, (2, 2, 2): 0, (1, 2, 2): 0, (1, 1, 2): 0, (2, 2, 0): -1, (1, 2, 0): 0, (2, 0, 0): -1, (2, 2, 1): 0, (1, 2, 1): 0, (2, 1, 0): -1, (2, 1, 1): 0, (1, 0, 1): -1, (3, 3, 3): 0, (2, 3, 3): 0, (2, 2, 3): 0, (1, 3, 3): 0, (1, 2, 3): 1, (1, 1, 3): 1, (3, 3, 0): -1, (2, 3, 0): 0, (1, 3, 0): 0, (3, 0, 0): -1, (3, 3, 1): 0, (2, 3, 1): 0, (1, 3, 1): 0, (3, 1, 0): -1, (3, 1, 1): -1, (2, 0, 1): -1, (3, 3, 2): 0, (2, 3, 2): 0, (1, 3, 2): 0, (3, 2, 0): -1, (3, 2, 1): -1, (3, 2, 2): 0, (2, 1, 2): 0, (1, 0, 2): 1, (2, 0, 2) : -1} 


        #self.three_seq_LUT = {(4, 4, 4): 0, (4, 4, 1): -1, (4, 1, 1): -1, (4, 4, 2): -1, (4, 2, 1): -1, (4, 2, 2): -1, (4, 4, 3): 0, (4, 3, 1): -1, (4, 3, 2): -1, (4, 3, 3): -1, (5, 5, 5): 0, (4, 5, 5): 0, (4, 4, 5): 0, (5, 5, 2): -1, (4, 5, 2): 0, (5, 2, 2): -1, (4, 1, 2): -1, (5, 5, 3): 0, (4, 5, 3): 0, (5, 3, 2): -1, (5, 3, 3): -1, (4, 2, 3): -1, (5, 5, 4): 0, (4, 5, 4): 0, (5, 4, 2): -1, (5, 4, 3): -1, (5, 4, 4): 0, (4, 3, 4): -1, (6, 6, 6): 0, (5, 6, 6): 0, (5, 5, 6): 0, (4, 6, 6): 0, (4, 5, 6): 1, (4, 4, 6): 1, (6, 6, 3): -1, (5, 6, 3): 0, (4, 6, 3): 0, (6, 3, 3): -1, (5, 2, 3): -1, (4, 1, 3): -1, (6, 6, 4): 0, (5, 6, 4): 0, (4, 6, 4): 0, (6, 4, 3): -1, (6, 4, 4): -1, (5, 3, 4): -1, (4, 2, 4): -1, (6, 6, 5): 0, (5, 6, 5): 0, (4, 6, 5): 0, (6, 5, 3): -1, (6, 5, 4): -1, (6, 5, 5): 0, (5, 4, 5): 0, (4, 3, 5): 1, (5, 5, 0) : -1, (4, 4, 0) : -1, (4, 0, 0) : -1, (5, 4, 0) : -1, (4, 5, 0) : -1, (6, 6, 0) : -1, (6, 5, 0) : -1, (5, 6, 0) : -1}
        
        # Bias late
        #self.three_seq_LUT = {(4, 4, 4): 0, (4, 4, 1): -1, (4, 1, 1): -1, (4, 4, 2): -1, (4, 2, 1): -1, (4, 2, 2): -1, (4, 4, 3): 0, (4, 3, 1): -1, (4, 3, 2): -1, (4, 3, 3): -1, (5, 5, 5): 0, (4, 5, 5): 0, (4, 4, 5): 0, (5, 5, 2): -1, (4, 5, 2): 0, (5, 2, 2): -1, (4, 1, 2): -1, (5, 5, 3): 0, (4, 5, 3): 0, (5, 3, 2): -1, (5, 3, 3): -1, (4, 2, 3): -1, (5, 5, 4): 0, (4, 5, 4): 0, (5, 4, 2): -1, (5, 4, 3): -1, (5, 4, 4): 0, (4, 3, 4): 1, (6, 6, 6): 0, (5, 6, 6): 0, (5, 5, 6): 0, (4, 6, 6): 0, (4, 5, 6): 1, (4, 4, 6): 1, (6, 6, 3): -1, (5, 6, 3): 0, (4, 6, 3): 0, (6, 3, 3): -1, (5, 2, 3): -1, (4, 1, 3): -1, (6, 6, 4): 0, (5, 6, 4): 0, (4, 6, 4): 0, (6, 4, 3): -1, (6, 4, 4): -1, (5, 3, 4): -1, (4, 2, 4): 1, (6, 6, 5): 0, (5, 6, 5): 0, (4, 6, 5): 0, (6, 5, 3): -1, (6, 5, 4): -1, (6, 5, 5): 0, (5, 4, 5): 0, (4, 3, 5): 1, (5, 5, 0) : 0, (4, 4, 0) : 0, (4, 0, 0) : 0, (5, 4, 0) : 0, (4, 5, 0) : 0, (6, 6, 0) : -1, (6, 5, 0) : -1, (5, 6, 0) : 0, (6, 4, 0) : -1, (5, 0, 0) : -1, (4, 0, 4) : 0, (6, 0, 0) : -1, (4, 0, 5) : 1, (4, 0, 6) : 1, (5, 0, 4) : -1, (4, 6, 0) : 0, (6, 4, 5) : -1, (6, 0, 4) : -1, (6, 5, 6) : 0, (5, 0, 6) : 1, (5, 4, 6) : 1, (5, 0, 5) : -1, (6, 0, 5) : -1, (6, 0, 6) : -1}

        # Adjusted based on N=[0,999] run
        self.three_seq_LUT = {(4, 4, 4): 0, (4, 4, 1): -1, (4, 1, 1): -1, (4, 4, 2): -1, (4, 2, 1): -1, (4, 2, 2): -1, (4, 4, 3): 0, (4, 3, 1): -1, (4, 3, 2): -1, (4, 3, 3): -1, (5, 5, 5): 0, (4, 5, 5): 0, (4, 4, 5): 0, (5, 5, 2): -1, (4, 5, 2): 0, (5, 2, 2): -1, (4, 1, 2): -1, (5, 5, 3): 0, (4, 5, 3): 0, (5, 3, 2): -1, (5, 3, 3): -1, (4, 2, 3): -1, (5, 5, 4): 0, (4, 5, 4): 0, (5, 4, 2): -1, (5, 4, 3): -1, (5, 4, 4): 0, (4, 3, 4): 1, (6, 6, 6): 0, (5, 6, 6): 0, (5, 5, 6): 0, (4, 6, 6): 0, (4, 5, 6): 1, (4, 4, 6): 1, (6, 6, 3): -1, (5, 6, 3): 0, (4, 6, 3): 0, (6, 3, 3): -1, (5, 2, 3): -1, (4, 1, 3): -1, (6, 6, 4): 0, (5, 6, 4): 0, (4, 6, 4): 0, (6, 4, 3): -1, (6, 4, 4): 0, (5, 3, 4): -1, (4, 2, 4): 1, (6, 6, 5): 0, (5, 6, 5): 0, (4, 6, 5): 0, (6, 5, 3): -1, (6, 5, 4): 0, (6, 5, 5): 0, (5, 4, 5): 0, (4, 3, 5): 1, (5, 5, 0) : -1, (4, 4, 0) : -1, (4, 0, 0) : 0, (5, 4, 0) : 0, (4, 5, 0) : 0, (6, 6, 0) : -1, (6, 5, 0) : -1, (5, 6, 0) : 0, (6, 4, 0) : -1, (5, 0, 0) : -1, (4, 0, 4) : 0, (6, 0, 0) : -1, (4, 0, 5) : 1, (4, 0, 6) : 1, (5, 0, 4) : 0, (4, 6, 0) : 0, (6, 4, 5) : -1, (6, 0, 4) : 0, (6, 5, 6) : 0, (5, 0, 6) : 1, (5, 4, 6) : 1, (5, 0, 5) : 0, (6, 0, 5) : -1, (6, 0, 6) : -1}


class Vector_Manager:
    def __init__(self):
        self.vectors = np.zeros((15,192,3,17,6), dtype=np.uint32) # partition, strip, bx, pid, ly
        self.lcs = np.zeros((15,192,3,17), dtype=np.uint8) # partition, strip, bx, pid

    def shift_regs(self, new_vectors, new_lcs, partition, strip):
        self.vectors[partition, strip] = np.concatenate((self.vectors[partition,strip,1:], new_vectors[np.newaxis, :]))
        self.lcs[partition, strip] = np.concatenate((self.lcs[partition,strip,1:], new_lcs[np.newaxis, :]))

    def or_vectors(self, partition, strip):
        return np.bitwise_or(np.bitwise_or(self.vectors[partition,strip,0], self.vectors[partition,strip,1]), self.vectors[partition,strip,2])
 
class Config:

    def __init__(self, patlist=DEFAULT_PATLIST):
        # For pulse stretching, store 192-bit integer for sbit information as 3 64-bit np.uint64s. When calculating pulse streching, probably better to have the BXs and VFATs as the inner dimensions for better cache locality.
        # Initialize sbit storage here, so it is not shared between different Config objects, which causes following tests to still see old data that may interfere.
        self.sbits_pulse_stretched = np.zeros((8, 6, 3, 3), dtype=np.uint64) # Used for sbits pulse stretching; dimensions = (partitions, layers, limbs, BXs)
        self.initialize_patlist(patlist)
        
    def start_peaking_manager(self):
        self.old_segments = [Segment(0, 0) for _ in range(8)]
        self.peaking_manager = Peaking_Manager()
        self._peaking_enabled = True

    def start_vectoring_manager(self):
        self.vector_manager = Vector_Manager()
        self.vectoring_enabled = True

    def calculate_ly_spans(self):
        max_spans = [0 for _ in range(6)]
        for pat in self.patlist:
            for ly_i, ly in enumerate(pat.layers):
                max_spans[ly_i] = max(max_spans[ly_i], ly.hi)

        self.ly_spans = tuple([sp*2 + 1 for sp in max_spans])

    def shift_center(self, ly, ly_span):
        """Patterns are defined as a +hi and -lo around a center point of a pattern. e.g. for a pattern 37 strips wide, there is a central strip,
        and 18 strips to the left and right of it. This patterns shifts from a +hi and -lo around the central strip, to an offset +hi and -lo.
        e.g. for (hi, lo) = (1, -1) and a window of 37, this will return (17,19)"""

        center = math.floor(ly_span/2)
        hi = ly.hi + center
        lo = ly.lo + center
        return (lo, hi)
    
    def set_high_bits(self, lo_hi_pair):
        """Given a high bit and low bit, this function will return a bitmask with all the bits in between the high and low set to 1"""
        hi = lo_hi_pair[1]
        lo = lo_hi_pair[0]
        return 2**(hi-lo+1)-1 << lo

    def get_ly_mask(self, ly_pat : patdef_t, ly_spans : List[int]):
        """takes in a given layer pattern and returns a list of integer bit masks for each layer"""

        #for each layer, shift the provided hi and lo values for each layer from pattern definition by center
        m_vals = [self.shift_center(ly, span) for ly, span in zip(ly_pat.layers, ly_spans)]

        # use the high and low indices to determine where the high bits must go for each layer
        m_vec = np.array([self.set_high_bits(x) for x in m_vals])
        return m_vec
        # return Mask(m_vec, ly_pat.id)

    # Computes the spans of all pattern windows, for use in shifting the coordinate origin for the substrip output by the fitter
    def initialize_pat_spans(self, patlist):
        pat_spans = []
        # Highest high and lowest low for a pattern must be in either layer 0 or layer 5, so only need to check these 4 values
        for pat in patlist:
            high = max(pat.layers[0].hi, pat.layers[5].hi)
            low = min(pat.layers[0].lo, pat.layers[5].lo)
            pat_spans.append(high - low + 1)

        return pat_spans

    # Computes the offset for each [pid, ly] that is used in pat_unit to align sbit data for the centroid finder
    def initialize_offset_LUT(self, patlist):
        LUT = []
        for pat, pat_span in zip(patlist, self.pat_spans):

            max_span = self.ly_spans[0]//2 # Use one of the outer layers to get the max_span
 
            shift_amount_left = [max_span - ly_span//2 for ly_span in self.ly_spans] # This shift will go from hourglass shape -> rectangular (i.e. origin is aligned for all layers)
            shift_amount_right = max_span - pat_span//2 # This shift will get only the pattern bits, and is constant for all layers. Depends only on the pattern and max_span. Shifts the origin to the rightmost bit of the pattern mask.

            LUT.append([left - shift_amount_right for left in shift_amount_left])
        return LUT
       

    def initialize_patlist(self, patlist):
        self.patlist = patlist
        self.calculate_ly_spans()
        """create layer masks for patterns in patlist"""
        self.ly_mask = np.array([self.get_ly_mask(pat, self.ly_spans) for pat in self.patlist], dtype=np.uint64)
        self.pat_spans = self.initialize_pat_spans(patlist)
        self.offset_LUT = self.initialize_offset_LUT(patlist)
 

    patlist = None
    ly_mask = None
    ly_spans : List[int] = [0 for _ in range(6)]

    skip_centroids : bool = False
    deghost_pre : bool = True
    deghost_post : bool = False
    x_prt_en : bool = True
    en_non_pointing : bool = False
    check_ids : bool = False
    pulse_stretch_bx : int = 0 # Number of BX to pulse stretch for, usually 0 or 2
    bend_ang_cut = 1.0

    # This should only be modified by the start_peaking() function, so should not be modified outside the class
    _peaking_enabled : bool = False

    @property
    def peaking_enabled(self):
        return self._peaking_enabled

    vectoring_enabled : bool = False # Vectoring not used, can be deleted later if no longer interested

    # Helper function to convert a chamber array of 3 uint64 limbs to Python integers.
    # TODO: Rework everything to work in 3 unit64 limbs for better vectorization
    def uint64x3_array_to_int(self, arr):
        bytes_view = arr.view(np.uint8).reshape(*arr.shape[:2], 24) # View the 3 uint64 limbs as 24 bytes
        out = np.empty(arr.shape[:2], dtype=object) # Initialize output array

        # Apply Python bytes->int function on each bytelist of chamber array
        for idx in np.ndindex(arr.shape[:2]):
            out[idx] = int.from_bytes(bytes_view[idx], byteorder="little", signed=False)
        return out

    def int_array_to_uint64x3(self, arr):
        arr = np.asarray(arr) # Convert to numpy array if it is not already
        out = np.empty(arr.shape + (3,), dtype=np.uint64)

        for idx in np.ndindex(arr.shape):
            x = int(arr[idx])
            b = x.to_bytes(24, byteorder="little", signed=False)
            out[idx] = np.frombuffer(b, dtype=np.uint64)

        return out

    def pulse_stretch(self, new_data):
        # Assuming input data is Python integers, convert into 3 np.uint64 limbs
        new_data_limbs = self.int_array_to_uint64x3(new_data)

        self.sbits_pulse_stretched[..., 1:] = self.sbits_pulse_stretched[..., :-1] # Shift data to the right along BX axis
        self.sbits_pulse_stretched[..., 0] = new_data_limbs # Insert new data

        stretched_data = np.bitwise_or.reduce(self.sbits_pulse_stretched, axis=3) # Bitwise OR along the BX axis to do the stretching

        stretched_data_ints = self.uint64x3_array_to_int(stretched_data)
        
        return stretched_data_ints

    ly_thresh_patid : list[int] = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    ly_thresh_eta : list[int] = [4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4]

    width : int = 192
    group_width : int = 8
    ghost_width : int = 1
    cross_part_seg_width : int = 4
    clearance_width: int = 0 # use 2 if you want to try this
    num_outputs : int = 4
    edge_distance : int = 2
    num_or : int = 2

class Mask:
    def __init__(self, mask, id):
        self.mask = mask
        self.id = id
    def __str__(self):
        s = ["{0:b}".format(x).zfill(38) + "\n" for x in self.mask]
        return ''.join(s)

class Segment:

    ignore_bend = False

    def __init__(self, lc, id, hc=0, strip=0, partition=0, centroid=None,
                 substrip=None, bend_ang=None, mse = None, bx=-9999,
                 max_cluster_size = None, max_noise = None,
                 nlayers_withcsg3 = None, nlayers_withcsg5 = None, nlayers_withcsg10 = None, nlayers_withcsg15 = None,
                 nlayers_withnoiseg3 = None, nlayers_withnoiseg5 = None, nlayers_withnoiseg10 = None, nlayers_withnoiseg15 = None,
                 slope = None, fit_strip = None, intercept = None):
        self.hc = hc
        self.lc = lc
        self.id = id
        self.strip = strip
        self.partition = partition
        self.centroid = centroid
        self.substrip = substrip
        self.bend_ang = bend_ang
        self.mse = mse
        self.bx = bx
        self.max_cluster_size = max_cluster_size
        self.max_noise = max_noise
        self.nlayers_withcsg3 = nlayers_withcsg3
        self.nlayers_withcsg5 = nlayers_withcsg5
        self.nlayers_withcsg10 = nlayers_withcsg10
        self.nlayers_withcsg15 = nlayers_withcsg15
        self.nlayers_withnoiseg3 = nlayers_withnoiseg3
        self.nlayers_withnoiseg5 = nlayers_withnoiseg5
        self.nlayers_withnoiseg10 = nlayers_withnoiseg10
        self.nlayers_withnoiseg15 = nlayers_withnoiseg15
        self.slope = slope
        self.fit_strip = fit_strip
        self.intercept = intercept
        self.valid = True if lc > 0 else False

        self.update_quality()

    def reset(self):
        self.valid = False
        self.hc = 0
        self.lc = 0
        self.id = 0
        self.update_quality()
        return self

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

        if (lc > 0):
            if self.ignore_bend:
                # 0xFE to ignore the least significant bit of the pattern id
                # which just specifies the direction of the bend, which we don't
                # really care about
                idmask = 0xFE
            else:
                idmask = 0xFF

            quality = (lc << 23) | (hc << 17) | ((id & idmask) << 12) | (strip << 4) | prt

        self.quality=quality

    def fit(self, pat_span):
        self.bend_ang = 0
        self.substrip = 0
        #print (self.centroid)
        if self.id !=0:
            #x = [i-2.5 for (i, cent) in enumerate(self.centroid) if cent > 0] #need to improve for lc<6?
            #centroids = [(cent/2)-(max_span//2+1) for cent in self.centroid if cent > 0] # Divide by factor 2 for double resolution
            #print (x)
            #print (centroids)
            #fit_llse = llse_fit(x, centroids)
            if self.centroid is None:
                print(self)
            valid_mask = [1 if cent > 0 else 0 for cent in self.centroid]
            fit = vhdl_exact_fit(self.centroid, valid_mask)

            # Resolution factor used in find_centroid is currently 2.0, so need to adjust here to interpret the results correctly

            self.bend_ang = fit[0] / 2.0 #m
            #self.substrip = fit[1] #b
            self.substrip = (fit[2] / 2.0) - pat_span//2 - 1 # b; Subtract pat_span//2 to shift origin to center of pattern window frame (aligned with segment's global integer strip so this and the substrip can be added together); Subtract another 1 to change form 1-indexing to 0-indexing
            #self.mse = fit_llse[2] #mse
            #self.mse = 0 # Fitter does not currently output a quality factor

            #print(f"Slope diff = {abs(fit_llse[0]-self.bend_ang)}")


    def __str__(self):

        if (self.lc==0):
            return "n/a"

        return f"id={self.id}, lc={self.lc}, strip={self.strip}, prt={self.partition}, quality={self.quality}"

    def __repr__(self):
        return f"Seg {self.quality}"

    def __eq__(self, other):

        # If both are invalid, consider them equal
        if (not self.valid and not other.valid):
            return True

        return self.quality == other.quality

    def __gt__(self, other):

        if isinstance(other, Segment):
            # Compare valid flags first for faster comparisons on average
            if self.valid and not other.valid:
                return True
            if not self.valid and other.valid:
                return False
            return self.quality > other.quality

    def __lt__(self, other):
        # Compare valid flags first for faster comparisons on average
        if self.valid and not other.valid:
            return False
        if not self.valid and other.valid:
            return True

        if isinstance(other, Segment):
            return self.quality < other.quality

def count_ones(x):
    # """takes in an integer and counts how many ones are in that integer's binary form"""
    return np.bitwise_count(x)

def max_cluster_size(x):
    """calculate maximum cluster size in that integer's binary form"""
    size = 0
    max_size = 0
    while (x > 0):
        if (x&1)==1:
            size += 1
        else:
            if size > max_size:
                max_size = size
            size = 0
        x = x>>1
    if size > max_size:
        max_size = size
    return max_size

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
    # note that the positions returned are in 1-index system
    return ones

def find_centroid(data : int):
    """get the centroid for some given binary hitmask"""

    ones = find_ones(data)

    if len(ones)==0:
        return 0, ones

    resolution_factor = 2.0 # 1.0 = single strip resolution, 2.0 = half strip resolution, ...; FW is bit-retricted, so this must match the FW implementation
    center_of_mass = (resolution_factor * sum(ones)) / len(ones)
    rounded_center = round(center_of_mass) # FW outputs the nearest integer to the true value

    return rounded_center, ones

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
    if len(x) == 0 or len(x) == 1:
        return 0, 0, 0
    x_sum = sum(x)
    y_sum = sum(y)
    n = len(x)
    products = 0
    squares = 0
    for i in range(len(x)):
        products += (n * x[i] - x_sum) * (n * y[i] - y_sum)
        squares += (n * x[i] - x_sum) ** 2

    if squares == 0:
        print(x)
        print(y)

    m = 1.0 * products / squares
    b = 1.0 / n * (y_sum - m * x_sum)
    
    # calculate mse
    sse = 0
    for i in range(len(x)):
        sse += (y[i] - m * x[i] - b)**2
    mse = sse / n
    
    return m, b, mse

def chunk(in_list, n):
    return [in_list[i * n:(i + 1) * n]
            for i in range((len(in_list) + n - 1) // n )]

Partition = List[Segment]
Chamber = List[Partition]

def get_sbits_from_event(event):
    hit_data = [[0 for _ in range(6)] for _ in range(8)]

    for tup in zip(event["me0_digi_hit_strip_i"], [e-1 for e in event["me0_digi_hit_eta_partition_i"]], [e-1 for e in event["me0_digi_hit_layer_i"]], event["me0_digi_hit_region_i"], event["me0_digi_hit_chamber_i"]):
        strip, prt, ly, reg, station = tup
        if reg == 1 and station == 1:
            hit_data[prt][ly] |= 1 << (int(strip)//2)

    return hit_data

# Finds the sim hits that are near a given segment, and finds the expected bending angle
def get_bending_angle_from_event(event, seg):

    if seg.partition % 2 != 0:
        print("Segment is from a cross-partition, not supported!")

    # TODO: add support for cross-partition segments
    hit_data = [0 for _ in range(6)]

    leftmost = 0
    rightmost = 383

    for tup in zip(event["me0_sim_hit_strip_i"], [e-1 for e in event["me0_sim_hit_eta_partition_i"]], [e-1 for e in event["me0_sim_hit_layer_i"]], event["me0_sim_hit_region_i"], event["me0_sim_hit_chamber_i"]):
        strip, prt, ly, reg, station = tup
        print(f"Hit found: {tup}")
        if reg == 1 and station == 1 and prt == seg.partition//2 and abs(strip - seg.strip*2) <= 36:
            leftmost = max(leftmost, strip)
            rightmost = min(rightmost, strip)

    return (rightmost-leftmost)/6 # Ouputs bending angle in strips/layer, where strips are the physical readout board strips (384 per layer)

# For debugging get_bending_angle_from_event
def debug_bending_angle_function():
    import uproot
    from read_ntuple import read_ntuple
    
    events = read_ntuple("test_data/step3_noPU.root")
    
    for i in [4]:
        seg = Segment(strip=71, partition=0, lc=6, id=17)
    
        event = events[i]
        get_bending_angle_from_event(event, seg)

if __name__ == "__main__":
    debug_bending_angle_function()

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

#def test_find_ones():
#    assert find_ones(0b100) == [3]
#    assert find_ones(0b111) == [1,2,3]
#    assert find_ones(0b001) == [1]
#
#def test_find_centroid():
#    assert find_centroid(0b001) == 1
#    assert find_centroid(0b010) == 2
#    assert find_centroid(0b100) == 3
#    assert find_centroid(0b101) == 2
#    assert find_centroid(0b110) == 2.5
#    assert find_centroid(0b111) == 2


