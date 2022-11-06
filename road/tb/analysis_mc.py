#!/usr/bin/env python3
import uproot
import event_display as disp
from subfunc import *
from chamber_beh import process_chamber
import matplotlib.pyplot as plt
from datagen import datagen_with_segs
import numpy as np
import random
import boost_histogram as bh
from read_ntuple import *
import ROOT
import sys, os, glob

# read in the data
#file_path = "/home/uclame0teststand/Documents/Segment_Finder/offline_results/MuonGun_MuonGE0Segments_1.root"
file_path = "../../../test_ntuples/MuonGun_1k_eta_All_SegmentAnalyzer/MuonGE0Segments.root"
root_dat = read_ntuple(file_path)

# defining histograms
offline_effi_passed = ROOT.TH1F("offline_effi_pass", "offline_effi_pass",14, -7., 7.)
offline_effi_total = ROOT.TH1F("offline_effi_total", "offline_effi_total",14, -7., 7.) 
offline_effi_mres = ROOT.TH1F("offline_effi_Bend_Ang_Res", "offline_effi_Bend_Ang_Res", 20, -0.6, 0.6)
offline_effi_sres = ROOT.TH1F("offline_effi_Strip_Res", "offline_effi_Strip_Res", 20, -0.9, 0.9)
n_offline_effi_total = 0
n_offline_effi_passed = 0

n_total_events = len(root_dat)
prev_frac_done = 0

for (ievent, event) in enumerate(root_dat):
    frac_done = (ievent+1)/n_total_events
    if (frac_done - prev_frac_done) >= 0.05:
        print ("%.2f"%(frac_done*100) + "% Events Done")
        prev_frac_done = frac_done
    #print ("Event number = %d"%ievent)
   
    # read simhit info


    # read simtrack info


    # read rechit info
    rechit_region = event["me0_rec_hit_region"]
    rechit_chamber = event["me0_rec_hit_chamber"] - 1
    rechit_eta_partition = event["me0_rec_hit_eta_partition"] - 1
    rechit_layer = event["me0_rec_hit_layer"] - 1
    rechit_sbit = np.floor(event["me0_rec_hit_strip"] / 2.0)
    rechit_bx = event["me0_rec_hit_bx"]

    # read segment info
    seg_region = event["me0_seg_region"]
    seg_chamber = event["me0_seg_chamber"] - 1
    seg_rechit_index = event["me0_seg_rec_hit_index"]
    seg_substrip = []
    seg_bending_angle = []
    n_offline_seg = len(seg_region)
    seg_chamber_nr = []
    seg_eta_partition = []
    seg_nrechits = []
    
    # Find the bending angle
    for i in range(0, n_offline_seg):
        if seg_region[i] == 1:
            seg_chamber_nr.append(18 + seg_chamber[i])
        else:
            seg_chamber_nr.append(seg_chamber[i])

        top_layer_sbit = 0
        top_layer = 0
        bot_layer_sbit = 0
        bot_layer = 9999
        eta_partition_list = []
        for index in seg_rechit_index[i]:
            sbit = rechit_sbit[index]
            layer = rechit_layer[index]
            eta_partition_list.append(rechit_eta_partition[index])
            if layer > top_layer:
                top_layer = layer
                top_layer_sbit = sbit
            if layer < bot_layer:
                bot_layer = layer
                bot_layer_sbit = sbit
        delta_sbit = top_layer_sbit - bot_layer_sbit
        delta_layer = top_layer - bot_layer
        bending_angle = delta_sbit/delta_layer
        substrip = (top_layer_sbit + bot_layer_sbit)/2.0
        seg_bending_angle.append(bending_angle)
        seg_substrip.append(substrip)
        seg_eta_partition.append(max(eta_partition_list,key=eta_partition_list.count))
        seg_nrechits.append(len(seg_rechit_index[i]))

    # initialize the dat_list that will be used as input of emulator
    # 36 * 8 * 2 * [6, 2]
    datlist = np.array([[[[0 for i in range(6)], [(0, 0)]] for j in range(8)] for k in range(36)], dtype = object)
    
    # loop every hit inside an event
    for hit in range(len(rechit_region)):
        if rechit_region[hit] == 1:
            chamb_idx = 18 + rechit_chamber[hit]
        else:
            chamb_idx = rechit_chamber[hit]
        part_idx = rechit_eta_partition[hit]
        layer_idx = rechit_layer[hit]
        sbit_idx = int(rechit_sbit[hit])
    
        # insert the hit
        datlist[chamb_idx, part_idx, 0][layer_idx] = (datlist[chamb_idx, part_idx, 0][layer_idx]) | (1 << sbit_idx)

    # Find segments per chamber
    online_segment_chamber = {}
    for (chamber_nr, dat_w_segs) in enumerate(datlist):
        
        seg_m_b = [dat[1] for dat in dat_w_segs]
        data = [dat[0] for dat in dat_w_segs] 
        non_zero_data = 0
        for e in data:
            for d in e:
                if d != 0:
                    non_zero_data = 1
                    break
            if non_zero_data:
                break
        if not non_zero_data:
            continue

        seglist = process_chamber(data, ghost_width=10, num_outputs=10)
        seglist_final = []
        for seg in seglist:
            seg.fit()
            if seg.id != 0:
                seglist_final.append(seg)
            #    print ("  Online Segment in Chamber (0-17 for region -1, 18-35 for region 1) %d: "%chamber_nr)
            #    print ("    Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, ID = %d, Layer count = %d, Quality = %d"%(seg.partition, seg.substrip+seg.strip, seg.bend_ang, seg.id, seg.lc, seg.quality))
            #    print ("")
        online_segment_chamber[chamber_nr] = seglist_final

        #for i in range(0, n_offline_seg):
        #    if seg_chamber_nr[i] != chamber_nr:
        #        continue
        #    print ("  Offline Segment in Chamber (0-17 for region -1, 18-35 for region 1) %d: "%chamber_nr)
        #    print ("     Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d"%(seg_eta_partition[i], seg_substrip[i], seg_bending_angle[i], seg_nrechits[i]))
        #    print ("")

    # Checking efficiency w.r.t offline segments
    for i in range(0, n_offline_seg):
        offline_chamber = seg_chamber_nr[i]
        offline_eta_partition = seg_eta_partition[i]
        offline_bending_angle = seg_bending_angle[i]
        offline_substrip = seg_substrip[i]
        offline_effi_total.Fill(offline_bending_angle)
        n_offline_effi_total += 1

        if (len(online_segment_chamber[offline_chamber]) == 0):
            continue

        for seg in online_segment_chamber[offline_chamber]:
            online_eta_partition = seg.partition
            online_substrip = seg.substrip+seg.strip
            online_bending_angle = seg.bend_ang
            if online_eta_partition == offline_eta_partition:
                if abs(online_substrip - offline_substrip) <= 0.75: # match criteria
                    offline_effi_passed.Fill(offline_bending_angle)
                    n_offline_effi_passed += 1
                    offline_effi_mres.Fill(offline_bending_angle - online_bending_angle)
                    offline_effi_sres.Fill(offline_substrip - online_substrip)
                    break

