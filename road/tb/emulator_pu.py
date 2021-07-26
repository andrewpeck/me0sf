#Python implementation of the pat_unit.vhd behavior
from printly_dat import printly_dat
from datadev import datadev
from subfunc import*

def process_pat(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN=37):

    def get_ly_mask(ly_pat,MAX_SPAN=37):
        m_vec=[]
        center=round(MAX_SPAN/2)
        a_lo=ly_pat.ly0.lo+center
        a_hi=ly_pat.ly0.hi+center
        b_lo=ly_pat.ly1.lo+center
        b_hi=ly_pat.ly1.hi+center
        c_lo=ly_pat.ly2.lo+center
        c_hi=ly_pat.ly2.hi+center
        d_lo=ly_pat.ly3.lo+center
        d_hi=ly_pat.ly3.hi+center
        e_lo=ly_pat.ly4.lo+center
        e_hi=ly_pat.ly4.hi+center
        f_lo=ly_pat.ly5.lo+center
        f_hi=ly_pat.ly5.hi+center
        m_vals=[[a_lo,a_hi],[b_lo,b_hi],[c_lo,c_hi],[d_lo,d_hi],[e_lo,e_hi],[f_lo,f_hi]]
        for i in range(len(m_vals)):
            index=m_vals[i][0]
            holder=0
            while (index!=m_vals[i][1]+1):
                val=1<<index
                holder=holder|val
                index+=1
            m_vec.append(holder)
        return m_vec

    def get_lc_id(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN=37):
        corr_pat_id=[]
        pats_m=[]
        for w in range(len(patlist)):
            pats_m.append(get_ly_mask(patlist[w]))
        lc_vec_x=[]
        lc_id_vec=[]
        for v in range(len(patlist)):
            ly0_hold=ly0_x&pats_m[v][0]
            ly1_hold=ly1_x&pats_m[v][1]
            ly2_hold=ly2_x&pats_m[v][2]
            ly3_hold=ly3_x&pats_m[v][3]
            ly4_hold=ly4_x&pats_m[v][4]
            ly5_hold=ly5_x&pats_m[v][5]
            ly0_ones=count_ones(ly0_hold)
            ly1_ones=count_ones(ly1_hold)
            ly2_ones=count_ones(ly2_hold)
            ly3_ones=count_ones(ly3_hold)
            ly4_ones=count_ones(ly4_hold)
            ly5_ones=count_ones(ly5_hold)
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
            lc_vec_x.append(ly0_h+ly1_h+ly2_h+ly3_h+ly4_h+ly5_h)
        for i in range(len(patlist)):
                    corr_pat_id.append(patlist[i].id)
        for p in range(len(patlist)):
                    lc_id_vec.append([lc_vec_x[p],corr_pat_id[p]])

        return lc_id_vec


    lc_id_vec=get_lc_id(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x)

    def priority_encoder(lc_id_vec):
        max_lc=0
        max_id=0
        s_list=[]
        for r in range(len(lc_id_vec)):
            if (lc_id_vec[r][0]>=max_lc):
                max_lc=lc_id_vec[r][0]
        for s in range(len(lc_id_vec)):
            if (lc_id_vec[s][0]==max_lc):
                s_list.append(lc_id_vec[s])
        for t in range(len(s_list)):
            if (s_list[t][1]>max_id):
                max_id=s_list[t][1]
                b_pat_index=t
        [b_lc,b_id]=s_list[b_pat_index]
        b_lc=int(b_lc)
        b_id=int(b_id)
        return b_lc,b_id

    [ly_c,pat_id]=priority_encoder(lc_id_vec)

    return pat_id,ly_c
