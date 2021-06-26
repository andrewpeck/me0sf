#Testcases for pat_unit testbench
from datadev_b import datadev_b

def datadev_t(MAX_SPAN=37):
    a=datadev_b(MAX_SPAN)
    print(a)
    ly0=a[0]
    ly1=a[1]
    ly2=a[2]
    ly3=a[3]
    ly4=a[4]
    ly5=a[5]
    ly0_l=ly0.tolist()
    ly1_l=ly1.tolist()
    ly2_l=ly2.tolist()
    ly3_l=ly3.tolist()
    ly4_l=ly4.tolist()
    ly5_l=ly5.tolist()
    ly0_sl=list(map(str,ly0_l))
    ly1_sl=list(map(str,ly1_l))
    ly2_sl=list(map(str,ly2_l))
    ly3_sl=list(map(str,ly3_l))
    ly4_sl=list(map(str,ly4_l))
    ly5_sl=list(map(str,ly5_l))
    ly0_s=', '.join(ly0_sl)
    ly0_f=int(ly0_s.replace(', ',''))
    ly1_s=', '.join(ly1_sl)
    ly1_f=int(ly1_s.replace(', ',''))
    ly2_s=', '.join(ly2_sl)
    ly2_f=int(ly2_s.replace(', ',''))
    ly3_s=', '.join(ly3_sl)
    ly3_f=int(ly3_s.replace(', ',''))
    ly4_s=', '.join(ly4_sl)
    ly4_f=int(ly4_s.replace(', ',''))
    ly5_s=', '.join(ly5_sl)
    ly5_f=int(ly5_s.replace(', ',''))
    return ly0_f,ly1_f,ly2_f,ly3_f,ly4_f,ly5_f


