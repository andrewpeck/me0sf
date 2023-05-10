# Generates visual representations of pat_unit.vhd masks
import math
from subfunc import *
from printly_dat import printly_dat
from pat_unit_beh import get_ly_mask, calculate_global_layer_mask

num_or = 2
num_or_to_span = {2:37, 4:19, 8:11, 16:7}
input_max_span = num_or_to_span[num_or]
factor = num_or / 2
pat_straight = patdef_t(19, create_pat_ly(-0.4 / factor, 0.4 / factor))
pat_l = patdef_t(18, create_pat_ly(0.2 / factor, 0.9 / factor))
pat_r = mirror_patdef(pat_l, pat_l.id - 1)
pat_l2 = patdef_t(16, create_pat_ly(0.5 / factor, 1.2 / factor))
pat_r2 = mirror_patdef(pat_l2, pat_l2.id - 1)
pat_l3 = patdef_t(14, create_pat_ly(0.9 / factor, 1.7 / factor))
pat_r3 = mirror_patdef(pat_l3, pat_l3.id - 1)
pat_l4 = patdef_t(12, create_pat_ly(1.4 / factor, 2.3 / factor))
pat_r4 = mirror_patdef(pat_l4, pat_l4.id - 1)
pat_l5 = patdef_t(10, create_pat_ly(2.0 / factor, 3.0 / factor))
pat_r5 = mirror_patdef(pat_l5, pat_l5.id - 1)
pat_l6 = patdef_t(8, create_pat_ly(2.7 / factor, 3.8 / factor))
pat_r6 = mirror_patdef(pat_l6, pat_l6.id - 1)
pat_l7 = patdef_t(6, create_pat_ly(3.5 / factor, 4.7 / factor))
pat_r7 = mirror_patdef(pat_l7, pat_l7.id-1)
pat_l8 = patdef_t(4, create_pat_ly(4.3 / factor, 5.5 / factor))
pat_r8 = mirror_patdef(pat_l8, pat_l8.id-1)
pat_l9 = patdef_t(2, create_pat_ly(5.4 / factor, 7.0 / factor))
pat_r9 = mirror_patdef(pat_l9, pat_l9.id - 1)

dynamic_patlist = (
    pat_straight,
    pat_l,
    pat_r,
    pat_l2,
    pat_r2,
    pat_l3,
    pat_r3,
    pat_l4,
    pat_r4,
    pat_l5,
    pat_r5,
    pat_l6,
    pat_r6,
    pat_l7,
    pat_r7,
    pat_l8,
    pat_r8,
    pat_l9,
    pat_r9)

def calculate_global_layer_mask(patlist, max_span):
    """create layer masks for patterns in patlist"""
    global LAYER_MASK
    LAYER_MASK = [get_ly_mask(pat, max_span) for pat in patlist]

pat_id_list = [pat.id for pat in dynamic_patlist]
calculate_global_layer_mask(dynamic_patlist, input_max_span)

def print_my_masks(pats_m, pat_id_list, max_span):
    for x in range(len(pats_m)):
        print("Pattern ID: %d" % pat_id_list[x])
        printly_dat(pats_m[x].mask, MAX_SPAN=max_span)
        print("\n")

print_my_masks(LAYER_MASK, pat_id_list, input_max_span)
print("num_or:", num_or)
print("max_span:", input_max_span)
print("calculated factor:", factor)


# Emulator patlist:
# ------------------------------------------
# Pattern ID: 19
# ly5 -----------------XXX-----------------

# ly4 -----------------XXX-----------------

# ly3 -----------------XXX-----------------

# ly2 -----------------XXX-----------------

# ly1 -----------------XXX-----------------

# ly0 -----------------XXX-----------------



# Pattern ID: 18
# ly5 ------------------XXXX---------------

# ly4 ------------------XXX----------------

# ly3 ------------------XX-----------------

# ly2 -----------------XX------------------

# ly1 ----------------XXX------------------

# ly0 ---------------XXXX------------------



# Pattern ID: 17
# ly5 ---------------XXXX------------------

# ly4 ----------------XXX------------------

# ly3 -----------------XX------------------

# ly2 ------------------XX-----------------

# ly1 ------------------XXX----------------

# ly0 ------------------XXXX---------------



# Pattern ID: 16
# ly5 -------------------XXX---------------

# ly4 ------------------XXX----------------

