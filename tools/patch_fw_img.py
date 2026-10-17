#!/usr/bin/env python3
"""Repack an OSSC SD firmware image: keep FPGA bitstream, replace SW image.

Layout (tools/create_fw_img.c):
  [0:512]   header: "OSSC" + ver_major + ver_minor + suffix[8] +
            hdr_len(u32 BE=26) + data_len(u32 BE) + data_crc(u32 BE) +
            pad[482] + hdr_crc(u32 BE)
  [512:]    data: RBF bitstream + 0xFF padding to bin_offset + bitswapped SW bin
"""
import struct, sys, zlib, pathlib

def bitswap8(b):
    return int('{:08b}'.format(b)[::-1], 2)

def parse(path):
    d = pathlib.Path(path).read_bytes()
    assert d[:4] == b'OSSC', "not an OSSC fw image"
    maj, mnr = d[4], d[5]
    suffix = d[6:14].split(b'\0')[0].decode()
    hdr_len, data_len, data_crc = struct.unpack('>III', d[14:26])
    hdr_crc, = struct.unpack('>I', d[508:512])
    assert hdr_len == 26
    calc = zlib.crc32(d[:26]) & 0xFFFFFFFF
    print(f"ver {maj}.{mnr}{'-'+suffix if suffix else ''} data_len={data_len} "
          f"data_crc={data_crc:08x} hdr_crc={hdr_crc:08x} (calc {calc:08x}) "
          f"file={len(d)}")
    assert calc == hdr_crc, "header crc mismatch"
    data = d[512:512+data_len]
    assert zlib.crc32(data) & 0xFFFFFFFF == data_crc, "data crc mismatch"
    print("CRCs OK")
    return maj, mnr, suffix, data

def build(data, sw_path, bin_offset, out_path, suffix):
    rbf = data[:bin_offset]
    sw = bytes(bitswap8(b) for b in pathlib.Path(sw_path).read_bytes())
    new_data = rbf + sw
    maj, mnr = 1, 22
    hdr = b'OSSC' + bytes([maj, mnr]) + suffix.encode().ljust(8, b'\0') + \
          struct.pack('>III', 26, len(new_data), zlib.crc32(new_data) & 0xFFFFFFFF)
    assert len(hdr) == 26
    hdr += b'\0' * 482 + struct.pack('>I', zlib.crc32(hdr) & 0xFFFFFFFF)
    assert len(hdr) == 512
    pathlib.Path(out_path).write_bytes(hdr + new_data)
    print(f"wrote {out_path}: {512+len(new_data)} bytes "
          f"(rbf+pad {len(rbf)}, sw {len(sw)})")

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ossc_1.22-aud.bin'
    if len(sys.argv) > 2 and sys.argv[2] == 'build':
        maj, mnr, suffix, data = parse(src)
        build(data, '/mnt/c/Users/rpf16/ossc-fork/software/sys_controller/mem_init/flash.bin',
              0x50000, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else 'rpf')
        parse(sys.argv[3])
    else:
        maj, mnr, suffix, data = parse(src)
        # locate sw start: first long run? verify bin_offset hypothesis
        import re
        m = re.search(b'\xff{256,}', data)
        print("first 0xff run at", hex(m.start()) if m else "none")
        print("sw region guess @0x50000:", data[0x50000:0x50010].hex())
