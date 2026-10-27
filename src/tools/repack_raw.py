#!/usr/bin/env python3
"""Rebuild pvz2data.zip.* copying unchanged entries as raw compressed streams."""
import io
import os
import struct
import sys
import zlib
import zipfile

APK = r"K:\pvz2-lostcity-wsa-main\PvZ2-LostCity-1.7.5.apk"
PARTS = ["assets/pvz2data.zip.001", "assets/pvz2data.zip.002", "assets/pvz2data.zip.003"]
TARGET = "com.popcap.pvz2cthd/files/dynamic.rsb.smf"
PATCHED = r"C:\Users\SpokeIsThere\AppData\Local\Temp\pvz2work\dyn_patched.rsb"
OUT_DIR = r"C:\Users\SpokeIsThere\AppData\Local\Temp\pvz2work\zipnew2"
PART_SIZE = 419430400


class Concat(io.RawIOBase):
    def __init__(self, apk, names):
        self.infos = [i for i in apk.infolist() if i.filename in names]
        self.fps = [apk.open(n) for n in names]
        self.starts = []
        self.size = 0
        for inf in self.infos:
            self.starts.append(self.size)
            self.size += inf.file_size
        self.pos = 0

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        out = bytearray()
        while n > 0 and self.pos < self.size:
            for idx, inf in enumerate(self.infos):
                start = self.starts[idx]
                end = start + inf.file_size
                if start <= self.pos < end:
                    fp = self.fps[idx]
                    fp.seek(self.pos - start)
                    chunk = fp.read(min(n, end - self.pos))
                    out += chunk
                    self.pos += len(chunk)
                    n -= len(chunk)
                    break
            else:
                break
        return bytes(out)

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def tell(self):
        return self.pos


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    src = Concat(zipfile.ZipFile(APK), PARTS)
    zsrc = zipfile.ZipFile(src)
    out_path = os.path.join(OUT_DIR, "pvz2data.zip")
    out = open(out_path, "wb")
    central = []
    patched = open(PATCHED, "rb").read()
    for info in zsrc.infolist():
        if info.is_dir():
            continue
        offset = out.tell()
        # read local header raw
        src.seek(info.header_offset)
        hdr = src.read(30)
        sig, ver, flags, method, mtime, mdate, crc, csize, usize, nlen, elen = struct.unpack("<IHHHHHIIIHH", hdr)
        assert sig == 0x04034B50, hex(sig)
        name = src.read(nlen)
        extra = src.read(elen)
        data_start = info.header_offset + 30 + nlen + elen
        if info.filename == TARGET:
            # recompress the patched data
            comp = zlib.compressobj(6, zlib.DEFLATED, -15)
            cdata = comp.compress(patched) + comp.flush()
            crc = zlib.crc32(patched) & 0xFFFFFFFF
            csize = len(cdata)
            usize = len(patched)
            crc = zlib.crc32(patched) & 0xFFFFFFFF
        else:
            src.seek(data_start)
            cdata = src.read(info.compress_size)
        # local header (no data descriptor)
        lh = struct.pack("<IHHHHHIIIHH", 0x04034B50, ver, 0, method, mtime, mdate, crc, csize, usize, nlen, elen)
        out.write(lh)
        out.write(name)
        out.write(extra)
        out.write(cdata)
        central.append((name, extra, ver, method, mtime, mdate, crc, csize, usize, offset))
        print("entry", info.filename, usize, "->", csize, flush=True)
    cd_start = out.tell()
    for (name, extra, ver, method, mtime, mdate, crc, csize, usize, offset) in central:
        out.write(struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, ver, 0, method, mtime, mdate,
                              crc, csize, usize, len(name), len(extra), 0, 0, 0, 0, offset))
        out.write(name)
        out.write(extra)
    cd_size = out.tell() - cd_start
    out.write(struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(central), len(central), cd_size, cd_start, 0))
    out.close()
    print("zip size", os.path.getsize(out_path))
    with open(out_path, "rb") as f:
        idx = 0
        while True:
            chunk = f.read(PART_SIZE)
            if not chunk:
                break
            part = os.path.join(OUT_DIR, "pvz2data.zip.%03d" % (idx + 1))
            with open(part, "wb") as g:
                g.write(chunk)
            print("part", os.path.basename(part), len(chunk), flush=True)
            idx += 1


if __name__ == "__main__":
    main()
