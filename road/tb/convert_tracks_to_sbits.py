import uproot
import sys

from printly_dat import printly_dat
import get_sbits_from_root as sfr

def read_stack_tracks(file_path, entry_start=None, entry_stop=None):
    with uproot.open(file_path + ":trackTree") as tracks:

        # print("read all: ", tracks.keys())
        
        events = tracks.arrays(tracks.keys(), entry_start=entry_start, entry_stop=entry_stop)

        return events

BL = 574.8
BS = 235.2
H = 787.9
LY_GAP = 35 # mm/ly

def get_width_from_y(y):
    return BL - (y*(BL-BS))/H

def get_sbits_from_track(track):
        x0 = track["trackInterceptX"]
        y0 = track["trackInterceptY"]
        x_slope = track["trackSlopeX"]
        y_slope = track["trackSlopeY"]

        y0_shift_mm = H/2.0 - y0 
        y_proj_mm = [y0_shift_mm - ly*LY_GAP*y_slope for ly in range(6)]

        y_proj_eta = [round(y_proj_mm[ly]*8.0/H - 0.5) for ly in range(6)]
        print(f"Projected Etas: {y_proj_eta}")

        x_widths = [get_width_from_y(y_proj_mm[ly]) for ly in range(6)]

        x0_shift_mm = x_widths[0]/2.0 - x0
        x_proj_mm = [x0_shift_mm - ly*LY_GAP*x_slope for ly in range(6)]

        x_proj_strip = [round(x_proj_mm[ly]*191/x_widths[ly]) for ly in range(6)]
        print(f"Projected Strips: {x_proj_strip}")
 
        return (x_proj_strip, y_proj_eta)

def format_seg(hits_strip, hits_eta):
    hits_display = [[0 for _ in range(6)] for _ in range (8)]
    for ly in range(6):
        if not (hits_strip[ly] > 191 or hits_strip[ly] < 0):
            hits_display[hits_eta[ly]][ly] = 2**(191-hits_strip[ly])
    return hits_display

if __name__ == "__main__":
    
    tracks = read_stack_tracks("tracks_1030.root")
    #tracks = read_stack_tracks("stack_testdata_tracks.root")

    params = ("trackInterceptX", "trackInterceptY", "trackSlopeX", "trackSlopeY")

    #sbits_root = sfr.read_ntuple_stack("00001199.root")
    sbits_root = sfr.read_ntuple_stack("digi_1030.root")

    for i in range(11, 14):
        print(f"\n\n\nEVENT {i}")
        
        sbits_ev = sfr.get_sbits_from_event(sbits_root[i])

        for param in params:
            print(param + ": " + str(tracks[i][param]))

        hits_strip, hits_eta = get_sbits_from_track(tracks[i])

        hits_display = format_seg(hits_strip, hits_eta)

        for prt in range(8):
            print(f"Partition: {prt}")
            printly_dat(mask=hits_display[prt], data=sbits_ev[prt], MAX_SPAN=192)
