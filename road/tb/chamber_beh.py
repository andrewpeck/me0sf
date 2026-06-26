# Emulator for chamber.vhd
import functools
import multiprocessing.pool
import operator
import os
from copy import deepcopy
from itertools import repeat, cycle, starmap
from typing import List

from partition_beh import process_partition
from subfunc import *

def deghosting_clearance(segments : List[List[Segment]],
                         clearance_width : int) -> List[List[Segment]]:
    # Make a copy of input array to do concurrent deghosting, as FW will do
    segs_out = deepcopy(segments)
    # Look at each chunk in each partition. In real partitions, only look left and right. In virtual partitions, look in all (max 8) directions.
    for prt_i in range(0,len(segments)):
        for seg_i in range(0, len(segments[prt_i])):
            prts = [0]
            chunks = [0]
            # If virtual partition, do x-prt deghosting. If at top or bottom, don't try to look out of bounds.
            if (prt_i % 2 == 1):
                if prt_i != 0:
                    prts.append(-1)
                if prt_i != len(segments)-1:
                    prts.append(1)
            # Don't look out of bounds
            if seg_i != 0:
                chunks.append(-1)
            if seg_i != len(segments[prt_i])-1:
                chunks.append(1)
            # Generate all permutations of (relative_partition, relative_chunk)
            relative_indices = [(prt, chunk) for prt in prts for chunk in chunks]
            # Don't compare with self: remove (0,0)
            relative_indices.remove((0,0))
            seg = segments[prt_i][seg_i]
            for x,y in relative_indices:
                if (abs(segments[prt_i+x][seg_i+y].strip - seg.strip) <= clearance_width):
                    if seg.quality > segments[prt_i+x][seg_i+y].quality:
                        segs_out[prt_i+x][seg_i+y].reset()
                    else:
                        segs_out[prt_i][seg_i].reset()
    return segs_out

def cross_partition_cancellation(segments,
                                 cross_part_seg_width : int) -> List[List[Segment]]:
    # Make a copy of the segments so each step is effectively done in parallel (as FW does it)
    segs_real_killed = [prt for prt in deepcopy(segments)]
    # Step 1: Kill real segments with a better nearby virtual segment
    for i in range(1,15,2):        
        for (v_seg_i, v_seg) in enumerate(segments[i]):
            if v_seg.lc == 0:
                continue

            for (seg_above_i, seg_above) in enumerate(segments[i-1]):
                if seg_above.lc != 0 and abs(v_seg.strip - seg_above.strip) <= cross_part_seg_width and ((v_seg.lc<<5) + v_seg.id > (seg_above.lc<<5) + seg_above.id):
                    segs_real_killed[i-1][seg_above_i].reset()
            for (seg_below_i, seg_below) in enumerate(segments[i+1]):
                if seg_below.lc != 0 and abs(v_seg.strip - seg_below.strip) <= cross_part_seg_width and ((v_seg.lc<<5) + v_seg.id > (seg_below.lc<<5) + seg_below.id):
                    segs_real_killed[i+1][seg_below_i].reset()
    # Make a copy, to update segments for Step 2
    segs_o = [prt for prt in deepcopy(segs_real_killed)]
    # Step 2: Kill virtual segments that still have a nearby real segment (i.e. virtual segments with a better nearby real segment)
    for i in range(1, 15, 2):
        for (v_seg_i, v_seg) in enumerate(segs_real_killed[i]):
            if v_seg.lc == 0:
                continue

            for (seg_above_i, seg_above) in enumerate(segs_real_killed[i-1]):
                if seg_above.lc != 0 and abs(v_seg.strip - seg_above.strip) <= cross_part_seg_width:
                    segs_o[i][v_seg_i].reset()
            for (seg_below_i, seg_below) in enumerate(segs_real_killed[i+1]):
                if seg_below.lc != 0 and abs(v_seg.strip - seg_below.strip) <= cross_part_seg_width:
                    segs_o[i][v_seg_i].reset()

    return segs_o

