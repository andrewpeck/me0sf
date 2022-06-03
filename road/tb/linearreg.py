import matplotlib.pyplot as plt
import random
from datadev import datadev
from pat_unit_beh import process_pat
from printly_dat import printly_dat
from subfunc import *
import statistics as stat


# FIX ME: NEED TO GET RID OF THE FANCY BITWISE ANDING OF DATA BEFORE FINDING CENTROID
# WE CAN ASSUME THAT WE WILL FEED IN DATA VALUES THAT ARE ALREADY WITHIN THE MASK IN QUESTION
# FIX ME: CHANGE 'NONE' DESIGNATION FOR NO HITS TO 0


def find_pos(dat_pos_bin):
    """takes in a string detailing the hits within a mask and returns these hit positions"""
    positions = []
    count = 0
    for i in range(len(dat_pos_bin)):
        if dat_pos_bin[i] == "1":
            positions.append(i)
            count += 1
    # set any layer without hits within the mask to None; will be used in future data filtering
    if count == 0:
        positions = None
    return positions


def find_true_coordinates(centroids, pat_id, patlist, MAX_SPAN=37):
    """takes in a list of centroids for all layers, pat_id, patlist, and MAX_SPAN to determine the centroid coordinates relative to the entire layer"""
    center = MAX_SPAN // 2
    y_list = []
    pattern = get_mypattern(pat_id, patlist)
    if centroids[0] != None:
        y_list.append(centroids[0] + pattern.ly0.lo + center)
    else:
        y_list.append(None)
    if centroids[1] != None:
        y_list.append(centroids[1] + pattern.ly1.lo + center)
    else:
        y_list.append(None)
    if centroids[2] != None:
        y_list.append(centroids[2] + pattern.ly2.lo + center)
    else:
        y_list.append(None)
    if centroids[3] != None:
        y_list.append(centroids[3] + pattern.ly3.lo + center)
    else:
        y_list.append(None)
    if centroids[4] != None:
        y_list.append(centroids[4] + pattern.ly4.lo + center)
    else:
        y_list.append(None)
    if centroids[5] != None:
        y_list.append(centroids[5] + pattern.ly5.lo + center)
    else:
        y_list.append(None)
    return y_list


def best_fit(x_data, y_data):
    """takes in x_data and y_data to determine the values necessary for linear regression; uses linear least squares method"""
    # eliminate data values that correlate to no hits within the mask of a layer
    # elimination_indices = []
    # for i in range(len(y_data)):
    #     if y_data[i] == None:
    #         elimination_indices.append(i)
    # elimination_vals = []
    # for j in range(len(elimination_indices)):
    #     elimination_vals.append(x_data[elimination_indices[j]])
    # x_data = set(x_data)
    # elimination_vals = set(elimination_vals)
    # x_data = x_data - elimination_vals
    # x_data = list(x_data)
    # y_data = [n for n in y_data if n != None]
    sum_x = 0
    sum_y = 0
    for i in range(len(x_data)):
        sum_x = sum_x + x_data[i]
        sum_y = sum_y + y_data[i]
    n = len(x_data)
    xy_list = []
    x_sq_list = []
    for k in range(len(x_data)):
        xy_list.append(x_data[k] * y_data[k])
        x_sq_list.append(x_data[k] ** 2)
    sum_xy = sum(xy_list)
    sum_x_sq = sum(x_sq_list)
    denominator = n * sum_x_sq - sum_x**2
    if denominator == 0:
        denominator = 1
    slope = (n * sum_xy - (sum_x * sum_y)) / denominator
    b = (sum_y - slope * sum_x) / n
    y_fit = []
    for j in range(len(y_data)):
        y_fit.append(slope * x_data[j] + b)
    slope = round(slope, 8)
    b = round(b, 8)
    int(slope)
    int(b)
    for i in range(len(y_fit)):
        y_fit[i] = int(y_fit[i])

    return slope, b, y_fit


def plot_my_best_fit(slope, b, x_data, y_data, y_fit):
    """uses matplotlib.pyplot to plot line of best fit and print its equation to the figure"""
    string = "y=" + str(slope) + "x" + "+" + str(b)
    plt.ylim(1, 36)
    plt.plot(x_data, y_data, "o")
    plt.plot(x_data, y_fit, "k-")
    plt.title("Sample Data")
    plt.legend([None, string])
    plt.show()


# plot_my_best_fit(slope=1,b=0,x_data=[1,2,3,4,5],y_data=[1,12,3,4,5],y_fit=[1,2,3,4,5])

# temporary testing framework
# for i in range(15):
#     [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x] = datadev()
#     ly_dat = [ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x]
#     [pat_id, ly_c] = process_pat(
#         patlist, ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x, MAX_SPAN=37
#     )
#     centroids = find_centroids(pat_id, patlist, ly_dat, MAX_SPAN=37)
#     x_list = [0, 1, 2, 3, 4, 5]
#     y_list = find_true_coordinates(centroids, pat_id, patlist)
#     [slope, b, y_fit, x_data, y_data] = best_fit(x_list, y_list)
#     plot_my_best_fit(slope, b, x_data, y_data, y_fit)
