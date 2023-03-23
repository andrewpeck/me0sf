# Emulator for chamber.vhd
from subfunc import *
import functools
import operator
from partition_beh import process_partition
import math

def process_chamber(chamber_data,
                    hit_thresh : int = 4,
                    ly_thresh : int = 4,
                    max_span : int = 37,
                    width : int = 192,
                    enable_gcl : bool = True,
                    group_width : int = 8,
                    ghost_width : int = 4,
                    cross_part_seg_width : int = 4,
                    num_outputs : int = 4):

    # gather segments from each partition
    # this will return a 8 x N list of segments

    segments = [
        process_partition(
            partition_data=data,
            hit_thresh = hit_thresh,
            ly_thresh = ly_thresh,
            max_span = max_span,
            enable_gcl = enable_gcl,
            width = width,
            group_width = group_width,
            ghost_width = ghost_width,
            partition = partition)
        for (partition, data) in enumerate(chamber_data)]

    NUM_PARTITIONS = len(segments)

    # compare partitions 0 & 1, 2 & 3, 4 & 5.. etc
    # return NUM_OUTPUTS segments from each partition pair

    # Remove redundant segments from cross-partitions and grouping neighbouring eta partitions
    if (cross_part_seg_width > 0):
        for i in range(1,15,2):
            #print (i)
            for (l,seg) in enumerate(segments[i]):
                if seg.id == 0:
                    continue
                #print ("Seg 0: ", l, seg, seg.strip)
                strip = seg.strip
                #quality = seg.quality
                seg1_max_quality = -9999
                seg2_max_quality = -9999
                seg1_max_quality_index = -9999
                seg2_max_quality_index = -9999
                for (j,seg1) in enumerate(segments[i-1]):
                    if seg1.id == 0:
                        continue
                    #print ("Seg 1: ", l, seg1, seg1.strip)
                    if abs(strip - seg1.strip) <= cross_part_seg_width:
                        if seg1.quality > seg1_max_quality:
                            if seg1_max_quality_index != -9999:
                                segments[i-1][seg1_max_quality_index].reset()
                            seg1_max_quality_index = j
                            seg1_max_quality = seg1.quality
                for (k,seg2) in enumerate(segments[i+1]):
                    if seg2.id == 0:
                        continue
                    #print ("Seg 2: ", l, seg2, seg2.strip)
                    if abs(strip - seg2.strip) <= cross_part_seg_width:
                        if seg2.quality > seg2_max_quality:
                            if seg2_max_quality_index != -9999:
                                segments[i+1][seg2_max_quality_index].reset()
                            seg2_max_quality_index = k
                            seg2_max_quality = seg2.quality

                if seg1_max_quality_index != -9999 and seg2_max_quality_index != -9999:
                    segments[i-1][seg1_max_quality_index].reset()
                    segments[i+1][seg2_max_quality_index].reset()
                elif seg1_max_quality_index != -9999:
                    segments[i][l].reset()
                elif seg2_max_quality_index != -9999:
                    segments[i][l].reset()

                '''
                if seg1_max_quality_index != -9999 and seg2_max_quality_index != -9999:
                    seg1 = segments[i-1][seg1_max_quality_index]
                    seg2 = segments[i+1][seg2_max_quality_index]
                    if quality > seg1.quality:
                        segments[i-1][seg1_max_quality_index].reset()
                        if quality > seg2.quality:
                            segments[i+1][seg2_max_quality_index].reset()
                        else:
                            segments[i][l].reset()
                    else:
                        segments[i][l].reset()
                        if seg1.quality > seg2.quality:
                            segments[i+1][seg2_max_quality_index].reset()
                        else:
                            segments[i-1][seg1_max_quality_index].reset()
                elif seg1_max_quality_index != -9999:
                    seg1 = segments[i-1][seg1_max_quality_index]
                    if quality > seg1.quality:
                        segments[i-1][seg1_max_quality_index].reset()
                    else:
                        segments[i][l].reset()
                elif seg2_max_quality_index != -9999:
                    seg2 = segments[i+1][seg2_max_quality_index]
                    if quality > seg2.quality:
                        segments[i+1][seg2_max_quality_index].reset()
                    else:
                        segments[i][l].reset()
                '''

    if NUM_PARTITIONS > 8:
        segments_reduced = []
        for i in range(0,8):
            segments_reduced.append([])
        for (i,seg_list) in enumerate(segments):
            for seg in seg_list:
                seg.partition = math.ceil(seg.partition/2)
                segments_reduced[math.ceil(i/2)].append(seg)
    else:
        segments_reduced = segments

    # sort each partition and pick the best N outputs
    # pick the best N outputs from each partition
    segments_reduced = [ sorted(x, reverse=True)[:num_outputs] for x in segments_reduced]

    # join each 2 partitions and pick the best N outputs from them
    segments_reduced = [ x[0]+x[1] for x in zip(*[iter(segments_reduced)] * 2)]
    segments_reduced = [ sorted(x, reverse=True)[:num_outputs] for x in segments_reduced]

    # concatenate together all of the segments, sort them, and pick the best N outputs
    segments_reduced = functools.reduce(operator.iconcat, segments_reduced, []) # equivalent to segments_reduced[0] + segments_reduced[1] + segments_reduced[2] + etc
    segments_reduced = sorted(segments_reduced, reverse=True)[:num_outputs]

    return segments_reduced
