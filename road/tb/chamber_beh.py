# Emulator for chamber.vhd
from subfunc import *
import functools
import operator
from partition_beh import work_partition

def process_chamber(chamber_data, thresh : int,
                    max_span : int = 37,
                    width : int = 102,
                    group_width : int=8 ,
                    ghost_width : int=4 ,
                    num_outputs : int=4 ):

    # (1) gather segments from each partition
    # this will return a 8 x N list of segments

    fnpartition = lambda partition, data : work_partition(
        partition_data=data,
        thresh = thresh,
        max_span=max_span,
        width=width,
        group_width=group_width,
        ghost_width=ghost_width,
        enable_gcl=True,
        partition=partition)

    # (2) collect segments from each partition
    segments = [fnpartition(partition, data)
                 for (partition, data) in enumerate(chamber_data)]

    # (3) compare partitions 0 & 1, 2 & 3, 4 & 5.. etc
    # return NUM_OUTPUTS segments from each partition pair

    # segments = [segments[0] + segments[1],
    #             segments[2] + segments[3],
    #             segments[4] + segments[5],
    #             segments[6] + segments[7]]

    segments = list(map(lambda x: sorted(x, reverse=True)[:num_outputs], segments))

    # (4) reduce N lists of segments into a single list,
    # i.e. segments[0] + segments[1] + segments[2] + segments[3]
    segments = functools.reduce(operator.iconcat, segments, [])

    # (5) reverse the list and pick the first N outputs
    segments.sort(reverse=True)
    segments = segments[:num_outputs]
    return segments
