# Emulator for chamber.vhd
from subfunc import *
from datadev_mux import datadev_mux
from partition_beh import work_partition


def work_chamber(
    chamber_data,
    patlist,
    NUM_PARTITIONS=8,
    MAX_SPAN=37,
    WIDTH=192,
    group_width=8,
    ghost_width=4,
    NUM_VALS=4,
):
    def priority_encoder(group_vals, num_output=NUM_VALS):
        quality_vec = []
        store_index = []
        final_vals = []
        for i in range(len(group_vals)):
            # data received in order of id, cnt, strip, partition
            partition = group_vals[i][3]
            strip = group_vals[i][2]
            pat_id = group_vals[i][0]
            ly_c = group_vals[i][1]
            quality = (
                partition | (strip << 3) | (pat_id << (3 + 9)) | (ly_c << (3 + 9 + 4))
            )
            quality_vec.append(quality)
        for j in range(num_output):
            max_val = max(quality_vec)
            index = quality_vec.index(max_val)
            store_index.append(index)
            quality_vec = [z for z in quality_vec if z != quality_vec[index]]
        for k in range(len(store_index)):
            final_vals.append(group_vals[store_index[k]])
        return final_vals

    chamber_dat = []
    for i in range(NUM_PARTITIONS):
        partition_dat = work_partition(
            chamber_data=chamber_data[i],
            patlist=patlist,
            MAX_SPAN=MAX_SPAN,
            WIDTH=WIDTH,
            group_width=group_width,
            ghost_width=ghost_width,
        )
        for j in range(len(partition_dat)):
            partition_dat[j].append(i)
        chamber_dat = chamber_dat + partition_dat

    # chamber_filt1=[]
    # for k in range(1,len(chamber_dat),2):
    #     chamber_filt1=chamber_filt1+priority_encoder(group_vals=chamber_dat[k-1:k+1],num_output=int((len(chamber_dat[k])/2))) #FIXME: remember to set this chamber dat[k]/2 value to be a known value

    # chamber_filt2=priority_encoder(group_vals=chamber_filt1,num_output=NUM_VALS)

    return chamber_dat


# chamber_data=[datadev_mux(WIDTH=192) for i in range(8)]
# # print(chamber_data)
# output=work_chamber(chamber_data, patlist, NUM_PARTITIONS=8, MAX_SPAN=37, WIDTH=192,group_width=8,ghost_width=4,NUM_VALS=12)
