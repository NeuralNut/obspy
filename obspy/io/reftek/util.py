# -*- coding: utf-8 -*-
"""
REFTEK130 read support, utility functions.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future.builtins import *  # NOQA

import numpy as np
from obspy import UTCDateTime
from obspy.io.mseed.util import _unpack_steim_1


NOW = UTCDateTime()


def _bcd_uint_array(chars):
    """
    http://stackoverflow.com/questions/11668969/..
    ..python-how-to-decode-binary-coded-decimal-bcd
    http://stackoverflow.com/questions/26369520/..
    ..how-to-load-4-bit-data-into-numpy-array
    """
    right = np.bitwise_and(chars, 0x0f)
    left = np.bitwise_and(chars >> 4, 0x0f)
    result = np.empty(2 * len(chars), dtype=np.uint8)
    result[::2] = left
    result[1::2] = right
    return result


def _bcd(chars):
    return _bcd_uint_array(np.fromstring(chars, dtype=np.int8))


def _bcd_str(chars):
    return "".join(map(str, _bcd(chars)))


def _bcd_hexstr(chars):
    return "".join(map(lambda x: '{:X}'.format(int(x)), _bcd(chars)))


def _bits(char):
    bits = np.unpackbits(np.fromstring(char, dtype=np.uint8))
    return bits.astype(np.bool_).tolist()


def _flags(char):
    bits = _bits(char)
    keys = ("first_packet", "last_packet", "second_EH_ET", "unused",
            "ST_command_trigger_event", "stacked_data_in_packet",
            "overscaled_data_detected_during_packet",
            "calibration_signal_enabled_during_packet")
    return {key: bit for key, bit in zip(keys, bits)}


def _bcd_int(chars):
    chars = _bcd_str(chars)
    return int(chars) if chars else None


def _parse_short_time(year, time_string):
    if NOW.year > 2050:
        raise NotImplementedError()
    if year < 50:
        year += 2000
    else:
        year += 1900
    time_string = str(year) + time_string
    return _parse_long_time(time_string, decode=False)


def _parse_long_time(time_bytestring, decode=True):
    if decode:
        time_string = time_bytestring.decode()
    else:
        time_string = time_bytestring
    if not time_string.strip():
        return None
    time_string, milliseconds = time_string[:-3], int(time_string[-3:])
    return (UTCDateTime().strptime(time_string, '%Y%j%H%M%S') +
            1e-3 * milliseconds)


def _parse_data(data):
    npts = _bcd_int(data[0:2])
    # flags = _bcd_int(data[2])
    data_format = _bcd_hexstr(data[3])
    data = data[4:]
    if data_format == "C0":
        data = data[40:]
        # XXX why need to swap? verbose for now..
        return _unpack_steim_1(data, npts, swapflag=1, verbose=True)
    else:
        raise NotImplementedError()


def _decode_ascii(chars):
    return chars.decode("ASCII")


def _16_tuple_ascii(bytestring):
    item_count = 16
    chars = bytestring.decode("ASCII")
    if len(chars) % item_count != 0:
        raise NotImplementedError("Should not happen, contact developers.")
    item_size = int(len(chars) / item_count)
    return tuple(chars[i*item_size:(i+1)*item_size]
                 for i in range(item_count))


def _16_tuple_int(bytestring):
    ascii_tuple = _16_tuple_ascii(bytestring)
    int_tuple = tuple(int(chars) if chars.strip() else None
                      for chars in ascii_tuple)
    return int_tuple


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
