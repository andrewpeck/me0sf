#trying out a comparison function for patition_beh.py

def compare_ghosts(val,comp_list):
    for i in range(len(comp_list)):
        if (val[0]==comp_list[i][0] or val[0]==comp_list[i][0]+2 or val[0]==comp_list[i][0]-2):
            val=0
            break
    return val


#check if this works with sample data; pattern=[[pat_id, ly_c, strip]]
val=[2,13,69]
comp_list=[[5,24,129],[5,23,192],[2,24,139]]

val=compare_ghosts(val,comp_list=comp_list)
print(val)