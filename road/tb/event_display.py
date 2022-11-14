# Matplotlib display for different levels of hardware design
import matplotlib.pyplot as plt
from subfunc import *
from pat_unit_beh import find_best_seg, get_ly_mask
from datagen import datagen
import random
import math
from centroid_finding import *
from matplotlib.patches import Rectangle

def int2_xy(masks, offset):

    x = [list(map (lambda x : x+offset, find_ones(ly))) for ly in masks]
    y = [[i]*len(ones) for (i,ones) in enumerate(x)]

    # converting 2d list into 1d
    # using list comprehension
    x = [j for sub in x for j in sub]
    y = [j for sub in y for j in sub]

    return x,y

def llse_fit(x, y):

    x_sum = sum(x)
    y_sum = sum(y)
    n = len(x)

    products = 0
    squares = 0
    for i in range(len(x)):
        products += (n * x[i] - x_sum) * (n * y[i] - y_sum)
        squares += (n * x[i] - x_sum) ** 2

    m = 1.0 * products / squares
    b = 1.0 / n * (y_sum - m * x_sum)

    return m, b

def event_display(hits=None, fits=None, pats=None, width=192, max_span=37, event=None, chamber=None, partition=None):

    # hits come in as a list of 6 integers
    # fits should come in as a m and a b --> might have to have info
    # on what vals we also used to create these; centroid info o/w fits not gonna work
    # fits = [[m,b,[centroids_x]]]
    # pat found should come in as a pat id and strip; must orient this on the strip given
    # use the read of patlist from firmware and getmypattern function to configure this
    # order of operations --> get the pattern get drawn first in cyan 'c' with a markersize=10
    # then throw on the hits with black o's 'ko'
    # then connect the dots with black lines--> fits come last

    # f = plt.figure()
    # f.set_figwidth(4)
    # ax.set_aspect(5)

    fig, ax = plt.subplots()

    fig.set_figheight(3.0)
    fig.set_figwidth(width*0.1)

    plt.xlabel('strip', fontsize=12)
    plt.ylabel('layer', fontsize=12)
    plt.xlim([0, width+2])
    plt.ylim(-1, 6)
    plt.xticks([x*16 for x in range(0,int(width/16)+1)])
    plt.yticks([0,1,2,3,4,5])

    if event is not None and chamber is not None and partition is not None:
        plt.title("Event " + str(event) + ", Chamber "+ str(chamber) + ", Partition " + str(partition))
    width = 1
    height = 0.25

    # plot pattern masks
    if pats is not None:

        for pat in pats:
            (pat, strip) = pat
            mask = get_ly_mask(pat)
            # print(mask)
            (x, y) = int2_xy(mask.mask, strip-math.floor(max_span/2.0))
            # plt.scatter(x, y, s=60, marker='s', facecolors='cyan',  alpha=0.5, edgecolors='gray')
            for (px, py) in zip(x,y):
                ax.add_patch(Rectangle(
                    xy=(px-width/2, py-height/2) ,width=width, height=height,
                    linewidth=1, color='teal', fill=False))

    # plot raw hits
    if hits is not None:
        (x, y) = int2_xy(hits, 0)
        for (px, py) in zip(x,y):
            ax.add_patch(Rectangle(
                xy=(px-width/2, py-height/2) ,width=width, height=height,
                linewidth=1, color='#666', fill=True))

    # plot fitted lines
    if fits is not None:
        for fit in fits:

            m = fit[0]
            b = fit[1]
            strip = fit[2]

            y = (0, 5)
            x = (strip+b -2.5*m , strip+b +2.5*m  )
            


            plt.plot(x,y)

    plt.show()

# testing with pat_unit.vhd
if __name__ == '__main__':

    random.seed(56)

    MAX_SPAN = 37
    #hits = datagen(MAX_SPAN=MAX_SPAN)
    hits = [2113536, 1085440, 2445312, 1183744, 5308416, 4194368]
    segment = find_best_seg(hits, max_span=MAX_SPAN)
    print (segment)
    strip = MAX_SPAN // 2

    pats = [[PATLIST_LUT[segment.id], 18]]
    fits = [[-0.25, 1, 20]] # (m, b, strip)
    # fits = None
    event_display(hits=hits, fits=fits, pats=pats, width=192, max_span=MAX_SPAN)
