from subfunc import get_ly_mask


def printly_dat(mask=None, data=None, MAX_SPAN=37):
    """takes in data and/or a mask and returns a visual representation of the info"""
    assert type(MAX_SPAN)==int,"MAX_SPAN input must be an integer."
    # create an iterable mask string
    if mask is not None:
        iterable_mask = []
        for m in range(len(mask)):
            mask_v = mask[m]
            val_m = bin(mask_v)[2:]
            val_m = val_m.zfill(MAX_SPAN)
            iterable_mask.append(val_m)
    # create an iterable data string
    if data is not None:
        iterable_data = []
        for n in range(len(data)):
            data_v = data[n]
            val_d = bin(data_v)[2:]
            val_d = val_d.zfill(MAX_SPAN)
            iterable_data.append(val_d)
    if mask is None and data is None:
        print("Error; need to provide values")
    for i in range(6):
        print("ly%d " % i, end="")
        for j in range(MAX_SPAN):
            if data is not None and mask is not None:
                if iterable_data[i][j] == "1":
                    print("1", end="")
                elif iterable_mask[i][j] == "1":
                    print("X", end="")
                else:
                    print("-", end="")
            elif data is not None:
                if iterable_data[i][j] == "1":
                    print("1", end="")
                else:
                    print("-", end="")
            elif mask is not None:
                if iterable_mask[i][j] == "1":
                    print("X", end="")
                else:
                    print("-", end="")
            else:
                print("-", end="")
        print("\n")
