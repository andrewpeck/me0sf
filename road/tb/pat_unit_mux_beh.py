# Emulator for pat_unit_mux.vhd
from subfunc import *
from pat_unit_beh import pat_unit
from constants import *

def parse_data(data, strip, max_span):
    """takes in data, a strip index, and a MAX_SPAN to get the data a pat_unit on that strip would see"""
    if strip < max_span // 2 + 1:
        data_shifted = data << (max_span // 2 - strip)
        parsed_data = data_shifted & (2**max_span - 1)
    else:
        shift = strip - max_span // 2
        parsed_data = (data >> shift) & (2**max_span - 1)
    return parsed_data

def extract_data_window(ly_dat, strip, max_span):
    """extracts data window around given strip"""
    return [parse_data(data, strip, max_span) for data in ly_dat]

def parse_bx_data(bx_data, strip, max_span):
    if strip < max_span // 2 + 1:
        data_shifted = [-9999 for _ in range(max_span // 2 - strip)] + bx_data
        parsed_bx_data = data_shifted[:max_span]
    else:
        shift = strip - max_span // 2
        num_appended_nedded = shift + max_span - len(bx_data)
        if num_appended_nedded > 0:
            data_shifted = bx_data + [-9999 for _ in range(num_appended_nedded)]
        else:
            data_shifted = bx_data
        parsed_bx_data = data_shifted[shift:shift+max_span]
    return parsed_bx_data

def extract_bx_data_window(ly_dat, strip, max_span):
    """extracts data window around given strip"""
    return [parse_bx_data(data, strip, max_span) for data in ly_dat]

def pat_mux(partition_data, partition, config : Config, partition_bx_data):
    """
    takes in a list of integers for the partition data in each layer,
    the MAX_SPAN of each pat_unit, and the partition width to return a list of the
    segments the pat_unit_mux.vhd would find
    """
    # todo : after extracting window the span is 37 or smaller
    fn = lambda strip : pat_unit(data = extract_data_window(partition_data, strip, config.max_span),
                                 bx_data = extract_bx_data_window(partition_bx_data, strip, config.max_span),
                                 ly_thresh_patid = config.ly_thresh_patid,
                                 ly_thresh_eta = config.ly_thresh_eta,
                                 strip = strip,
                                 partition = partition, 
                                 input_max_span = config.max_span,
                                 skip_centroids = config.skip_centroids,
                                 num_or = config.num_or)

    return [fn(x) for x in range(config.width)]

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

def test_parse_data():
    """ test function for parse_data"""
    assert parse_data(0b1000000000000000000, 10, 37) == 0b100000000000000000000000000
    assert parse_data(0b1000000000000000000, 25, 37) == 0b100000000000

def test_extract_data_window():
    """test function for extract_data_window"""
    assert extract_data_window(max_span=37, strip=8, ly_dat=[0b100000000000000000, 0b1000100000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]) == [134217728, 285212672, 268435456, 268435456, 268435456, 268435456]
    assert extract_data_window(max_span=37, strip=20, ly_dat=[0b100000000000000000, 0b1000100000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000, 0b1000000000000000000]) == [32768, 69632, 65536, 65536, 65536, 65536]

def test_pat_mux():
    data = [0b1, 0b1, 0b1, 0b1, 0b1, 0b1]

    config = Config()
    config.ly_thresh=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 5, 4, 4, 4, 4, 4]
    config.max_span=37

    mux = pat_mux(data, partition=0, config=config)
    # check for expected pattern
    assert mux[0].id == 19
    assert mux[0].lc == 6
    # check for lack of unexpected pattern
    assert mux[4].lc == 0

def test_parse_bx_data():
    test_data = [0,1,1,1,0,0,1,1,0,0,1,0]
    assert parse_bx_data(test_data, 4, 7) == [1, 1, 1, 0, 0, 1, 1]
    assert parse_bx_data(test_data, 1, 7) == [-9999, -9999, 0, 1, 1, 1, 0]
    assert parse_bx_data(test_data, 11, 7) == [0, 0, 1, 0, -9999, -9999, -9999]
