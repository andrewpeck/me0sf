# Emulator for pat_unit_mux.vhd
from subfunc import *
from pat_unit_beh import process_pat
from constants import *

def parse_data(data, strip, MAX_SPAN=37):
    """takes in data, a strip index, and a MAX_SPAN to get the data a pat_unit on that strip would see"""
    if strip < MAX_SPAN // 2 + 1:
        data_shifted = data << (MAX_SPAN // 2 - strip)
        parsed_data = data_shifted & (2**MAX_SPAN - 1)
    else:
        shift = strip - MAX_SPAN // 2
        parsed_data = (data >> shift) & (2**MAX_SPAN - 1)
    return parsed_data

def test_parse_data():
    """ test function for parse_data"""
    assert parse_data(0b1000000000000000000, 18) == 0b1000000000000000000
    assert parse_data(0b1000000000000000000, 10) == 0b100000000000000000000000000
    assert parse_data(0b1000000000000000000, 25) == 0b100000000000
    assert parse_data(0b100000000000000000, 30) == 0b100000

def extract_data_window(ly_dat, strip, MAX_SPAN=37):
    """extracts data window around given strip"""
    return [parse_data(data, strip, MAX_SPAN) for data in ly_dat]

def test_extract_data_window():
    """test function for extract_data_window"""
    assert extract_data_window([0b100000000000000000, 0b1000100000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 8) == [134217728, 285212672, 268435456, 268435456, 268435456, 268435456]
    assert extract_data_window([0b100000000000000000, 0b1000100000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000], 20) == [32768, 69632, 65536, 65536, 65536, 65536]

def pat_mux(chamber_data, MAX_SPAN=37, WIDTH=192):
    """
    takes in a list of integers for the chamber data in each layer, 
    the MAX_SPAN of each pat_unit, and the chamber width to return a list of the
    patterns the pat_unit_mux.vhd would find as segment objects
    """
    return[process_pat(extract_data_window(chamber_data, strip, MAX_SPAN), strip) for strip in range(WIDTH)] 
    
def test_pat_mux():
    assert pat_mux([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000])[0].id == 2
    assert pat_mux([0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000])[0].lc == 1 