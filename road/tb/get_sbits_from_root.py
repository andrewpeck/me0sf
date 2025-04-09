import uproot
import sys

from printly_dat import printly_dat

def read_ntuple_stack(file_path, entry_start=None, entry_stop=None):
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

def get_sbits_from_event(event):
    hit_data = [[0 for _ in range(6)] for _ in range(8)]

    for tup in zip(event["digiStrip"], [e-1 for e in event["digiStripEta"]], event["digiStripChamber"]):
        hit_data[tup[1]][tup[2]] |= 1 << (int(tup[0])//2)

    return hit_data



if __name__ == "__main__":
    
    segs = read_ntuple_stack("00001199.root")

    for i in range(5):
        print(f"\n\n\nEVENT {i}")
        hit_data = get_sbits_from_event(segs[i])
        
        for prt, prt_data in enumerate(hit_data):
            print(f"Partition {prt}:")
            printly_dat(mask=prt_data, MAX_SPAN=192)