def deghosting_clearance(segments : List[List[Segment]],
                         clearance_width : int) -> List[List[Segment]]:
    # Make a copy of input array to do concurrent deghosting, as FW will do
    segs_out = deepcopy(segments)

    # Look at each chunk in each partition. In real partitions, only look left and right. In virtual partitions, look in all (max 8) directions.
    for prt_i in range(0,len(segments)):
        for seg_i in range(0, len(segments[prt_i])):

            prts = [0]
            chunks = [0]

            # If virtual partition, do x-prt deghosting. If at top or bottom, don't try to look out of bounds.
            if (prt_i % 2 == 1):
                if prt_i != 0:
                    prts.append(-1)
                if prt_i != len(segments)-1:
                    prts.append(1)

            # Don't look out of bounds
            if seg_i != 0:
                chunks.append(-1)
            if seg_i != len(segments[prt_i])-1:
                chunks.append(1)
            
            # Generate all permutations of (relative_partition, relative_chunk)
            relative_indices = [(prt, chunk) for prt in prts for chunk in chunks]
            # Don't compare with self: remove (0,0)
            relative_indices.remove((0,0))

            seg = segments[prt_i][seg_i]
            for x,y in relative_indices:
                if (abs(segments[prt_i+x][seg_i+y].strip - seg.strip) <= clearance_width):
                    if seg > segments[prt_i+x][seg_i+y]:
                        segs_out[prt_i+x][seg_i+y].reset()
                    else:
                        segs_out[prt_i][seg_i].reset()
    return segs_out

