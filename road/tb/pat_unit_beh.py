#Python implementation of the pat_unit.vhd behavior
from subfunc import*

def process_pat(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN=37):
    """takes in a list of patterns and sample data for each layer to generate a layer count and id for the pattern that best matches the data"""

    def get_ly_mask(ly_pat, MAX_SPAN=37):
        """takes in a given layer pattern and returns a list of integer bit masks for each layer"""
        assert type(ly_pat)==patdef_t,"ly_pat input must be defined in the patdef_t class"
        assert type(ly_pat.ly0)==hi_lo_t,"each layer of ly_pat must be of the class hi_lo_t"
        assert type(ly_pat.id)==int,"ly_pat's id must be an integer"
        assert type(MAX_SPAN)==int,"MAX_SPAN input must be an integer"
        m_vec = []
        center = round(MAX_SPAN / 2)
        # generate indices of the high bits for each layer based on the provided hi and lo values from the pattern definition
        a_lo = ly_pat.ly0.lo + center
        a_hi = ly_pat.ly0.hi + center
        b_lo = ly_pat.ly1.lo + center
        b_hi = ly_pat.ly1.hi + center
        c_lo = ly_pat.ly2.lo + center
        c_hi = ly_pat.ly2.hi + center
        d_lo = ly_pat.ly3.lo + center
        d_hi = ly_pat.ly3.hi + center
        e_lo = ly_pat.ly4.lo + center
        e_hi = ly_pat.ly4.hi + center
        f_lo = ly_pat.ly5.lo + center
        f_hi = ly_pat.ly5.hi + center
        m_vals = [
            [a_lo, a_hi],
            [b_lo, b_hi],
            [c_lo, c_hi],
            [d_lo, d_hi],
            [e_lo, e_hi],
            [f_lo, f_hi],
        ]
        # use the high and low indices to determine where the high bits must go for each layer
        for i in range(len(m_vals)):
            holder = 0
            # keep setting high bits from the low index to the high index; leave all else as low bits
            for index in range(m_vals[i][0], m_vals[i][1] + 1):
                val = 1 << index
                holder = holder | val
            m_vec.append(holder)
        return m_vec

    def get_lc_id(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN):
        """takes in patlist and the data from each layer to determine the layer count that would be obtained from the data overlaying any mask; returns id and layer count for each mask"""
        corr_pat_id=[]
        pats_m=[]
        for w in range(len(patlist)):
            pats_m.append(get_ly_mask(patlist[w],MAX_SPAN))
        lc_vec_x=[]
        lc_id_vec=[]
        #and the layer data with the respective mask layer to determine how many hits are in each layer
        for v in range(len(patlist)):
            ly0_hold=ly0_x&pats_m[v][0]
            ly1_hold=ly1_x&pats_m[v][1]
            ly2_hold=ly2_x&pats_m[v][2]
            ly3_hold=ly3_x&pats_m[v][3]
            ly4_hold=ly4_x&pats_m[v][4]
            ly5_hold=ly5_x&pats_m[v][5]
        #count the hits in each layer
            ly0_ones=count_ones(ly0_hold)
            ly1_ones=count_ones(ly1_hold)
            ly2_ones=count_ones(ly2_hold)
            ly3_ones=count_ones(ly3_hold)
            ly4_ones=count_ones(ly4_hold)
            ly5_ones=count_ones(ly5_hold)
        #assign a layer count of 1 for at least 1 hit in a mask for a given layer
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
        #total up layer counts for each layer to get pattern's total layer count
            lc_vec_x.append(ly0_h+ly1_h+ly2_h+ly3_h+ly4_h+ly5_h)
        for i in range(len(patlist)):
                    corr_pat_id.append(patlist[i].id)
        #match the correct pattern id to its total layer count
        for p in range(len(patlist)):
                    lc_id_vec.append([lc_vec_x[p],corr_pat_id[p]])

        return lc_id_vec


    lc_id_vec=get_lc_id(patlist,ly0_x,ly1_x,ly2_x,ly3_x,ly4_x,ly5_x,MAX_SPAN)

    def priority_encoder(lc_id_vec):
        """receives a list of layer counts and ids from each mask and the layer data to determine which pattern is the best fit, based on the highest layer count; returns the id of this best pattern; if the layer count is the same for two patterns, the pattern higher id will be returned"""
        max_lc=0
        max_id=0
        s_list=[]
        #find the highest layer count and save its index r
        for r in range(len(lc_id_vec)):
            if (lc_id_vec[r][0]>=max_lc):
                max_lc=lc_id_vec[r][0]
        #check if any other patterns have the same layer count as the max layer count and save these values to slist
        for s in range(len(lc_id_vec)):
            if (lc_id_vec[s][0]==max_lc):
                s_list.append(lc_id_vec[s])
        #check which id value in slist has the highest pattern id; save the index as the best pattern index
        for t in range(len(s_list)):
            if (s_list[t][1]>max_id):
                max_id=s_list[t][1]
                b_pat_index=t
        #choose the highest layer count and pattern id from slist
        [b_lc,b_id]=s_list[b_pat_index]
        b_lc=int(b_lc)
        b_id=int(b_id)
        return b_lc,b_id

    [ly_c,pat_id]=priority_encoder(lc_id_vec)
    if (ly_c==0):
        pat_id=0
    return pat_id,ly_c
