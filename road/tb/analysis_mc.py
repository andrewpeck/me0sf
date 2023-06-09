#!/usr/bin/env python3
import argparse
import glob
import math
import os
import random
import sys
from array import array

import boost_histogram as bh
import matplotlib.pyplot as plt
import numpy as np
import ROOT
import uproot

import event_display as disp
from chamber_beh import process_chamber
from read_ntuple import *
from subfunc import *


def analysis(root_dat, hits, bx, bx_list, cross_part, verbose, pu, num_or):
    # Output text file
    file_out = open("output_log_%s_bx%s_crosspart_%s_or%d.txt"%(hits, bx, cross_part, num_or), "w")

    # Nr. of segments per chamber per event
    num_seg_per_chamber = ROOT.TH1D("num_seg_per_chamber","Fraction of Events vs Number of Segments per Chamber",13,-0.5,12.5)
    num_seg_per_chamber_offline = ROOT.TH1D("num_seg_per_chamber_offline","Fraction of Events vs Number of Segments per Chamber",13,-0.5,12.5)

    # defining histograms for offline vs online
    offline_effi_passed = ROOT.TH1F("offline_effi_pass", "offline_effi_pass",14, -7., 7.)
    offline_effi_total = ROOT.TH1F("offline_effi_total", "offline_effi_total",14, -7., 7.) 
    offline_effi_mres = ROOT.TH1F("offline_effi_Bend_Ang_Res", "offline_effi_Bend_Ang_Res", 20, -0.6, 0.6)
    offline_effi_sres = ROOT.TH1F("offline_effi_Strip_Res", "offline_effi_Strip_Res", 20, -0.9, 0.9)

    # defining histograms for simtrack vs online
    bins = [0.0,1.0,2.0,3.0,4.0,5.0,10.0,15.0,20.0,25.0,30.0,35.0,40.0,45.0,50.0]
    st_effi_passed_pt = ROOT.TH1F("st_effi_pass_pt", "st_effi_pass_pt",14, array('d',bins))
    st_effi_total_pt = ROOT.TH1F("st_effi_total_pt", "st_effi_total_pt",14, array('d',bins)) 
    st_effi_passed_eta = ROOT.TH1F("st_effi_pass_eta", "st_effi_pass_eta",8,0.5,8.5)
    st_effi_total_eta = ROOT.TH1F("st_effi_total_eta", "st_effi_total_eta",8,0.5,8.5) 
    st_effi_passed_bending = ROOT.TH1F("st_effi_pass_bending", "st_effi_pass_bending",14, -7., 7.)
    st_effi_total_bending = ROOT.TH1F("st_effi_total_bending", "st_effi_total_bending",14, -7., 7.) 
    st_effi_mres = ROOT.TH1F("st_effi_Bend_Ang_Res", "st_effi_Bend_Ang_Res", 20, -0.6, 0.6)
    st_effi_sres = ROOT.TH1F("st_effi_Strip_Res", "st_effi_Strip_Res", 20, -0.9, 0.9)
    st_purity_passed_eta = ROOT.TH1F("st_purity_pass_eta", "st_purity_pass_eta",8,0.5,8.5)
    st_purity_total_eta = ROOT.TH1F("st_purity_total_eta", "st_purity_total_eta",8,0.5,8.5) 
    st_purity_passed_bending = ROOT.TH1F("st_purity_passed_bending", "st_purity_passed_bending",14, -7., 7.)
    st_purity_total_bending = ROOT.TH1F("st_purity_total_bending", "st_purity_total_bending",14, -7., 7.) 

    n_offline_effi_total = 0
    n_offline_effi_passed = 0
    n_offline_purity_total = 0
    n_offline_purity_passed = 0
    n_st_effi_total = 0
    n_st_effi_passed = 0
    n_st_purity_total = 0
    n_st_purity_passed = 0
    
    n_total_events = len(root_dat)
    prev_frac_done = 0

    for (ievent, event) in enumerate(root_dat):
        frac_done = (ievent+1)/n_total_events
        if (frac_done - prev_frac_done) >= 0.05:
            print ("%.2f"%(frac_done*100) + "% Events Done")
            prev_frac_done = frac_done
        if ievent!=1:
            continue
        if verbose:
            file_out.write("Event number = %d\n"%ievent)

        # read simhit info
        simhit_region = event["me0_sim_hit_region_i"]
        simhit_chamber = event["me0_sim_hit_chamber_i"] - 1
        simhit_eta_partition = event["me0_sim_hit_eta_partition_i"] - 1
        simhit_layer = event["me0_sim_hit_layer_i"] - 1
        simhit_sbit = np.floor(event["me0_sim_hit_strip_i"] / num_or)
        simhit_particle = event["me0_sim_hit_particle_i"]

        # read simtrack info
        track_type = event["me0_sim_track_type_i"]
        track_sim_pt = event["me0_sim_track_pt_i"]
        track_hit_index = event["me0_sim_track_hit_index_i"]
        n_track = len(track_type)
        track_substrip = []
        track_pt = []
        track_bending_angle = []
        track_chamber_nr = []
        track_eta_partition = []
        track_nhits = []
        track_nlayers = []
        me0_tracks = []

        # read digihit info
        digihit_region = event["me0_digi_hit_region_i"]
        digihit_chamber = event["me0_digi_hit_chamber_i"] - 1
        digihit_eta_partition = event["me0_digi_hit_eta_partition_i"] - 1
        digihit_layer = event["me0_digi_hit_layer_i"] - 1
        digihit_sbit = np.floor(event["me0_digi_hit_strip_i"] / num_or)
        digihit_bx = event["me0_digi_hit_bx_i"]

        # read rechit info
        rechit_region = event["me0_rec_hit_region_i"]
        rechit_chamber = event["me0_rec_hit_chamber_i"] - 1
        rechit_eta_partition = event["me0_rec_hit_eta_partition_i"] - 1
        rechit_layer = event["me0_rec_hit_layer_i"] - 1
        rechit_sbit = np.floor(event["me0_rec_hit_strip_i"] / num_or)
        rechit_bx = event["me0_rec_hit_bx_i"]

        # read offline segment info
        seg_region = event["me0_seg_region_i"]
        seg_chamber = event["me0_seg_chamber_i"] - 1
        seg_rechit_index = event["me0_seg_rec_hit_index_i"]
        seg_substrip = []
        seg_bending_angle = []
        n_offline_seg = len(seg_region)
        seg_chamber_nr = []
        seg_eta_partition = []
        seg_nrechits = []
        seg_nlayers = []

        # check if the track is from ME0 and is a muon and if >= 4 hits in track, record all valid tracks into me0_tracks
        for i in range(0, n_track):
            if len(track_hit_index[i]) >= 4:
                if track_type[i] == 13 or track_type[i] == -13:
                    muon_hits = 0
                    for index in track_hit_index[i]:
                        if simhit_particle[index] == 13 or simhit_particle[index] == -13:
                            muon_hits += 1
                    if len(track_hit_index[i]) == muon_hits:
                        me0_tracks.append(i)
        n_me0_track = len(me0_tracks)

        # Find the bending angle for sim tracks that are valid
        for i in me0_tracks:
            # using the first hit's region and chamber as the track's region and chamber
            if simhit_region[track_hit_index[i][0]] == 1:
                track_chamber_nr.append(18 + simhit_chamber[track_hit_index[i][0]])
            else:
                track_chamber_nr.append(simhit_chamber[track_hit_index[i][0]])

            top_layer_sbit = 0
            top_layer = 0
            bot_layer_sbit = 0
            bot_layer = 9999
            eta_partition_list = []
            nlayers_hit = [0,0,0,0,0,0]
            for index in track_hit_index[i]:
                sbit = simhit_sbit[index]
                layer = simhit_layer[index]
                eta_partition_list.append(simhit_eta_partition[index])
                if layer > top_layer:
                    top_layer = layer
                    top_layer_sbit = sbit
                if layer < bot_layer:
                    bot_layer = layer
                    bot_layer_sbit = sbit
                nlayers_hit[layer] += 1
            delta_sbit = top_layer_sbit - bot_layer_sbit
            delta_layer = top_layer - bot_layer
            bending_angle = delta_sbit/delta_layer
            substrip = (top_layer_sbit + bot_layer_sbit)/2.0
            track_bending_angle.append(bending_angle)
            track_pt.append(track_sim_pt[i])
            track_substrip.append(substrip)
            eta_partition_list_sorted = eta_partition_list
            eta_partition_list_sorted.sort(reverse=True)
            track_eta_partition.append(max(eta_partition_list_sorted,key=eta_partition_list_sorted.count))
            track_nhits.append(len(track_hit_index[i]))
            nlayers = 0
            for l in nlayers_hit:
                if l > 0:
                    nlayers += 1
            track_nlayers.append(nlayers)
        
        # Find the bending angle for rechit
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
            nlayers_hit = [0,0,0,0,0,0]
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
                nlayers_hit[layer] += 1
            delta_sbit = top_layer_sbit - bot_layer_sbit
            delta_layer = top_layer - bot_layer
            bending_angle = delta_sbit/delta_layer
            substrip = (top_layer_sbit + bot_layer_sbit)/2.0
            seg_bending_angle.append(bending_angle)
            seg_substrip.append(substrip)
            eta_partition_list_sorted = eta_partition_list
            eta_partition_list_sorted.sort(reverse=True)
            seg_eta_partition.append(max(eta_partition_list_sorted,key=eta_partition_list_sorted.count))
            seg_nrechits.append(len(seg_rechit_index[i]))
            nlayers = 0
            for l in nlayers_hit:
                if l > 0:
                    nlayers += 1
            seg_nlayers.append(nlayers)

        # initialize the dat_list that will be used as input of emulator
        # 36 * 8 * 2 * [6, 2]
        # could be if we use the virtual layers:
        # 36 * 15 * 2 * [6, 2]

        # virtual partitions included
        #datlist = np.array([[[[0 for i in range(6)], [(0, 0)]] for j in range(15)] for k in range(36)], dtype = object)
        datlist = np.array([[[[0 for i in range(6)], [(0, 0)]] for j in range(8)] for k in range(36)], dtype = object)

        # mapping from part_idx to real array index we want to insert is different
        # id  virtual real virtual
        # 0 ->          0     1
        # 1 ->   1      2     3
        # 2 ->   3      4     5
        # 3 ->   5      6     7
        # 4 ->   7      8     9
        # 5 ->   9      10    11
        # 6 ->   11     12    13
        # 7 ->   13     14

        # loop every hit inside an event
        if hits == "rec":
            for hit in range(len(rechit_region)):
                if rechit_region[hit] == 1:
                    chamb_idx = 18 + rechit_chamber[hit]
                else:
                    chamb_idx = rechit_chamber[hit]
                part_idx = rechit_eta_partition[hit]
                layer_idx = rechit_layer[hit]
                sbit_idx = int(rechit_sbit[hit])
                if rechit_bx[hit] not in bx_list:
                    continue

                # insert the hit
                datlist[chamb_idx, part_idx, 0][layer_idx] = (datlist[chamb_idx, part_idx, 0][layer_idx]) | (1 << sbit_idx)

                #datlist[chamb_idx, part_idx*2, 0][layer_idx] = (datlist[chamb_idx, part_idx*2, 0][layer_idx]) | (1 << sbit_idx)
                #if cross_part == "full":
                #    if part_idx != 7:
                #        datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx]) | (1 << sbit_idx)
                #    if part_idx != 0:
                #        datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx]) | (1 << sbit_idx)
                #elif cross_part == "partial":
                #    if part_idx != 7 and layer_idx >= 2:
                #        datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx]) | (1 << sbit_idx)
                #    if part_idx != 0 and layer_idx <= 3:
                #        datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx]) | (1 << sbit_idx)                

        elif hits == "digi":
            for hit in range(len(digihit_region)):
                if digihit_region[hit] == 1:
                    chamb_idx = 18 + digihit_chamber[hit]
                else:
                    chamb_idx = digihit_chamber[hit]
                part_idx = digihit_eta_partition[hit]
                layer_idx = digihit_layer[hit]
                sbit_idx = int(digihit_sbit[hit])
                if digihit_bx[hit] not in bx_list:
                    continue
                
                # insert the hit
                datlist[chamb_idx, part_idx, 0][layer_idx] = (datlist[chamb_idx, part_idx, 0][layer_idx]) | (1 << sbit_idx)

                #datlist[chamb_idx, part_idx*2, 0][layer_idx] = (datlist[chamb_idx, part_idx*2, 0][layer_idx]) | (1 << sbit_idx)
                #if cross_part == "full":
                #    if part_idx != 7:
                #        datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx]) | (1 << sbit_idx)
                #    if part_idx != 0:
                #        datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx]) | (1 << sbit_idx)
                #elif cross_part == "partial":
                #    if part_idx != 7 and layer_idx >= 2:
                #        datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)+1, 0][layer_idx]) | (1 << sbit_idx)
                #    if part_idx != 0 and layer_idx <= 3:
                #        datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx] = (datlist[chamb_idx, (part_idx*2)-1, 0][layer_idx]) | (1 << sbit_idx)    
        
        # Find segments per chamber
        online_segment_chamber = {}
        for (chamber_nr, dat_w_segs) in enumerate(datlist):
            
            online_segment_chamber[chamber_nr] = []
            #print ("  Chamber %d"%chamber_nr)
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
            #print (data)

            config = Config()
            config.num_outputs = 10
            config.cross_part_seg_width = 4
            config.ghost_width = 10
            num_or_to_span = {2:37, 4:19, 8:11, 16:7}
            #num_or = 4
            config.max_span = num_or_to_span[num_or]
            config.num_or = num_or
            seglist = process_chamber(data, config)
            seglist_final = []
            #print (seglist)
            for seg in seglist:
                if seg.id == 0:
                    continue
                seg.fit(config.max_span)
                if seg.partition % 2 != 0:
                    seg.partition = (seg.partition // 2) + 1
                else:
                    seg.partition = (seg.partition // 2)
                #print (seg)
                seglist_final.append(seg)
                if verbose:
                    file_out.write("  Online Segment in Chamber (0-17 for region -1, 18-35 for region 1) %d:\n "%chamber_nr)
                    file_out.write("    Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, ID = %d, Hit count = %d, Layer count = %d, Quality = %d\n"%(seg.partition, seg.substrip+seg.strip, seg.bend_ang, seg.id, seg.hc, seg.lc, seg.quality))
                    file_out.write("\n")
            online_segment_chamber[chamber_nr] = seglist_final

            for i in range(0, n_offline_seg):
                if seg_chamber_nr[i] != chamber_nr:
                    continue
                if verbose:
                    file_out.write("  Offline Segment in Chamber (0-17 for region -1, 18-35 for region 1) %d:\n "%chamber_nr)
                    file_out.write("     Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d\n"%(seg_eta_partition[i], seg_substrip[i], seg_bending_angle[i], seg_nrechits[i], seg_nlayers[i]))
                    file_out.write("\n")

            #for i in range(0, n_me0_track):
            #    if track_chamber_nr[i] != chamber_nr:
            #        continue
            #    if verbose:
            #       file_out.write("  Sim Track in Chamber (0-17 for region -1, 18-35 for region 1) %d\n: "%chamber_nr)
            #       file_out.write("     Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d, pT = %.4f\n"%(track_eta_partition[i], track_substrip[i], track_bending_angle[i], track_nhits[i], track_nlayers[i], track_pt[i]))
            #       file_out.write("\n")

        for chamber_nr in online_segment_chamber:
            num_seg_per_chamber.Fill(len(online_segment_chamber[chamber_nr]))

        for r in [-1,1]:
            for c in range(0,18):
                n_seg_chamber = 0
                for i in range(0, n_offline_seg):
                    if r==seg_region[i] and c==seg_chamber[i]:
                        n_seg_chamber += 1
                num_seg_per_chamber_offline.Fill(n_seg_chamber)

        #print ("  Offline - Online Segment Matching: ")
        unmatched_offline_index = []
        # Checking efficiency w.r.t offline segments
        for i in range(0, n_offline_seg):
            offline_chamber = seg_chamber_nr[i]
            offline_eta_partition = seg_eta_partition[i]
            offline_bending_angle = seg_bending_angle[i]
            offline_substrip = seg_substrip[i]
            offline_nrechits = seg_nrechits[i]
            offline_nlayers = seg_nlayers[i]
            offline_effi_total.Fill(offline_bending_angle)
            n_offline_effi_total += 1

            seg_match = 0
            seg_matched_index = []
            if (len(online_segment_chamber[offline_chamber]) == 0):

                unmatched_offline_index.append(i)
                continue

            for (j,seg) in enumerate(online_segment_chamber[offline_chamber]):
                if j in seg_matched_index:
                    continue
                online_eta_partition = seg.partition
                online_substrip = seg.substrip+seg.strip
                online_bending_angle = seg.bend_ang
                online_id = seg.id
                online_hc = seg.hc
                online_lc = seg.lc
                online_quality = seg.quality
                if abs(online_eta_partition - offline_eta_partition)<=1:
                #if online_eta_partition == offline_eta_partition:
                    #if online_bending_angle == 0:
                    #    bending_angle_err = abs(offline_bending_angle)
                    #else:
                    #    bending_angle_err = abs((offline_bending_angle - online_bending_angle)/online_bending_angle)
                    if abs(online_substrip - offline_substrip) <= 5: # match criteria for strip
                        #if bending_angle_err < 0.4 or abs(online_bending_angle - offline_bending_angle) <= 0.6: # match criteria for bending angle
                        offline_effi_passed.Fill(offline_bending_angle)
                        n_offline_effi_passed += 1
                        offline_effi_mres.Fill(offline_bending_angle - online_bending_angle)
                        offline_effi_sres.Fill(offline_substrip - online_substrip)
                        seg_match = 1
                        seg_matched_index.append(j)
                        #if verbose:
                            #file_out.write("    Offline segment: Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d\n"%(offline_chamber, offline_eta_partition, offline_substrip, offline_bending_angle, offline_nrechits, offline_nlayers))
                            #file_out.write("    Online segment: Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, ID = %d, Hit count = %d, Layer count = %d, Quality = %d\n"%(st_chamber, online_eta_partition, online_substrip, online_bending_angle, online_id, online_hc, online_lc, online_quality))
                            #file_out.write("\n")
                        break
            if seg_match == 0:
                unmatched_offline_index.append(i)
            
        #if verbose:
            #file_out.write("  Offline segments not matched to online segments:\n")
            #for i in unmatched_offline_index:
            #    file_out.write("    Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d\n"%(seg_chamber_nr[i], seg_eta_partition[i], seg_substrip[i], seg_bending_angle[i], seg_nrechits[i], seg_nlayers[i]))
            #file_out.write("\n\n")

        if verbose:
            file_out.write("  SimTrack - Online Segment Matching: \n")
        unmatched_st_index = []
        # Checking efficiency w.r.t sim tracks
        for i in range(0, n_me0_track):
            st_chamber = track_chamber_nr[i]
            st_eta_partition = track_eta_partition[i]
            st_bending_angle = track_bending_angle[i]
            st_pt = track_pt[i]
            st_substrip = track_substrip[i]
            st_nrechits = track_nhits[i]
            st_nlayers = track_nlayers[i]
            st_effi_total_bending.Fill(st_bending_angle)
            st_effi_total_pt.Fill(st_pt)
            st_effi_total_eta.Fill(st_eta_partition+1)
            n_st_effi_total += 1

            track_match = 0
            track_matched_index = []
            if (len(online_segment_chamber[st_chamber]) == 0):
                unmatched_st_index.append(i)
                continue

            for (j,seg) in enumerate(online_segment_chamber[st_chamber]):
                if j in track_matched_index:
                    continue
                online_eta_partition = seg.partition
                online_substrip = seg.substrip+seg.strip
                online_bending_angle = seg.bend_ang
                online_id = seg.id
                online_hc = seg.hc
                online_lc = seg.lc
                online_quality = seg.quality
                if abs(online_eta_partition - st_eta_partition)<=1:
                #if online_eta_partition == st_eta_partition:
                    #if online_bending_angle == 0:
                    #    bending_angle_err = abs(st_bending_angle)
                    #else:
                    #    bending_angle_err = abs((st_bending_angle - online_bending_angle)/online_bending_angle)
                    if abs(online_substrip - st_substrip) <= 5: # match criteria for strip
                        #if bending_angle_err < 0.4 or abs(online_bending_angle - st_bending_angle) <= 0.6: # match criteria for bending angle
                        st_effi_passed_bending.Fill(st_bending_angle)
                        st_effi_passed_pt.Fill(st_pt)
                        st_effi_passed_eta.Fill(st_eta_partition+1)
                        n_st_effi_passed += 1
                        st_effi_mres.Fill(st_bending_angle - online_bending_angle)
                        st_effi_sres.Fill(st_substrip - online_substrip)
                        track_match = 1
                        track_matched_index.append(j)
                        if verbose:
                            file_out.write("    Sim Track: Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d, pT = %.4f\n"%(st_chamber, st_eta_partition, st_substrip, st_bending_angle, st_nrechits, st_nlayers, st_pt))
                            file_out.write("    Online segment: Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, ID = %d, Hit count = %d, Layer count = %d, Quality = %d\n"%(st_chamber, online_eta_partition, online_substrip, online_bending_angle, online_id, online_hc, online_lc, online_quality))
                            file_out.write("\n")
                        break
            if track_match == 0:
                unmatched_st_index.append(i)
            
        if verbose:
            file_out.write("  Sim Tracks not matched to online segments:\n")
            for i in unmatched_st_index:
                file_out.write("    Chamber = %d: , Eta Partition = %d, Center Strip = %.4f, Bending angle = %.4f, Hit count = %d, Layer_count = %d, pT = %.4f\n"%(track_chamber_nr[i], track_eta_partition[i], track_substrip[i], track_bending_angle[i], track_nhits[i], track_nlayers[i], track_pt[i]))
            file_out.write("\n\n")

        # Checking Purity w.r.t sim tracks
        for chamber in online_segment_chamber: 
            for seg in online_segment_chamber[chamber]:
                online_eta_partition = seg.partition
                online_substrip = seg.substrip+seg.strip
                online_bending_angle = seg.bend_ang
                st_purity_total_eta.Fill(online_eta_partition+1)
                st_purity_total_bending.Fill(online_bending_angle)
                n_st_purity_total += 1
                n_offline_purity_total += 1

                for i in range(0, n_offline_seg):
                    offline_chamber = seg_chamber_nr[i]
                    offline_eta_partition = seg_eta_partition[i]
                    offline_bending_angle = seg_bending_angle[i]
                    offline_substrip = seg_substrip[i]
                    if (chamber == offline_chamber) and abs(online_eta_partition - offline_eta_partition)<=1:
                    #if (chamber == offline_chamber) and (online_eta_partition == offline_eta_partition):
                        #if online_bending_angle == 0:
                        #    bending_angle_err = abs(offline_bending_angle)
                        #else:
                        #    bending_angle_err = abs((offline_bending_angle - online_bending_angle)/online_bending_angle)
                        if abs(online_substrip - offline_substrip) <= 5: # match criteria for strip
                            #if bending_angle_err < 0.4 or abs(online_bending_angle - offline_bending_angle) <= 0.6: # match criteria for bending angle
                            n_offline_purity_passed += 1
                            break

                for i in range(0, n_me0_track):
                    st_chamber = track_chamber_nr[i]
                    st_eta_partition = track_eta_partition[i]
                    st_bending_angle = track_bending_angle[i]
                    st_substrip = track_substrip[i]
                    if (chamber == st_chamber) and abs(online_eta_partition - st_eta_partition)<=1:
                    #if (chamber == st_chamber) and (online_eta_partition == st_eta_partition):
                        #if online_bending_angle == 0:
                        #    bending_angle_err = abs(st_bending_angle)
                        #else:
                        #    bending_angle_err = abs((st_bending_angle - online_bending_angle)/online_bending_angle)
                        if abs(online_substrip - st_substrip) <= 5: # match criteria for strip
                            #if bending_angle_err < 0.4 or abs(online_bending_angle - st_bending_angle) <= 0.6: # match criteria for bending angle
                            st_purity_passed_eta.Fill(online_eta_partition+1)
                            st_purity_passed_bending.Fill(online_bending_angle)
                            n_st_purity_passed += 1
                            break

    print ("")

    # Overall efficiency
    offline_efficiency =  n_offline_effi_passed/n_offline_effi_total
    print ("Overall efficiency w.r.t offline segments = %.4f\n"%(offline_efficiency))
    file_out.write("Overall efficiency w.r.t offline segments = %.4f\n\n"%(offline_efficiency))
    offline_purity =  n_offline_purity_passed/n_offline_purity_total
    print ("Overall purity w.r.t offline segments = %.4f\n"%(offline_purity))
    file_out.write("Overall purity w.r.t offline segments = %.4f\n\n"%(offline_purity))
    if n_st_effi_total != 0:
        st_efficiency =  n_st_effi_passed/n_st_effi_total
        print ("Overall efficiency w.r.t sim tracks = %.4f\n"%(st_efficiency))
        file_out.write("Overall efficiency w.r.t sim tracks = %.4f\n\n"%(st_efficiency))
        st_purity =  n_st_purity_passed/n_st_purity_total
        print ("Overall purity w.r.t sim tracks = %.4f\n"%(st_purity))
        file_out.write("Overall purity w.r.t sim tracks = %.4f\n\n"%(st_purity))

    plot_file = ROOT.TFile("output_plots_%s_bx%s_crosspart_%s_or%d.root"%(hits, bx, cross_part, num_or), "recreate")
    plot_file.cd()

    # Plotting
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAlign(31)
    latex.SetTextSize(0.035)
    Lint = (5 * 10 ** 34) * (float(pu)/140.0)
    if (pu == 0):
        plot_text1 = "Muon Gun (0 PU)"
    else:
        plot_text1 = "L = %.1e"%(Lint) + " Hz/cm^{2} (" + pu + " PU)"
    plot_text2 = "CMS Simulation #sqrt{s}=14 TeV"

    c1 = ROOT.TCanvas('', '', 800, 650)
    c1.SetGrid()
    c1.DrawFrame(-8, 0, 8, 1.1, ";Bending Angle (sbits/layer);Efficiency")
    offline_eff = ROOT.TEfficiency(offline_effi_passed, offline_effi_total)
    offline_eff.Draw("same")
    offline_eff.SetMarkerStyle(8)
    offline_eff.SetMarkerSize(1)
    offline_eff.SetMarkerColor(1)
    offline_eff.SetLineWidth(1)
    offline_eff.SetLineColor(1)
    ROOT.gPad.Update()
    offline_eff.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_eff.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c1.Print("offline_eff_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_eff.Write()

    c2 = ROOT.TCanvas('', '', 800, 650)
    c2.SetGrid()
    c2.DrawFrame(-1, 0, 1, 1.5, ";Bending Angle (sbits/layer);")
    #offline_effi_mres.SetTitle("Bending Angle Resolution w.r.t Offline Segments")
    offline_effi_mres.SetTitle("")
    offline_effi_mres.Fit("gaus")
    offline_effi_mres.Draw("same")
    ROOT.gPad.Update()
    st2 = offline_effi_mres.FindObject("stats")
    st2.SetY1NDC(0.6); 
    st2.SetY2NDC(0.8); 
    offline_effi_mres.SetMarkerStyle(8)
    offline_effi_mres.SetMarkerSize(1)
    offline_effi_mres.SetMarkerColor(1)
    offline_effi_mres.SetLineWidth(1)
    offline_effi_mres.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c2.Print("offline_effi_mres_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_effi_mres.Write()

    c3 = ROOT.TCanvas('', '', 800, 650)
    c3.SetGrid()
    c3.DrawFrame(-1, 0, 1, 1.5, ";Sbit;")
    #offline_effi_sres.SetTitle("Sbit Resolution w.r.t Offline Segments")
    offline_effi_sres.SetTitle("")
    offline_effi_sres.GetXaxis().SetTitle("Sbit")
    offline_effi_sres.Fit("gaus")
    offline_effi_sres.Draw("same")
    ROOT.gPad.Update()
    st3 = offline_effi_sres.FindObject("stats")
    st3.SetY1NDC(0.6); 
    st3.SetY2NDC(0.8); 
    offline_effi_sres.SetMarkerStyle(8)
    offline_effi_sres.SetMarkerSize(1)
    offline_effi_sres.SetMarkerColor(1)
    offline_effi_sres.SetLineWidth(1)
    offline_effi_sres.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c3.Print("offline_effi_sres_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_effi_sres.Write()

    if n_st_effi_total != 0:
        c4 = ROOT.TCanvas('', '', 800, 650)
        c4.SetGrid()
        c4.DrawFrame(-8, 0, 8, 1.1, ";Bending Angle (sbits/layer);Efficiency")
        st_eff_bending = ROOT.TEfficiency(st_effi_passed_bending, st_effi_total_bending)
        st_eff_bending.Draw("same")
        st_eff_bending.SetMarkerStyle(8)
        st_eff_bending.SetMarkerSize(1)
        st_eff_bending.SetMarkerColor(1)
        st_eff_bending.SetLineWidth(1)
        st_eff_bending.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_bending.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_bending.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c4.Print("st_eff_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_bending.Write()

        c5 = ROOT.TCanvas('', '', 800, 650)
        c5.SetGrid()
        c5.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt = ROOT.TEfficiency(st_effi_passed_pt, st_effi_total_pt)
        st_eff_pt.Draw("same")
        st_eff_pt.SetMarkerStyle(8)
        st_eff_pt.SetMarkerSize(1)
        st_eff_pt.SetMarkerColor(1)
        st_eff_pt.SetLineWidth(1)
        st_eff_pt.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c5.Print("st_eff_pt_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt.Write()

        c6 = ROOT.TCanvas('', '', 800, 650)
        c6.SetGrid()
        c6.DrawFrame(0, 0, 9, 1.1, ";#eta Partition;Efficiency")
        st_eff_eta = ROOT.TEfficiency(st_effi_passed_eta, st_effi_total_eta)
        st_eff_eta.Draw("same")
        st_eff_eta.SetMarkerStyle(8)
        st_eff_eta.SetMarkerSize(1)
        st_eff_eta.SetMarkerColor(1)
        st_eff_eta.SetLineWidth(1)
        st_eff_eta.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_eta.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_eta.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c6.Print("st_eff_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_eta.Write()

        c7 = ROOT.TCanvas('', '', 800, 650)
        c7.SetGrid()
        c7.DrawFrame(-1, 0, 1, 1.5, ";Bending Angle (sbits/layer);")
        #st_effi_mres.SetTitle("Bending Angle Resolution w.r.t Sim Tracks")
        st_effi_mres.SetTitle("")
        st_effi_mres.Fit("gaus")
        st_effi_mres.Draw("same")
        ROOT.gPad.Update()
        st7 = st_effi_mres.FindObject("stats")
        st7.SetY1NDC(0.6); 
        st7.SetY2NDC(0.8); 
        st_effi_mres.SetMarkerStyle(8)
        st_effi_mres.SetMarkerSize(1)
        st_effi_mres.SetMarkerColor(1)
        st_effi_mres.SetLineWidth(1)
        st_effi_mres.SetLineColor(1)
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c7.Print("st_effi_mres_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_effi_mres.Write()

        c8 = ROOT.TCanvas('', '', 800, 650)
        c8.SetGrid()
        c8.DrawFrame(-1, 0, 1, 1.5, ";Sbit;")
        #st_effi_sres.SetTitle("Sbit Resolution w.r.t Sim Tracks")
        st_effi_sres.SetTitle("")
        st_effi_sres.Fit("gaus")
        st_effi_sres.Draw("same")
        ROOT.gPad.Update()
        st8 = st_effi_sres.FindObject("stats")
        st8.SetY1NDC(0.6); 
        st8.SetY2NDC(0.8); 
        st_effi_sres.SetMarkerStyle(8)
        st_effi_sres.SetMarkerSize(1)
        st_effi_sres.SetMarkerColor(1)
        st_effi_sres.SetLineWidth(1)
        st_effi_sres.SetLineColor(1)
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c8.Print("st_effi_sres_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_effi_sres.Write()

        c9 = ROOT.TCanvas('', '', 800, 650)
        c9.SetGrid()
        c9.DrawFrame(0, 0, 9, 1.1, ";#eta Partition;Purity")
        st_purity_eta = ROOT.TEfficiency(st_purity_passed_eta, st_purity_total_eta)
        st_purity_eta.Draw("same")
        st_purity_eta.SetMarkerStyle(8)
        st_purity_eta.SetMarkerSize(1)
        st_purity_eta.SetMarkerColor(1)
        st_purity_eta.SetLineWidth(1)
        st_purity_eta.SetLineColor(1)
        ROOT.gPad.Update()
        st_purity_eta.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_purity_eta.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c9.Print("st_purity_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_purity_eta.Write()

        c10 = ROOT.TCanvas('', '', 800, 650)
        c10.SetGrid()
        c10.DrawFrame(-8, 0, 8, 1.1, ";Bending Angle (sbits/layer);Purity")
        st_purity_bending = ROOT.TEfficiency(st_purity_passed_bending, st_purity_total_bending)
        st_purity_bending.Draw("same")
        st_purity_bending.SetMarkerStyle(8)
        st_purity_bending.SetMarkerSize(1)
        st_purity_bending.SetMarkerColor(1)
        st_purity_bending.SetLineWidth(1)
        st_purity_bending.SetLineColor(1)
        ROOT.gPad.Update()
        st_purity_bending.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_purity_bending.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c10.Print("st_purity_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_purity_bending.Write()

    c11 = ROOT.TCanvas('', '', 800, 650)
    c11.SetGrid()
    c11.DrawFrame(-0.5, -0.05, 12.5, 1.05, ";Number of Segments per Chamber/Event;Fraction of Events")
    num_seg_per_chamber.Scale(1.0/num_seg_per_chamber.Integral())
    num_seg_per_chamber.Draw("same HE")
    num_seg_per_chamber.SetMarkerStyle(8)
    num_seg_per_chamber.SetMarkerSize(1)
    num_seg_per_chamber.SetMarkerColor(1)
    num_seg_per_chamber.SetLineWidth(1)
    num_seg_per_chamber.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c11.Print("num_seg_per_chamber_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_seg_per_chamber.Write()

    c11a = ROOT.TCanvas('', '', 800, 650)
    c11a.SetLogy()
    c11a.SetGrid()
    c11a.DrawFrame(-0.5, 0.000001, 12.5, 1.5, ";Number of Segments per Chamber/Event;Fraction of Events")
    num_seg_per_chamber.Scale(1.0/num_seg_per_chamber.Integral())
    num_seg_per_chamber.Draw("same HE")
    num_seg_per_chamber.SetMarkerStyle(8)
    num_seg_per_chamber.SetMarkerSize(1)
    num_seg_per_chamber.SetMarkerColor(1)
    num_seg_per_chamber.SetLineWidth(1)
    num_seg_per_chamber.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c11a.Print("num_seg_per_chamber_%s_bx%s_crosspart_%s_or%d_log.pdf"%(hits, bx, cross_part, num_or))
    num_seg_per_chamber.Write()

    c12 = ROOT.TCanvas('', '', 800, 650)
    c12.SetGrid()
    c12.DrawFrame(-0.5, -0.05, 12.5, 1.05, ";Number of Offline Segments per Chamber/Event;Fraction of Events")
    num_seg_per_chamber_offline.Scale(1.0/num_seg_per_chamber_offline.Integral())
    num_seg_per_chamber_offline.Draw("same HE")
    num_seg_per_chamber_offline.SetMarkerStyle(8)
    num_seg_per_chamber_offline.SetMarkerSize(1)
    num_seg_per_chamber_offline.SetMarkerColor(1)
    num_seg_per_chamber_offline.SetLineWidth(1)
    num_seg_per_chamber_offline.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c12.Print("num_seg_per_chamber_offline_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_seg_per_chamber_offline.Write()

    c12a = ROOT.TCanvas('', '', 800, 650)
    c12a.SetLogy()
    c12a.SetGrid()
    c12a.DrawFrame(-0.5, 0.000001, 12.5, 1.5, ";Number of Offline Segments per Chamber/Event;Fraction of Events")
    num_seg_per_chamber_offline.Scale(1.0/num_seg_per_chamber_offline.Integral())
    num_seg_per_chamber_offline.Draw("same HE")
    num_seg_per_chamber_offline.SetMarkerStyle(8)
    num_seg_per_chamber_offline.SetMarkerSize(1)
    num_seg_per_chamber_offline.SetMarkerColor(1)
    num_seg_per_chamber_offline.SetLineWidth(1)
    num_seg_per_chamber_offline.SetLineColor(1)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c12a.Print("num_seg_per_chamber_offline_%s_bx%s_crosspart_%s_or%d_log.pdf"%(hits, bx, cross_part, num_or))
    num_seg_per_chamber_offline.Write()

    file_out.close()
    plot_file.Close()

def test_analysis_mc():
    root_dat = read_ntuple(os.path.abspath(os.path.dirname(__file__)) + "/test_data/mc_ntuple.root")
    hits = "digi"
    bx = "all"
    bx_list = list(range(-9999,10000))
    #cross_part_list = ["none", "partial", "full"]
    cross_part_list = ["partial"]
    num_or_list = [2, 4]
    for cross_part in cross_part_list:
        for num_or in num_or_list:
            print ("Comparing cross partition: %s"%cross_part)
            analysis(root_dat, hits, bx, bx_list, cross_part, True, 0, num_or)
        
            # checking
            file_out_name = "output_log_%s_bx%s_crosspart_%s_or%d.txt"%(hits, bx, cross_part, num_or)
            file_compare_name = "test_data/%s"%file_out_name
            os.system("diff %s %s > out.txt"%(file_out_name, file_compare_name))
            file_out = open("out.txt")
            assert len(file_out.readlines()) == 0
            file_out.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Emulator for Online ME0 Segment Finder')
    parser.add_argument("-f", "--file_path", action="store", dest="file_path", help="file_path = the .root file path to be read")
    parser.add_argument("-t", "--hits", action="store", dest="hits", default="digi", help="hits = digi or rec")
    parser.add_argument("-b", "--bx", action="store", dest="bx", default="all", help="bx = all or nr. of BXs to consider")
    #parser.add_argument("-c", "--cross_part", action="store", dest="cross_part", help="cross_part = 'full' or 'partial' or 'none'")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="whether to print all track segment matching info")
    parser.add_argument("-p", "--pu", action="store", dest="pu", help="PU")
    parser.add_argument("-o", "--num_or", action="store", dest="num_or", default = "2", help="number of strips that are OR-ed together")
    args = parser.parse_args()

    # read in the data
    root_dat = read_ntuple(args.file_path)

    if int(args.num_or) < 2:
        print ("At least 2 strips OR-ed together")
        sys.exit()

    #if args.cross_part not in ["full", "partial", "none"]:
    #    print ("Incorrect argument for cross partition")
    #    sys.exit()

    if args.hits not in ["digi", "rec"]:
        print ("Incorrect argument for hits option")
        sys.exit()
    bx_list = []
    if args.bx == "all":
        bx_list = list(range(-9999,10000))
    else:
        n_bx = int(args.bx)
        if n_bx <= 0:
            print ("N_BX has to be larger than 0 or all")
            sys.exit()
        if n_bx%2 == 0:
            print ("N_BX has to be odd")
            sys.exit()
        if n_bx == 1:
            bx_list.append(0)
        else:
            bx_list = list(range(-(math.floor(n_bx/2)), math.floor(n_bx/2)+1))

    #analysis(root_dat, args.hits, args.bx, bx_list, args.cross_part, args.verbose, args.pu, int(args.num_or))
    analysis(root_dat, args.hits, args.bx, bx_list, "partial", args.verbose, args.pu, int(args.num_or))
