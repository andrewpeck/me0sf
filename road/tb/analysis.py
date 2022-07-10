#!/usr/bin/env python3
import uproot
import event_display as disp

with uproot.open("MuonGE0Segments.root:ge0/segments") as segments:
    print(segments.keys())

    events = segments.arrays(["strip", "ly", "chamber", "partition"],

                             aliases={"strip": "floor(me0_rec_hit_strip/2.0)",
                                      "ly": "me0_rec_hit_layer-1",
                                      "chamber": "me0_rec_hit_chamber",
                                      "partition": "me0_rec_hit_eta_partition-1",
                                      })

    for (ievent, event) in enumerate(events):

        layers = [[0]*6]*8

        for (ly, strip, partition, chamber) in zip(event["ly"], event["strip"], event["partition"], event["chamber"]):
            print(f'{partition=}')
            if (chamber==4):
                layers[partition][int(ly)] |= 1 << int(strip)

        for layer in layers:
            disp.event_display(hits=layer)
