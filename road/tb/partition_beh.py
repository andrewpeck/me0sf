""" Emulator that processes a single partition (6 layers x 192 strips) and returns a collection of segments"""
from typing import List

from pat_unit_mux_beh import pat_mux
from subfunc import *


def is_ghost(seg : Segment,
             comp : Segment,
             check_ids : bool = False,
             check_strips : bool = False):

    '''takes in a segment and a list of segments to ensure that there aren't
    copies of the same data (ID value identical) or mirrors (ID value + 2 or - 2
    from each other)

    '''

    if seg.strip is None or comp.strip is None or  \
       seg.id is None or comp.id is None:
        raise Exception("Tried to compare is_ghost with None types")

    ghost = seg.quality < comp.quality \
        and (not check_strips or abs(seg.strip - comp.strip) < 2) and \
        (not check_ids or (seg.id == comp.id or seg.id + 2 == comp.id or seg.id == comp.id + 2))

    return ghost


def cancel_edges(segments : List[Segment],
                 group_width : int = 8,
                 ghost_width : int = 2,
                 edge_distance : int = 2,
                 verbose : bool = False):

    '''Takes in a list of SEGMENTS and is designed to perform ghost
    cancellation on the edges of the "groups".

    during segment sorting, an initial step is that the partition is chunked into
    groups of width GROUP_WIDTH. The firmware selects just one segment from each group.

    Since segments can ghost (produce duplicates of the same segment on
    different strips), we do a ghost cancellation before this group filtering process.

    This is done by looking at the edges of the group and zeroing off a segment
    if it is of lower quality than its neighbors. Segments away from the edges
    of the group will not need to be de-duplicated since this is handled by the
    group filtering process itself. This is only needed to prevent duplicates
    from appearing in different groups.

    An implementation that cancels after the filtering is much simpler and less
    resource intensive but comes with the downside that we may lose segments.

    ghost_width = 0 means do not compare
    ghost_width = 1 means look 1 to the left and right
    ghost_width = 2 means look 2 to the left and right

    edge_distance specifies which strips will have ghost cancellation done on them
    edge_distance = 0 means to only look at strips directly on the edges (0 7 8 15 etc)
    edge_distance = 1 means to look one away from the edge (0 1 6 7 8 9 14 15 16 17 etc)

    etc

    '''

    cancelled_segments = segments.copy()

    def is_at_edge(x):
        if group_width > 0:
            return x % group_width < edge_distance or (x % group_width) >= (group_width-edge_distance)
        else:
            return True

    for i in range(len(segments)):
        if is_at_edge(i):

            # for a given strip N, create a list of indexes to which the current
            # strip should be compared e.g. [N-2, N-1, N+1, N+2]
            #
            comps = \
                [x for x in range(i-ghost_width, i, 1) if x >= 0] + \
                [x for x in range(i+1,i+ghost_width+1,  1) if x < len(segments)]

            if verbose:
                print(f"Comparing strip {i} to strips %s" % str(comps))

            for comp in comps:
                ghost = is_ghost(segments[i], segments[comp], check_strips = False)
                if ghost:
                    cancelled_segments[i] = Segment(0,0,0)

    return cancelled_segments


def process_partition(partition_data : List[int],
                      partition : int,
                      config : Config):

    '''takes in partition data, a group size, and a ghost width to return a
    smaller data set, using ghost edge cancellation and segment quality
    filtering

    NOTE: ghost width denotes the width where we can likely see copies of the
    same segment in the data

    steps: process partition data with pat_mux, perfom edge cancellations,
    divide partition into pieces, take best segment from each piece

    '''

    segments = pat_mux(partition_data, partition=partition, config=config)

    if (config.deghost_pre):
        segments = cancel_edges(segments=segments,
                                edge_distance=config.edge_distance,
                                group_width=config.group_width,
                                ghost_width=config.ghost_width)

    # divide partition into pieces and take best segment from each piece
    chunked = chunk(segments, config.group_width)

    segments = [max(x) for x in chunked]

    if (config.deghost_post):
        segments = cancel_edges(segments=segments, group_width=0,
                                ghost_width=1, edge_distance=1)

    return segments

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def test_process_partition():

    data = [1]*6

    config = Config();
    config.ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    config.deghost_pre=True

    part = process_partition(data, partition=0, config=config)

    assert part[0].id == 19
    assert part[0].lc == 6
    assert part[1].id == 0
    assert part[1].lc == 0

def test_compare_ghosts():

    seg1 = Segment(hc=6, lc=6, id=15, partition=0, strip=0)
    seg2 = Segment(hc=6, lc=6, id=10, partition=0, strip=0)
    seg3 = Segment(hc=6, lc=6, id=7, partition=0, strip=0)

    #check for reset with copy, ID+2, ID-2
    assert is_ghost(seg1, seg1) == False
    assert is_ghost(seg2, seg1) == True
    assert is_ghost(seg3, seg1) == True
    assert is_ghost(seg1, seg3) == False

def test_cancel_edges():

    # create a list of all equal segments and check cancellation on them
    segments = [Segment(hc=6, lc=6, id=15, partition=0, strip=i) for i in range(24)]

    cancelled = cancel_edges(segments, group_width = 8, ghost_width = 2, verbose = False)

    # this should NOT really happen but right now it does...
    # no reason to cancel edges at the left  / right side of chamber
    assert cancelled[0].id == 0
    assert cancelled[1].id == 0

    #check first edge is cancelled correctly
    assert cancelled[5].id == 15
    assert cancelled[6].id == 0
    assert cancelled[7].id == 0
    assert cancelled[8].id == 0
    assert cancelled[9].id == 0
    assert cancelled[10].id == 15

    #check second edge is cancelled correctly
    assert cancelled[13].id == 15
    assert cancelled[14].id == 0
    assert cancelled[15].id == 0
    assert cancelled[16].id == 0
    assert cancelled[17].id == 0
    assert cancelled[18].id == 15
