#Subfunctions helpful for pat_unit testbench
import numpy as np
import math



class hi_lo_t:
    def __init__(self,hi,lo):
        self.hi=hi
        self.lo=lo

class patdef_t:
    def __init__(self, id, ly0, ly1, ly2, ly3, ly4, ly5):
        self.id=id
        self.ly0=ly0
        self.ly1=ly1
        self.ly2=ly2
        self.ly3=ly3
        self.ly4=ly4
        self.ly5=ly5

def mirror_patdef(pat,id):
    ly0_h=pat.ly0.lo*(-1)
    ly0_l=pat.ly0.hi*(-1)
    ly1_h=pat.ly1.lo*(-1)
    ly1_l=pat.ly1.hi*(-1)
    ly2_h=pat.ly2.lo*(-1)
    ly2_l=pat.ly2.hi*(-1)
    ly3_h=pat.ly3.lo*(-1)
    ly3_l=pat.ly3.hi*(-1)
    ly4_h=pat.ly4.lo*(-1)
    ly4_l=pat.ly4.hi*(-1)
    ly5_h=pat.ly5.lo*(-1)
    ly5_l=pat.ly5.hi*(-1)
    ly0=hi_lo_t(ly0_h,ly0_l)
    ly1=hi_lo_t(ly1_h,ly1_l)
    ly2=hi_lo_t(ly2_h,ly2_l)
    ly3=hi_lo_t(ly3_h,ly3_l)
    ly4=hi_lo_t(ly4_h,ly4_l)
    ly5=hi_lo_t(ly5_h,ly5_l)
    result=patdef_t(id,ly0,ly1,ly2,ly3,ly4,ly5)
    return result

def count_ones(ones_vec):
        n_ones=0
        for i in range(len(ones_vec)):
            if ones_vec[i]==1:
                n_ones=n_ones+1
        return n_ones;

def get_ly_mask(ly_pat,MAX_SPAN=37):
        m_ly0=np.zeros(MAX_SPAN)
        m_ly1=np.zeros(MAX_SPAN)
        m_ly2=np.zeros(MAX_SPAN)
        m_ly3=np.zeros(MAX_SPAN)
        m_ly4=np.zeros(MAX_SPAN)
        m_ly5=np.zeros(MAX_SPAN)
        center=round(MAX_SPAN/2)
        a_lo=ly_pat.ly0.lo+center
        a_hi=ly_pat.ly0.hi+center+1
        b_lo=ly_pat.ly1.lo+center
        b_hi=ly_pat.ly1.hi+center+1
        c_lo=ly_pat.ly2.lo+center
        c_hi=ly_pat.ly2.hi+center+1
        d_lo=ly_pat.ly3.lo+center
        d_hi=ly_pat.ly3.hi+center+1
        e_lo=ly_pat.ly4.lo+center
        e_hi=ly_pat.ly4.hi+center+1
        f_lo=ly_pat.ly5.lo+center
        f_hi=ly_pat.ly5.hi+center+1
        for a in range(a_lo,a_hi):
            m_ly0[a]=1
        for b in range(b_lo,b_hi):
            m_ly1[b]=1
        for c in range(c_lo,c_hi):
            m_ly2[c]=1
        for d in range(d_lo,d_hi):
            m_ly3[d]=1
        for e in range(e_lo,e_hi):
            m_ly4[e]=1
        for f in range(f_lo,f_hi):
            m_ly5[f]=1
        m_vec=[m_ly0,m_ly1,m_ly2,m_ly3,m_ly4,m_ly5]
        return m_vec







def get_lc_id(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN=37):
        len_patlist=len(patlist)
        corr_pat_id=np.zeros(len_patlist)
        pats_m=[]
        for w in range(len_patlist):
            pats_m.append(get_ly_mask(patlist[w]))
        ly0_a=np.zeros(MAX_SPAN)
        ly1_a=np.zeros(MAX_SPAN)
        ly2_a=np.zeros(MAX_SPAN)
        ly3_a=np.zeros(MAX_SPAN)
        ly4_a=np.zeros(MAX_SPAN)
        ly5_a=np.zeros(MAX_SPAN)
        lc_vec_x=np.zeros(len_patlist)
        lc_id_vec=[]
        for v in range(len_patlist):
            for h in range(MAX_SPAN):
                ly0_a[h]=pats_m[v][0][h]*ly0_x[h]
                ly1_a[h]=pats_m[v][1][h]*ly1_x[h]
                ly2_a[h]=pats_m[v][2][h]*ly2_x[h]
                ly3_a[h]=pats_m[v][3][h]*ly3_x[h]
                ly4_a[h]=pats_m[v][4][h]*ly4_x[h]
                ly5_a[h]=pats_m[v][5][h]*ly5_x[h]
            ly0_ones=count_ones(ly0_a)
            ly1_ones=count_ones(ly1_a)
            ly2_ones=count_ones(ly2_a)
            ly3_ones=count_ones(ly3_a)
            ly4_ones=count_ones(ly4_a)
            ly5_ones=count_ones(ly5_a)
            if (ly0_ones>=1):
                ly0_h=1
            else:
                ly0_h=0
            if (ly1_ones>=1):
                ly1_h=1
            else:
                ly1_h=0
            if (ly2_ones>=1):
                ly2_h=1
            else:
                ly2_h=0
            if (ly3_ones>=1):
                ly3_h=1
            else:
                ly3_h=0
            if (ly4_ones>=1):
                ly4_h=1
            else:
                ly4_h=0
            if (ly5_ones>=1):
                ly5_h=1
            else:
                ly5_h=0
            lc_vec_x[v]=ly0_h+ly1_h+ly2_h+ly3_h+ly4_h+ly5_h

        for i in range(len(patlist)):
                    corr_pat_id[i]=patlist[i].id
        for p in range(len_patlist):
                    lc_id_vec.append([lc_vec_x[p],corr_pat_id[p]])

        return lc_id_vec
