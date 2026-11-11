#!/usr/bin/env python3
"""Adapt a legacy script image to Rockchip's 0xffffffff length-table sentinel.

The recovered vendor cmd/source.c scans until IMAGE_PARAM_INVAL, defined as
0xffffffff in include/image.h. Upstream mkimage writes a zero sentinel.
"""
import struct
import sys
import zlib
from pathlib import Path

path = Path(sys.argv[1])
data = bytearray(path.read_bytes())
assert struct.unpack_from('>I', data)[0] == 0x27051956
assert data[30] == 6  # IH_TYPE_SCRIPT
assert len(data) == 64 + struct.unpack_from('>I', data, 12)[0]
assert struct.unpack_from('>I', data, 64)[0] == len(data) - 72
assert data[68:72] in [b'\0' * 4, b'\xff' * 4]
data[68:72] = b'\xff' * 4
struct.pack_into('>I', data, 24, zlib.crc32(data[64:]))
struct.pack_into('>I', data, 4, 0)
struct.pack_into('>I', data, 4, zlib.crc32(data[:64]))
path.write_bytes(data)
