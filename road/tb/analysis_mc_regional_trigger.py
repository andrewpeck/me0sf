#!/usr/bin/env python3
import argparse
import glob
import math
import os
import random
import sys
from array import array

#import boost_histogram as bh
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
    file_out = open("output_regional_trigger_log_%s_bx%s_crosspart_%s_or%d.txt"%(hits, bx, cross_part, num_or), "w")

    # Histograms for segment frac vs eta
    me0_h_seg_rate_frac_eta_partition = ROOT.TH1F("me0_h_seg_rate_frac_eta_partition","Average Segment Fraction per VFAT (in ME0) vs #eta Partition;#eta Partition;Seg Rate Fraction",8,0.5,8.5)
    me0_h_seg_rate_frac_vfat_window = ROOT.TH1F("me0_h_seg_rate_frac_vfat_window","Average Segment Fraction per VFAT (in ME0) vs #eta Partition;#eta Partition;Seg Rate Fraction",8,0.5,8.5)
    me0_h_seg_rate_frac_vfat_digihits = ROOT.TH1F("me0_h_seg_rate_frac_vfat_digihits","Average Fraction per VFAT (in ME0) vs #eta Partition;#eta Partition;Seg Rate Fraction",8,0.5,8.5)

    # Counters for Regional Trigger
    n_events_base = 0
    n_total_event_chamber = [0 for i in range(0,36)]
    n_total_event_chamber_eta = [[0 for j in range(0,8)] for i in range(0,36)]
    n_total_event_chamber_eta_layer_vfat_window= [[[ [0 for l in range(0,3)]for k in range(0,6)] for j in range(0,8)] for i in range(0,36)]
    n_total_event_chamber_eta_layer_vfat_digihits = [[[ [0 for l in range(0,3)]for k in range(0,6)] for j in range(0,8)] for i in range(0,36)]

    n_total_events = len(root_dat)
    prev_frac_done = 0

    for (ievent, event) in enumerate(root_dat):
        frac_done = (ievent+1)/n_total_events
        if (frac_done - prev_frac_done) >= 0.05:
            print ("%.2f"%(frac_done*100) + "% Events Done")
            prev_frac_done = frac_done
        #if ievent >= 3:
        #    continue
        if verbose:
            file_out.write("Event number = %d\n"%ievent)

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
        # 0 .          0     1
        # 1 .   1      2     3
        # 2 .   3      4     5
        # 3 .   5      6     7
        # 4 .   7      8     9
        # 5 .   9      10    11
        # 6 .   11     12    13
        # 7 .   13     14

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
                #if seg.partition % 2 != 0:
                #    seg.partition = (seg.partition // 2) + 1
                #else:
                #    seg.partition = (seg.partition // 2)
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

        
        # Regional triggering fractions for online segments
        n_segments_chamber = [0 for i in range(0,36)]
        n_segments_chamber_eta = [[0 for j in range(0,8)] for i in range(0,36)]
        n_segments_chamber_eta_layer_vfat_window = [[[ [0 for l in range(0,3)]for k in range(0,6)] for j in range(0,8)] for i in range(0,36)]
        n_segments_chamber_eta_layer_vfat_digihits = [[[ [0 for l in range(0,3)]for k in range(0,6)] for j in range(0,8)] for i in range(0,36)]

        # Looping over all segments in ME0 in an event
        for chamber in online_segment_chamber: 
            for seg in online_segment_chamber[chamber]:
                online_eta_partition = seg.partition
                online_strip = seg.strip
                online_substrip = seg.substrip+seg.strip
                online_lc = seg.lc

                num_or_to_span = {2:37, 4:19, 8:11, 16:7}
                max_span = num_or_to_span[num_or]
                strip_window_ll = online_strip - max_span//2
                strip_window_ul = online_strip + max_span//2
                if strip_window_ll < 1:
                    strip_window_ll = 1
                if strip_window_ul > 191:
                    strip_window_ul = 191

                seg_eta = []
                seg_eta_layer_vfat_window = [[[] for j in range(0,6)] for i in range(0,8)]
                seg_eta_layer_vfat_digihits = [[[] for j in range(0,6)] for i in range(0,8)]

                if online_lc < 4:
                    continue

                if seg.partition % 2 != 0:
                    seg_eta.append(int(seg.partition // 2))
                    seg_eta.append(int(seg.partition // 2) + 1)
                    seg.partition = (seg.partition // 2) + 1
                else:
                    seg_eta.append(int(seg.partition // 2))
                    seg.partition = (seg.partition // 2)

                for e in seg_eta:
                    for l in range(0,6):
                        if strip_window_ll<=63:
                            seg_eta_layer_vfat_window[e][l].append(0)
                        elif strip_window_ll<=127:
                            seg_eta_layer_vfat_window[e][l].append(1)
                        elif strip_window_ll<=191:
                            seg_eta_layer_vfat_window[e][l].append(2)
                        if strip_window_ul >= 128:
                            if 2 not in seg_eta_layer_vfat_window[e][l]:
                                seg_eta_layer_vfat_window[e][l].append(2)
                        elif strip_window_ul >= 64:
                            if 1 not in seg_eta_layer_vfat_window[e][l]:
                                seg_eta_layer_vfat_window[e][l].append(1)
                        elif strip_window_ul >= 0:
                            if 0 not in seg_eta_layer_vfat_window[e][l]:
                                seg_eta_layer_vfat_window[e][l].append(0)

                for (d, hit_region) in enumerate(digihit_region):
                    if hit_region == 1:
                        hit_chamber = 18 + digihit_chamber[d]
                    else:
                        hit_chamber = digihit_chamber[d]
                    hit_eta_parition = digihit_eta_partition[d]
                    hit_layer = digihit_layer[d]
                    hit_sbit = digihit_sbit[d]
                    hit_vfat = -9999
                    if hit_sbit >=0 and hit_sbit <=63:
                        hit_vfat = 0
                    elif hit_sbit >=64 and hit_sbit <=127:
                        hit_vfat = 1
                    elif hit_sbit >=128 and hit_sbit <=191:
                        hit_vfat = 2
                    if hit_chamber == chamber:
                        if hit_vfat not in seg_eta_layer_vfat_digihits[hit_eta_parition][hit_layer]:
                            seg_eta_layer_vfat_digihits[hit_eta_parition][hit_layer].append(hit_vfat)

                n_segments_chamber[chamber] += 1
                for e in seg_eta:
                    n_segments_chamber_eta[chamber][e] += 1
                for j in range(0,8):
                    for k in range(0,6):
                        for v in seg_eta_layer_vfat_window[j][k]:
                            n_segments_chamber_eta_layer_vfat_window[chamber][j][k][v] += 1
                        for v in seg_eta_layer_vfat_digihits[j][k]:
                            n_segments_chamber_eta_layer_vfat_digihits[chamber][j][k][v] += 1

        n_event_match = 0
        for i in range(0,36):
            if n_segments_chamber[i] >= 1:
                n_total_event_chamber[i] += 1
                n_event_match = 1
            for j in range(0,8):
                if n_segments_chamber_eta[i][j] >= 1:
                    n_total_event_chamber_eta[i][j] += 1
                for k in range(0,6):
                    for l in range(0,3):
                        if n_segments_chamber_eta_layer_vfat_window[i][j][k][l] >= 1:
                            n_total_event_chamber_eta_layer_vfat_window[i][j][k][l] += 1
                        if n_segments_chamber_eta_layer_vfat_digihits[i][j][k][l] >= 1:
                            n_total_event_chamber_eta_layer_vfat_digihits[i][j][k][l] += 1
        if n_event_match == 1:
            n_events_base += 1

    print ("")

    print("100\% completed\n")
    print("Number of events with at least one segment in at least 1 chamber (L1A events): %d\n"%n_events_base)
    print("Fraction of L1A events with at least 1 segment in: \n\n")
    file_out.write("Number of events with at least one segment in at least 1 chamber (L1A events): %d\n\n"%n_events_base)
    file_out.write("Fraction of L1A events with at least 1 segment in: \n\n")

    avg_frac = 0
    for i in range(0,36):
        frac = float(n_total_event_chamber[i])/float(n_events_base)
        avg_frac += frac
        print("  Chamber #%d: %.4f\n\n"%(i, frac))
        file_out.write("  Chamber #%d: %.4f\n"%(i, frac))

    avg_frac = avg_frac/36.0
    print ("")
    file_out.write("\n")
    print("Average fraction of L1A events with at least 1 segment per chamber: %.4f\n"%avg_frac)
    file_out.write("Average fraction of L1A events with at least 1 segment per chamber: %.4f\n\n"%avg_frac)

    effi_loss = 0
    effi_loss_per_chamber = 0
    effi_loss_per_eta_partition = [0 for i in range(0,8)]
    effi_loss_per_vfat_window = [0 for i in range(0,8)]
    effi_loss_per_vfat_digihits = [0 for i in range(0,8)]
    L1A_rate = 750.00*1000 # 750 kHz
    BX = 25.00 * pow(10,-9) # 25 ns
    BX_gap = (1.0/L1A_rate)/BX
    deadtime = 8.0 # 8 BX
    effi_loss = (deadtime/BX_gap)*100
    effi_loss_per_chamber = effi_loss*avg_frac
    
    for i in range(0,8):
        avg_frac_eta = 0
        avg_frac_vfat_window = 0
        avg_frac_vfat_digihits = 0

        for j in range(0,36):
            avg_frac_eta += (float(n_total_event_chamber_eta[j][i])/float(n_events_base))
            for k in range(0,6):
                for l in range(0,3):
                    avg_frac_vfat_window += ((float(n_total_event_chamber_eta_layer_vfat_window[j][i][k][l])/float(n_events_base)))
                    avg_frac_vfat_digihits += ((float(n_total_event_chamber_eta_layer_vfat_digihits[j][i][k][l])/float(n_events_base)))
        avg_frac_eta = avg_frac_eta/36.0
        avg_frac_vfat_window = avg_frac_vfat_window/(36.0 * 6.0 * 3.0)
        avg_frac_vfat_digihits = avg_frac_vfat_digihits/(36.0 * 6.0 * 3.0)

        seg_eta = i+1
        me0_h_seg_rate_frac_eta_partition.SetBinContent(seg_eta, avg_frac_eta)
        me0_h_seg_rate_frac_vfat_window.SetBinContent(seg_eta, avg_frac_vfat_window)
        me0_h_seg_rate_frac_vfat_digihits.SetBinContent(seg_eta, avg_frac_vfat_digihits)
        me0_h_seg_rate_frac_eta_partition.SetBinError(seg_eta, 0)
        me0_h_seg_rate_frac_vfat_window.SetBinError(seg_eta, 0)
        me0_h_seg_rate_frac_vfat_digihits.SetBinError(seg_eta, 0)

        effi_loss_per_eta_partition[i] = effi_loss*avg_frac_eta
        effi_loss_per_vfat_window[i] = effi_loss*avg_frac_vfat_window
        effi_loss_per_vfat_digihits[i] = effi_loss*avg_frac_vfat_digihits


    print("")
    print("Efficiency loss without any mitigation = %.4f %s"%(effi_loss,"%"))
    print("Efficiency loss with regional triggering per chamber = %.4f %s"%(effi_loss_per_chamber, "%"))
    print("Efficiency loss with regional triggering per eta partition: ")
    for i in range(0,8):
        print("  For eta partition %d = %.4f %s"%(i, effi_loss_per_eta_partition[i], "%"))
    print("")
    print("Efficiency loss with regional triggering per Pattern Window: ")
    for i in range(0,8):
        print("  For eta partition %d = %.4f %s"%(i, effi_loss_per_vfat_window[i], "%"))
    print("")
    print("Efficiency loss with regional triggering per Digi Hits in VFATs in Chambers with >= 1 Segment: ")
    for i in range(0,8):
        print("  For eta partition %d = %.4f %s"%(i, effi_loss_per_vfat_digihits[i], "%"))
    print("\n")

    file_out.write("\n")
    file_out.write("Efficiency loss without any mitigation = %.4f %s\n\n"%(effi_loss, "%"))
    file_out.write("Efficiency loss with regional triggering per chamber = %.4f %s\n\n"%(effi_loss_per_chamber, "%"))
    file_out.write("Efficiency loss with regional triggering per eta partition: \n")
    for i in range(0,8):
        file_out.write("  For eta partition %d = %.4f %s\n"%(i, effi_loss_per_eta_partition[i], "%"))
    file_out.write("\n")
    file_out.write("Efficiency loss with regional triggering per Pattern Window: \n")
    for i in range(0,8):
        file_out.write("  For eta partition %d = %.4f %s\n"%(i, effi_loss_per_vfat_window[i], "%"))
    file_out.write("\n")
    file_out.write("Efficiency loss with regional triggering per Digi Hits in VFATs in Chambers with >= 1 Segment: \n")
    for i in range(0,8):
        file_out.write("  For eta partition %d = %.4f %s\n"%(i, effi_loss_per_vfat_digihits[i], "%"))
    file_out.write("\n")

    plot_file = ROOT.TFile("output_regional_trigger_plots_%s_bx%s_crosspart_%s_or%d.root"%(hits, bx, cross_part, num_or), "recreate")
    plot_file.cd()
    me0_h_seg_rate_frac_eta_partition.Write()
    me0_h_seg_rate_frac_vfat_window.Write()
    me0_h_seg_rate_frac_vfat_digihits.Write()

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

    c1 = ROOT.TCanvas("c1","test",720,500)
    c1.SetGrid()
    c1.DrawFrame(0, 0, 9, 0.08, ";#eta Partition;Average Fraction per VFAT")
    me0_h_seg_rate_frac_eta_partition.Draw("same HIST E TEXT")
    me0_h_seg_rate_frac_eta_partition.SetStats(0)
    me0_h_seg_rate_frac_eta_partition.SetMarkerSize(1)
    me0_h_seg_rate_frac_eta_partition.SetMarkerColor(ROOT.kBlack)
    me0_h_seg_rate_frac_eta_partition.SetLineWidth(2)
    me0_h_seg_rate_frac_eta_partition.SetLineColor(ROOT.kBlack)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.37, 0.91,plot_text2)
    c1.Print("regional_trigger_l1a_fraction_vs_eta_per_eta_partition_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))

    c3 = ROOT.TCanvas("c3","test",720,500)
    c3.SetGrid()
    c3.DrawFrame(0, 0, 9, 0.04, ";#eta Partition;Average Fraction per VFAT")
    me0_h_seg_rate_frac_vfat_window.Draw("same HIST E TEXT")
    me0_h_seg_rate_frac_vfat_window.SetStats(0)
    me0_h_seg_rate_frac_vfat_window.SetMarkerSize(1)
    me0_h_seg_rate_frac_vfat_window.SetMarkerColor(ROOT.kBlack)
    me0_h_seg_rate_frac_vfat_window.SetLineWidth(2)
    me0_h_seg_rate_frac_vfat_window.SetLineColor(ROOT.kBlack)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.37, 0.91,plot_text2)
    c3.Print("regional_trigger_l1a_fraction_vs_eta_per_vfat_window_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))

    c5 = ROOT.TCanvas("c5","test",720,500)
    c5.SetGrid()
    c5.DrawFrame(0, 0, 9, 0.08, ";#eta Partition;Average Fraction per VFAT")
    me0_h_seg_rate_frac_vfat_digihits.Draw("same HIST E TEXT")
    me0_h_seg_rate_frac_vfat_digihits.SetStats(0)
    me0_h_seg_rate_frac_vfat_digihits.SetMarkerSize(1)
    me0_h_seg_rate_frac_vfat_digihits.SetMarkerColor(ROOT.kBlack)
    me0_h_seg_rate_frac_vfat_digihits.SetLineWidth(2)
    me0_h_seg_rate_frac_vfat_digihits.SetLineColor(ROOT.kBlack)
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.37, 0.91,plot_text2)
    c5.Print("regional_trigger_l1a_fraction_vs_eta_per_vfat_digihits_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))

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
    parser = argparse.ArgumentParser(description='Emulator for Online ME0 Segment Finder Regional Triggering')
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
