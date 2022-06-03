# Emulator for pat_unit_mux.vhd
from subfunc import *
from pat_unit_beh import process_pat
from constants import *

def parse_data(data, strip, MAX_SPAN=37):
    """takes in data, a strip index, and a MAX_SPAN to get the data a pat_unit on that strip would see"""
    if strip < MAX_SPAN // 2 + 1:
        data_shifted = data << (MAX_SPAN // 2 - strip)
        parsed_data = data_shifted & (2**MAX_SPAN - 1)
    else:
        shift = strip - MAX_SPAN // 2
        parsed_data = (data >> shift) & (2**MAX_SPAN - 1)
    return parsed_data

def find_pattern(ly_dat, strip, patlist, MAX_SPAN=37):
    p_unit_dat = []
    for i in range(N_LAYERS):
        p_unit_dat.append(parse_data(ly_dat[i], strip, MAX_SPAN=MAX_SPAN))
    [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x] = p_unit_dat
    [pat_id, ly_c] = process_pat(
        patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN
    )
    return pat_id, ly_c, strip

def pat_mux(chamber_data, patlist, MAX_SPAN=37, WIDTH=192):
    """

    takes in a list of integers for the chamber data in each layer, the
    patlist, MAX_SPAN of each pat_unit, and the chamber width to return the
    patterns the pat_unit_mux.vhd would find

    """

    patterns = []
    for i in range(WIDTH):
        [pat_id, ly_c, strip] = find_pattern(chamber_data, i, patlist, MAX_SPAN)
        patterns.append([pat_id, ly_c, strip])

    return patterns
