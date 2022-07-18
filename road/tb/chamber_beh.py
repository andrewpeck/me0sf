# Emulator for chamber.vhd
from subfunc import *
import functools
import operator
from datadev_mux import datadev_mux
from partition_beh import work_partition


def process_chamber(
        chamber_data, max_span=37, width=192, group_width=8, ghost_width=4, num_outputs=4
):

    # gather segments from each partition
    # this will return a 8 x N list of segments

    segments = [
        work_partition(
            partition_data=data,
            max_span=max_span,
            width=width,
            group_width=group_width,
            ghost_width=ghost_width,
            enable_gcl=True,
            partition=partition
        ) for (partition, data) in enumerate(chamber_data)
    ]

    # compare partitions 0 & 1, 2 & 3, 4 & 5.. etc
    # return NUM_OUTPUTS segments from each partition pair

    segments = [
        segments[0] + segments[1],
        segments[2] + segments[3],
        segments[4] + segments[5],
        segments[6] + segments[7],
    ]

    segments = list(map(lambda x: sorted(x, reverse=True)[:num_outputs], segments))

    segments = functools.reduce(operator.iconcat, segments, [])
    #segments = segments[0] + segments[1] + segments[2] + segments[3]

    segments.sort(reverse=True)

    segments = segments[:num_outputs]

    return segments
