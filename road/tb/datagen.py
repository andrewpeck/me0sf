# Test case generator for pat_unit.vhd
# TODO: should slope be uniform or follow some distribution (e.g. vaguely modeling the pT distribution [from nick]?)
from math import floor
import random
from subfunc import *
from constants import *

def get_seg_hits(bend_ang=None, strip=None, eff=.9, max_span=37):
    """get the hits for given segment, if bend_ang and strip==None, create random slope and strip. eff= efficiency of data aquisition, default of 90%.
     Returns integer mask of the segment hits
     To do: add width to hits --> right now, takes a width of 1, 2 or 3 randomly
     """
    if bend_ang == None and strip == None:
        center_lo = max_span // 2 - 1
        center_hi = max_span // 2 + 1
        slope = random.uniform(-1 * (37 / (N_LAYERS - 1)), 37 / (N_LAYERS - 1)) 
        strip = random.randint(center_lo, center_hi) - slope * 2.5
    else:
        slope = bend_ang
        strip = strip
    hits = [[0]]*6 
    # get hit strips for each layer
    for layer in range(6):
        if random.uniform(0,1) < eff:
            width = random.randint(1,3)
            hits[layer] =[round(strip + slope*(2.5-layer))]
            if width == 2:
                #for clusters of 2, add extra hit 
                if round(strip + slope*(2.5-layer)) == floor(strip + slope*(2.5-layer)):
                   hits[layer] +=[hits[layer][0]-1]
                else:
                    hits[layer] +=[hits[layer][0]+1]
            if width == 3:
                for i in range(2):
                    hits[layer] +=[hits[layer][0]+(-1)**i]  #add extra hits to cluster, +- 1 strip
            #if any strips < 0 or > max_span, set them to 0 (outside pattern window)
            for (i, hit) in enumerate(hits[layer]):
                if hit < 0 or hit > max_span:
                    hits[layer][i] = 0
    #get integer mask for the hits
    hit_mask=[0]*6
    for (ly, dat) in enumerate(hits):
        for hit in dat:
            if hit != 0:
                hit_mask[ly] = set_bit(int(hit), hit_mask[ly])
    hit_mask.reverse()
    return (hit_mask, slope, strip) 

def get_noise(n, max_span=37):
    """generates integer mask for n background hits"""
    noise_mask = [0]*6
    for _ in range(n):
        ly = random.randint(0,5)
        strip = random.randint(0,max_span)
        noise_mask[ly] = set_bit(strip, noise_mask[ly])
    return noise_mask

def datagen_with_segs(n_segs, n_noise, max_span=192, bend_angs=None, strips=None):

    """generates data for each layer based on an artificial muon track and noise, returns a list of 6 intgers representing the generated hits on those layers, tuple of bend angles and strips

    Args: n_segs = # of segments, n_noise = # of background hits, max_span =  width of a pattern window (Default value = 37)
    bend_angs, strips = lists of bend angles and strips to create given segments """
    if n_segs == 0:
        seg_masks = [[0]*6]
        bend_ang_strip = []
    elif bend_angs !=None and strips !=None:
        n_segs = n_segs - len(bend_angs) #need to put in case for if n_segs< # of given bend_angs/strips?
        segs = list(map(lambda bend_ang, strip: get_seg_hits(bend_ang, strip, eff=1, max_span=max_span), bend_angs, strips))
        seg_masks = [seg[0] for seg in segs]
        bend_ang_strip = [(bend_ang, strip) for (bend_ang, strip) in zip(bend_angs, strips)]
        for _ in range(n_segs):
            rand_seg = get_seg_hits(max_span=max_span, eff=1)
            seg_masks.append(rand_seg[0])
            bend_ang_strip.append((rand_seg[1], rand_seg[2]))     
    else:
        segs = [get_seg_hits(max_span=max_span, eff=1) for _ in range(n_segs)]
        seg_masks = [seg[0] for seg in segs]
        bend_ang_strip = [(seg[1], seg[2]) for seg in segs]
        
    noise_mask = get_noise(n_noise, max_span = max_span)
    data_mask = [0]*6
    for mask in seg_masks:
        for i in range(6):
            data_mask[i] = mask[i] | noise_mask[i] | data_mask[i]
    return data_mask, bend_ang_strip

def datagen(n_segs, n_noise, max_span=192, bend_angs=None, strips=None):
    return datagen_with_segs(n_segs, n_noise, max_span=max_span, bend_angs=bend_angs, strips=strips)[0]
