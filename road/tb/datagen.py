# Test case generator for pat_unit.vhd
import random

from constants import *
from subfunc import *


def get_noise(n: int, max_span: int) -> list[int]:
    """generates integer mask for n background hits"""
    noise_mask = [0] * 6
    for _ in range(n):
        ly = random.randint(0, 5)
        strip = random.randint(0, max_span)
        noise_mask[ly] = set_bit(strip, noise_mask[ly])
    return noise_mask


def datagen(n_segs: int,
            n_noise: int,
            max_span: int,
            bend_angs: list[float] = [],
            strips: list[int] = [],
            efficiency: float = 0.9) -> list[int]:

    """
    generates data for each layer based on an artificial muon track and noise,
    returns a list of 6 integers representing the generated hits on those
    layers, tuple of bend angles and strips

    Args:

    n_segs = # of segments to generate

    n_noise = # of background hits (randomly distributed around the chamber)

    max_span = width of a pattern window (Default value = 37)

    bend_angs, strips = lists of bend angles and strips to create given segments

    """

    SPAN_MASK = 2**max_span - 1

    # if requested, generate noise for each layer
    if n_noise > 0:
        hits = get_noise(n_noise, max_span=max_span)
    else:
        hits = [0] * 6

    # if explicit segments are not specified then
    # we choose a collection of segments within the limits of the chamber
    if not bend_angs and not strips:
        max_slope = 37 / (N_LAYERS - 1)
        bend_angs = [random.uniform(-max_slope, max_slope) for _ in range(n_segs)]
        strips = [random.randint(0, max_span - 1) for _ in range(n_segs)]

    segments = zip(strips, bend_angs)

    for segment in segments:
        (strip, slope) = segment
        for ly in range(6):
            if random.uniform(0, 1) < efficiency:

                cluster_width = random.randint(1, 3)
                cluster_mask = 2**cluster_width - 1

                center = round(strip + slope * (2.5 - ly))

                if center > 0:
                    hits[ly] |= cluster_mask << center

    for ly in range(6):
        hits[ly] &= SPAN_MASK

    return hits
