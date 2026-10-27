#!/usr/bin/env python3
"""Minimal PvZ2 RSB (1bsr v4) reader, ported from Pvz2Tool's Kotlin implementation."""
import struct
import sys

MAGIC = 1920164401  # '1bsr'


class Reader:
    def __init__(self, data):
        self.d = data

    def u32(self, off):
        return struct.unpack_from("<I", self.d, off)[0]

    def i32(self, off):
        return struct.unpack_from("<i", self.d, off)[0]

    def u24(self, off):
        return self.d[off] | (self.d[off + 1] << 8) | (self.d[off + 2] << 16)


def parse_head(data):
    r = Reader(data)
    magic = r.u32(0)
    if magic != MAGIC:
        raise SystemExit("bad magic %08x" % magic)
    version = r.u32(4)
    h = {
        "version": version,
        "headLength": r.u32(0x0C),
        "fileList_Length": r.u32(0x10),
        "fileList_BeginOffset": r.u32(0x14),
        "rsgpList_Length": r.u32(0x20),
        "rsgpList_BeginOffset": r.u32(0x24),
        "rsgp_Number": r.u32(0x28),
        "rsgpInfo_BeginOffset": r.u32(0x2C),
        "rsgpInfo_EachLength": r.u32(0x30),
        "composite_Number": r.u32(0x34),
        "compositeInfo_BeginOffset": r.u32(0x38),
        "compositeInfo_EachLength": r.u32(0x3C),
        "compositeList_Length": r.u32(0x40),
        "compositeList_BeginOffset": r.u32(0x44),
        "autopool_Number": r.u32(0x48),
        "autopoolInfo_BeginOffset": r.u32(0x4C),
        "autopoolInfo_EachLength": r.u32(0x50),
        "ptx_Number": r.u32(0x54),
        "ptxInfo_BeginOffset": r.u32(0x58),
        "ptxInfo_EachLength": r.u32(0x5C),
        "xmlPart1_BeginOffset": r.u32(0x60),
        "xmlPart2_BeginOffset": r.u32(0x64),
        "xmlPart3_BeginOffset": r.u32(0x68),
        "rsbInfo_Length": r.u32(0x6C),
    }
    return h


def read_string_list(data, off, length, extra_type):
    end = off + length
    pos = off
    items = []
    defaults = [["", len(data)]]
    while pos < end:
        temp = ""
        temp_head = ""
        i = 0
        while i < len(defaults):
            d = defaults[i]
            if pos < d[1] * 4:
                temp_head += d[0]
                i += 1
            else:
                defaults.pop(i)
        start_index = 0
        tpend = defaults[-1][1] if defaults else 0
        while pos < end and data[pos] != 0:
            temp += chr(data[pos])
            pos += 1
            if pos + 3 > end:
                break
            tmp = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
            pos += 3
            if tmp != 0:
                if len(temp) != 1:
                    defaults.append([temp[start_index:len(temp) - 1], tpend])
                start_index = len(temp) - 1
                tpend = tmp
        pos += 1
        if pos + 3 <= end:
            tmp = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
            pos += 3
            if tmp != 0 and len(temp) != 1:
                defaults.append([temp[start_index:], tpend])
        full = temp_head + temp
        extra = None
        if pos + 4 <= end:
            if extra_type == 0:
                extra = struct.unpack_from("<i", data, pos)[0]
                pos += 4
            else:
                t = struct.unpack_from("<i", data, pos)[0]
                if t == 0:
                    t, o, s = struct.unpack_from("<iii", data, pos)
                    extra = (t, o, s)
                    pos += 12
                else:
                    extra = struct.unpack_from("<iiiiiiii", data, pos)
                    pos += 32
        items.append((full, extra))
    return items


def read_rsgp_info(data, off, count, each):
    out = []
    r = Reader(data)
    pos = off
    for n in range(count):
        base = pos
        idb = data[base:base + 0x80].split(b"\x00")[0].decode("utf-8", "replace")
        fields = []
        for k in range(13):
            fields.append(r.u32(base + 0x80 + k * 4))
        out.append({"ID": idb, "fields": fields, "at": base})
        pos += each
    return out


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\SpokeIsThere\AppData\Local\Temp\pvz2work\dyn.rsb"
    data = open(path, "rb").read()
    h = parse_head(data)
    for k, v in h.items():
        print(f"{k:28} {v} (0x{v:x})" if isinstance(v, int) else f"{k:28} {v}")
    print("\n--- fileList ---")
    files = read_string_list(data, h["fileList_BeginOffset"], h["fileList_Length"], 0)
    print("count", len(files))
    for name, extra in files[:15]:
        print("   ", repr(name), extra)
    print("\n--- rsgpList ---")
    pkgs = read_string_list(data, h["rsgpList_BeginOffset"], h["rsgpList_Length"], 0)
    print("count", len(pkgs))
    for name, extra in pkgs:
        print("   ", repr(name), extra)
    print("\n--- rsgpInfo ---")
    infos = read_rsgp_info(data, h["rsgpInfo_BeginOffset"], h["rsgp_Number"], h["rsgpInfo_EachLength"])
    for it in infos:
        print("   ", repr(it["ID"]), [hex(x) for x in it["fields"][:10]], "at", hex(it["at"]))