def process_chamber(chamber_data, config : Config, chamber_bx_data):

    # Pulse stretch if enabled
    if config.pulse_stretch_bx > 0:
        if config.pulse_stretch_bx != 2:
            print("Pulse stretching only guaranteed to work for 0 or 2, can generalize this if desired.")
            assert False

        chamber_data = config.pulse_stretch(chamber_data)



    #chamber_data = [[ly if i != 3 else 0 for i,ly in enumerate(prt)] for prt in chamber_data]

    # gather segments from each partition
    # this will return a 8 x N list of segments

    if config.x_prt_en:

        num_finders = 15

        data = [[0 for _ in range(6)] for _ in range(num_finders)]
        processed_chamber_bx_data = [[[-9999 for _ in range(192)] for _ in range(6)] for _ in range(num_finders)]

        for finder in range(num_finders):

            # even finders are simple, just take the partition
            if finder % 2 == 0:
                data[finder] = chamber_data[finder//2]
                processed_chamber_bx_data[finder] = chamber_bx_data[finder//2]

            # odd finders are the OR of two adjacent partitions
            else:

                # for non-pointing, look both in +1 and -1 partitions
                if config.en_non_pointing:

                    raise Exception("Non pointing not supported yet...")

                # otherwise look only in the +1 partition
                else:
                    data[finder][0] =                                chamber_data[finder//2+1][0]
                    data[finder][1] =                                chamber_data[finder//2+1][1]
                    data[finder][2] = chamber_data[finder//2][2]  |  chamber_data[finder//2+1][2]
                    data[finder][3] = chamber_data[finder//2][3]  |  chamber_data[finder//2+1][3]
                    #data[finder][2] = chamber_data[finder//2+1][2]
                    #data[finder][3] = chamber_data[finder//2][3]
                    data[finder][4] = chamber_data[finder//2][4]
                    data[finder][5] = chamber_data[finder//2][5]

                    processed_chamber_bx_data[finder][0] = chamber_bx_data[finder//2+1][0]
                    processed_chamber_bx_data[finder][1] = chamber_bx_data[finder//2+1][1]
                    processed_chamber_bx_data[finder][2] = [max(chamber_bx_data[finder//2][2][i], chamber_bx_data[finder//2+1][2][i]) for i in range(len(chamber_bx_data[finder//2][2]))]
                    processed_chamber_bx_data[finder][3] = [max(chamber_bx_data[finder//2][3][i], chamber_bx_data[finder//2+1][3][i]) for i in range(len(chamber_bx_data[finder//2][3]))]
                    processed_chamber_bx_data[finder][4] = chamber_bx_data[finder//2][4]
                    processed_chamber_bx_data[finder][5] = chamber_bx_data[finder//2][5]
    else:

        data = chamber_data
        
    datazip  = zip(data, range(len(data)), repeat(config), processed_chamber_bx_data)

    #If x_prt is enabled, perform strict thresholding on x-partitions
    #strict_config = deepcopy(config)
    #if (config.x_prt_en):
    #    for i, thresh in enumerate(strict_config.ly_thresh_patid):           
    #        if (thresh < 5):
    #            strict_config.ly_thresh_patid[i] += 1 
    #datazip  = zip(data, range(len(data)), cycle((config, strict_config)))

    # for some reason multi-processing fails with questasim, generating an error
    # such as:
    #
    # Warning: (vsim-7) Failed to open process file
    # "/proc/self/task/1494057/stat" in read mode. # No such file or directory.
    #
    # (errno = ENOENT)

    ##### note: multiprocessing pool can not be used inside of another pool #####
    # if "SIM" in os.environ and os.environ["SIM"] == "questa":
    #     segments = starmap(process_partition, datazip)
    # else:
    #     with multiprocessing.pool.Pool() as pool:
    #         segments = pool.starmap(process_partition, datazip)
    #############################################################################
    segments = starmap(process_partition, datazip)

    segments = list(segments)

    # print("Outputs from process partition (raw)")
    # for prt in segments:
    #     print(f'{prt=}')
    #     for seg in prt:
    #         if (seg.lc > 0):
    #             print(seg)

    # compare partitions 0 & 1, 2 & 3, 4 & 5.. etc
    # return NUM_OUTPUTS segments from each partition pair

    # Remove redundant segments from cross-partitions and grouping neighbouring eta partitions
    if (config.cross_part_seg_width > 0):
        segments = cross_partition_cancellation(segments, config.cross_part_seg_width)
    if (config.clearance_width > 0):
        segments = deghosting_clearance(segments, config.clearance_width)

    # for prt in segments:
    #     for segment in prt:
    #         print(segment)

    # sort each partition and pick the best N outputs
    # pick the best N outputs from each partition
    segments = [ sorted(x, reverse=True)[:config.num_outputs] for x in segments]
    
    # join each 2 partitions and pick the best N outputs from them
    joined_segments = [ x[0] + x[1] for x in zip(*[iter(segments)] * 2)]
    if (len(segments)==15):
        joined_segments.append(segments[14])
    segments = joined_segments
    segments = [ sorted(x, reverse=True)[:config.num_outputs] for x in segments]

    # concatenate together all of the segments, sort them, and pick the best N outputs
    segments = functools.reduce(operator.iconcat, segments, []) # equivalent to segments[0] + segments[1] + segments[2] + etc
    segments = sorted(segments, reverse=True)[:config.num_outputs]

    # print(segments)

    # Fit segments and bending angle cut
    for seg in segments:
        if not seg.valid:
            seg.reset()
            continue
        seg.fit(config.pat_spans[seg.id-1])
        if abs(seg.bend_ang) > config.bend_ang_cut:
            seg.reset()

    # Final spatial clearance
    for i, seg in enumerate(segments):
        if not seg.valid:
            continue
        for j, seg2 in enumerate(segments):
            if i == j or not seg2.valid:
                continue
            if abs((seg.strip + seg.substrip) - (seg2.strip + seg2.substrip)) <= 5 and abs(seg.partition - seg2.partition) <= 1:
                seg2.reset() # segments are already sorted, so don't need to compare quality

    # Final temporal clearance
    for seg in segments:
        if not seg.valid:
            continue
        for seg2 in config.old_segments:
            if not seg2.valid:
                continue
            if abs((seg.strip + seg.substrip) - (seg2.strip + seg2.substrip)) <= 5 and abs(seg.partition - seg2.partition) <= 1:
                if seg2 > seg:
                    seg.reset()
                else:
                    seg2.reset()

    output_segments = sorted(config.old_segments, reverse=True) # Have to sort again in case some were reset

    config.old_segments = segments # Save segments for temporal deghosting next BX
    return (output_segments, config)


def test_chamber_beh():

    config = Config()

    config.num_or = 2
    config.x_prt_en = True
    config.en_non_pointing = False
    config.max_span = 37
    config.width = 192
    config.deghost_pre = False
    config.deghost_post = False
    config.group_width = 8
    config.num_outputs= 4
    config.ly_thresh_patid = [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    config.ly_thresh_eta = [4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4]
    config.cross_part_seg_width = 0
    config.skip_centroids = True

    null = lambda : [[0 for _ in range(6)] for _ in range(8)]

    for iprt in range(8):
        print(f"Partition={iprt}:")
        for istrip in range(192):

            print(f"Strip={istrip}:")

            data = null()

            for ly in range(6):
                data[iprt][ly] = 1<<istrip

            segments = process_chamber(chamber_data=data, config=config)
            if (config.x_prt_en==True):
                assert segments[0].partition == iprt*2
            else:
                assert segments[0].partition == iprt
            assert segments[0].lc == 6
            assert segments[0].id == 19
            assert segments[0].strip == istrip or  \
                segments[0].strip == istrip+1

            print(" > " + str(segments[0]))

if __name__=="__main__":
    test_chamber_beh()
