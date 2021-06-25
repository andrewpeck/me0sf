# takes in data and/or a mask and returns a visual representation of the info

def printly_dat(mask=None,data=None,MAX_SPAN=37):
    for i in range(6):
        print('ly%d '%i,end='')
        for j in range(MAX_SPAN):
            if (data is not None and mask is not None):
                if (data[i][j]==1):
                    print('1',end='')
                elif (mask[i][j]==1):
                    print('X',end='')
                else:
                    print('-',end='')
            elif (data is not None):
                if (data[i][j]==1):
                    print('1',end='')
                else:
                    print('-',end='')
            elif (mask is not None):
                if (mask[i][j]==1):
                    print('X',end='')
                else:
                    print('-',end='')
            else:
                 print('-',end='')
        print('\n')


