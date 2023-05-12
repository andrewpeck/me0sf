# Emulator for chamber.vhd
import functools
import operator
from typing import List

from partition_beh import process_partition
from subfunc import *


def cross_partition_cancellation(segments : List[List[Segment]],
                                 cross_part_seg_width : int) -> List[List[Segment]]:

    for i in range(1,15,2):

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

    return segments

def process_chamber(chamber_data : List[List[int]], config : Config):

    # gather segments from each partition
    # this will return a 8 x N list of segments

    if config.x_prt_en:

        num_finders = 15

        data = [[0 for _ in range(6)] for _ in range(num_finders)]

        for finder in range(num_finders):

            # even finders are simple, just take the partition
            if finder % 2 == 0:
                data[finder] = chamber_data[finder//2]

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
                    data[finder][4] = chamber_data[finder//2][4]
                    data[finder][5] = chamber_data[finder//2][5]

    else:

        data = chamber_data

    # for (i,prt) in enumerate(data):
    #     print(f"{i}" + str(prt))

    segments = [process_partition(partition_data = prt_data,
                                  partition = partition,
                                  config = config)
        for (partition, prt_data) in enumerate(data)]

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

    # for prt in segments:
    #     for segment in prt:
    #         print(segment)

    # sort each partition and pick the best N outputs
    # pick the best N outputs from each partition
    segments = [ sorted(x, reverse=True)[:config.num_outputs] for x in segments]
    
    # join each 2 partitions and pick the best N outputs from them
    joined_segments = [ x[0] + x[1] for x in zip(*[iter(segments)] * 2)]
    joined_segments.append(segments[14])
    segments = joined_segments
    segments = [ sorted(x, reverse=True)[:config.num_outputs] for x in segments]

    # concatenate together all of the segments, sort them, and pick the best N outputs
    segments = functools.reduce(operator.iconcat, segments, []) # equivalent to segments[0] + segments[1] + segments[2] + etc
    segments = sorted(segments, reverse=True)[:config.num_outputs]

    return segments


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
    config.ly_thresh = 4
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
