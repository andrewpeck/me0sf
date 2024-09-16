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
    file_out = open("output_log_%s_bx%s_crosspart_%s_or%d.txt"%(hits, bx, cross_part, num_or), "w")
    file_out_summary = open("output_log_%s_bx%s_crosspart_%s_or%d_summary.txt"%(hits, bx, cross_part, num_or), "w")

    # Nr. of segments per chamber per event
    num_seg_per_chamber = ROOT.TH1D("num_seg_per_chamber","Fraction of Events vs Number of Segments per Chamber",13,-0.5,12.5)
    num_seg_per_chamber_offline = ROOT.TH1D("num_seg_per_chamber_offline","Fraction of Events vs Number of Segments per Chamber",13,-0.5,12.5)

    # Nr. of background segments per chamber per event
    num_bkg_seg_per_chamber_per_event_eta = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_eta", "num_bkg_seg_per_chamber_per_event_eta",8,0.5,8.5)
    num_bkg_seg_per_chamber_per_event_bending = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending", "num_bkg_seg_per_chamber_per_event_bending",80,-4,4)
    num_bkg_seg_per_chamber_per_event_bending1 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending1", "num_bkg_seg_per_chamber_per_event_bending1",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending2 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending2", "num_bkg_seg_per_chamber_per_event_bending2",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending3 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending3", "num_bkg_seg_per_chamber_per_event_bending3",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending4 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending4", "num_bkg_seg_per_chamber_per_event_bending4",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending5 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending5", "num_bkg_seg_per_chamber_per_event_bending5",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending6 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending6", "num_bkg_seg_per_chamber_per_event_bending6",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending7 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending7", "num_bkg_seg_per_chamber_per_event_bending7",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending8 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending8", "num_bkg_seg_per_chamber_per_event_bending8",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending9 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending9", "num_bkg_seg_per_chamber_per_event_bending9",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending10 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending10", "num_bkg_seg_per_chamber_per_event_bending10",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending11 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending11", "num_bkg_seg_per_chamber_per_event_bending11",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending12 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending12", "num_bkg_seg_per_chamber_per_event_bending12",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending13 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending13", "num_bkg_seg_per_chamber_per_event_bending13",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending14 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending14", "num_bkg_seg_per_chamber_per_event_bending14",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending15 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending15", "num_bkg_seg_per_chamber_per_event_bending15",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending16 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending16", "num_bkg_seg_per_chamber_per_event_bending16",80,-4,4) 
    num_bkg_seg_per_chamber_per_event_bending17 = ROOT.TH1F("num_bkg_seg_per_chamber_per_event_bending17", "num_bkg_seg_per_chamber_per_event_bending17",80,-4,4) 

    # Nr. of signal segments per chamber per event
    num_signal_seg_per_chamber_per_event_bending = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending", "num_signal_seg_per_chamber_per_event_bending",40,-2,2)
    num_signal_seg_per_chamber_per_event_bending1 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending1", "num_signal_seg_per_chamber_per_event_bending1",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending2 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending2", "num_signal_seg_per_chamber_per_event_bending2",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending3 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending3", "num_signal_seg_per_chamber_per_event_bending3",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending4 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending4", "num_signal_seg_per_chamber_per_event_bending4",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending5 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending5", "num_signal_seg_per_chamber_per_event_bending5",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending6 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending6", "num_signal_seg_per_chamber_per_event_bending6",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending7 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending7", "num_signal_seg_per_chamber_per_event_bending7",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending8 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending8", "num_signal_seg_per_chamber_per_event_bending8",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending9 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending9", "num_signal_seg_per_chamber_per_event_bending9",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending10 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending10", "num_signal_seg_per_chamber_per_event_bending10",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending11 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending11", "num_signal_seg_per_chamber_per_event_bending11",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending12 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending12", "num_signal_seg_per_chamber_per_event_bending12",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending13 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending13", "num_signal_seg_per_chamber_per_event_bending13",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending14 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending14", "num_signal_seg_per_chamber_per_event_bending14",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending15 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending15", "num_signal_seg_per_chamber_per_event_bending15",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending16 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending16", "num_signal_seg_per_chamber_per_event_bending16",40,-2,2) 
    num_signal_seg_per_chamber_per_event_bending17 = ROOT.TH1F("num_signal_seg_per_chamber_per_event_bending17", "num_signal_seg_per_chamber_per_event_bending17",40,-2,2) 

    # defining histograms for offline vs online
    bins_bending = [-4.0, -3.0, -2.5, -2.0, -1.8, -1.6, -1.4, -1.2, -1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0]
    offline_effi_passed_bending = ROOT.TH1F("offline_effi_passed_bending", "offline_effi_passed_bending",36, array('d',bins_bending))
    offline_effi_total_bending = ROOT.TH1F("offline_effi_total_bending", "offline_effi_total_bending",36, array('d',bins_bending)) 
    offline_effi_passed_eta = ROOT.TH1F("offline_effi_passed_eta", "offline_effi_passed_eta",8,0.5,8.5)
    offline_effi_total_eta = ROOT.TH1F("offline_effi_total_eta", "offline_effi_total_eta",8,0.5,8.5) 
    offline_effi_mres = ROOT.TH1F("offline_effi_Bend_Ang_Res", "offline_effi_Bend_Ang_Res", 20, -0.6, 0.6)
    offline_effi_sres = ROOT.TH1F("offline_effi_Strip_Res", "offline_effi_Strip_Res", 20, -0.9, 0.9)
    offline_purity_passed_eta = ROOT.TH1F("offline_purity_pass_eta", "offline_purity_pass_eta",8,0.5,8.5)
    offline_purity_total_eta = ROOT.TH1F("offline_purity_total_eta", "offline_purity_total_eta",8,0.5,8.5) 
    offline_purity_passed_bending = ROOT.TH1F("offline_purity_passed_bending", "offline_purity_passed_bending",36, array('d',bins_bending))
    offline_purity_total_bending = ROOT.TH1F("offline_purity_total_bending", "offline_purity_total_bending",36, array('d',bins_bending)) 
    offline_effi_passed_id = ROOT.TH1F("offline_effi_passed_id", "offline_effi_passed_id",17, 0.5, 17.5)
    offline_effi_total_id = ROOT.TH1F("offline_effi_total_id", "offline_effi_total_id",17, 0.5, 17.5)
    offline_purity_passed_id = ROOT.TH1F("offline_purity_passed_id", "offline_purity_passed_id",17, 0.5, 17.5)
    offline_purity_total_id = ROOT.TH1F("offline_purity_total_id", "offline_purity_total_id",17, 0.5, 17.5)

    # defining histograms for simtrack vs online
    bins_pt = [0.0,1.0,2.0,3.0,4.0,5.0,10.0,15.0,20.0,25.0,30.0,35.0,40.0,45.0,50.0]
    st_effi_passed_pt = ROOT.TH1F("st_effi_pass_pt", "st_effi_pass_pt",14, array('d',bins_pt))
    st_effi_total_pt = ROOT.TH1F("st_effi_total_pt", "st_effi_total_pt",14, array('d',bins_pt)) 
    st_effi_eta_high_passed_pt = ROOT.TH1F("st_effi_eta_high_pass_pt", "st_effi_eta_high_pass_pt",14, array('d',bins_pt))
    st_effi_eta_high_total_pt = ROOT.TH1F("st_effi_eta_high_total_pt", "st_effi_eta_high_total_pt",14, array('d',bins_pt))
    st_effi_eta_low_passed_pt = ROOT.TH1F("st_effi_eta_low_passed_pt", "st_effi_eta_low_passed_pt",14, array('d',bins_pt))
    st_effi_eta_low_total_pt = ROOT.TH1F("st_effi_eta_low_total_pt", "st_effi_eta_low_total_pt",14, array('d',bins_pt))
    st_effi_passed_pt_eta = ROOT.TH2F("st_effi_passed_pt_eta", "st_effi_passed_pt_eta",14, array('d',bins_pt), 8, 0.5, 8.5)
    st_effi_total_pt_eta = ROOT.TH2F("st_effi_total_pt_eta", "st_effi_total_pt_eta",14, array('d',bins_pt), 8, 0.5, 8.5)
    st_effi_passed_eta = ROOT.TH1F("st_effi_pass_eta", "st_effi_pass_eta",8,0.5,8.5)
    st_effi_total_eta = ROOT.TH1F("st_effi_total_eta", "st_effi_total_eta",8,0.5,8.5) 
    st_effi_passed_bending = ROOT.TH1F("st_effi_pass_bending", "st_effi_pass_bending",36, array('d',bins_bending))
    st_effi_total_bending = ROOT.TH1F("st_effi_total_bending", "st_effi_total_bending",36, array('d',bins_bending)) 
    st_effi_mres = ROOT.TH1F("st_effi_Bend_Ang_Res", "st_effi_Bend_Ang_Res", 20, -0.6, 0.6)
    st_effi_sres = ROOT.TH1F("st_effi_Strip_Res", "st_effi_Strip_Res", 20, -0.9, 0.9)
    st_purity_passed_eta = ROOT.TH1F("st_purity_pass_eta", "st_purity_pass_eta",8,0.5,8.5)
    st_purity_total_eta = ROOT.TH1F("st_purity_total_eta", "st_purity_total_eta",8,0.5,8.5) 
    st_purity_passed_bending = ROOT.TH1F("st_purity_passed_bending", "st_purity_passed_bending",36, array('d',bins_bending))
    st_purity_total_bending = ROOT.TH1F("st_purity_total_bending", "st_purity_total_bending",36, array('d',bins_bending)) 
    st_effi_passed_id = ROOT.TH1F("st_effi_passed_id", "st_effi_passed_id",17, 0.5, 17.5)
    st_effi_total_id = ROOT.TH1F("st_effi_total_id", "st_effi_total_id",17, 0.5, 17.5)
    st_purity_passed_id = ROOT.TH1F("st_purity_passed_id", "st_purity_passed_id",17, 0.5, 17.5)
    st_purity_total_id = ROOT.TH1F("st_purity_total_id", "st_purity_total_id",17, 0.5, 17.5)

    '''
    st_effi_passed_max_cluster_size = ROOT.TH1F("st_effi_passed_max_cluster_size", "st_effi_passed_max_cluster_size", 37, 0.5, 37.5)
    st_effi_total_max_cluster_size = ROOT.TH1F("st_effi_total_max_cluster_size", "st_effi_total_max_cluster_size", 37, 0.5, 37.5)
    st_effi_passed_max_noise = ROOT.TH1F("st_effi_passed_max_noise", "st_effi_passed_max_noise", 37, 0.5, 37.5)
    st_effi_total_max_noise = ROOT.TH1F("st_effi_total_max_noise", "st_effi_total_max_noise", 37, 0.5, 37.5)
    st_effi_passed_nlayers_withcsg3 = ROOT.TH1F("st_effi_passed_nlayers_withcsg3", "st_effi_passed_nlayers_withcsg3", 6, 0.5, 6.5)
    st_effi_total_nlayers_withcsg3 = ROOT.TH1F("st_effi_total_nlayers_withcsg3", "st_effi_total_nlayers_withcsg3", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withcsg5 = ROOT.TH1F("st_effi_passed_nlayers_withcsg5", "st_effi_passed_nlayers_withcsg5", 6, 0.5, 6.5)
    st_effi_total_nlayers_withcsg5 = ROOT.TH1F("st_effi_total_nlayers_withcsg5", "st_effi_total_nlayers_withcsg5", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withcsg10 = ROOT.TH1F("st_effi_passed_nlayers_withcsg10", "st_effi_passed_nlayers_withcsg10", 6, 0.5, 6.5)
    st_effi_total_nlayers_withcsg10 = ROOT.TH1F("st_effi_total_nlayers_withcsg10", "st_effi_total_nlayers_withcsg10", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withcsg15 = ROOT.TH1F("st_effi_passed_nlayers_withcsg15", "st_effi_passed_nlayers_withcsg15", 6, 0.5, 6.5)
    st_effi_total_nlayers_withcsg15 = ROOT.TH1F("st_effi_total_nlayers_withcsg15", "st_effi_total_nlayers_withcsg15", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withnoiseg3 = ROOT.TH1F("st_effi_passed_nlayers_withnoiseg3", "st_effi_passed_nlayers_withnoiseg3", 6, 0.5, 6.5)
    st_effi_total_nlayers_withnoiseg3 = ROOT.TH1F("st_effi_total_nlayers_withnoiseg3", "st_effi_total_nlayers_withnoiseg3", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withnoiseg5 = ROOT.TH1F("st_effi_passed_nlayers_withnoiseg5", "st_effi_passed_nlayers_withnoiseg5", 6, 0.5, 6.5)
    st_effi_total_nlayers_withnoiseg5 = ROOT.TH1F("st_effi_total_nlayers_withnoiseg5", "st_effi_total_nlayers_withnoiseg5", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withnoiseg10 = ROOT.TH1F("st_effi_passed_nlayers_withnoiseg10", "st_effi_passed_nlayers_withnoiseg10", 6, 0.5, 6.5)
    st_effi_total_nlayers_withnoiseg10 = ROOT.TH1F("st_effi_total_nlayers_withnoiseg10", "st_effi_total_nlayers_withnoiseg10", 6, 0.5, 6.5)
    st_effi_passed_nlayers_withnoiseg15 = ROOT.TH1F("st_effi_passed_nlayers_withnoiseg15", "st_effi_passed_nlayers_withnoiseg15", 6, 0.5, 6.5)
    st_effi_total_nlayers_withnoiseg15 = ROOT.TH1F("st_effi_total_nlayers_withnoiseg15", "st_effi_total_nlayers_withnoiseg15", 6, 0.5, 6.5)
    st_purity_passed_max_cluster_size = ROOT.TH1F("st_purity_passed_max_cluster_size", "st_purity_passed_max_cluster_size", 37, 0.5, 37.5)
    st_purity_total_max_cluster_size = ROOT.TH1F("st_purity_total_max_cluster_size", "st_purity_total_max_cluster_size", 37, 0.5, 37.5)
    st_purity_passed_max_noise = ROOT.TH1F("st_purity_passed_max_noise", "st_purity_passed_max_noise", 37, 0.5, 37.5)
    st_purity_total_max_noise = ROOT.TH1F("st_purity_total_max_noise", "st_purity_total_max_noise", 37, 0.5, 37.5)
    st_purity_passed_nlayers_withcsg3 = ROOT.TH1F("st_purity_passed_nlayers_withcsg3", "st_purity_passed_nlayers_withcsg3", 6, 0.5, 6.5)
    st_purity_total_nlayers_withcsg3 = ROOT.TH1F("st_purity_total_nlayers_withcsg3", "st_purity_total_nlayers_withcsg3", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withcsg5 = ROOT.TH1F("st_purity_passed_nlayers_withcsg5", "st_purity_passed_nlayers_withcsg5", 6, 0.5, 6.5)
    st_purity_total_nlayers_withcsg5 = ROOT.TH1F("st_purity_total_nlayers_withcsg5", "st_purity_total_nlayers_withcsg5", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withcsg10 = ROOT.TH1F("st_purity_passed_nlayers_withcsg10", "st_purity_passed_nlayers_withcsg10", 6, 0.5, 6.5)
    st_purity_total_nlayers_withcsg10 = ROOT.TH1F("st_purity_total_nlayers_withcsg10", "st_purity_total_nlayers_withcsg10", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withcsg15 = ROOT.TH1F("st_purity_passed_nlayers_withcsg15", "st_purity_passed_nlayers_withcsg15", 6, 0.5, 6.5)
    st_purity_total_nlayers_withcsg15 = ROOT.TH1F("st_purity_total_nlayers_withcsg15", "st_purity_total_nlayers_withcsg15", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withnoiseg3 = ROOT.TH1F("st_purity_passed_nlayers_withnoiseg3", "st_purity_passed_nlayers_withnoiseg3", 6, 0.5, 6.5)
    st_purity_total_nlayers_withnoiseg3 = ROOT.TH1F("st_purity_total_nlayers_withnoiseg3", "st_purity_total_nlayers_withnoiseg3", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withnoiseg5 = ROOT.TH1F("st_purity_passed_nlayers_withnoiseg5", "st_purity_passed_nlayers_withnoiseg5", 6, 0.5, 6.5)
    st_purity_total_nlayers_withnoiseg5 = ROOT.TH1F("st_purity_total_nlayers_withnoiseg5", "st_purity_total_nlayers_withnoiseg5", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withnoiseg10 = ROOT.TH1F("st_purity_passed_nlayers_withnoiseg10", "st_purity_passed_nlayers_withnoiseg10", 6, 0.5, 6.5)
    st_purity_total_nlayers_withnoiseg10 = ROOT.TH1F("st_purity_total_nlayers_withnoiseg10", "st_purity_total_nlayers_withnoiseg10", 6, 0.5, 6.5)
    st_purity_passed_nlayers_withnoiseg15 = ROOT.TH1F("st_purity_passed_nlayers_withnoiseg15", "st_purity_passed_nlayers_withnoiseg15", 6, 0.5, 6.5)
    st_purity_total_nlayers_withnoiseg15 = ROOT.TH1F("st_purity_total_nlayers_withnoiseg15", "st_purity_total_nlayers_withnoiseg15", 6, 0.5, 6.5)
    '''

    # define the histograms efficiency vs pt for each pattern (simtracks)
    st_effi_passed_pt1 = ROOT.TH1F("st_effi_passed_pt1", "st_effi_passed_pt1",14, array('d',bins_pt)) 
    st_effi_passed_pt2 = ROOT.TH1F("st_effi_passed_pt2", "st_effi_passed_pt2",14, array('d',bins_pt)) 
    st_effi_passed_pt3 = ROOT.TH1F("st_effi_passed_pt3", "st_effi_passed_pt3",14, array('d',bins_pt)) 
    st_effi_passed_pt4 = ROOT.TH1F("st_effi_passed_pt4", "st_effi_passed_pt4",14, array('d',bins_pt)) 
    st_effi_passed_pt5 = ROOT.TH1F("st_effi_passed_pt5", "st_effi_passed_pt5",14, array('d',bins_pt)) 
    st_effi_passed_pt6 = ROOT.TH1F("st_effi_passed_pt6", "st_effi_passed_pt6",14, array('d',bins_pt)) 
    st_effi_passed_pt7 = ROOT.TH1F("st_effi_passed_pt7", "st_effi_passed_pt7",14, array('d',bins_pt)) 
    st_effi_passed_pt8 = ROOT.TH1F("st_effi_passed_pt8", "st_effi_passed_pt8",14, array('d',bins_pt)) 
    st_effi_passed_pt9 = ROOT.TH1F("st_effi_passed_pt9", "st_effi_passed_pt9",14, array('d',bins_pt)) 
    st_effi_passed_pt10 = ROOT.TH1F("st_effi_passed_pt10", "st_effi_passed_pt10",14, array('d',bins_pt)) 
    st_effi_passed_pt11 = ROOT.TH1F("st_effi_passed_pt11", "st_effi_passed_pt11",14, array('d',bins_pt)) 
    st_effi_passed_pt12 = ROOT.TH1F("st_effi_passed_pt12", "st_effi_passed_pt12",14, array('d',bins_pt)) 
    st_effi_passed_pt13 = ROOT.TH1F("st_effi_passed_pt13", "st_effi_passed_pt13",14, array('d',bins_pt)) 
    st_effi_passed_pt14 = ROOT.TH1F("st_effi_passed_pt14", "st_effi_passed_pt14",14, array('d',bins_pt)) 
    st_effi_passed_pt15 = ROOT.TH1F("st_effi_passed_pt15", "st_effi_passed_pt15",14, array('d',bins_pt)) 
    st_effi_passed_pt16 = ROOT.TH1F("st_effi_passed_pt16", "st_effi_passed_pt16",14, array('d',bins_pt)) 
    st_effi_passed_pt17 = ROOT.TH1F("st_effi_passed_pt17", "st_effi_passed_pt17",14, array('d',bins_pt)) 

    # Counters for Efficiency
    n_offline_effi_total = 0
    n_offline_effi_passed = 0
    n_offline_purity_total = 0
    n_offline_purity_passed = 0
    n_st_effi_total = 0
    n_st_effi_passed = 0
    n_st_purity_total = 0
    n_st_purity_passed = 0
    n_bkg_seg_per_chamber_per_event = 0

    n_total_events = len(root_dat)
    prev_frac_done = 0

    mse_th = 0.75 # threashold to reject a segment based on mse
    #mse_collections = [] # collect all mse for analysis of the distribution (only need to run once)
    seg_bx_collections = []

    for (ievent, event) in enumerate(root_dat):
        frac_done = (ievent+1)/n_total_events
        if (frac_done - prev_frac_done) >= 0.05:
            print ("%.2f"%(frac_done*100) + "% Events Done")
            prev_frac_done = frac_done
        #if ievent >= 3:
        #    continue
        if verbose:
            file_out.write("Event number = %d\n"%ievent)
            file_out_summary.write("Event number = %d\n"%ievent)

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

        # initialize the bx_data, bx data will be inserted based on different input
        # todo : 
        #bx_data = np.full((36, 8, 6, 192), -9999)
        bx_data = [[[[ -9999 for _ in range(192)] for _ in range(6)] for _ in range(8)] for _ in range(36)]

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
                bx_data[chamb_idx][part_idx][layer_idx][sbit_idx] = rechit_bx[hit]

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
                else:
                    bx_data[chamb_idx][part_idx][layer_idx][sbit_idx] = digihit_bx[hit]
                    #print(digihit_bx[hit])
                
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
            chamber_bx_data = bx_data[chamber_nr][:][:][:]

            config = Config()
            config.num_outputs = 10
            config.cross_part_seg_width = 4
            config.ghost_width = 10
            num_or_to_span = {2:37, 4:19, 8:11, 16:7}
            config.max_span = num_or_to_span[num_or]
            config.num_or = num_or
            seglist = process_chamber(data, config, chamber_bx_data)
            seglist_final = []
            for seg in seglist:
                seg.fit(config.max_span)
                if seg.mse is not None and seg.mse >= mse_th:
                    seg.id = 0
                if seg.id == 0:
                    continue
                #mse_collections.append(seg.mse)
                #print(seg.mse)
                seg_bx_collections.append(seg.bx)
                #print(seg.bx)
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
            offline_effi_total_bending.Fill(offline_bending_angle)
            offline_effi_total_eta.Fill(offline_eta_partition)
            for id in range(1,18):
                offline_effi_total_id.Fill(id)
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
                        offline_effi_passed_bending.Fill(offline_bending_angle)
                        offline_effi_passed_eta.Fill(offline_eta_partition)
                        offline_effi_passed_id.Fill(online_id)
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
        online_seg_sim_track_matched_pt = []
        online_seg_sim_track_matched_bending_angle = []
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
            if st_eta_partition <= 3:
                st_effi_eta_low_total_pt.Fill(st_pt)
            else:
                st_effi_eta_high_total_pt.Fill(st_pt)
            st_effi_total_pt_eta.Fill(st_pt, st_eta_partition+1)
            st_effi_total_eta.Fill(st_eta_partition+1)
            for id in range(1,18):
                st_effi_total_id.Fill(id)
            '''
            for counts in range(1,38):
                st_effi_total_max_cluster_size.Fill(counts)
                st_effi_total_max_noise.Fill(counts)
            for l in range(1,7):
                st_effi_total_nlayers_withcsg3.Fill(l)
                st_effi_total_nlayers_withcsg5.Fill(l)
                st_effi_total_nlayers_withcsg10.Fill(l)
                st_effi_total_nlayers_withcsg15.Fill(l)
                st_effi_total_nlayers_withnoiseg3.Fill(l)
                st_effi_total_nlayers_withnoiseg5.Fill(l)
                st_effi_total_nlayers_withnoiseg10.Fill(l)
                st_effi_total_nlayers_withnoiseg15.Fill(l)
            '''

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
                        if st_eta_partition <= 3:
                            st_effi_eta_low_passed_pt.Fill(st_pt)
                        else:
                            st_effi_eta_high_passed_pt.Fill(st_pt)
                        st_effi_passed_pt_eta.Fill(st_pt, st_eta_partition+1)
                        st_effi_passed_eta.Fill(st_eta_partition+1)
                        st_effi_passed_id.Fill(online_id)

                        online_seg_sim_track_matched_pt.append(st_pt)
                        online_seg_sim_track_matched_bending_angle.append(online_bending_angle)

                        '''
                        st_effi_passed_max_cluster_size.Fill(seg.max_cluster_size)
                        st_effi_passed_max_noise.Fill(seg.max_noise)
                        st_effi_passed_nlayers_withcsg3.Fill(seg.nlayers_withcsg3)
                        st_effi_passed_nlayers_withcsg5.Fill(seg.nlayers_withcsg5)
                        st_effi_passed_nlayers_withcsg10.Fill(seg.nlayers_withcsg10)
                        st_effi_passed_nlayers_withcsg15.Fill(seg.nlayers_withcsg15)
                        st_effi_passed_nlayers_withnoiseg3.Fill(seg.nlayers_withnoiseg3)
                        st_effi_passed_nlayers_withnoiseg5.Fill(seg.nlayers_withnoiseg5)
                        st_effi_passed_nlayers_withnoiseg10.Fill(seg.nlayers_withnoiseg10)
                        st_effi_passed_nlayers_withnoiseg15.Fill(seg.nlayers_withnoiseg15)
                        '''

                        if online_id == 1:
                            st_effi_passed_pt1.Fill(st_pt)
                        elif online_id == 2:
                            st_effi_passed_pt2.Fill(st_pt)
                        elif online_id == 3:
                            st_effi_passed_pt3.Fill(st_pt)
                        elif online_id == 4:
                            st_effi_passed_pt4.Fill(st_pt)
                        elif online_id == 5:
                            st_effi_passed_pt5.Fill(st_pt)
                        elif online_id == 6:
                            st_effi_passed_pt6.Fill(st_pt)
                        elif online_id == 7:
                            st_effi_passed_pt7.Fill(st_pt)
                        elif online_id == 8:
                            st_effi_passed_pt8.Fill(st_pt)
                        elif online_id == 9:
                            st_effi_passed_pt9.Fill(st_pt)
                        elif online_id == 10:
                            st_effi_passed_pt10.Fill(st_pt)
                        elif online_id == 11:
                            st_effi_passed_pt11.Fill(st_pt)
                        elif online_id == 12:
                            st_effi_passed_pt12.Fill(st_pt)
                        elif online_id == 13:
                            st_effi_passed_pt13.Fill(st_pt)
                        elif online_id == 14:
                            st_effi_passed_pt14.Fill(st_pt)
                        elif online_id == 15:
                            st_effi_passed_pt15.Fill(st_pt)
                        elif online_id == 16:
                            st_effi_passed_pt16.Fill(st_pt)
                        elif online_id == 17:
                            st_effi_passed_pt17.Fill(st_pt)

                        num_signal_seg_per_chamber_per_event_bending.Fill(online_bending_angle)
                        if online_id == 1:
                            num_signal_seg_per_chamber_per_event_bending1.Fill(online_bending_angle)
                        elif online_id == 2:
                            num_signal_seg_per_chamber_per_event_bending2.Fill(online_bending_angle)
                        elif online_id == 3:
                            num_signal_seg_per_chamber_per_event_bending3.Fill(online_bending_angle)
                        elif online_id == 4:
                            num_signal_seg_per_chamber_per_event_bending4.Fill(online_bending_angle)
                        elif online_id == 5:
                            num_signal_seg_per_chamber_per_event_bending5.Fill(online_bending_angle)
                        elif online_id == 6:
                            num_signal_seg_per_chamber_per_event_bending6.Fill(online_bending_angle)
                        elif online_id == 7:
                            num_signal_seg_per_chamber_per_event_bending7.Fill(online_bending_angle)
                        elif online_id == 8:
                            num_signal_seg_per_chamber_per_event_bending8.Fill(online_bending_angle)
                        elif online_id == 9:
                            num_signal_seg_per_chamber_per_event_bending9.Fill(online_bending_angle)
                        elif online_id == 10:
                            num_signal_seg_per_chamber_per_event_bending10.Fill(online_bending_angle)
                        elif online_id == 11:
                            num_signal_seg_per_chamber_per_event_bending11.Fill(online_bending_angle)
                        elif online_id == 12:
                            num_signal_seg_per_chamber_per_event_bending12.Fill(online_bending_angle)
                        elif online_id == 13:
                            num_signal_seg_per_chamber_per_event_bending13.Fill(online_bending_angle)
                        elif online_id == 14:
                            num_signal_seg_per_chamber_per_event_bending14.Fill(online_bending_angle)
                        elif online_id == 15:
                            num_signal_seg_per_chamber_per_event_bending15.Fill(online_bending_angle)
                        elif online_id == 16:
                            num_signal_seg_per_chamber_per_event_bending16.Fill(online_bending_angle)
                        elif online_id == 17:
                            num_signal_seg_per_chamber_per_event_bending17.Fill(online_bending_angle)

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

        # Checking Purity w.r.t sim tracks and offline segments
        for chamber in online_segment_chamber: 
            for seg in online_segment_chamber[chamber]:
                online_eta_partition = seg.partition
                online_substrip = seg.substrip+seg.strip
                online_bending_angle = seg.bend_ang
                online_id = seg.id
                st_purity_total_eta.Fill(online_eta_partition+1)
                st_purity_total_bending.Fill(online_bending_angle)
                st_purity_total_id.Fill(online_id)
                '''
                st_purity_total_max_cluster_size.Fill(seg.max_cluster_size)
                st_purity_total_max_noise.Fill(seg.max_noise)
                st_purity_total_nlayers_withcsg3.Fill(seg.nlayers_withcsg3)
                st_purity_total_nlayers_withcsg5.Fill(seg.nlayers_withcsg5)
                st_purity_total_nlayers_withcsg10.Fill(seg.nlayers_withcsg10)
                st_purity_total_nlayers_withcsg15.Fill(seg.nlayers_withcsg15)
                st_purity_total_nlayers_withnoiseg3.Fill(seg.nlayers_withnoiseg3)
                st_purity_total_nlayers_withnoiseg5.Fill(seg.nlayers_withnoiseg5)
                st_purity_total_nlayers_withnoiseg10.Fill(seg.nlayers_withnoiseg10)
                st_purity_total_nlayers_withnoiseg15.Fill(seg.nlayers_withnoiseg15)
                '''
                offline_purity_total_eta.Fill(online_eta_partition+1)
                offline_purity_total_bending.Fill(online_bending_angle)
                offline_purity_total_id.Fill(online_id)
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
                            offline_purity_passed_eta.Fill(online_eta_partition+1)
                            offline_purity_passed_bending.Fill(online_bending_angle)
                            offline_purity_passed_id.Fill(online_id)
                            n_offline_purity_passed += 1
                            break

                match_found = 0
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
                            st_purity_passed_id.Fill(online_id)
                            '''
                            st_purity_passed_max_cluster_size.Fill(seg.max_cluster_size)
                            st_purity_passed_max_noise.Fill(seg.max_noise)
                            st_purity_passed_nlayers_withcsg3.Fill(seg.nlayers_withcsg3)
                            st_purity_passed_nlayers_withcsg5.Fill(seg.nlayers_withcsg5)
                            st_purity_passed_nlayers_withcsg10.Fill(seg.nlayers_withcsg10)
                            st_purity_passed_nlayers_withcsg15.Fill(seg.nlayers_withcsg15)
                            st_purity_passed_nlayers_withnoiseg3.Fill(seg.nlayers_withnoiseg3)
                            st_purity_passed_nlayers_withnoiseg5.Fill(seg.nlayers_withnoiseg5)
                            st_purity_passed_nlayers_withnoiseg10.Fill(seg.nlayers_withnoiseg10)
                            st_purity_passed_nlayers_withnoiseg15.Fill(seg.nlayers_withnoiseg15)
                            '''
                            n_st_purity_passed += 1
                            match_found = 1
                            break
                if match_found == 0:
                    num_bkg_seg_per_chamber_per_event_eta.Fill(online_eta_partition+1)
                    num_bkg_seg_per_chamber_per_event_bending.Fill(online_bending_angle)
                    if online_id == 1:
                        num_bkg_seg_per_chamber_per_event_bending1.Fill(online_bending_angle)
                    elif online_id == 2:
                        num_bkg_seg_per_chamber_per_event_bending2.Fill(online_bending_angle)
                    elif online_id == 3:
                        num_bkg_seg_per_chamber_per_event_bending3.Fill(online_bending_angle)
                    elif online_id == 4:
                        num_bkg_seg_per_chamber_per_event_bending4.Fill(online_bending_angle)
                    elif online_id == 5:
                        num_bkg_seg_per_chamber_per_event_bending5.Fill(online_bending_angle)
                    elif online_id == 6:
                        num_bkg_seg_per_chamber_per_event_bending6.Fill(online_bending_angle)
                    elif online_id == 7:
                        num_bkg_seg_per_chamber_per_event_bending7.Fill(online_bending_angle)
                    elif online_id == 8:
                        num_bkg_seg_per_chamber_per_event_bending8.Fill(online_bending_angle)
                    elif online_id == 9:
                        num_bkg_seg_per_chamber_per_event_bending9.Fill(online_bending_angle)
                    elif online_id == 10:
                        num_bkg_seg_per_chamber_per_event_bending10.Fill(online_bending_angle)
                    elif online_id == 11:
                        num_bkg_seg_per_chamber_per_event_bending11.Fill(online_bending_angle)
                    elif online_id == 12:
                        num_bkg_seg_per_chamber_per_event_bending12.Fill(online_bending_angle)
                    elif online_id == 13:
                        num_bkg_seg_per_chamber_per_event_bending13.Fill(online_bending_angle)
                    elif online_id == 14:
                        num_bkg_seg_per_chamber_per_event_bending14.Fill(online_bending_angle)
                    elif online_id == 15:
                        num_bkg_seg_per_chamber_per_event_bending15.Fill(online_bending_angle)
                    elif online_id == 16:
                        num_bkg_seg_per_chamber_per_event_bending16.Fill(online_bending_angle)
                    elif online_id == 17:
                        num_bkg_seg_per_chamber_per_event_bending17.Fill(online_bending_angle)

                    n_bkg_seg_per_chamber_per_event += 1

        if verbose:
            file_out_summary.write("  Online Segments: \n")
            for chamber in range(0, 36):
                if len(online_segment_chamber[chamber]) == 0:
                    continue
                file_out_summary.write("    Chamber %d: "%chamber)
                eta_partition_list = []
                pattern_id_list = []
                pt_list = []
                for seg in online_segment_chamber[chamber]:
                    eta_partition_list.append(seg.partition)
                    pattern_id_list.append(seg.id)
                eta_partition_pattern_id_zip = zip(eta_partition_list, pattern_id_list)
                eta_partition_pattern_id_zip_sorted = sorted(eta_partition_pattern_id_zip)
                eta_partition_list_sorted, pattern_id_list_sorted = zip(*eta_partition_pattern_id_zip_sorted)
                eta_partition_list_sorted = list(eta_partition_list_sorted)
                pattern_id_list_sorted = list(pattern_id_list_sorted)
                file_out_summary.write(', '.join(str(x) for x in eta_partition_list_sorted))
                file_out_summary.write(" (Pattern IDs: ")
                file_out_summary.write(', '.join(str(x) for x in pattern_id_list_sorted))
                file_out_summary.write(")")
                file_out_summary.write("\n")
            file_out_summary.write("\n")
            file_out_summary.write("  Sim Tracks: \n")
            for chamber in range(0, 36):
                chamber_match = 0
                for i in range(0, n_me0_track):
                    if chamber == track_chamber_nr[i]:
                        chamber_match = 1
                        break
                if chamber_match == 0:
                    continue
                file_out_summary.write("    Chamber %d: "%chamber)
                eta_partition_list = []
                for i in range(0, n_me0_track):
                    if chamber != track_chamber_nr[i]:
                        continue
                    eta_partition_list.append(track_eta_partition[i])
                    pt_list.append(track_pt[i])
                eta_partition_pt_zip = zip(eta_partition_list, pt_list)
                eta_partition_pt_zip_sorted = sorted(eta_partition_pt_zip)
                eta_partition_list_sorted, pt_list_sorted = zip(*eta_partition_pt_zip_sorted)
                eta_partition_list_sorted = list(eta_partition_list_sorted)
                pt_list_sorted = list(pt_list_sorted)
                file_out_summary.write(', '.join(str(x) for x in eta_partition_list_sorted))
                file_out_summary.write(" (pT: ")
                file_out_summary.write(', '.join(str(x) for x in pt_list_sorted))
                file_out_summary.write(")")
                file_out_summary.write("\n")
        file_out_summary.write("\n\n")
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
    n_bkg_seg_per_chamber_per_event /= (36.0*n_total_events)
    print ("Number of Fake segments per chamber per event = %.4f\n"%n_bkg_seg_per_chamber_per_event)
    file_out.write("Number of Fake segments per chamber per event = %.4f\n\n"%n_bkg_seg_per_chamber_per_event)
    rate_bkg_seg_per_chamber_per_event = (n_bkg_seg_per_chamber_per_event*1000) / (25.0)
    print ("Rate of Fake segments per chamber per event = %.4f MHz\n"%rate_bkg_seg_per_chamber_per_event)
    file_out.write("Rate of Fake segments per chamber per event = %.4f MHz\n\n"%rate_bkg_seg_per_chamber_per_event)

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
    c1.DrawFrame(-4, 0, 4, 1.1, ";Bending Angle (sbits/layer);Efficiency")
    offline_eff_bending = ROOT.TEfficiency(offline_effi_passed_bending, offline_effi_total_bending)
    offline_eff_bending.Draw("same")
    offline_eff_bending.SetMarkerStyle(8)
    offline_eff_bending.SetMarkerSize(1)
    offline_eff_bending.SetMarkerColor(1)
    offline_eff_bending.SetLineWidth(1)
    offline_eff_bending.SetLineColor(1)
    ROOT.gPad.Update()
    offline_eff_bending.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_eff_bending.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c1.Print("offline_eff_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_eff_bending.Write()

    c1eta = ROOT.TCanvas('', '', 800, 650)
    c1eta.SetGrid()
    c1eta.DrawFrame(0, 0, 9, 1.1, ";#eta Partition;Efficiency")
    offline_eff_eta = ROOT.TEfficiency(offline_effi_passed_eta, offline_effi_total_eta)
    offline_eff_eta.Draw("same")
    offline_eff_eta.SetMarkerStyle(8)
    offline_eff_eta.SetMarkerSize(1)
    offline_eff_eta.SetMarkerColor(1)
    offline_eff_eta.SetLineWidth(1)
    offline_eff_eta.SetLineColor(1)
    ROOT.gPad.Update()
    offline_eff_eta.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_eff_eta.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c1eta.Print("offline_eff_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_eff_eta.Write()


    c1id = ROOT.TCanvas('', '', 800, 650)
    c1id.SetGrid()
    c1id.DrawFrame(0, 0, 18, 1.1, ";Pattern ID;Efficiency")
    offline_eff_id = ROOT.TEfficiency(offline_effi_passed_id, offline_effi_total_id)
    offline_eff_id.Draw("same")
    offline_eff_id.SetMarkerStyle(8)
    offline_eff_id.SetMarkerSize(1)
    offline_eff_id.SetMarkerColor(1)
    offline_eff_id.SetLineWidth(1)
    offline_eff_id.SetLineColor(1)
    ROOT.gPad.Update()
    offline_eff_id.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_eff_id.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c1id.Print("offline_eff_id_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_eff_id.Write()

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
        c4.DrawFrame(-4, 0, 4, 1.1, ";Bending Angle (sbits/layer);Efficiency")
        st_eff_bending_bending = ROOT.TEfficiency(st_effi_passed_bending, st_effi_total_bending)
        st_eff_bending_bending.Draw("same")
        st_eff_bending_bending.SetMarkerStyle(8)
        st_eff_bending_bending.SetMarkerSize(1)
        st_eff_bending_bending.SetMarkerColor(1)
        st_eff_bending_bending.SetLineWidth(1)
        st_eff_bending_bending.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_bending_bending.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_bending_bending.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c4.Print("st_eff_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_bending_bending.Write()

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

        c_pt_eta_low = ROOT.TCanvas('', '', 800, 650)
        c_pt_eta_low.SetGrid()
        c_pt_eta_low.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_eta_low_pt = ROOT.TEfficiency(st_effi_eta_low_passed_pt, st_effi_eta_low_total_pt)
        st_eff_eta_low_pt.Draw("same")
        st_eff_eta_low_pt.SetMarkerStyle(8)
        st_eff_eta_low_pt.SetMarkerSize(1)
        st_eff_eta_low_pt.SetMarkerColor(1)
        st_eff_eta_low_pt.SetLineWidth(1)
        st_eff_eta_low_pt.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_eta_low_pt.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_eta_low_pt.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_eta_low.Print("st_eff_eta_low_pt_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_eta_low_pt.Write()

        c_pt_eta_high = ROOT.TCanvas('', '', 800, 650)
        c_pt_eta_high.SetGrid()
        c_pt_eta_high.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_eta_high_pt = ROOT.TEfficiency(st_effi_eta_high_passed_pt, st_effi_eta_high_total_pt)
        st_eff_eta_high_pt.Draw("same")
        st_eff_eta_high_pt.SetMarkerStyle(8)
        st_eff_eta_high_pt.SetMarkerSize(1)
        st_eff_eta_high_pt.SetMarkerColor(1)
        st_eff_eta_high_pt.SetLineWidth(1)
        st_eff_eta_high_pt.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_eta_high_pt.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_eta_high_pt.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_eta_high.Print("st_eff_eta_high_pt_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_eta_high_pt.Write()

        c_pt_1 = ROOT.TCanvas('', '', 800, 650)
        c_pt_1.SetGrid()
        c_pt_1.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_1 = ROOT.TEfficiency(st_effi_passed_pt1, st_effi_total_pt)
        st_eff_pt_1.Draw("same")
        st_eff_pt_1.SetMarkerStyle(8)
        st_eff_pt_1.SetMarkerSize(1)
        st_eff_pt_1.SetMarkerColor(1)
        st_eff_pt_1.SetLineWidth(1)
        st_eff_pt_1.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_1.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_1.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_1.Print("st_eff_pt_id1_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_1.Write()

        c_pt_2 = ROOT.TCanvas('', '', 800, 650)
        c_pt_2.SetGrid()
        c_pt_2.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_2 = ROOT.TEfficiency(st_effi_passed_pt2, st_effi_total_pt)
        st_eff_pt_2.Draw("same")
        st_eff_pt_2.SetMarkerStyle(8)
        st_eff_pt_2.SetMarkerSize(1)
        st_eff_pt_2.SetMarkerColor(1)
        st_eff_pt_2.SetLineWidth(1)
        st_eff_pt_2.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_2.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_2.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_2.Print("st_eff_pt_id2_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_2.Write()

        c_pt_3 = ROOT.TCanvas('', '', 800, 650)
        c_pt_3.SetGrid()
        c_pt_3.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_3 = ROOT.TEfficiency(st_effi_passed_pt3, st_effi_total_pt)
        st_eff_pt_3.Draw("same")
        st_eff_pt_3.SetMarkerStyle(8)
        st_eff_pt_3.SetMarkerSize(1)
        st_eff_pt_3.SetMarkerColor(1)
        st_eff_pt_3.SetLineWidth(1)
        st_eff_pt_3.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_3.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_3.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_3.Print("st_eff_pt_id3_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_3.Write()

        c_pt_4 = ROOT.TCanvas('', '', 800, 650)
        c_pt_4.SetGrid()
        c_pt_4.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_4 = ROOT.TEfficiency(st_effi_passed_pt4, st_effi_total_pt)
        st_eff_pt_4.Draw("same")
        st_eff_pt_4.SetMarkerStyle(8)
        st_eff_pt_4.SetMarkerSize(1)
        st_eff_pt_4.SetMarkerColor(1)
        st_eff_pt_4.SetLineWidth(1)
        st_eff_pt_4.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_4.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_4.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_4.Print("st_eff_pt_id4_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_4.Write()

        c_pt_5 = ROOT.TCanvas('', '', 800, 650)
        c_pt_5.SetGrid()
        c_pt_5.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_5 = ROOT.TEfficiency(st_effi_passed_pt5, st_effi_total_pt)
        st_eff_pt_5.Draw("same")
        st_eff_pt_5.SetMarkerStyle(8)
        st_eff_pt_5.SetMarkerSize(1)
        st_eff_pt_5.SetMarkerColor(1)
        st_eff_pt_5.SetLineWidth(1)
        st_eff_pt_5.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_5.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_5.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_5.Print("st_eff_pt_id5_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_5.Write()

        c_pt_6 = ROOT.TCanvas('', '', 800, 650)
        c_pt_6.SetGrid()
        c_pt_6.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_6 = ROOT.TEfficiency(st_effi_passed_pt6, st_effi_total_pt)
        st_eff_pt_6.Draw("same")
        st_eff_pt_6.SetMarkerStyle(8)
        st_eff_pt_6.SetMarkerSize(1)
        st_eff_pt_6.SetMarkerColor(1)
        st_eff_pt_6.SetLineWidth(1)
        st_eff_pt_6.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_6.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_6.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_6.Print("st_eff_pt_id6_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_6.Write()

        c_pt_7 = ROOT.TCanvas('', '', 800, 650)
        c_pt_7.SetGrid()
        c_pt_7.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_7 = ROOT.TEfficiency(st_effi_passed_pt7, st_effi_total_pt)
        st_eff_pt_7.Draw("same")
        st_eff_pt_7.SetMarkerStyle(8)
        st_eff_pt_7.SetMarkerSize(1)
        st_eff_pt_7.SetMarkerColor(1)
        st_eff_pt_7.SetLineWidth(1)
        st_eff_pt_7.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_7.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_7.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_7.Print("st_eff_pt_id7_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_7.Write()

        c_pt_8 = ROOT.TCanvas('', '', 800, 650)
        c_pt_8.SetGrid()
        c_pt_8.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_8 = ROOT.TEfficiency(st_effi_passed_pt8, st_effi_total_pt)
        st_eff_pt_8.Draw("same")
        st_eff_pt_8.SetMarkerStyle(8)
        st_eff_pt_8.SetMarkerSize(1)
        st_eff_pt_8.SetMarkerColor(1)
        st_eff_pt_8.SetLineWidth(1)
        st_eff_pt_8.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_8.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_8.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_8.Print("st_eff_pt_id8_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_8.Write()

        c_pt_9 = ROOT.TCanvas('', '', 800, 650)
        c_pt_9.SetGrid()
        c_pt_9.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_9 = ROOT.TEfficiency(st_effi_passed_pt9, st_effi_total_pt)
        st_eff_pt_9.Draw("same")
        st_eff_pt_9.SetMarkerStyle(8)
        st_eff_pt_9.SetMarkerSize(1)
        st_eff_pt_9.SetMarkerColor(1)
        st_eff_pt_9.SetLineWidth(1)
        st_eff_pt_9.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_9.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_9.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_9.Print("st_eff_pt_id9_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_9.Write()

        c_pt_10 = ROOT.TCanvas('', '', 800, 650)
        c_pt_10.SetGrid()
        c_pt_10.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_10 = ROOT.TEfficiency(st_effi_passed_pt10, st_effi_total_pt)
        st_eff_pt_10.Draw("same")
        st_eff_pt_10.SetMarkerStyle(8)
        st_eff_pt_10.SetMarkerSize(1)
        st_eff_pt_10.SetMarkerColor(1)
        st_eff_pt_10.SetLineWidth(1)
        st_eff_pt_10.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_10.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_10.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_10.Print("st_eff_pt_id10_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_10.Write()

        c_pt_11 = ROOT.TCanvas('', '', 800, 650)
        c_pt_11.SetGrid()
        c_pt_11.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_11 = ROOT.TEfficiency(st_effi_passed_pt11, st_effi_total_pt)
        st_eff_pt_11.Draw("same")
        st_eff_pt_11.SetMarkerStyle(8)
        st_eff_pt_11.SetMarkerSize(1)
        st_eff_pt_11.SetMarkerColor(1)
        st_eff_pt_11.SetLineWidth(1)
        st_eff_pt_11.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_11.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_11.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_11.Print("st_eff_pt_id11_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_11.Write()

        c_pt_12 = ROOT.TCanvas('', '', 800, 650)
        c_pt_12.SetGrid()
        c_pt_12.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_12 = ROOT.TEfficiency(st_effi_passed_pt12, st_effi_total_pt)
        st_eff_pt_12.Draw("same")
        st_eff_pt_12.SetMarkerStyle(8)
        st_eff_pt_12.SetMarkerSize(1)
        st_eff_pt_12.SetMarkerColor(1)
        st_eff_pt_12.SetLineWidth(1)
        st_eff_pt_12.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_12.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_12.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_12.Print("st_eff_pt_id12_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_12.Write()

        c_pt_13 = ROOT.TCanvas('', '', 800, 650)
        c_pt_13.SetGrid()
        c_pt_13.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_13 = ROOT.TEfficiency(st_effi_passed_pt13, st_effi_total_pt)
        st_eff_pt_13.Draw("same")
        st_eff_pt_13.SetMarkerStyle(8)
        st_eff_pt_13.SetMarkerSize(1)
        st_eff_pt_13.SetMarkerColor(1)
        st_eff_pt_13.SetLineWidth(1)
        st_eff_pt_13.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_13.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_13.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_13.Print("st_eff_pt_id13_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_13.Write()

        c_pt_14 = ROOT.TCanvas('', '', 800, 650)
        c_pt_14.SetGrid()
        c_pt_14.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_14 = ROOT.TEfficiency(st_effi_passed_pt14, st_effi_total_pt)
        st_eff_pt_14.Draw("same")
        st_eff_pt_14.SetMarkerStyle(8)
        st_eff_pt_14.SetMarkerSize(1)
        st_eff_pt_14.SetMarkerColor(1)
        st_eff_pt_14.SetLineWidth(1)
        st_eff_pt_14.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_14.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_14.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_14.Print("st_eff_pt_id14_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_14.Write()

        c_pt_15 = ROOT.TCanvas('', '', 800, 650)
        c_pt_15.SetGrid()
        c_pt_15.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_15 = ROOT.TEfficiency(st_effi_passed_pt15, st_effi_total_pt)
        st_eff_pt_15.Draw("same")
        st_eff_pt_15.SetMarkerStyle(8)
        st_eff_pt_15.SetMarkerSize(1)
        st_eff_pt_15.SetMarkerColor(1)
        st_eff_pt_15.SetLineWidth(1)
        st_eff_pt_15.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_15.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_15.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_15.Print("st_eff_pt_id15_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_15.Write()

        c_pt_16 = ROOT.TCanvas('', '', 800, 650)
        c_pt_16.SetGrid()
        c_pt_16.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_16 = ROOT.TEfficiency(st_effi_passed_pt16, st_effi_total_pt)
        st_eff_pt_16.Draw("same")
        st_eff_pt_16.SetMarkerStyle(8)
        st_eff_pt_16.SetMarkerSize(1)
        st_eff_pt_16.SetMarkerColor(1)
        st_eff_pt_16.SetLineWidth(1)
        st_eff_pt_16.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_16.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_16.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_16.Print("st_eff_pt_id16_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_16.Write()

        c_pt_17 = ROOT.TCanvas('', '', 800, 650)
        c_pt_17.SetGrid()
        c_pt_17.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_17 = ROOT.TEfficiency(st_effi_passed_pt17, st_effi_total_pt)
        st_eff_pt_17.Draw("same")
        st_eff_pt_17.SetMarkerStyle(8)
        st_eff_pt_17.SetMarkerSize(1)
        st_eff_pt_17.SetMarkerColor(1)
        st_eff_pt_17.SetLineWidth(1)
        st_eff_pt_17.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_pt_17.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_pt_17.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_17.Print("st_eff_pt_id17_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_17.Write()

        c_pt_all = ROOT.TCanvas('', '', 800, 650)
        c_pt_all.SetGrid()
        c_pt_all.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_pt_1.Draw("same")
        st_eff_pt_2.Draw("same")
        st_eff_pt_3.Draw("same")
        st_eff_pt_4.Draw("same")
        st_eff_pt_5.Draw("same")
        st_eff_pt_6.Draw("same")
        st_eff_pt_7.Draw("same")
        st_eff_pt_8.Draw("same")
        st_eff_pt_9.Draw("same")
        st_eff_pt_10.Draw("same")
        st_eff_pt_11.Draw("same")
        st_eff_pt_12.Draw("same")
        st_eff_pt_13.Draw("same")
        st_eff_pt_14.Draw("same")
        st_eff_pt_15.Draw("same")
        st_eff_pt_16.Draw("same")
        st_eff_pt_17.Draw("same")

        st_eff_pt_1.SetMarkerColor(3)
        st_eff_pt_1.SetLineColor(3)
        st_eff_pt_2.SetMarkerColor(2)
        st_eff_pt_2.SetLineColor(2)
        st_eff_pt_3.SetMarkerColor(4)
        st_eff_pt_3.SetLineColor(4)
        st_eff_pt_4.SetMarkerColor(6)
        st_eff_pt_4.SetLineColor(6)
        st_eff_pt_5.SetMarkerColor(7)
        st_eff_pt_5.SetLineColor(7)
        st_eff_pt_6.SetMarkerColor(8)
        st_eff_pt_6.SetLineColor(8)
        st_eff_pt_7.SetMarkerColor(9)
        st_eff_pt_7.SetLineColor(9)
        st_eff_pt_8.SetMarkerColor(11)
        st_eff_pt_8.SetLineColor(11)
        st_eff_pt_9.SetMarkerColor(14)
        st_eff_pt_9.SetLineColor(14)
        st_eff_pt_10.SetMarkerColor(28)
        st_eff_pt_10.SetLineColor(28)
        st_eff_pt_11.SetMarkerColor(30)
        st_eff_pt_11.SetLineColor(30)
        st_eff_pt_12.SetMarkerColor(38)
        st_eff_pt_12.SetLineColor(38)
        st_eff_pt_13.SetMarkerColor(39)
        st_eff_pt_13.SetLineColor(39)
        st_eff_pt_14.SetMarkerColor(41)
        st_eff_pt_14.SetLineColor(41)
        st_eff_pt_15.SetMarkerColor(42)
        st_eff_pt_15.SetLineColor(42)
        st_eff_pt_16.SetMarkerColor(45)
        st_eff_pt_16.SetLineColor(45)
        st_eff_pt_17.SetMarkerColor(46)
        st_eff_pt_17.SetLineColor(46)
        ROOT.gPad.Update()
        leg = ROOT.TLegend(0.8,0.1,0.9,0.6)
        leg.AddEntry(st_eff_pt_1,"ID 1","l")
        leg.AddEntry(st_eff_pt_2,"ID 2","l")
        leg.AddEntry(st_eff_pt_3,"ID 3","l")
        leg.AddEntry(st_eff_pt_4,"ID 4","l")
        leg.AddEntry(st_eff_pt_5,"ID 5","l")
        leg.AddEntry(st_eff_pt_6,"ID 6","l")
        leg.AddEntry(st_eff_pt_7,"ID 7","l")
        leg.AddEntry(st_eff_pt_8,"ID 8","l")
        leg.AddEntry(st_eff_pt_9,"ID 9","l")
        leg.AddEntry(st_eff_pt_10,"ID 10","l")
        leg.AddEntry(st_eff_pt_11,"ID 11","l")
        leg.AddEntry(st_eff_pt_12,"ID 12","l")
        leg.AddEntry(st_eff_pt_13,"ID 13","l")
        leg.AddEntry(st_eff_pt_14,"ID 14","l")
        leg.AddEntry(st_eff_pt_15,"ID 15","l")
        leg.AddEntry(st_eff_pt_16,"ID 16","l")
        leg.AddEntry(st_eff_pt_17,"ID 17","l")
        leg.Draw()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_all.Print("st_eff_pt_id_all_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))

        c_pt_stacked = ROOT.TCanvas('', '', 800, 650)
        c_pt_stacked.SetGrid()
        c_pt_stacked.DrawFrame(0, 0, 50, 1.1, ";pT (GeV);Efficiency")
        st_eff_stack_pt = ROOT.THStack("st_eff_hist", "st_eff_hist")
        st_eff_hist_1 = st_effi_passed_pt1.Clone()
        st_eff_hist_1.SetName("st_eff_hist_1")
        st_eff_hist_1.Divide(st_effi_total_pt)
        st_eff_hist_2 = st_effi_passed_pt2.Clone()
        st_eff_hist_2.SetName("st_eff_hist_2")
        st_eff_hist_2.Divide(st_effi_total_pt)
        st_eff_hist_3 = st_effi_passed_pt3.Clone()
        st_eff_hist_3.SetName("st_eff_hist_3")
        st_eff_hist_3.Divide(st_effi_total_pt)
        st_eff_hist_4 = st_effi_passed_pt4.Clone()
        st_eff_hist_4.SetName("st_eff_hist_4")
        st_eff_hist_4.Divide(st_effi_total_pt)
        st_eff_hist_5 = st_effi_passed_pt5.Clone()
        st_eff_hist_5.SetName("st_eff_hist_5")
        st_eff_hist_5.Divide(st_effi_total_pt)
        st_eff_hist_6 = st_effi_passed_pt6.Clone()
        st_eff_hist_6.SetName("st_eff_hist_6")
        st_eff_hist_6.Divide(st_effi_total_pt)
        st_eff_hist_7 = st_effi_passed_pt7.Clone()
        st_eff_hist_7.SetName("st_eff_hist_7")
        st_eff_hist_7.Divide(st_effi_total_pt)
        st_eff_hist_8 = st_effi_passed_pt8.Clone()
        st_eff_hist_8.SetName("st_eff_hist_8")
        st_eff_hist_8.Divide(st_effi_total_pt)
        st_eff_hist_9 = st_effi_passed_pt9.Clone()
        st_eff_hist_9.SetName("st_eff_hist_9")
        st_eff_hist_9.Divide(st_effi_total_pt)
        st_eff_hist_10 = st_effi_passed_pt10.Clone()
        st_eff_hist_10.SetName("st_eff_hist_10")
        st_eff_hist_10.Divide(st_effi_total_pt)
        st_eff_hist_11 = st_effi_passed_pt11.Clone()
        st_eff_hist_11.SetName("st_eff_hist_11")
        st_eff_hist_11.Divide(st_effi_total_pt)
        st_eff_hist_12 = st_effi_passed_pt12.Clone()
        st_eff_hist_12.SetName("st_eff_hist_12")
        st_eff_hist_12.Divide(st_effi_total_pt)
        st_eff_hist_13 = st_effi_passed_pt13.Clone()
        st_eff_hist_13.SetName("st_eff_hist_13")
        st_eff_hist_13.Divide(st_effi_total_pt)
        st_eff_hist_14 = st_effi_passed_pt14.Clone()
        st_eff_hist_14.SetName("st_eff_hist_14")
        st_eff_hist_14.Divide(st_effi_total_pt)
        st_eff_hist_15 = st_effi_passed_pt15.Clone()
        st_eff_hist_15.SetName("st_eff_hist_15")
        st_eff_hist_15.Divide(st_effi_total_pt)
        st_eff_hist_16 = st_effi_passed_pt16.Clone()
        st_eff_hist_16.SetName("st_eff_hist_16")
        st_eff_hist_16.Divide(st_effi_total_pt)
        st_eff_hist_17 = st_effi_passed_pt17.Clone()
        st_eff_hist_17.SetName("st_eff_hist_17")
        st_eff_hist_17.Divide(st_effi_total_pt)

        st_eff_hist_1.SetFillColor(3)
        st_eff_hist_2.SetFillColor(2)
        st_eff_hist_3.SetFillColor(4)
        st_eff_hist_4.SetFillColor(6)
        st_eff_hist_5.SetFillColor(7)
        st_eff_hist_6.SetFillColor(8)
        st_eff_hist_7.SetFillColor(9)
        st_eff_hist_8.SetFillColor(11)
        st_eff_hist_9.SetFillColor(14)
        st_eff_hist_10.SetFillColor(28)
        st_eff_hist_11.SetFillColor(30)
        st_eff_hist_12.SetFillColor(38)
        st_eff_hist_13.SetFillColor(39)
        st_eff_hist_14.SetFillColor(41)
        st_eff_hist_15.SetFillColor(42)
        st_eff_hist_16.SetFillColor(45)
        st_eff_hist_17.SetFillColor(46)

        st_eff_stack_pt.Add(st_eff_hist_1)
        st_eff_stack_pt.Add(st_eff_hist_2)
        st_eff_stack_pt.Add(st_eff_hist_3)
        st_eff_stack_pt.Add(st_eff_hist_4)
        st_eff_stack_pt.Add(st_eff_hist_5)
        st_eff_stack_pt.Add(st_eff_hist_6)
        st_eff_stack_pt.Add(st_eff_hist_7)
        st_eff_stack_pt.Add(st_eff_hist_8)
        st_eff_stack_pt.Add(st_eff_hist_9)
        st_eff_stack_pt.Add(st_eff_hist_10)
        st_eff_stack_pt.Add(st_eff_hist_11)
        st_eff_stack_pt.Add(st_eff_hist_12)
        st_eff_stack_pt.Add(st_eff_hist_13)
        st_eff_stack_pt.Add(st_eff_hist_14)
        st_eff_stack_pt.Add(st_eff_hist_15)
        st_eff_stack_pt.Add(st_eff_hist_16)
        st_eff_stack_pt.Add(st_eff_hist_17)
        st_eff_stack_pt.Draw("same")
        ROOT.gPad.Update()
        leg2 = ROOT.TLegend(0.8,0.1,0.9,0.6)
        leg2.AddEntry(st_eff_hist_1,"ID 1", "f")
        leg2.AddEntry(st_eff_hist_2,"ID 2", "f")
        leg2.AddEntry(st_eff_hist_3,"ID 3", "f")
        leg2.AddEntry(st_eff_hist_4,"ID 4", "f")
        leg2.AddEntry(st_eff_hist_5,"ID 5", "f")
        leg2.AddEntry(st_eff_hist_6,"ID 6", "f")
        leg2.AddEntry(st_eff_hist_7,"ID 7", "f")
        leg2.AddEntry(st_eff_hist_8,"ID 8", "f")
        leg2.AddEntry(st_eff_hist_9,"ID 9", "f")
        leg2.AddEntry(st_eff_hist_10,"ID 10", "f")
        leg2.AddEntry(st_eff_hist_11,"ID 11", "f")
        leg2.AddEntry(st_eff_hist_12,"ID 12", "f")
        leg2.AddEntry(st_eff_hist_13,"ID 13", "f")
        leg2.AddEntry(st_eff_hist_14,"ID 14", "f")
        leg2.AddEntry(st_eff_hist_15,"ID 15", "f")
        leg2.AddEntry(st_eff_hist_16,"ID 16", "f")
        leg2.AddEntry(st_eff_hist_17,"ID 17", "f")
        leg2.Draw()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c_pt_stacked.Print("st_eff_pt_id_allstacked_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))

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

        c2d_eta_pt = ROOT.TCanvas('', '', 800, 650)
        c2d_eta_pt.SetGrid()
        c2d_eta_pt.DrawFrame(0, 0, 50, 9, ";pT (GeV);#eta Partition")
        st_eff_pt_eta = ROOT.TEfficiency(st_effi_passed_pt_eta, st_effi_total_pt_eta)
        st_eff_pt_eta.Draw("same COLZ")
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c2d_eta_pt.Print("st_eff_pt_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_pt_eta.Write()

        c6id = ROOT.TCanvas('', '', 800, 650)
        c6id.SetGrid()
        c6id.DrawFrame(0, 0, 18, 1.1, ";Pattern ID;Efficiency")
        st_eff_id = ROOT.TEfficiency(st_effi_passed_id, st_effi_total_id)
        st_eff_id.Draw("same")
        st_eff_id.SetMarkerStyle(8)
        st_eff_id.SetMarkerSize(1)
        st_eff_id.SetMarkerColor(1)
        st_eff_id.SetLineWidth(1)
        st_eff_id.SetLineColor(1)
        ROOT.gPad.Update()
        st_eff_id.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
        st_eff_id.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
        ROOT.gPad.Update()
        latex.DrawLatex(0.9, 0.91,plot_text1)
        latex.DrawLatex(0.42, 0.91,plot_text2)
        c6id.Print("st_eff_id_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
        st_eff_id.Write()

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
    c10.DrawFrame(-4, 0, 4, 1.1, ";Bending Angle (sbits/layer);Purity")
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

    c10id = ROOT.TCanvas('', '', 800, 650)
    c10id.SetGrid()
    c10id.DrawFrame(0, 0, 18, 1.1, ";Pattern ID;Purity")
    st_purity_id = ROOT.TEfficiency(st_purity_passed_id, st_purity_total_id)
    st_purity_id.Draw("same")
    st_purity_id.SetMarkerStyle(8)
    st_purity_id.SetMarkerSize(1)
    st_purity_id.SetMarkerColor(1)
    st_purity_id.SetLineWidth(1)
    st_purity_id.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_id.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_id.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c10id.Print("st_purity_id_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_id.Write()

    c9_off = ROOT.TCanvas('', '', 800, 650)
    c9_off.SetGrid()
    c9_off.DrawFrame(0, 0, 9, 1.1, ";#eta Partition;Purity")
    offline_purity_eta = ROOT.TEfficiency(offline_purity_passed_eta, offline_purity_total_eta)
    offline_purity_eta.Draw("same")
    offline_purity_eta.SetMarkerStyle(8)
    offline_purity_eta.SetMarkerSize(1)
    offline_purity_eta.SetMarkerColor(1)
    offline_purity_eta.SetLineWidth(1)
    offline_purity_eta.SetLineColor(1)
    ROOT.gPad.Update()
    offline_purity_eta.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_purity_eta.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c9_off.Print("offline_purity_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_purity_eta.Write()

    c10_off = ROOT.TCanvas('', '', 800, 650)
    c10_off.SetGrid()
    c10_off.DrawFrame(-4, 0, 4, 1.1, ";Bending Angle (sbits/layer);Purity")
    offline_purity_bending = ROOT.TEfficiency(offline_purity_passed_bending, offline_purity_total_bending)
    offline_purity_bending.Draw("same")
    offline_purity_bending.SetMarkerStyle(8)
    offline_purity_bending.SetMarkerSize(1)
    offline_purity_bending.SetMarkerColor(1)
    offline_purity_bending.SetLineWidth(1)
    offline_purity_bending.SetLineColor(1)
    ROOT.gPad.Update()
    offline_purity_bending.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_purity_bending.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c10_off.Print("offline_purity_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_purity_bending.Write()

    c10_offid = ROOT.TCanvas('', '', 800, 650)
    c10_offid.SetGrid()
    c10_offid.DrawFrame(0, 0, 18, 1.1, ";Pattern ID;Purity")
    offline_purity_id = ROOT.TEfficiency(offline_purity_passed_id, offline_purity_total_id)
    offline_purity_id.Draw("same")
    offline_purity_id.SetMarkerStyle(8)
    offline_purity_id.SetMarkerSize(1)
    offline_purity_id.SetMarkerColor(1)
    offline_purity_id.SetLineWidth(1)
    offline_purity_id.SetLineColor(1)
    ROOT.gPad.Update()
    offline_purity_id.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    offline_purity_id.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c10_offid.Print("offline_purity_id_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    offline_purity_id.Write()

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

    c13a = ROOT.TCanvas('', '', 800, 650)
    c13a.SetGrid()
    num_bkg_seg_per_chamber_per_event_eta.SetStats(False)
    num_bkg_seg_per_chamber_per_event_eta.SetTitle("")
    num_bkg_seg_per_chamber_per_event_eta.SetXTitle("#eta Partition")
    num_bkg_seg_per_chamber_per_event_eta.SetYTitle("Nr. of Fakes per Chamber per BX")
    num_bkg_seg_per_chamber_per_event_eta.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_eta.Draw("same HE")
    num_bkg_seg_per_chamber_per_event_eta.SetMarkerStyle(8)
    num_bkg_seg_per_chamber_per_event_eta.SetMarkerSize(1)
    num_bkg_seg_per_chamber_per_event_eta.SetMarkerColor(1)
    num_bkg_seg_per_chamber_per_event_eta.SetLineWidth(1)
    num_bkg_seg_per_chamber_per_event_eta.SetLineColor(1)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c13a.Print("num_bkg_seg_per_chamber_per_event_eta_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_bkg_seg_per_chamber_per_event_eta.Write()

    c13b = ROOT.TCanvas('', '', 800, 650)
    c13b.SetGrid()
    num_bkg_seg_per_chamber_per_event_bending.SetStats(False)
    num_bkg_seg_per_chamber_per_event_bending.SetTitle("")
    num_bkg_seg_per_chamber_per_event_bending.SetXTitle("Bending Angle (sbits/layer)")
    num_bkg_seg_per_chamber_per_event_bending.SetYTitle("Nr. of Fakes per Chamber per BX")
    num_bkg_seg_per_chamber_per_event_bending.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending.Draw("same HE")
    num_bkg_seg_per_chamber_per_event_bending.SetMarkerStyle(8)
    num_bkg_seg_per_chamber_per_event_bending.SetMarkerSize(1)
    num_bkg_seg_per_chamber_per_event_bending.SetMarkerColor(1)
    num_bkg_seg_per_chamber_per_event_bending.SetLineWidth(1)
    num_bkg_seg_per_chamber_per_event_bending.SetLineColor(1)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c13b.Print("num_bkg_seg_per_chamber_per_event_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_bkg_seg_per_chamber_per_event_bending.Write()

    c13c = ROOT.TCanvas('', '', 800, 650)
    c13c.SetGrid()
    c13c.DrawFrame(-4, 0, 4, 1.1*num_bkg_seg_per_chamber_per_event_bending.GetMaximum(), ";Bending Angle (sbits/layer);Nr. of Fakes per Chamber per BX")
    num_bkg_seg_per_chamber_per_event_bending_stack = ROOT.THStack("num_bkg_seg_per_chamber_per_event_bending_stack", "num_bkg_seg_per_chamber_per_event_bending_stack")
    num_bkg_seg_per_chamber_per_event_bending1.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending2.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending3.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending4.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending5.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending6.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending7.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending8.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending9.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending10.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending11.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending12.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending13.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending14.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending15.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending16.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending17.Scale(1/(36.0*n_total_events))
    num_bkg_seg_per_chamber_per_event_bending1.SetFillColor(3)
    num_bkg_seg_per_chamber_per_event_bending2.SetFillColor(2)
    num_bkg_seg_per_chamber_per_event_bending3.SetFillColor(4)
    num_bkg_seg_per_chamber_per_event_bending4.SetFillColor(6)
    num_bkg_seg_per_chamber_per_event_bending5.SetFillColor(7)
    num_bkg_seg_per_chamber_per_event_bending6.SetFillColor(8)
    num_bkg_seg_per_chamber_per_event_bending7.SetFillColor(9)
    num_bkg_seg_per_chamber_per_event_bending8.SetFillColor(11)
    num_bkg_seg_per_chamber_per_event_bending9.SetFillColor(14)
    num_bkg_seg_per_chamber_per_event_bending10.SetFillColor(28)
    num_bkg_seg_per_chamber_per_event_bending11.SetFillColor(30)
    num_bkg_seg_per_chamber_per_event_bending12.SetFillColor(38)
    num_bkg_seg_per_chamber_per_event_bending13.SetFillColor(39)
    num_bkg_seg_per_chamber_per_event_bending14.SetFillColor(41)
    num_bkg_seg_per_chamber_per_event_bending15.SetFillColor(42)
    num_bkg_seg_per_chamber_per_event_bending16.SetFillColor(45)
    num_bkg_seg_per_chamber_per_event_bending17.SetFillColor(46)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending1)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending2)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending3)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending4)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending5)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending6)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending7)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending8)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending9)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending10)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending11)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending12)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending13)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending14)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending15)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending16)
    num_bkg_seg_per_chamber_per_event_bending_stack.Add(num_bkg_seg_per_chamber_per_event_bending17)
    num_bkg_seg_per_chamber_per_event_bending_stack.Draw("same HE")
    ROOT.gPad.Update()
    leg13c = ROOT.TLegend(0.8,0.1,0.9,0.6)
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending1,"ID 1", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending2,"ID 2", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending3,"ID 3", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending4,"ID 4", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending5,"ID 5", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending6,"ID 6", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending7,"ID 7", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending8,"ID 8", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending9,"ID 9", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending10,"ID 10", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending11,"ID 11", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending12,"ID 12", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending13,"ID 13", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending14,"ID 14", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending15,"ID 15", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending16,"ID 16", "f")
    leg13c.AddEntry(num_bkg_seg_per_chamber_per_event_bending17,"ID 17", "f")
    leg13c.Draw()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c13c.Print("num_bkg_seg_per_chamber_per_event_bending_stacked_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_bkg_seg_per_chamber_per_event_bending1.Write()
    num_bkg_seg_per_chamber_per_event_bending2.Write()
    num_bkg_seg_per_chamber_per_event_bending3.Write()
    num_bkg_seg_per_chamber_per_event_bending4.Write()
    num_bkg_seg_per_chamber_per_event_bending5.Write()
    num_bkg_seg_per_chamber_per_event_bending6.Write()
    num_bkg_seg_per_chamber_per_event_bending7.Write()
    num_bkg_seg_per_chamber_per_event_bending8.Write()
    num_bkg_seg_per_chamber_per_event_bending9.Write()
    num_bkg_seg_per_chamber_per_event_bending10.Write()
    num_bkg_seg_per_chamber_per_event_bending11.Write()
    num_bkg_seg_per_chamber_per_event_bending12.Write()
    num_bkg_seg_per_chamber_per_event_bending13.Write()
    num_bkg_seg_per_chamber_per_event_bending14.Write()
    num_bkg_seg_per_chamber_per_event_bending15.Write()
    num_bkg_seg_per_chamber_per_event_bending16.Write()
    num_bkg_seg_per_chamber_per_event_bending17.Write()

    c13d = ROOT.TCanvas('', '', 800, 650)
    c13d.SetGrid()
    num_signal_seg_per_chamber_per_event_bending.SetStats(False)
    num_signal_seg_per_chamber_per_event_bending.SetTitle("")
    num_signal_seg_per_chamber_per_event_bending.SetXTitle("Bending Angle (sbits/layer)")
    num_signal_seg_per_chamber_per_event_bending.SetYTitle("Nr. of Signal Segments per Chamber per BX")
    num_signal_seg_per_chamber_per_event_bending.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending.Draw("same HE")
    num_signal_seg_per_chamber_per_event_bending.SetMarkerStyle(8)
    num_signal_seg_per_chamber_per_event_bending.SetMarkerSize(1)
    num_signal_seg_per_chamber_per_event_bending.SetMarkerColor(1)
    num_signal_seg_per_chamber_per_event_bending.SetLineWidth(1)
    num_signal_seg_per_chamber_per_event_bending.SetLineColor(1)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c13d.Print("num_signal_seg_per_chamber_per_event_bending_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_signal_seg_per_chamber_per_event_bending.Write()

    c13e = ROOT.TCanvas('', '', 800, 650)
    c13e.SetGrid()
    c13e.DrawFrame(-2, 0, 2, 1.1*num_signal_seg_per_chamber_per_event_bending.GetMaximum(), ";Bending Angle (sbits/layer);Nr. of Signal Segments per Chamber per BX")
    num_signal_seg_per_chamber_per_event_bending_stack = ROOT.THStack("num_signal_seg_per_chamber_per_event_bending_stack", "num_signal_seg_per_chamber_per_event_bending_stack")
    num_signal_seg_per_chamber_per_event_bending1.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending2.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending3.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending4.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending5.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending6.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending7.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending8.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending9.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending10.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending11.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending12.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending13.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending14.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending15.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending16.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending17.Scale(1/(36.0*n_total_events))
    num_signal_seg_per_chamber_per_event_bending1.SetFillColor(3)
    num_signal_seg_per_chamber_per_event_bending2.SetFillColor(2)
    num_signal_seg_per_chamber_per_event_bending3.SetFillColor(4)
    num_signal_seg_per_chamber_per_event_bending4.SetFillColor(6)
    num_signal_seg_per_chamber_per_event_bending5.SetFillColor(7)
    num_signal_seg_per_chamber_per_event_bending6.SetFillColor(8)
    num_signal_seg_per_chamber_per_event_bending7.SetFillColor(9)
    num_signal_seg_per_chamber_per_event_bending8.SetFillColor(11)
    num_signal_seg_per_chamber_per_event_bending9.SetFillColor(14)
    num_signal_seg_per_chamber_per_event_bending10.SetFillColor(28)
    num_signal_seg_per_chamber_per_event_bending11.SetFillColor(30)
    num_signal_seg_per_chamber_per_event_bending12.SetFillColor(38)
    num_signal_seg_per_chamber_per_event_bending13.SetFillColor(39)
    num_signal_seg_per_chamber_per_event_bending14.SetFillColor(41)
    num_signal_seg_per_chamber_per_event_bending15.SetFillColor(42)
    num_signal_seg_per_chamber_per_event_bending16.SetFillColor(45)
    num_signal_seg_per_chamber_per_event_bending17.SetFillColor(46)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending1)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending2)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending3)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending4)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending5)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending6)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending7)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending8)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending9)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending10)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending11)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending12)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending13)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending14)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending15)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending16)
    num_signal_seg_per_chamber_per_event_bending_stack.Add(num_signal_seg_per_chamber_per_event_bending17)
    num_signal_seg_per_chamber_per_event_bending_stack.Draw("same HE")
    ROOT.gPad.Update()
    leg13e = ROOT.TLegend(0.8,0.1,0.9,0.6)
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending1,"ID 1", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending2,"ID 2", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending3,"ID 3", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending4,"ID 4", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending5,"ID 5", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending6,"ID 6", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending7,"ID 7", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending8,"ID 8", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending9,"ID 9", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending10,"ID 10", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending11,"ID 11", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending12,"ID 12", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending13,"ID 13", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending14,"ID 14", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending15,"ID 15", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending16,"ID 16", "f")
    leg13e.AddEntry(num_signal_seg_per_chamber_per_event_bending17,"ID 17", "f")
    leg13e.Draw()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c13e.Print("num_signal_seg_per_chamber_per_event_bending_stacked_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    num_signal_seg_per_chamber_per_event_bending1.Write()
    num_signal_seg_per_chamber_per_event_bending2.Write()
    num_signal_seg_per_chamber_per_event_bending3.Write()
    num_signal_seg_per_chamber_per_event_bending4.Write()
    num_signal_seg_per_chamber_per_event_bending5.Write()
    num_signal_seg_per_chamber_per_event_bending6.Write()
    num_signal_seg_per_chamber_per_event_bending7.Write()
    num_signal_seg_per_chamber_per_event_bending8.Write()
    num_signal_seg_per_chamber_per_event_bending9.Write()
    num_signal_seg_per_chamber_per_event_bending10.Write()
    num_signal_seg_per_chamber_per_event_bending11.Write()
    num_signal_seg_per_chamber_per_event_bending12.Write()
    num_signal_seg_per_chamber_per_event_bending13.Write()
    num_signal_seg_per_chamber_per_event_bending14.Write()
    num_signal_seg_per_chamber_per_event_bending15.Write()
    num_signal_seg_per_chamber_per_event_bending16.Write()
    num_signal_seg_per_chamber_per_event_bending17.Write()

    cg = ROOT.TCanvas('', '', 800, 650)
    cg.SetGrid()
    cg.DrawFrame(-2, 0, 2, 200, ";Bending Angle (sbits/layer);pT (GeV)")
    online_seg_sim_track_matched_pt = [float(x) for x in online_seg_sim_track_matched_pt]
    online_seg_sim_track_matched_bending_angle = [float(x) for x in online_seg_sim_track_matched_bending_angle]
    st_pt_bending_total = ROOT.TGraph(len(online_seg_sim_track_matched_bending_angle), array('d', online_seg_sim_track_matched_bending_angle), array('d', online_seg_sim_track_matched_pt))
    st_pt_bending_total.SetStats(False)
    st_pt_bending_total.SetTitle("")
    st_pt_bending_total.GetXaxis().SetTitle("Bending Angle (sbits/layer)")
    st_pt_bending_total.GetYaxis().SetTitle("pT (GeV)")
    st_pt_bending_total.Draw("same P")
    st_pt_bending_total.SetMarkerStyle(8)
    st_pt_bending_total.SetMarkerSize(1)
    st_pt_bending_total.SetMarkerColor(1)
    st_pt_bending_total.SetLineWidth(1)
    st_pt_bending_total.SetLineColor(1)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    cg.Print("sim_track_pt_vs_bending_angle_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_pt_bending_total.Write()

    '''
    c_max_cluster_size_p = ROOT.TCanvas('', '', 800, 650)
    c_max_cluster_size_p.SetGrid()
    c_max_cluster_size_p.DrawFrame(0, 0, 38, 1.1, ";Max Cluster Size;Purity")
    st_purity_max_cluster_size = ROOT.TEfficiency(st_purity_passed_max_cluster_size, st_purity_total_max_cluster_size)
    st_purity_max_cluster_size.Draw("same")
    st_purity_max_cluster_size.SetMarkerStyle(8)
    st_purity_max_cluster_size.SetMarkerSize(1)
    st_purity_max_cluster_size.SetMarkerColor(1)
    st_purity_max_cluster_size.SetLineWidth(1)
    st_purity_max_cluster_size.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_max_cluster_size.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_max_cluster_size.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_max_cluster_size_p.Print("st_purity_max_cluster_size_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_max_cluster_size.Write()

    c_max_noise_p = ROOT.TCanvas('', '', 800, 650)
    c_max_noise_p.SetGrid()
    c_max_noise_p.DrawFrame(0, 0, 38, 1.1, ";Max Noise;Purity")
    st_purity_max_noise = ROOT.TEfficiency(st_purity_passed_max_noise, st_purity_total_max_noise)
    st_purity_max_noise.Draw("same")
    st_purity_max_noise.SetMarkerStyle(8)
    st_purity_max_noise.SetMarkerSize(1)
    st_purity_max_noise.SetMarkerColor(1)
    st_purity_max_noise.SetLineWidth(1)
    st_purity_max_noise.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_max_noise.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_max_noise.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_max_noise_p.Print("st_purity_max_noise_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_max_noise.Write()

    c_nlayers_withcsg3_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg3_p.SetGrid()
    c_nlayers_withcsg3_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withcsg3 = ROOT.TEfficiency(st_purity_passed_nlayers_withcsg3, st_purity_total_nlayers_withcsg3)
    st_purity_nlayers_withcsg3.Draw("same")
    st_purity_nlayers_withcsg3.SetMarkerStyle(8)
    st_purity_nlayers_withcsg3.SetMarkerSize(1)
    st_purity_nlayers_withcsg3.SetMarkerColor(1)
    st_purity_nlayers_withcsg3.SetLineWidth(1)
    st_purity_nlayers_withcsg3.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withcsg3.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withcsg3.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg3_p.Print("st_purity_nlayers_withcsg3_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withcsg3.Write()

    c_nlayers_withcsg5_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg5_p.SetGrid()
    c_nlayers_withcsg5_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withcsg5 = ROOT.TEfficiency(st_purity_passed_nlayers_withcsg5, st_purity_total_nlayers_withcsg5)
    st_purity_nlayers_withcsg5.Draw("same")
    st_purity_nlayers_withcsg5.SetMarkerStyle(8)
    st_purity_nlayers_withcsg5.SetMarkerSize(1)
    st_purity_nlayers_withcsg5.SetMarkerColor(1)
    st_purity_nlayers_withcsg5.SetLineWidth(1)
    st_purity_nlayers_withcsg5.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withcsg5.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withcsg5.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg5_p.Print("st_purity_nlayers_withcsg5_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withcsg5.Write()

    c_nlayers_withcsg10_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg10_p.SetGrid()
    c_nlayers_withcsg10_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withcsg10 = ROOT.TEfficiency(st_purity_passed_nlayers_withcsg10, st_purity_total_nlayers_withcsg10)
    st_purity_nlayers_withcsg10.Draw("same")
    st_purity_nlayers_withcsg10.SetMarkerStyle(8)
    st_purity_nlayers_withcsg10.SetMarkerSize(1)
    st_purity_nlayers_withcsg10.SetMarkerColor(1)
    st_purity_nlayers_withcsg10.SetLineWidth(1)
    st_purity_nlayers_withcsg10.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withcsg10.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withcsg10.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg10_p.Print("st_purity_nlayers_withcsg10_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withcsg10.Write()

    c_nlayers_withcsg15_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg15_p.SetGrid()
    c_nlayers_withcsg15_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layerse;Purity")
    st_purity_nlayers_withcsg15 = ROOT.TEfficiency(st_purity_passed_nlayers_withcsg15, st_purity_total_nlayers_withcsg15)
    st_purity_nlayers_withcsg15.Draw("same")
    st_purity_nlayers_withcsg15.SetMarkerStyle(8)
    st_purity_nlayers_withcsg15.SetMarkerSize(1)
    st_purity_nlayers_withcsg15.SetMarkerColor(1)
    st_purity_nlayers_withcsg15.SetLineWidth(1)
    st_purity_nlayers_withcsg15.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withcsg15.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withcsg15.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg15_p.Print("st_purity_nlayers_withcsg15_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withcsg15.Write()

    c_nlayers_withnoiseg3_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg3_p.SetGrid()
    c_nlayers_withnoiseg3_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withnoiseg3 = ROOT.TEfficiency(st_purity_passed_nlayers_withnoiseg3, st_purity_total_nlayers_withnoiseg3)
    st_purity_nlayers_withnoiseg3.Draw("same")
    st_purity_nlayers_withnoiseg3.SetMarkerStyle(8)
    st_purity_nlayers_withnoiseg3.SetMarkerSize(1)
    st_purity_nlayers_withnoiseg3.SetMarkerColor(1)
    st_purity_nlayers_withnoiseg3.SetLineWidth(1)
    st_purity_nlayers_withnoiseg3.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withnoiseg3.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withnoiseg3.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg3_p.Print("st_purity_nlayers_withnoiseg3_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withnoiseg3.Write()

    c_nlayers_withnoiseg5_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg5_p.SetGrid()
    c_nlayers_withnoiseg5_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withnoiseg5 = ROOT.TEfficiency(st_purity_passed_nlayers_withnoiseg5, st_purity_total_nlayers_withnoiseg5)
    st_purity_nlayers_withnoiseg5.Draw("same")
    st_purity_nlayers_withnoiseg5.SetMarkerStyle(8)
    st_purity_nlayers_withnoiseg5.SetMarkerSize(1)
    st_purity_nlayers_withnoiseg5.SetMarkerColor(1)
    st_purity_nlayers_withnoiseg5.SetLineWidth(1)
    st_purity_nlayers_withnoiseg5.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withnoiseg5.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withnoiseg5.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg5_p.Print("st_purity_nlayers_withnoiseg5_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withnoiseg5.Write()

    c_nlayers_withnoiseg10_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg10_p.SetGrid()
    c_nlayers_withnoiseg10_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Purity")
    st_purity_nlayers_withnoiseg10 = ROOT.TEfficiency(st_purity_passed_nlayers_withnoiseg10, st_purity_total_nlayers_withnoiseg10)
    st_purity_nlayers_withnoiseg10.Draw("same")
    st_purity_nlayers_withnoiseg10.SetMarkerStyle(8)
    st_purity_nlayers_withnoiseg10.SetMarkerSize(1)
    st_purity_nlayers_withnoiseg10.SetMarkerColor(1)
    st_purity_nlayers_withnoiseg10.SetLineWidth(1)
    st_purity_nlayers_withnoiseg10.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withnoiseg10.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withnoiseg10.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg10_p.Print("st_purity_nlayers_withnoiseg10_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withnoiseg10.Write()

    c_nlayers_withnoiseg15_p = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg15_p.SetGrid()
    c_nlayers_withnoiseg15_p.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layerse;Purity")
    st_purity_nlayers_withnoiseg15 = ROOT.TEfficiency(st_purity_passed_nlayers_withnoiseg15, st_purity_total_nlayers_withnoiseg15)
    st_purity_nlayers_withnoiseg15.Draw("same")
    st_purity_nlayers_withnoiseg15.SetMarkerStyle(8)
    st_purity_nlayers_withnoiseg15.SetMarkerSize(1)
    st_purity_nlayers_withnoiseg15.SetMarkerColor(1)
    st_purity_nlayers_withnoiseg15.SetLineWidth(1)
    st_purity_nlayers_withnoiseg15.SetLineColor(1)
    ROOT.gPad.Update()
    st_purity_nlayers_withnoiseg15.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_purity_nlayers_withnoiseg15.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg15_p.Print("st_purity_nlayers_withnoiseg15_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_purity_nlayers_withnoiseg15.Write()







    c_max_cluster_size_e = ROOT.TCanvas('', '', 800, 650)
    c_max_cluster_size_e.SetGrid()
    c_max_cluster_size_e.DrawFrame(0, 0, 38, 1.1, ";Max Cluster Size;Efficiency")
    st_effi_max_cluster_size = ROOT.TEfficiency(st_effi_passed_max_cluster_size, st_effi_total_max_cluster_size)
    st_effi_max_cluster_size.Draw("same")
    st_effi_max_cluster_size.SetMarkerStyle(8)
    st_effi_max_cluster_size.SetMarkerSize(1)
    st_effi_max_cluster_size.SetMarkerColor(1)
    st_effi_max_cluster_size.SetLineWidth(1)
    st_effi_max_cluster_size.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_max_cluster_size.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_max_cluster_size.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_max_cluster_size_e.Print("st_effi_max_cluster_size_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_max_cluster_size.Write()

    c_max_noise_e = ROOT.TCanvas('', '', 800, 650)
    c_max_noise_e.SetGrid()
    c_max_noise_e.DrawFrame(0, 0, 38, 1.1, ";Max Noise;Efficiency")
    st_effi_max_noise = ROOT.TEfficiency(st_effi_passed_max_noise, st_effi_total_max_noise)
    st_effi_max_noise.Draw("same")
    st_effi_max_noise.SetMarkerStyle(8)
    st_effi_max_noise.SetMarkerSize(1)
    st_effi_max_noise.SetMarkerColor(1)
    st_effi_max_noise.SetLineWidth(1)
    st_effi_max_noise.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_max_noise.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_max_noise.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_max_noise_e.Print("st_effi_max_noise_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_max_noise.Write()

    c_nlayers_withcsg3_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg3_e.SetGrid()
    c_nlayers_withcsg3_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withcsg3 = ROOT.TEfficiency(st_effi_passed_nlayers_withcsg3, st_effi_total_nlayers_withcsg3)
    st_effi_nlayers_withcsg3.Draw("same")
    st_effi_nlayers_withcsg3.SetMarkerStyle(8)
    st_effi_nlayers_withcsg3.SetMarkerSize(1)
    st_effi_nlayers_withcsg3.SetMarkerColor(1)
    st_effi_nlayers_withcsg3.SetLineWidth(1)
    st_effi_nlayers_withcsg3.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withcsg3.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withcsg3.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg3_e.Print("st_effi_nlayers_withcsg3_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withcsg3.Write()

    c_nlayers_withcsg5_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg5_e.SetGrid()
    c_nlayers_withcsg5_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withcsg5 = ROOT.TEfficiency(st_effi_passed_nlayers_withcsg5, st_effi_total_nlayers_withcsg5)
    st_effi_nlayers_withcsg5.Draw("same")
    st_effi_nlayers_withcsg5.SetMarkerStyle(8)
    st_effi_nlayers_withcsg5.SetMarkerSize(1)
    st_effi_nlayers_withcsg5.SetMarkerColor(1)
    st_effi_nlayers_withcsg5.SetLineWidth(1)
    st_effi_nlayers_withcsg5.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withcsg5.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withcsg5.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg5_e.Print("st_effi_nlayers_withcsg5_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withcsg5.Write()

    c_nlayers_withcsg10_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg10_e.SetGrid()
    c_nlayers_withcsg10_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withcsg10 = ROOT.TEfficiency(st_effi_passed_nlayers_withcsg10, st_effi_total_nlayers_withcsg10)
    st_effi_nlayers_withcsg10.Draw("same")
    st_effi_nlayers_withcsg10.SetMarkerStyle(8)
    st_effi_nlayers_withcsg10.SetMarkerSize(1)
    st_effi_nlayers_withcsg10.SetMarkerColor(1)
    st_effi_nlayers_withcsg10.SetLineWidth(1)
    st_effi_nlayers_withcsg10.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withcsg10.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withcsg10.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg10_e.Print("st_effi_nlayers_withcsg10_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withcsg10.Write()

    c_nlayers_withcsg15_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withcsg15_e.SetGrid()
    c_nlayers_withcsg15_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layerse;Efficiency")
    st_effi_nlayers_withcsg15 = ROOT.TEfficiency(st_effi_passed_nlayers_withcsg15, st_effi_total_nlayers_withcsg15)
    st_effi_nlayers_withcsg15.Draw("same")
    st_effi_nlayers_withcsg15.SetMarkerStyle(8)
    st_effi_nlayers_withcsg15.SetMarkerSize(1)
    st_effi_nlayers_withcsg15.SetMarkerColor(1)
    st_effi_nlayers_withcsg15.SetLineWidth(1)
    st_effi_nlayers_withcsg15.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withcsg15.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withcsg15.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withcsg15_e.Print("st_effi_nlayers_withcsg15_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withcsg15.Write()

    c_nlayers_withnoiseg3_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg3_e.SetGrid()
    c_nlayers_withnoiseg3_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withnoiseg3 = ROOT.TEfficiency(st_effi_passed_nlayers_withnoiseg3, st_effi_total_nlayers_withnoiseg3)
    st_effi_nlayers_withnoiseg3.Draw("same")
    st_effi_nlayers_withnoiseg3.SetMarkerStyle(8)
    st_effi_nlayers_withnoiseg3.SetMarkerSize(1)
    st_effi_nlayers_withnoiseg3.SetMarkerColor(1)
    st_effi_nlayers_withnoiseg3.SetLineWidth(1)
    st_effi_nlayers_withnoiseg3.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withnoiseg3.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withnoiseg3.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg3_e.Print("st_effi_nlayers_withnoiseg3_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withnoiseg3.Write()

    c_nlayers_withnoiseg5_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg5_e.SetGrid()
    c_nlayers_withnoiseg5_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withnoiseg5 = ROOT.TEfficiency(st_effi_passed_nlayers_withnoiseg5, st_effi_total_nlayers_withnoiseg5)
    st_effi_nlayers_withnoiseg5.Draw("same")
    st_effi_nlayers_withnoiseg5.SetMarkerStyle(8)
    st_effi_nlayers_withnoiseg5.SetMarkerSize(1)
    st_effi_nlayers_withnoiseg5.SetMarkerColor(1)
    st_effi_nlayers_withnoiseg5.SetLineWidth(1)
    st_effi_nlayers_withnoiseg5.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withnoiseg5.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withnoiseg5.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg5_e.Print("st_effi_nlayers_withnoiseg5_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withnoiseg5.Write()

    c_nlayers_withnoiseg10_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg10_e.SetGrid()
    c_nlayers_withnoiseg10_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layers;Efficiency")
    st_effi_nlayers_withnoiseg10 = ROOT.TEfficiency(st_effi_passed_nlayers_withnoiseg10, st_effi_total_nlayers_withnoiseg10)
    st_effi_nlayers_withnoiseg10.Draw("same")
    st_effi_nlayers_withnoiseg10.SetMarkerStyle(8)
    st_effi_nlayers_withnoiseg10.SetMarkerSize(1)
    st_effi_nlayers_withnoiseg10.SetMarkerColor(1)
    st_effi_nlayers_withnoiseg10.SetLineWidth(1)
    st_effi_nlayers_withnoiseg10.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withnoiseg10.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withnoiseg10.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg10_e.Print("st_effi_nlayers_withnoiseg10_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withnoiseg10.Write()

    c_nlayers_withnoiseg15_e = ROOT.TCanvas('', '', 800, 650)
    c_nlayers_withnoiseg15_e.SetGrid()
    c_nlayers_withnoiseg15_e.DrawFrame(0, 0, 7, 1.1, ";Nr. of Layerse;Efficiency")
    st_effi_nlayers_withnoiseg15 = ROOT.TEfficiency(st_effi_passed_nlayers_withnoiseg15, st_effi_total_nlayers_withnoiseg15)
    st_effi_nlayers_withnoiseg15.Draw("same")
    st_effi_nlayers_withnoiseg15.SetMarkerStyle(8)
    st_effi_nlayers_withnoiseg15.SetMarkerSize(1)
    st_effi_nlayers_withnoiseg15.SetMarkerColor(1)
    st_effi_nlayers_withnoiseg15.SetLineWidth(1)
    st_effi_nlayers_withnoiseg15.SetLineColor(1)
    ROOT.gPad.Update()
    st_effi_nlayers_withnoiseg15.GetPaintedGraph().GetYaxis().SetLabelSize(0.04)
    st_effi_nlayers_withnoiseg15.GetPaintedGraph().GetXaxis().SetLabelSize(0.04)
    ROOT.gPad.Update()
    latex.DrawLatex(0.9, 0.91,plot_text1)
    latex.DrawLatex(0.42, 0.91,plot_text2)
    c_nlayers_withnoiseg15_e.Print("st_effi_nlayers_withnoiseg15_%s_bx%s_crosspart_%s_or%d.pdf"%(hits, bx, cross_part, num_or))
    st_effi_nlayers_withnoiseg15.Write()
    '''

    file_out.close()
    file_out_summary.close()
    plot_file.Close()

    #plt.hist(mse_collections)
    #plt.savefig('./mse_histogram.png')
    #print(seg_bx_collections)
    plt.hist(seg_bx_collections)
    plt.savefig('./seg_bx_collections.png')

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
    parser.add_argument("-n", "--nevents", action="store", dest="nevents", default = "all", help="Nr. of events to analyze")
    parser.add_argument("-o", "--num_or", action="store", dest="num_or", default = "2", help="number of strips that are OR-ed together")
    args = parser.parse_args()

    # read in the data
    if args.nevents == "all":
        root_dat = read_ntuple(args.file_path)
    else:
        root_dat = read_ntuple(args.file_path, 0, int(args.nevents))

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
