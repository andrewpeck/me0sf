""" Emulator that processes a single partition (6 layers x 192 strips) and returns a collection of segments"""
from pat_unit_mux_beh import pat_mux
from datadev_mux import datadev_mux
from subfunc import *

def compare_ghosts(val, comp_list):
    """takes in a strip value and a list of strip values to ensure that there aren't copies of the same data (ID value identical) or mirrors (ID value +2 or -2 from each other)"""
    comp_list = [x for x in comp_list if x != 0]
    if len(comp_list) != 0:
        for i in range(len(comp_list)):
            if val == 0:
                break
            if (
                val[0] == comp_list[i][0]
                or val[0] + 2 == comp_list[i][0]
                or val[0] - 2 == comp_list[i][0]
            ):
                val = 0
    return val

def priority_encoder(group_vals):
    max_lyc = 0
    quality_index = 0
    ID_group = []
    original_indices = []
    for l in range(len(group_vals)):
        # determine the strip with the max layer count
        if group_vals[l] != 0 and group_vals[l][1] >= max_lyc:
            max_lyc = group_vals[l][1]
            quality_index = l
    for m in range(len(group_vals)):
        # check if we have any layer count ties; save them to a list
        if group_vals[m] != 0 and group_vals[m][1] == max_lyc:
            ID_group.append(group_vals[m])
            # save the original indices of the ID group values
            original_indices.append(m)
    if len(ID_group) > 1:
        # go through layer count tie strip values; choose value with highest pattern ID
        quality_index = 0
        max_ID = 0
        for n in range(len(ID_group)):
            if ID_group[n][0] > max_ID:  # don't compare on the rightmost; we want lower
                max_ID = ID_group[n][0]
                quality_index = original_indices[n]
    # save data from the highest quality pattern; set all other values to 0
    best_strip = group_vals[quality_index]
    return best_strip


def partition_filtering(pat_mux_dat, group_width=8, ghost_width=4, WIDTH=37):
    """takes in pat_unit_mux_data and performs edge cancellation"""
    for group in range(round((WIDTH - 1) / group_width)):
        lo_index = int(
            (group + group_width - (ghost_width / 2))
        )  # maybe check this first if there's discrepancies
        hi_index = lo_index + (ghost_width)
        values = pat_mux_dat[lo_index:hi_index]
        for j in range(len(values)):
            values[j] = compare_ghosts(values[j], values[(j + 1) :])
        pat_mux_dat[lo_index:hi_index] = values
    return pat_mux_dat

def work_partition(
    chamber_data, patlist, MAX_SPAN=37, WIDTH=192, group_width=8, ghost_width=4
):

    """takes in pat_unit_mux_data, a group size, and a ghost width to return a smaller data set, using ghost edge cancellation
    and segment quality filtering

    NOTE: ghost width denotes the width where we can likely see copies of the same segment in the data"""
    pat_mux_dat = pat_mux(
        chamber_data=chamber_data, patlist=patlist, MAX_SPAN=MAX_SPAN, WIDTH=WIDTH
    )

    # pat_mux_dat = partition_filtering(
    #     pat_mux_dat=pat_mux_dat,
    #     group_width=group_width,
    #     ghost_width=ghost_width,
    #     WIDTH=WIDTH,
    # )
    # ADD ME LATER!

    final_dat = []
    for s in range(0, len(pat_mux_dat), group_width):
        final_dat.append(priority_encoder(pat_mux_dat[s : (s + group_width)]))

    return final_dat