# ly3 ------------------XX-----------------

# ly2 -----------------XX------------------

# ly1 ----------------XXX------------------

# ly0 ---------------XXX-------------------



# Pattern ID: 15
# ly5 ---------------XXX-------------------

# ly4 ----------------XXX------------------

# ly3 -----------------XX------------------

# ly2 ------------------XX-----------------

# ly1 ------------------XXX----------------

# ly0 -------------------XXX---------------



# Pattern ID: 14
# ly5 --------------------XXXX-------------

# ly4 -------------------XXX---------------

# ly3 ------------------XX-----------------

# ly2 -----------------XX------------------

# ly1 ---------------XXX-------------------

# ly0 -------------XXXX--------------------



# Pattern ID: 13
# ly5 -------------XXXX--------------------

# ly4 ---------------XXX-------------------

# ly3 -----------------XX------------------

# ly2 ------------------XX-----------------

# ly1 -------------------XXX---------------

# ly0 --------------------XXXX-------------



# Pattern ID: 12
# ly5 ---------------------XXXX------------

# ly4 --------------------XXX--------------

# ly3 ------------------XXX----------------

# ly2 ----------------XXX------------------

# ly1 --------------XXX--------------------

# ly0 ------------XXXX---------------------



# Pattern ID: 11
# ly5 ------------XXXX---------------------

# ly4 --------------XXX--------------------

# ly3 ----------------XXX------------------

# ly2 ------------------XXX----------------

# ly1 --------------------XXX--------------

# ly0 ---------------------XXXX------------



# Pattern ID: 10
# ly5 -----------------------XXXX----------

# ly4 ---------------------XXX-------------

# ly3 -------------------XX----------------

# ly2 ----------------XX-------------------

# ly1 -------------XXX---------------------

# ly0 ----------XXXX-----------------------



# Pattern ID: 9
# ly5 ----------XXXX-----------------------

# ly4 -------------XXX---------------------

# ly3 ----------------XX-------------------

# ly2 -------------------XX----------------

# ly1 ---------------------XXX-------------

# ly0 -----------------------XXXX----------



# Pattern ID: 8
# ly5 ------------------------XXXXX--------

# ly4 ----------------------XXX------------

# ly3 -------------------XX----------------

# ly2 ----------------XX-------------------

# ly1 ------------XXX----------------------

# ly0 --------XXXXX------------------------



# Pattern ID: 7
# ly5 --------XXXXX------------------------

# ly4 ------------XXX----------------------

# ly3 ----------------XX-------------------

# ly2 -------------------XX----------------

# ly1 ----------------------XXX------------

# ly0 ------------------------XXXXX--------



# Pattern ID: 6
# ly5 --------------------------XXXXX------

# ly4 -----------------------XXXX----------

# ly3 -------------------XXX---------------

# ly2 ---------------XXX-------------------

# ly1 ----------XXXX-----------------------

# ly0 ------XXXXX--------------------------



# Pattern ID: 5
# ly5 ------XXXXX--------------------------

# ly4 ----------XXXX-----------------------

# ly3 ---------------XXX-------------------

# ly2 -------------------XXX---------------

# ly1 -----------------------XXXX----------

# ly0 --------------------------XXXXX------



# Pattern ID: 4
# ly5 ----------------------------XXXXX----

# ly4 ------------------------XXXX---------

# ly3 --------------------XX---------------

# ly2 ---------------XX--------------------

# ly1 ---------XXXX------------------------

# ly0 ----XXXXX----------------------------



# Pattern ID: 3
# ly5 ----XXXXX----------------------------

# ly4 ---------XXXX------------------------

# ly3 ---------------XX--------------------

# ly2 --------------------XX---------------

# ly1 ------------------------XXXX---------

# ly0 ----------------------------XXXXX----



# Pattern ID: 2
# ly5 -------------------------------XXXXXX

# ly4 --------------------------XXXX-------

# ly3 --------------------XXX--------------

# ly2 --------------XXX--------------------

# ly1 -------XXXX--------------------------

# ly0 XXXXXX-------------------------------



# Pattern ID: 1
# ly5 XXXXXX-------------------------------

# ly4 -------XXXX--------------------------

# ly3 --------------XXX--------------------

# ly2 --------------------XXX--------------

# ly1 --------------------------XXXX-------

# ly0 -------------------------------XXXXXX
