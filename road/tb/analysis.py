#!/usr/bin/env python3
from read_ntuple import *
import uproot
import ROOT
import matplotlib.pyplot as plt
import numpy as np
import event_display as disp
from subfunc import *
from chamber_beh import process_chamber
from datagen import datagen_with_segs
import random
import boost_histogram as bh
import sys


# read in the data
file_path = "/home/uclame0teststand/Documents/Segment_Finder/offline_results/MuonGun_MuonGE0Segments_1.root"
root_dat = read_ntuple(file_path)

# extract useful data and turn them into np array
region = root_dat["me0_rec_hit_region"].array(library="np")
chamber = root_dat["me0_rec_hit_chamber"].array(library="np")
eta_partition = root_dat["me0_rec_hit_eta_partition"].array(library="np") - 1
layer = root_dat["me0_rec_hit_layer"].array(library="np") - 1
sbit = np.floor((root_dat["me0_rec_hit_strip"].array(library="np")) / 2.0)

# loop every event 
for event in range(len(region)):

    # initialize the dat_list that will be used as input of emulator
    # 36 * 8 * 2 * [6, 2]
    dat_list = np.array([[[[0 for i in range(6)], [(0, 0)]] for j in range(8)] for k in range(36)], dtype = object)

    # loop every hit inside an event
    for hit in range(len(region[event])):
        if region[event, hit] == 1:
            chamb_idx = 17 + chamber[event, hit]
        else:
            chamb_idx = chamber[event, hit]
        part_idx = eta_partition[event, hit]
        layer_idx = layer[event, hit]
        sbit_idx = sbit[event, hit]
        # insert the hit
        dat_list[chamb_idx, part_idx, 0, layer_idx] = (dat_list[chamb_idx, part_idx, 0, layer_idx]) | (1 << sbit_idx)

        print(dat_list)
        break
    break
sys.exit()

# with uproot.open("MuonGE0Segments2.root:ge0/segments") as segments:
#     print(segments.keys())

#     events = segments.arrays(["strip", "ly", "chamber", "partition", "pt", "sim_hit_ind", "sim_chamb", "sim_ly", "sim_part"],

#                              aliases={"strip": "floor(me0_rec_hit_strip/2.0)",
#                                       "ly": "me0_rec_hit_layer-1",
#                                       "chamber": "me0_rec_hit_chamber",
#                                       "partition": "me0_rec_hit_eta_partition-1",
#                                       "pt": "me0_sim_track_pt",
#                                       "track_ind": "me0_sim_track_hit_index",
#                                       "sim_chamb": "me0_sim_hit_chamber",
#                                       "sim_ly": "me0_sim_hit_layer",
#                                       "sim_part": "me0_sim_hit_eta_partition-1",
#                                       "sim_strip": "floor(me0_sim_hit_strip/2.0)"
#                                       })
#     hpass= bh.Histogram(bh.axis.Regular(18, 0, 180))  
#     htotal = bh.Histogram(bh.axis.Regular(18, 0, 180)) 
#     for (ievent, event) in enumerate(events):
#         seglist = [] # store the segment strip, partition, chamber to compare with the tracks
#         for j in range(1, 19):
#             layers = [[0]*6 for n in range(8)]
#             for (ly, strip, partition, chamber) in zip(event["ly"], event["strip"], event["partition"], event["chamber"]): 
#                 if (chamber==j):
#                     layers[partition][int(ly)] |= 1 << int(strip)

#             seg_list = process_chamber(layers) 
#             for seg in seg_list:
#                 seg.fit()
#                 if seg.id !=0:
#                     seglist.append((seg.strip, seg.partition, j))

#             pats = [(PATLIST[len(PATLIST)-seg.id], seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
#             fits = [(seg.bend_ang, seg.substrip, seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
#             for (i, layer) in enumerate(layers):
#                 pat = [(p[0], p[1]) for p in pats if p[2] == i]
#                 fitlist = [(fit[0], fit[1], fit[2]) for fit in fits if fit[3] == i and fit[2] != None]
#                 counter=0
#                 for f in fitlist:
#                     found_m = f[0]
#                     found_strip =f[2] + f[1]
#                     given_m = llse_fit()
#                     given_strip = 
#                     counter +=1
#                     htotal.fill(given_m)
#                     strip_res.fill(given_strip-found_strip)
#                     m_res.fill(given_m - found_m)
#                     if found_m ==0:
#                         m_err = given_m
#                     else:
#                         m_err = abs((given_m - found_m)/given_m)
            
