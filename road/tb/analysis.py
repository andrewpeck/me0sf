#!/usr/bin/env python3
import uproot
import event_display as disp
from subfunc import *
from chamber_beh import process_chamber

with uproot.open("MuonGE0Segments_1.root:ge0/segments") as segments:
    print(segments.keys())

    events = segments.arrays(["strip", "ly", "chamber", "partition"],

                             aliases={"strip": "floor(me0_rec_hit_strip/2.0)",
                                      "ly": "me0_rec_hit_layer-1",
                                      "chamber": "me0_rec_hit_chamber",
                                      "partition": "me0_rec_hit_eta_partition-1",
                                      })

    for (ievent, event) in enumerate(events):
        for j in range(1, 19):
            layers = [[0]*6 for n in range(8)]
            for (ly, strip, partition, chamber) in zip(event["ly"], event["strip"], event["partition"], event["chamber"]): 
                if (chamber==j):
                    layers[partition][int(ly)] |= 1 << int(strip)
            seg_list = process_chamber(layers) 
            for seg in seg_list:
                seg.fit()
            #print(seg.bend_ang, seg.substrip)

            pats = [(PATLIST[15-seg.id], seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
            fits = [(seg.bend_ang, seg.substrip, seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
        
            for i in range(len(layers)):
                pat = [(p[0], p[1]) for p in pats if p[2] == i]
                fitlist = [(fit[0], fit[1], fit[2]) for fit in fits if fit[3] == i and fit[2] != None]
                if pat !=[]:
                    disp.event_display(hits=layers[i], fits=fitlist, pats=pat, event=ievent+1, chamber=j)


        # for (ly, strip, partition, chamber) in zip(event["ly"], event["strip"], event["partition"], event["chamber"]): #for each hit in the event
        #     #print(f'{partition=}')                
        #     if (chamber==8):
        #         layers[partition][int(ly)] |= 1 << int(strip)
        # seg_list = process_chamber(layers) 

        # for seg in seg_list:
        #     seg.fit()
        #     #print(seg.bend_ang, seg.substrip)

        # pats = [(PATLIST[15-seg.id], seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
        # fits = [(seg.bend_ang, seg.substrip, seg.strip, seg.partition) for seg in seg_list if seg.id !=0]
        
        # for i in range(len(layers)):
        #     pat = [(p[0], p[1]) for p in pats if p[2] == i]
        #     fitlist = [(fit[0], fit[1], fit[2]) for fit in fits if fit[3] == i and fit[2] != None]
        #     if pat !=[]:
        #         disp.event_display(hits=layers[i], fits=fitlist, pats=pat)