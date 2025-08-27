# Python implementation of the pat_unit.vhd behavior
import math
import numpy as np
from typing import List

from constants import *
from subfunc import *

def mask_layer_data (data, mask):
    """
    AND together a list of layer masks with a list of layers

    data is a 6 layer collection of integers

    mask is a 6 layer collection of masks

    """
    # return np.bitwise_and(data, mask)
    return list(map(lambda ly_dat, ly_mask: ly_dat & ly_mask , data, mask))

def calculate_centroids(single_pattern_masked_data : List[int], partition_bx_data) -> List[float]:
    """takes in a []*6 list of masked data and gives the found centroids"""
    centroids = []
    bxs = []
    for layer_index, layer in enumerate(single_pattern_masked_data):
        cur_centroid, hits_indices = find_centroid(layer)
        centroids.append(cur_centroid)
        for hit_index in hits_indices:
            bxs.append(partition_bx_data[layer_index][hit_index-1])
            #print(partition_bx_data[layer_index][hit_index-1])
    if len(bxs) == 0:
        return centroids, -9999
    #print(bxs)
    #print(np.mean(bxs))
    return centroids, np.mean(bxs)

def calculate_hit_count(masked_data, light : bool = False) -> int:
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
        return sum([min(7,np.bitwise_count(masked_data[ly])) for ly in enabled_layers])
    else:
        return sum([np.bitwise_count(x) for x in masked_data])

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
             bx_data,
             config : Config,
             strip : int = 0,
             ly_thresh_patid : list[int] = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4],
             ly_thresh_eta : list[int] = [4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4],
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


        dynamic_patlist = (
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
    #    for each of the 17 patterns, the masked []*6 layer data

    ####################################################################################


    hcs = [0]*17
    lcs = [0]*17
    pids = [0]*17

    pids = np.arange(1, 18, dtype=np.uint8)
    data_tiled = np.tile(data, (17, 1))

  #  spans = (37, 23, 9, 9, 23, 37)
  #  for pat in LAYER_MASK:
  #      for ly_i, ly in enumerate(pat):
  #         bin_str = format(ly, f"0{spans[ly_i]}b")
  #         print(' '*( ( (37 - len(bin_str)) // 2) ) + bin_str)

    masked_data = np.bitwise_and(LAYER_MASK, data_tiled)

    if light_hit_count:
        bit_count_arr = np.bitwise_count(np.vstack((masked_data[:,0], masked_data[:,5])).T)
    else:
        bit_count_arr = np.bitwise_count(masked_data)

    # HC IS DISABLED FOR NOW
    # hcs = np.sum(np.clip(bit_count_arr, a_min = None, a_max = 7), axis=1, dtype=np.uint16)
    hcs = np.zeros((17,), dtype=np.uint16)

    lcs = np.count_nonzero(masked_data, axis=1).astype(np.uint32)

    if config.vectoring_enabled:
        new_vectors = masked_data > 0

        config.vector_manager.shift_regs(new_vectors, lcs, partition, strip)

        # OR the 3 vectors together, for each PID
        # ord_vectors = config.vector_manager.or_vectors(partition, strip)

        # lcs = np.count_nonzero(ord_vectors, axis=1).astype(np.uint64)

        # if np.count_nonzero(config.vector_manager.lcs[partition,strip,1]) > 0:
        #     print(config.vector_manager.lcs[partition,strip])

        # lcs = config.vector_manager.lcs[partition, strip, 1]

        # Case of 2, 2, 2 and 3, 3: How to resolve? The current implementation will miss the 2,2,2 case ~=0.6% of cases
        # for i in range(len(lcs)):
        #     if not ((config.vector_manager.lcs[partition, strip, 1, i] >= config.vector_manager.lcs[partition, strip, 0, i]) and (config.vector_manager.lcs[partition, strip, 1, i] >= config.vector_manager.lcs[partition, strip, 2, i])):
        #         lcs[i] = 0
        
        #TODO: combine ^^ 2 of those lines in a function in vector_manager
        #TODO: create function in vector_manager to OR together the 3 vectors for a given partition, strip; call it here, and use that for LCs
        #TODO: only return segment if LC for central BX is highest. break ties somehow? (maybe with HC)
    
    combined_segs = np.bitwise_or(np.bitwise_or(np.left_shift(lcs, np.uint8(11)), np.left_shift(hcs, np.uint(5))), pids)
    best_pid = (np.sort(combined_segs))[-1] & 2**5-1

    #print(bxs)
    # (5) process segments
    # seg_list = [Segment(lc=lc,
    #                     hc=hc,
    #                     id=pid,
    #                     partition=partition,
    #                     strip=strip)
    #             for (hc, lc, pid) in
    #             zip(hcs, lcs, pids)]

    # (6) choose the max of all patterns

    #print(best.bx)

    # (4) process centroids
    if skip_centroids:
        centroid = [0 for _ in range(6)]
        bx = -9999
    else:
        centroid, bx = calculate_centroids(masked_data[best_pid-1], bx_data)

    best = Segment(lc=lcs[best_pid-1], hc=hcs[best_pid-1], id=best_pid, partition=partition, strip=strip, centroid=centroid, bx=bx)


    ####################################################################################
    # masked_data = [mask_layer_data(x.mask, data) for x in LAYER_MASK]

    # # (3) count # of hits
    # hcs = [calculate_hit_count(x, light_hit_count) for x in masked_data]
    # lcs = [calculate_layer_count(x) for x in masked_data]
    # pids = [x.id for x in LAYER_MASK]

    # # (4) process centroids
    # if skip_centroids:
    #     centroids = [[0 for _ in range(6)] for _ in range(len(masked_data))]
    #     bxs = [-9999 for _ in range(len(masked_data))]
    # else:
    #     centroids = []
    #     bxs = []
    #     for single_pattern_masked_data in masked_data:
    #         cur_pattern_centroids, cur_pattern_bx = calculate_centroids(single_pattern_masked_data, bx_data)
    #         #print(cur_pattern_bx)
    #         centroids.append(cur_pattern_centroids)
    #         bxs.append(cur_pattern_bx)
    # #print(bxs)
    # # (5) process segments
    # seg_list = [Segment(lc=lc,
    #                     hc=hc,
    #                     id=pid,
    #                     partition=partition,
    #                     strip=strip,
    #                     centroid=centroid,
    #                     bx=bx)
    #             for (hc, lc, pid, centroid, bx) in
    #             zip(hcs, lcs, pids, centroids, bxs)]

    # # (6) choose the max of all patterns
    # best = max(seg_list) # type: ignore

    ####################################################################################
    
    # (7) apply a layer threshold
    ly_thresh_final = max(ly_thresh_patid[best.id-1], ly_thresh_eta[partition]) 
    if (best.lc < ly_thresh_final):
        best.reset()

    # (8) remove very wide segments
    #if (best.id <= 10):
        #best.reset()

    #for i in seg_list:
    #    if i.id == 17:
    #        print(i)

    # (9) remove segments with large clusters for wide segments - ONLY NEEDED FOR PU200 - NOT USED AT THE MOEMENT
    cluster_size_max_limits = [3, 6, 9, 12, 15]
    n_hits_max_limits = [3, 6, 9, 12, 15]
    cluster_size_counts = calculate_cluster_size(data)
    n_hits_counts = calculate_hits(data)
    n_layers_large_clusters = [0, 0, 0, 0, 0]
    n_layers_large_hits = [0, 0, 0, 0, 0]
    for i, threshold in enumerate(cluster_size_max_limits):
        for l in cluster_size_counts:
            if l > threshold:
                n_layers_large_clusters[i] += 1
    for i, threshold in enumerate(n_hits_max_limits):
        for l in n_hits_counts:
            if l > threshold:
                n_layers_large_hits[i] += 1

    best.max_cluster_size = max(cluster_size_counts)
    best.max_noise = max(n_hits_counts)
    '''
    best.nlayers_withcsg3 = n_layers_large_clusters[0]
    best.nlayers_withcsg5 = n_layers_large_clusters[1]
    best.nlayers_withcsg10 = n_layers_large_clusters[2]
    best.nlayers_withcsg15 = n_layers_large_clusters[3]
    best.nlayers_withnoiseg3 = n_layers_large_hits[0]
    best.nlayers_withnoiseg5 = n_layers_large_hits[1]
    best.nlayers_withnoiseg10 = n_layers_large_hits[2]
    best.nlayers_withnoiseg15 = n_layers_large_hits[3]
    '''

    #if n_layers_large_clusters[4] >= 1:
    #    best.reset()
    #if partition >= 11:
    #    if n_layers_large_clusters[4] >= 1:
    #        best.reset()
    #    if (best.lc - n_layers_large_clusters[0]) < 4:
    #        best.reset()
    #if partition >= 9:
    #    if (best.lc - n_layers_large_hits[2]) < 3:
    #        best.reset()
    #else:
    #    if (best.lc - n_layers_large_hits[1]) < 3:
    #        best.reset()

    #print("id is: " + str(best.id))
    #print("threshold is: " + str(ly_thresh[best.id]))

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

        # for seg in seg_list:
        #     print(seg)


    best.hc=0
    best.update_quality()

    return best

################################################################################
# Tests
################################################################################

def test_pat_unit():
#changed ly_thresh to list form (used to be flat integer). haven't tested these functions yet, the pattern id's are outdated
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4], data=[0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]).id == 19
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4], data=[0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]).lc == 6
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000]).id == 19
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000, 0b100000000000000000]).lc == 6
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).id == 18
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b1000000000000000000, 0b10000000000000000000, 0b1000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).lc == 5
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).id == 0
    assert pat_unit(strip=0, partition=0, ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
, data=[0b100000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000, 0b100000000000000000000] ).lc == 0

def test_get_ly_mask():
    """ test function for get_ly_mask """
    assert get_ly_mask(pat_straight).mask == [0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000, 0b11100000000000000000]
    assert get_ly_mask(pat_l).mask == [0b1111000000000000000, 0b1110000000000000000,0b1100000000000000000,0b11000000000000000000,0b111000000000000000000, 0b1111000000000000000000]
    assert get_ly_mask(pat_r).mask == [0b1111000000000000000000, 0b111000000000000000000, 0b11000000000000000000, 0b1100000000000000000, 0b1110000000000000000, 0b1111000000000000000]