print ("")

# Overall efficiency
offline_efficiency =  n_offline_effi_passed/n_offline_effi_total
print ("Overall efficiency w.r.t offline segments = %.4f\n"%(offline_efficiency))

#Plotting done in ROOT
c1 = ROOT.TCanvas('', '', 1000, 700)
c1.DrawFrame(-8, 0, 8, 1.1, "Efficiency w.r.t. Offline Segments; Bending Angle (strips/layer); #epsilon")
offline_eff = ROOT.TEfficiency(offline_effi_passed, offline_effi_total)
offline_eff.Draw("same")
ROOT.gPad.Update()
offline_eff.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
offline_eff.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
ROOT.gPad.Update()
c1.Print("offline_eff.pdf")

c2 =  ROOT.TCanvas('', '', 700, 700)
offline_effi_mres.SetTitle("Bending Angle Resolution w.r.t Offline Segments")
offline_effi_mres.GetXaxis().SetTitle("Bending Angle (strips/layer)")
offline_effi_mres.Fit("gaus")
offline_effi_mres.Draw("same")
c2.Print("offline_effi_mres.pdf")

c3=ROOT.TCanvas('', '', 700, 700)
offline_effi_mres.SetTitle("Strip Resolution w.r.t Offline Segments")
offline_effi_mres.GetXaxis().SetTitle("Strip")
offline_effi_mres.Fit("gaus")
offline_effi_mres.Draw("same")
c3.Print("offline_effi_sres.pdf")



