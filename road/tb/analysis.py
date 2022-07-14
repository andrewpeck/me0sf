#!/usr/bin/env python3
import uproot
import event_display as disp
from subfunc import *
from chamber_beh import process_chamber

with uproot.open("MuonGE0Segments.root:ge0/segments") as segments:
    print(segments.keys())

    events = segments.arrays(["strip", "ly", "chamber", "partition"],

                             aliases={"strip": "floor(me0_rec_hit_strip/2.0)",
                                      "ly": "me0_rec_hit_layer-1",
                                      "chamber": "me0_rec_hit_chamber",
                                      "partition": "me0_rec_hit_eta_partition-1",
                                      })

    for (ievent, event) in enumerate(events):
        print(ievent)
        layers = [[0]*6 for n in range(8)]
        for (ly, strip, partition, chamber) in zip(event["ly"], event["strip"], event["partition"], event["chamber"]):
            #print(f'{partition=}')
        
            if (chamber==4):
                layers[partition][int(ly)] |= 1 << int(strip)

        pats = [(PATLIST[15-seg.id], seg.strip, seg.partition) for seg in process_chamber(layers) if seg.id !=0]
        
        for i in range(len(layers)):
            pat = [(p[0], p[1]) for p in pats if p[2] == i]
            disp.event_display(hits=layers[i], pats=pat)