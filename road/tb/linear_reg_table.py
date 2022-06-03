# generates the look up table for our linear regression software

from subfunc import *

# set widths to current and anticipated pattern sizes
all_widths = range(1, 15)

def generate_all_comb(width=all_widths):
    all_comb = []
    # create a list of integer values for every binary combination possible in each of the widths specified
    for i in range(len(width)):
        temp_list = [l for l in range(2 ** width[i])]
        # store the width with each list of possible integer values for that width (in binary); will be necessary for find_pos function
        all_comb.append([width[i], temp_list])
    return all_comb


all_comb = generate_all_comb()


def find_pos(dat_pos_bin):
    """takes in a string detailing the hits within a mask and returns these hit positions"""
    positions = []
    count = 0
    for i in range(len(dat_pos_bin)):
        if dat_pos_bin[i] == "1":
            positions.append(i)
            count += 1
    # set any layer without hits within the mask to 0; will be used in future data filtering
    if count == 0:
        positions = 0
    return positions


def general_findcentroid(data, width):
    """takes in an integer and a set binary width to return a centroid for the data set"""
    bin_dat = bin(data)[2:].zfill(width)
    ly_pos = find_pos(bin_dat)
    sum_ly_pos = 0
    if type(ly_pos) != int:
        # average the different positions of hits within the layer to find the 'true' centroid of the data set
        for l in range(len(ly_pos)):
            sum_ly_pos = sum_ly_pos + ly_pos[l]
        centroid = sum_ly_pos // len(ly_pos)
        # determine which data value in the layer is closest to this 'true' centroid; set that as the centroid for the data
        min_dist = 999
        closest = 0
        for i in range(len(ly_pos)):
            dist = abs(ly_pos[i] - centroid)
            if dist <= min_dist:
                min_dist = dist
                closest = ly_pos[i]
        centroid = closest
    else:
        centroid = 0
    return centroid


# generate centroids for each data set
all_centroids = []
for i in range(len(all_comb)):
    centroids = []
    for j in range(len(all_comb[i][1])):
        centroids.append(
            general_findcentroid(data=all_comb[i][1][j], width=all_comb[i][0])
        )
    all_centroids.append(centroids)


# match the centroids to their data values; store in data,centroid format
final_pairings = []
for k in range(len(all_centroids)):
    binary_vals = [bin(g)[2:].zfill(all_comb[k][0]) for g in all_comb[k][1]]
    final_pairings.append([all_comb[k][0], binary_vals, all_centroids[k]])


def generate_VHDL_lines(final_pairings):
    """convert final centroid, data, and width pairings into VHDL lines to write to find_centoid.vhd file"""
    VHDL_lines = []
    for i in range(len(final_pairings)):
        VHDL_lines.append("if (length = %d then)" % final_pairings[i][0])
        VHDL_lines.append(
            " index := %d when ly = '%s' else"
            % (final_pairings[i][2][0], final_pairings[i][1][0])
        )
        for j in range(1, (len(final_pairings[i][1]) - 1)):
            VHDL_lines.append(
                "          %d when ly = '%s' else"
                % (final_pairings[i][2][j], final_pairings[i][1][j])
            )
        j = (
            len(final_pairings[i][1]) - 1
        )  # FIX ME; FIGURE OUT WHY THIS ASSIGNMENT IS NECESSARY OR REPLACE IT
        VHDL_lines.append(
            "          %d when ly = '%s' else 0;"
            % (final_pairings[i][2][j], final_pairings[i][1][j])
        )
        VHDL_lines.append("end if;")
        VHDL_lines.append("\n")
    return VHDL_lines


VHDL_lines = generate_VHDL_lines(final_pairings)

# remember this lut is arranged every combo of each width from [1,3,4,5,6,8,9,12,14]
# write stored VHDL lines into the find_centoid.vhd file; use same format as the find_centoid function in the me0sf repository
start = [
    "function centroid (ly : std_logic_vector; length : natural) return natural is",
    "  variable index : natural;",
    "begin",
]
f = open("./find_centroid.vhd", "w")
for i in range(len(start)):
    f.write(start[i])
    f.write("\n")
for j in range(len(VHDL_lines)):
    f.write(VHDL_lines[j])
    f.write("\n")
f.write("return index;")
f.close()
