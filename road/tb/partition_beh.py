#Python implementation of the partition.vhd behavior
from pat_unit_mux_beh import pat_mux
from datadev_mux import datadev_mux
from subfunc import*
import pprint

def work_partition(pat_mux_dat,group_size=8,ghost_width=2):
    """takes in pat unit mux data, a group size, and a ghost width to return a smaller data set, using ghost edge cancellation
    and segment quality filtering
    NOTE: ghost width denotes the width where we can likely see copies of the same segment in the data"""
    def edge_cancellation(pat_mux_dat, group_size):
        '''takes in pat_unit_mux data, parses it into groups of the specified size and sets any ghost values in the groups to None'''
        #sort strip data into groups
        groups=[]
        for i in range(group_size-1,len(pat_mux_dat),group_size):
            j=i+1
            group=pat_mux_dat[j-group_size:j]
            groups.append(group)
        # print('groups prior to cancellation ')
        # pprint.pprint(groups)
        #determine what repeated edge values "ghosts" we need to eliminate
        for k in range(1,len(groups),2):
            comp_group=[groups[k-1],groups[k]]
            #define the list of possible ghosts in the first and second groups
            comp_1=comp_group[0][(group_size-ghost_width//2):]
            comp_2=comp_group[1][:ghost_width//2]
            total_id_comp=comp_1+comp_2
            for n in range(len(total_id_comp)):
                curr_id_comp=total_id_comp[:n]+total_id_comp[n+1:]
                for o in range(len(curr_id_comp)):
                    if (total_id_comp[n][0]==curr_id_comp[o][0] or total_id_comp[n][0]+2==curr_id_comp[o][0] or total_id_comp[n][0]-2==curr_id_comp[o][0]):
                        total_id_comp[n]=[0,0,0] #setting the first instance of a ghost to 000's should get rid of all the ghosts; CHECK ME LATER
            #reassign values based on changed comparison groups
            groups[k-1][(group_size-ghost_width//2):]=total_id_comp[:ghost_width//2]
            groups[k][:ghost_width//2]=total_id_comp[ghost_width//2:]
        return groups
    groups=edge_cancellation(pat_mux_dat, group_size)

    def determine_quality(groups):
        best_quality=[]
        for p in range(len(groups)):
            #eliminate any ghost occurrences denoted by [0,0,0]
            groups[p]=[x for x in groups[p] if x!=[0,0,0]]
            max_lc=0
            max_id=0
            s_list=[]
            #find the highest layer count and save its index r
            for r in range(len(groups[p])):
                if (groups[p][r][1]>=max_lc):
                    max_lc=groups[p][r][1]
                    b_pat_index=r
            #check if any other patterns have the same layer count as the max layer count and save these values to slist
            for s in range(len(groups[p])):
                if (groups[p][s][1]==max_lc):
                    s_list.append(groups[p][s])
            #check which id value in slist has the highest pattern id; save the index as the best pattern index
            if (len(s_list)!=0):
                for t in range(len(s_list)):
                    if (s_list[t][0]>max_id):
                        max_id=s_list[t][0]
                        b_pat_index=t
                #choose the highest layer count and pattern id from slist
                best_quality.append(s_list[b_pat_index])
            else:
                best_quality.append(groups[p][b_pat_index])
        return best_quality
    partition_strips=determine_quality(groups)

    return partition_strips








#temporary testing format
# for i in range(50):
#     [patterns,strips_data]=pat_mux(chamber_data=datadev_mux(),patlist=patlist,MAX_SPAN=37,WIDTH=192)
#     part_strips=work_partition(pat_mux_dat=patterns,group_size=8,ghost_width=4)
#     if len(part_strips)!=24:
#         print('ERROR')