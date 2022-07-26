# Test case generator for pat_unit.vhd
# TODO: should slope be uniform or follow some distribution (e.g. vaguely modeling the pT distribution [from nick]?)
import random
from subfunc import *
from constants import *

def get_seg_hits(bend_ang=None, substrip=None, eff=.9, MAX_SPAN=37):
    """get the hits for given segment, if bend_ang and substrip==None, create random slope and substrip. eff= efficiency of data aquisition, default of 90%.
     Returns integer mask of the segment hits
     To do: add width to hits --> right now, takes a width of 1, 2 or 3 and just adds extra hits to either side
     """
    if bend_ang == None and substrip == None:
        center_lo = MAX_SPAN // 2 - 1
        center_hi = MAX_SPAN // 2 + 1
        slope = random.uniform(-1 * (37 / (N_LAYERS - 1)), 37 / (N_LAYERS - 1)) 
        substrip = round(random.randint(center_lo, center_hi) - slope * 2.5)
    else:
        slope = bend_ang
        substrip = round(substrip)
    hits = [[0]]*6 
    # get hit strips for each layer
    for layer in range(6):
        if random.uniform(0,1) < eff:
            width = random.randint(1,3)
            hits[layer] =[round(substrip + slope*(2.5-layer))]
            if width>1:
                for i in range(1, width):
                    hits[layer] +=[hits[layer][0]+(-1)**i] #add extra hits to cluster, +- 1 strip
            #if any strips < 0 or > MAX_SPAN, set them to 0 (outside pattern window)
            for (i, hit) in enumerate(hits[layer]):
                if hit < 0 or hit > MAX_SPAN:
                    hits[layer][i] = 0
    #get integer mask for the hits
    hit_mask=[0]*6
    for (ly, dat) in enumerate(hits):
        for hit in dat:
            if hit != 0:
                hit_mask[ly] = set_bit(hit, hit_mask[ly])
    hit_mask.reverse()
    return (hit_mask, slope, substrip) 

def get_noise(n, MAX_SPAN=37):
    """generates integer mask for n background hits"""
    noise_mask = [0]*6
    for _ in range(n):
        ly = random.randint(0,5)
        strip = random.randint(0,MAX_SPAN)
        noise_mask[ly] = set_bit(strip, noise_mask[ly])
    return noise_mask

def datagen_with_segs(n_segs, n_noise, MAX_SPAN=192, bend_angs=None, substrips=None):
    """generates data for each layer based on an artificial muon track and noise, returns a list of 6 intgers representing the generated hits on those layers, tuple of bend angles and substrips 

    Args: n_segs = # of segments, n_noise = # of background hits, MAX_SPAN =  width of a pattern window (Default value = 37)
    bend_angs, substrips = lists of bend angles and substrips to create given segments """
    if n_segs == 0:
        seg_masks = [[0]*6]
        bend_ang_strip = []
    elif bend_angs !=None and substrips !=None:
        n_segs = n_segs - len(bend_angs) #need to put in case for if n_segs< # of given bend_angs/substrips?
        segs = list(map(lambda bend_ang, substrip: get_seg_hits(bend_ang, substrip), bend_angs, substrips))
        seg_masks = [seg[0] for seg in segs]
        bend_ang_strip = [(bend_ang, substrip) for (bend_ang, substrip) in zip(bend_angs, substrips)]
        for _ in range(n_segs):
            rand_seg = get_seg_hits(MAX_SPAN=MAX_SPAN)
            seg_masks.append(rand_seg[0])
            bend_ang_strip.append((rand_seg[1], rand_seg[2]))     
    else:
        segs = [get_seg_hits(MAX_SPAN=MAX_SPAN) for _ in range(n_segs)]
        seg_masks = [seg[0] for seg in segs]
        bend_ang_strip = [(seg[1], seg[2]) for seg in segs]
        
    noise_mask = get_noise(n_noise, MAX_SPAN = MAX_SPAN)
    data_mask = [0]*6
    for mask in seg_masks:
        for i in range(6):
            data_mask[i] = mask[i] | noise_mask[i] | data_mask[i]
    return data_mask, bend_ang_strip

def datagen(n_segs, n_noise, MAX_SPAN=192, bend_angs=None, substrips=None):
    return datagen_with_segs(n_segs, n_noise, MAX_SPAN=MAX_SPAN, bend_angs=bend_angs, substrips=substrips)[0]