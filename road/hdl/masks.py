
from printly_dat import printly_dat
from subfunc import*
import numpy as np

pat_straight=patdef_t(15,hi_lo_t(1,-1),hi_lo_t(1,-1),hi_lo_t(1,-1),hi_lo_t(0,0),hi_lo_t(1,-1),hi_lo_t(1,-1))
pat_l=patdef_t(14,hi_lo_t(-1,-4),hi_lo_t(0,-3),hi_lo_t(1,-1),hi_lo_t(1,-1),hi_lo_t(3,0),hi_lo_t(4,1))
pat_r=mirror_patdef(pat_l,pat_l.id-1)
pat_l2=patdef_t(12,hi_lo_t(-2,-5),hi_lo_t(1,-4),hi_lo_t(1,-1),hi_lo_t(1,-1),hi_lo_t(4,1),hi_lo_t(5,2))
pat_r2=mirror_patdef(pat_l2,pat_l2.id-1)
pat_l3=patdef_t(10,hi_lo_t(-5,-8),hi_lo_t(-4,-7),hi_lo_t(0,-3),hi_lo_t(2,-2),hi_lo_t(7,4),hi_lo_t(8,5))
pat_r3=mirror_patdef(pat_l3,pat_l3.id-1)
pat_l4=patdef_t(8,hi_lo_t(-5,-8),hi_lo_t(-4,-7),hi_lo_t(0,-3),hi_lo_t(2,-2),hi_lo_t(7,4),hi_lo_t(8,5))
pat_r4=mirror_patdef(pat_l4,pat_l4.id-1)
pat_l5=patdef_t(6,hi_lo_t(-8,-11),hi_lo_t(-5,-9),hi_lo_t(0,-3),hi_lo_t(3,0),hi_lo_t(9,5),hi_lo_t(11,8))
pat_r5=mirror_patdef(pat_l5,pat_l5.id-1)
pat_l6=patdef_t(4,hi_lo_t(-11,-15),hi_lo_t(-9,-11),hi_lo_t(4,-9),hi_lo_t(9,4),hi_lo_t(11,9),hi_lo_t(15,11))
pat_r6=mirror_patdef(pat_l6,pat_l6.id-1)
pat_l7=patdef_t(2,hi_lo_t(-10,-18),hi_lo_t(-6,-14),hi_lo_t(2,-9),hi_lo_t(9,2),hi_lo_t(14,6),hi_lo_t(18,10))
pat_r7=mirror_patdef(pat_l7,pat_l7.id-1)

patlist=[pat_straight,pat_l,pat_r,pat_l2,pat_r2,pat_l3,pat_r3,pat_l4,pat_r4,pat_l5,pat_r5,pat_l6,pat_r6,pat_l7,pat_r7]

pats_m=[]
for w in range(len(patlist)):
            pats_m.append(get_ly_mask(patlist[w],37))
pat_id_list=np.zeros(len(patlist))
for y in range(len(patlist)):
    pat_id_list[y]=patlist[y].id

def print_my_mask(pats_m,pat_id_list):
    for x in range(len(pats_m)):
        print('Pattern ID: %d' %pat_id_list[x])
        printly_dat(pats_m[x])
        print('\n')

print_my_mask(pats_m,pat_id_list)

# Pattern ID: 15
# ly0 -----------------XXX-----------------

# ly1 -----------------XXX-----------------

# ly2 -----------------XXX-----------------

# ly3 ------------------X------------------

# ly4 -----------------XXX-----------------

# ly5 -----------------XXX-----------------



# Pattern ID: 14
# ly0 --------------XXXX-------------------

# ly1 ---------------XXXX------------------

# ly2 -----------------XXX-----------------

# ly3 -----------------XXX-----------------

# ly4 ------------------XXXX---------------

# ly5 -------------------XXXX--------------



# Pattern ID: 13
# ly0 -------------------XXXX--------------

