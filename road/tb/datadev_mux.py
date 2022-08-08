# Data development for the pat_unit_mux.vhd
# TODO:  rename to _partition instead of _mux
# TODO:  list -> tuple ?
# TODO:  add type hints ?
# TODO:  lowercase

from subfunc import *
from datagen import datagen
from constants import *


def datagen_mux(WIDTH=192, track_num=4, nhit_lo=3, nhit_hi=10, ly_t=6):
    """takes a given chamber width and a range of hits to generate a random number of tracks for populating data throughout layers

    Args:
      WIDTH: (Default value = 192)
      track_num: (Default value = 4)
      nhit_lo: (Default value = 3)
      nhit_hi: (Default value = 10)
      ly_t:  (Default value = 6)

    Returns:
      : A list of 6 integers representing TRACK_NUM overlaid tracks in a partition

    Raises:

    """

    assert type(WIDTH) == int, "WIDTH input must be an integer"
    assert type(track_num) == int, "track_num input must be an integer"
    assert type(nhit_lo) == int, "nhit_lo input must be an integer"
    assert type(nhit_hi) == int, "nhit_hi input must be an integer"

    # create space for 6 layers of data
    data_store = [0, 0, 0, 0, 0, 0]
    # create tracks with datagen(); overlay hits from multiple muon tracks onto strip data
    for _ in range(track_num):
        # vary the number of layers for each muon track
        data = datagen(ly_t=ly_t, MAX_SPAN=WIDTH, nhit_lo=nhit_lo, nhit_hi=nhit_hi)
        for j in range(N_LAYERS):
            # ADD track data onto existing layer data
            data_store[j] = data_store[j] | data[j]
    data_out = data_store
    return data_out