#                     if found_strip<= given_strip + .5 and found_strip>= given_strip - .5: 
#                         if m_err<.2 or (found_m - given_m <=0.3 and found_m - given_m >=-.3):
#                     # if f[3] != 6:
#                     #     print("layer count", f[3]) 
#                     #     print("given", given_m, given_strip, "found", found_m, found_strip, "pattern", [p[0].id for p in pat],f[3])
#                     #     print("percent error for m", m_err*100)
#                     #     print("centroids", [cent-19 for cent in f[4]])
#                     #     disp.event_display(hits=ly, fits=fitlist, pats=pat) 
#                     #     break
#                             hpass.fill(given_m)
#                             break 


datlist=[]
for i in range(1000):
    datlist.append([datagen_with_segs(1,0,bend_angs=[random.uniform(-7,7)], strips=[random.uniform(50, 150)]) for _ in range(8)])

passed = ROOT.TH1F("pass", "pass",14, -7., 7.)
total = ROOT.TH1F("total", "total",14, -7., 7.) 
mres = ROOT.TH1F("Bend_Ang_Res", "Bend_Ang_Res", 20, -0.6, 0.6)
sres = ROOT.TH1F("Strip_Res", "Strip_Res", 20, -0.9, 0.9)

for dat_w_segs in datlist:
    seg_m_b = [dat[1] for dat in dat_w_segs]
    data = [dat[0] for dat in dat_w_segs] 
    seglist = process_chamber(data, ghost_width=10, num_outputs=10)
    for seg in seglist:
        seg.fit()
    calc_seg_m_b = []
    pats = [(PATLIST[len(PATLIST)-seg.id], seg.strip, seg.partition) for seg in seglist if seg.id !=0] 
    fits = [(seg.bend_ang, seg.substrip, seg.strip, seg.partition, seg.centroid) for seg in seglist if seg.id !=0] 

    for (i, ly) in enumerate(data):
        pat = [(p[0], p[1]) for p in pats if p[2] == i]
        fitlist = [(fit[0], fit[1], fit[2], fit[4]) for fit in fits if fit[3] == i and fit[2] != None]
        counter=0
        for f in fitlist:
            found_m = f[0]
            found_strip =f[2] + f[1]
            given_m = seg_m_b[i][0][0]
            given_strip = seg_m_b[i][0][1]
            counter +=1
            total.Fill(given_m)
            sres.Fill(given_strip-found_strip)
            mres.Fill(given_m - found_m)
            if found_m ==0:
                m_err = given_m
            else:
                m_err = abs((given_m - found_m)/given_m)
            
            if found_strip<= given_strip + .75 and found_strip>= given_strip - .75: 
                if m_err<.4 or abs(found_m - given_m) <=0.6 :
                    passed.Fill(given_m)
                    break
            # elif counter==len(fitlist):
            #     print("given", given_m, given_strip, "found", found_m, found_strip, "pattern", [p[0].id for p in pat],"lc", f[3])
            #     print("percent error for m", m_err*100)
            #     print("centroids", [cent-19 for cent in f[4]])
            #     disp.event_display(hits=ly, fits=fitlist, pats=pat)
#Plotting done in ROOT
c1 = ROOT.TCanvas('', '', 1000, 700)
eff = ROOT.TEfficiency(passed, total)
eff.SetTitle("Efficiency; Bending Angle (strips/layer); #epsilon")
eff.Draw()
ROOT.gPad.Update()
eff.GetPaintedGraph().GetYaxis().SetRangeUser(.9, 1.05)
eff.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
eff.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
ROOT.gPad.Update()
c1.SaveAs("eff.pdf")

c2 =  ROOT.TCanvas('', '', 700, 700)
mres.SetTitle("Bending Angle Resolution")
mres.GetXaxis().SetTitle("Bending Angle (strips/layer)")
mres.Fit("gaus")
mres.Draw()
c2.SaveAs("mres.pdf")

c3=ROOT.TCanvas('', '', 700, 700)
sres.SetTitle("Strip Resolution")
sres.GetXaxis().SetTitle("Strip")
sres.Fit("gaus")
sres.Draw()
c3.SaveAs("sres.pdf")