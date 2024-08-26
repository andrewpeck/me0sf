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
    file_out = open("plot_hits_%s_bx%s_crosspart_%s_or%d.txt"%(hits, bx, cross_part, num_or), "w")

    n_total_events = len(root_dat)
    prev_frac_done = 0

    for (ievent, event) in enumerate(root_dat):
        frac_done = (ievent+1)/n_total_events
        if (frac_done - prev_frac_done) >= 0.05:
            print ("%.2f"%(frac_done*100) + "% Events Done")
            prev_frac_done = frac_done
        #if ievent!=1:
        #    continue
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

        datlist = np.array([[[[0 for i in range(6)], [(0, 0)]] for j in range(8)] for k in range(36)], dtype = object)

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
        
        if verbose:
            file_out.write("\n")
        for (chamber_nr, dat_w_segs) in enumerate(datlist):
            
            #print ("  Chamber %d"%chamber_nr)
            if verbose:
                file_out.write("Chamber %d\n"%chamber_nr)
            data = [dat[0] for dat in dat_w_segs] 
            #print (data)
            for (eta_part, eta_part_data) in enumerate(data):
                if verbose:
                    file_out.write("  Eta Partition %d\n"%eta_part)
                plot_layer = []
                for (layer, layer_data) in enumerate(eta_part_data):
                    layer_str = ""
                    for sbit in range(0,192):
                        hit = (layer_data >> sbit) & 1
                        if hit == 1:
                            layer_str += "x"
                        else:
                            layer_str += "-"
                    plot_layer.append(layer_str)
                if verbose:
                    for layer in range(0,6):
                        plot_layer_str = plot_layer[5-layer]
                        file_out.write("    " + plot_layer_str + "\n")
                    file_out.write("\n")
        if verbose:
            file_out.write("\n\n")

    print ("")

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
    root_dat = read_ntuple(args.file_path, 0, 1000)

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
