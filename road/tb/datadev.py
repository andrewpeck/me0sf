# Test case generator for pat_unit.vhd
import random
from printly_dat import printly_dat
from subfunc import *


def datadev(ly_t=6, MAX_SPAN=37, nhit_lo=3, nhit_hi=10):
    """generates data for each layer based on an artificial muon track and noise"""
    N_LAYERS = 6

    # nhits corresponds to the number of hits from noise; slope and hit1 determine the muon track to generate hits from
    nhits = random.randint(nhit_lo, nhit_hi)
    slope = random.uniform(-1 * (MAX_SPAN / (N_LAYERS - 1)), MAX_SPAN / (N_LAYERS - 1))
    hit1 = round(random.randint(17, 19) - slope * 2.5)
    data = []

    # generate the different hits for each layer based on how many layers the muon traveled through
    if ly_t == 2:
        ly0_h = hit1
        ly1_h = round((slope * 1) + hit1)
        ly2_h = 0
        ly3_h = 0
        ly4_h = 0
        ly5_h = 0
    elif ly_t == 3:
        ly0_h = hit1
        ly1_h = round((slope * 1) + hit1)
        ly2_h = round((slope * 2) + hit1)
        ly3_h = 0
        ly4_h = 0
        ly5_h = 0
    elif ly_t == 4:
        ly0_h = hit1
        ly1_h = round((slope * 1) + hit1)
        ly2_h = round((slope * 2) + hit1)
        ly3_h = round((slope * 3) + hit1)
        ly4_h = 0
        ly5_h = 0
    elif ly_t == 5:
        ly0_h = hit1
        ly1_h = round((slope * 1) + hit1)
        ly2_h = round((slope * 2) + hit1)
        ly3_h = round((slope * 3) + hit1)
        ly4_h = round((slope * 4) + hit1)
        ly5_h = 0
    elif ly_t == 6:
        ly0_h = hit1
        ly1_h = round((slope * 1) + hit1)
        ly2_h = round((slope * 2) + hit1)
        ly3_h = round((slope * 3) + hit1)
        ly4_h = round((slope * 4) + hit1)
        ly5_h = round((slope * 5) + hit1)

    # setting the hit index boundaries at the thresholds 0 and 36
    lyx_h = [ly0_h, ly1_h, ly2_h, ly3_h, ly4_h, ly5_h]
    for z in range(len(lyx_h)):
        if lyx_h[z] > (MAX_SPAN - 1) or lyx_h[z] < 0:
            lyx_h[z] = None
        else:
            lyx_h[z] = lyx_h[z]

    # layer 0 data without noise
    if ly_t == 1 or ly_t == 2 or ly_t == 3 or ly_t == 4 or ly_t == 5 or ly_t == 6:
        if lyx_h[0] is not None:
            data.append(set_bit(lyx_h[0]))
        else:
            data.append(0)

    # layer 1 data without noise
    if ly_t == 2 or ly_t == 3 or ly_t == 4 or ly_t == 5 or ly_t == 6:
        if lyx_h[1] is not None:
            data.append(set_bit(lyx_h[1]))
        else:
            data.append(0)

    # layer 2 data without noise
    if ly_t == 3 or ly_t == 4 or ly_t == 5 or ly_t == 6:
        if lyx_h[2] is not None:
            data.append(set_bit(lyx_h[2]))
        else:
            data.append(0)

    # layer 3 data without noise
    if ly_t == 4 or ly_t == 5 or ly_t == 6:
        if lyx_h[3] is not None:
            data.append(set_bit(lyx_h[3]))
        else:
            data.append(0)

    # layer 4 data without noise
    if ly_t == 5 or ly_t == 6:
        if lyx_h[4] is not None:
            data.append(set_bit(lyx_h[4]))
        else:
            data.append(0)

    # layer 5 data without noise
    if ly_t == 6:
        if lyx_h[5] is not None:
            data.append(set_bit(lyx_h[5]))
        else:
            data.append(0)

    # noise for all 6 layers
    for ihit in range(nhits):
        strip = random.randint(0, MAX_SPAN - 1)
        ly = random.randint(0, N_LAYERS - 1)
        data[ly] = set_bit(strip, data[ly])

    # simulate 90% data acquisition to make testing scenario more realistic
    ones_ct = 0
    iterable_data = []
    for i in range(len(data)):
        ones_ct = ones_ct + count_ones(data[i])
        iterable_data_v = bin(data[i])[2:]
        iterable_data_v = iterable_data_v.zfill(MAX_SPAN)
        iterable_data.append(iterable_data_v)

    def return_indices(data, iterable_data, MAX_SPAN=37):
        """determines where the high bits are in all the layer data; returns the indices of the layer and strip of each high bit"""
        indices = []
        # create a mask of ones with the same dimensions as the given data value; AND the mask with the data value and count the ones to detemine if high bits are present
        for n in range(len(data)):
            mask = ones_bit_mask(data[n])
            check = count_ones(data[n] & mask)
            if check >= 1:
                # create iterable binary version of the mask and data integers; set the dimensions of each to be the max layer strip span
                iterable_mask = bin(mask)[2:]
                iterable_mask = iterable_mask.zfill(MAX_SPAN)
                # AND the iterable data and iterable mask to find the high bits; return the layer n and strip o where the high bit occurs
                for o in range(len(iterable_data[n])):
                    if int(iterable_data[n][o]) & int(iterable_mask[o]) == 1:
                        indices.append([n, o])
        return indices

    n_eliminate = round(ones_ct * 0.1)
    el_indices = return_indices(data, iterable_data)

    # clear 10% of the data on random strips and layers
    for k in range(n_eliminate):
        target = random.choice(el_indices)
        in_1 = target[0]
        in_2 = target[1]
        data[in_1] = clear_bit(data[in_1], in_2)

    return data


