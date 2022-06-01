from printly_dat import printly_dat
from subfunc import*

pat_id=2
ly0_x=0
ly1_x=0
ly2_x=0
ly3_x=0
ly4_x=0
ly5_x=0
MAX_SPAN=37
for m in range(len(patlist)):
    if patlist[m].id == pat_id:
        mask_v = get_ly_mask(patlist[m], MAX_SPAN)
        print("Emulator Pattern Assignment:")
        printly_dat(data=[ly0_x, ly1_x, ly2_x, ly3_x, ly4_x, ly5_x], mask=mask_v, MAX_SPAN=MAX_SPAN)
        print("\n")
    else:
        break
    print("Layer count smaller than layer count threshold.")