# Data development for the pat_unit_mux.vhd
# TODO:  rename to _partition instead of _mux
# TODO:  list -> tuple ?
# TODO:  add type hints ?
# TODO:  lowercase

from subfunc import *
from datagen import datagen
from constants import *


def datagen_mux(n_segs, n_noise, max_span):

    """takes a given chamber width and a range of hits to generate a random number of tracks for populating data throughout layers

    Args:

    Returns:
      : A list of 6 integers representing TRACK_NUM overlaid tracks in a partition

    Raises:

    """

    data_store = 6*[0]

    # create tracks with datagen(); overlay hits from multiple muon tracks onto strip data
    # vary the number of layers for each muon track
    data = datagen(n_segs, n_noise, max_span)
    for j in range(N_LAYERS):
        # ADD track data onto existing layer data
        data_store[j] = data_store[j] | data[j]

    data_out = data_store
    return data_out