# ly1 ------------------XXXX---------------

# ly2 -----------------XXX-----------------

# ly3 -----------------XXX-----------------

# ly4 ---------------XXXX------------------

# ly5 --------------XXXX-------------------



# Pattern ID: 12
# ly0 -------------XXXX--------------------

# ly1 --------------XXXXXX-----------------

# ly2 -----------------XXX-----------------

# ly3 -----------------XXX-----------------

# ly4 -------------------XXXX--------------

# ly5 --------------------XXXX-------------



# Pattern ID: 11
# ly0 --------------------XXXX-------------

# ly1 -----------------XXXXXX--------------

# ly2 -----------------XXX-----------------

# ly3 -----------------XXX-----------------

# ly4 --------------XXXX-------------------

# ly5 -------------XXXX--------------------



# Pattern ID: 10
# ly0 ----------XXXX-----------------------

# ly1 -----------XXXX----------------------

# ly2 ---------------XXXX------------------

# ly3 ----------------XXXXX----------------

# ly4 ----------------------XXXX-----------

# ly5 -----------------------XXXX----------



# Pattern ID: 9
# ly0 -----------------------XXXX----------

# ly1 ----------------------XXXX-----------

# ly2 ------------------XXXX---------------

# ly3 ----------------XXXXX----------------

# ly4 -----------XXXX----------------------

# ly5 ----------XXXX-----------------------



# Pattern ID: 8
# ly0 ----------XXXX-----------------------

# ly1 -----------XXXX----------------------

# ly2 ---------------XXXX------------------

# ly3 ----------------XXXXX----------------

# ly4 ----------------------XXXX-----------

# ly5 -----------------------XXXX----------



# Pattern ID: 7
# ly0 -----------------------XXXX----------

# ly1 ----------------------XXXX-----------

# ly2 ------------------XXXX---------------

# ly3 ----------------XXXXX----------------

# ly4 -----------XXXX----------------------

# ly5 ----------XXXX-----------------------



# Pattern ID: 6
# ly0 -------XXXX--------------------------

# ly1 ---------XXXXX-----------------------

# ly2 ---------------XXXX------------------

# ly3 ------------------XXXX---------------

# ly4 -----------------------XXXXX---------

# ly5 --------------------------XXXX-------



# Pattern ID: 5
# ly0 --------------------------XXXX-------

# ly1 -----------------------XXXXX---------

# ly2 ------------------XXXX---------------

# ly3 ---------------XXXX------------------

# ly4 ---------XXXXX-----------------------

# ly5 -------XXXX--------------------------



# Pattern ID: 4
# ly0 ---XXXXX-----------------------------

# ly1 -------XXX---------------------------

# ly2 ---------XXXXXXXXXXXXXX--------------

# ly3 ----------------------XXXXXX---------

# ly4 ---------------------------XXX-------

# ly5 -----------------------------XXXXX---



# Pattern ID: 3
# ly0 -----------------------------XXXXX---

# ly1 ---------------------------XXX-------

# ly2 --------------XXXXXXXXXXXXXX---------

# ly3 ---------XXXXXX----------------------

# ly4 -------XXX---------------------------

# ly5 ---XXXXX-----------------------------



# Pattern ID: 2
# ly0 XXXXXXXXX----------------------------

# ly1 ----XXXXXXXXX------------------------

# ly2 ---------XXXXXXXXXXXX----------------

# ly3 --------------------XXXXXXXX---------

# ly4 ------------------------XXXXXXXXX----

# ly5 ----------------------------XXXXXXXXX



# Pattern ID: 1
# ly0 ----------------------------XXXXXXXXX

# ly1 ------------------------XXXXXXXXX----

# ly2 ----------------XXXXXXXXXXXX---------

# ly3 ---------XXXXXXXX--------------------

# ly4 ----XXXXXXXXX------------------------

# ly5 XXXXXXXXX----------------------------



