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

def analysis(root_data, hits, bx, bx_list, num_or):
#def analysis(root_signal, root_bkg, hits, bx, bx_list, num_or):
    
    n_total_events = len(root_data)
    print ("Number of signal+background events: %d, for training: %d"%(n_total_events, n_total_events/2))
    #n_total_signal_events = len(root_signal)
    #n_total_bkg_events = len(root_bkg)
    #print ("Number of signal (MuonGun) events for training: %d", n_total_signal_events)
    #print ("Number of background (NeutrinoGun + MinBias) events for training: %d", n_total_bkg_events)
    print ("")

    signal_data = {}
    #background_data = {}
    n_max_sbits = int(384/num_or)
    for chamber in range(0,36):
        signal_data[chamber] = {}
        #background_data[chamber] = {}
        for eta_partition in range(0,15): # including pseudo eta partitions
            signal_data[chamber][eta_partition] = {}
            #background_data[chamber][eta_partition] = {}
            for layer in range(0,6):
                signal_data[chamber][eta_partition][layer] = 0
                #background_data[chamber][eta_partition][layer] = 0

    signal_track_data = {}
    for chamber in range(0,36):
        signal_track_data[chamber] = {}
        for eta_partition in range(0,15): # including pseudo eta partitions
            signal_track_data[chamber][eta_partition] = {}
            signal_track_data[chamber][eta_partition]["track_pt"] = []
            signal_track_data[chamber][eta_partition]["track_strip_center"] = []

    # Reading Signal Data
    for (ievent, event) in enumerate(root_data):
    #for (ievent, event) in enumerate(root_signal):

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
        me0_tracks = []

        # read digihit info
        digihit_region = event["me0_digi_hit_region_i"]
        digihit_chamber = event["me0_digi_hit_chamber_i"] - 1
        digihit_eta_partition = event["me0_digi_hit_eta_partition_i"] - 1
        digihit_layer = event["me0_digi_hit_layer_i"] - 1
        digihit_sbit = np.floor(event["me0_digi_hit_strip_i"] / num_or)
        digihit_bx = event["me0_digi_hit_bx_i"]

        # organize digi hit data
        signal_data[digihit_chamber][digihit_eta_partition*2][digihit_layer] |= (1 << int(digihit_sbit))
        for pseudo_eta_partition in range(1, 15, 2):
            if digihit_eta_partition == (pseudo_eta_partition-1)/2:
                if digihit_layer in [2, 3, 4, 5]:
                    signal_data[digihit_chamber][pseudo_eta_partition][digihit_layer] |= (1 << int(digihit_sbit))
            elif digihit_eta_partition == (pseudo_eta_partition+1)/2:
                if digihit_layer in [0, 1, 2, 3]:
                    signal_data[digihit_chamber][pseudo_eta_partition][digihit_layer] |= (1 << int(digihit_sbit))

        # check if the sim track is from ME0 and is a muon and if >= 4 hits in track, record all valid tracks into me0_tracks
        for i in range(0, n_track):
            if len(track_hit_index[i]) >= 1:
                if track_type[i] == 13 or track_type[i] == -13:
                    muon_hits = 0
                    for index in track_hit_index[i]:
                        if simhit_particle[index] == 13 or simhit_particle[index] == -13:
                            muon_hits += 1
                    if len(track_hit_index[i]) == muon_hits:
                        me0_tracks.append(i)
        n_me0_track = len(me0_tracks)

        # organize sim track data
        for i in me0_tracks:
            # using the first hit's region and chamber as the track's region and chamber
            track_chamber = -9999
            track_eta_partition = -9999
            track_pt = track_type[i]
            track_strip_center = -9999
            if simhit_region[track_hit_index[i][0]] == 1:
                track_chamber = 18 + simhit_chamber[track_hit_index[i][0]]
            else:
                track_chamber = simhit_chamber[track_hit_index[i][0]]
            top_layer_sbit = 0
            top_layer = 0
            bot_layer_sbit = 0
            bot_layer = 9999
            eta_partition_list = []
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
            track_strip_center = (top_layer_sbit + bot_layer_sbit)/2.0
            eta_partition_list_sorted = eta_partition_list
            eta_partition_list_sorted.sort(reverse=True)
            track_eta_partition = max(eta_partition_list_sorted,key=eta_partition_list_sorted.count)
            signal_track_data[track_chamber][track_eta_partition]["track_pt"].append(track_pt)
            signal_track_data[track_chamber][track_eta_partition]["track_strip_center"].append(track_strip_center)

    '''
    # Reading Background Data
    for (ievent, event) in enumerate(root_bkg):

        # read digihit info
        digihit_region = event["me0_digi_hit_region_i"]
        digihit_chamber = event["me0_digi_hit_chamber_i"] - 1
        digihit_eta_partition = event["me0_digi_hit_eta_partition_i"] - 1
        digihit_layer = event["me0_digi_hit_layer_i"] - 1
        digihit_sbit = np.floor(event["me0_digi_hit_strip_i"] / num_or)
        digihit_bx = event["me0_digi_hit_bx_i"]

        # organize digi hit data
        background_data[digihit_chamber][digihit_eta_partition*2][digihit_layer] |= (1 << int(digihit_sbit))
        for pseudo_eta_partition in range(1, 15, 2):
            if digihit_eta_partition == (pseudo_eta_partition-1)/2:
                if digihit_layer in [2, 3, 4, 5]:
                    background_data[digihit_chamber][pseudo_eta_partition][digihit_layer] |= (1 << int(digihit_sbit))
            elif digihit_eta_partition == (pseudo_eta_partition+1)/2:
                if digihit_layer in [0, 1, 2, 3]:
                    background_data[digihit_chamber][pseudo_eta_partition][digihit_layer] |= (1 << int(digihit_sbit))
    ''' 

    # Prepare data for NN training
       
      

                

   

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NN Training Script for Online ME0 Segment Finder')
    parser.add_argument("-f", "--file_path", action="store", dest="file_path", help="file_path = the .root file path to be read for signal+background")
    #parser.add_argument("-fs", "--file_path_signal", action="store", dest="file_path_signal", help="file_path_signal = the .root file path to be read for signal")
    #parser.add_argument("-fb", "--file_path_bkg", action="store", dest="file_path_bkg", help="file_path_bkg = the .root file path to be read for background")
    parser.add_argument("-t", "--hits", action="store", dest="hits", default="digi", help="hits = digi or rec")
    parser.add_argument("-b", "--bx", action="store", dest="bx", default="all", help="bx = all or nr. of BXs to consider")
    parser.add_argument("-o", "--num_or", action="store", dest="num_or", default = "2", help="number of strips that are OR-ed together")
    args = parser.parse_args()

    # read in the data
    print ("Reading root files...")
    root_dat = read_ntuple(args.file_path)
    print ("Reading root file done")
    #root_dat_signal = read_ntuple(args.file_path_signal)
    #print ("Reading signal file done")
    #root_dat_bkg = read_ntuple(args.file_path_bkg)
    #print ("Reading background file done")
    print ("")

    if int(args.num_or) < 2:
        print ("At least 2 strips OR-ed together")
        sys.exit()

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

    analysis(root_dat, args.hits, args.bx, bx_list, int(args.num_or))
    #analysis(root_dat_signal, root_dat_bkg, args.hits, args.bx, bx_list, int(args.num_or))
