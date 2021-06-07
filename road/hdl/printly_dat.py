#Takes in the individual layer vectors and prints a nice visual format
def print_vis(ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x):
    #print visual data
    for l in range(len(ly0_x)):
        if (ly0_x[l]!=1):
            ly0_x[l]='-'
        else:
            ly0_x[l]='1'

        if (ly1_x[l]!=1):
            ly1_x[l]='-'
        else:
            ly1_x[l]='1'

        if (ly2_x[l]!=1):
            ly2_x[l]='-'
        else:
            ly2_x[l]='1'

        if (ly3_x[l]!=1):
            ly3_x[l]='-'
        else:
            ly3_x[l]='1'

        if (ly4_x[l]!=1):
            ly4_x[l]='-'
        else:
            ly4_x[l]='1'

        if (ly5_x[l]!=1):
            ly5_x[l]='-'
        else:
            ly5_x[l]='1'

    separator=', '
    ly0_x=separator.join(ly0_x)
    ly1_x=separator.join(ly1_x)
    ly2_x=separator.join(ly2_x)
    ly3_x=separator.join(ly3_x)
    ly4_x=separator.join(ly4_x)
    ly5_x=separator.join(ly5_x)
    ly0_x=ly0_x.replace(', ','')
    ly1_x=ly1_x.replace(', ','')
    ly2_x=ly2_x.replace(', ','')
    ly3_x=ly3_x.replace(', ','')
    ly4_x=ly4_x.replace(', ','')
    ly5_x=ly5_x.replace(', ','')
    print("ly0 %s" % ly0_x)
    print("ly1 %s" % ly1_x)
    print("ly2 %s" % ly2_x)
    print("ly3 %s" % ly3_x)
    print("ly4 %s" % ly4_x)
    print("ly5 %s \n\n" % ly5_x)


