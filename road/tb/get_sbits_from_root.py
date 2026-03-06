import uproot
import sys

from printly_dat import printly_dat

def read_ntuple_stack_format(file_path, entry_start=None, entry_stop=None):
    with uproot.open(file_path + ":outputtree") as segments:
        
        #print("read all: ", segments.keys())

        events = segments.arrays(
            [
                ############# digi ##############
                'orbitNumber',
                'bunchCounter',
                'eventCounter',
                'runParameter',
                'pulse_stretch',
                'rawFed',
                'rawSlot',
                'rawOH',
                'rawVFAT',
                'rawChannel',
                'digiBX',
                'digiStripChamber',
                'digiStripEta',
                'digiStrip',
                'digiStripCharge',
                'digiStripTime',
                'digiPadChamber',
                'digiPadX',
                'digiPadY',
                'digiPadCharge',
                'digiPadTime'],
            entry_start=entry_start, 
            entry_stop=entry_stop
        )

    return events


def get_sbits_from_event_sim_format(event):
    hit_data = [[0 for _ in range(6)] for _ in range(8)]

    # Sim file format:
    # Strip = [0, 383]
    # Partition = [1, 8]
    # Layer = [1, 6]
    # Region = [-1 or 1]
    # Chamber = [1, 18]
    # BX = [-1, 1]

    for strip, partition, layer, region, chamber, bx in zip([int(s)//2 for s in event["me0_digi_hit_strip_i"]], [p-1 for p in event["me0_digi_hit_eta_partition_i"]], [l-1 for l in event["me0_digi_hit_layer_i"]], event["me0_digi_hit_region_i"], event["me0_digi_hit_chamber_i"], event["me0_digi_hit_bx_i"]):
        if region == 1 and chamber == 1 and bx == 0: # Only take data for one stack
            hit_data[partition][layer] |= 1 << strip

    return hit_data

def get_sbits_from_event_stack_format(event):
    hit_data = [[0 for _ in range(6)] for _ in range(8)]

    for tup in zip(event["digiStrip"], [e-1 for e in event["digiStripEta"]], event["digiStripChamber"]):
        hit_data[tup[1]][tup[2]] |= 1 << (int(tup[0])//2)

    return hit_data



if __name__ == "__main__":
    
    segs = read_ntuple_stack("digi_1199.root")

    for i in range(6, 7):
        print(f"\n\n\nEVENT {i}")
        hit_data = get_sbits_from_event(segs[i])
        
        for prt, prt_data in enumerate(hit_data):
            print(f"Partition {prt}:")
            printly_dat(mask=prt_data, MAX_SPAN=192)
