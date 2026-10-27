#!/usr/bin/env python3
"""Patch a PvZ2 1.7.5 APK so AndroidHttpProxy.GetNetworkStatus() always returns 0.

The shipped 1.7.5 build talks to the (long dead) 拓维 cloud endpoint
http://cloudpvz2android.ditwan.cn/index.php once per frame while the
"游戏公告" dialog is open.  Every request fails, the client never leaves the
waiting state, and the "服务器通讯中..." overlay (which also swallows taps)
stays on screen forever.

Returning NET_NOT_REACHABLE (0) makes the native side skip the whole cloud
flow: no request is issued at all, so the overlay never appears.  The notice
dialog still shows its built-in text.

Usage:
    python patch_dex_network_status.py PvZ2-LostCity-1.7.5.apk out.apk

The output APK is unsigned; sign it afterwards (apksigner / uber-apk-signer).
"""
import hashlib
import os
import struct
import sys
import zipfile
import zlib

CLASS = "Lcom/popcap/SexyAppFramework/AndroidHttpProxy;"
METHOD = "GetNetworkStatus"
ALIGN = 4
SKIP_META = "META-INF/"

# const/4 v0, #0 ; return v0
STUB = struct.pack("<HH", 0x0012, 0x000F)


def uleb(buf, off):
    value = 0
    shift = 0
    while True:
        byte = buf[off]
        off += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, off
        shift += 7


class Dex:
    def __init__(self, raw):
        self.buf = bytearray(raw)
        self.string_ids_size, self.string_ids_off = struct.unpack_from("<II", self.buf, 56)
        self.type_ids_size, self.type_ids_off = struct.unpack_from("<II", self.buf, 64)
        self.method_ids_off = struct.unpack_from("<I", self.buf, 92)[0]
        self.class_defs_size, self.class_defs_off = struct.unpack_from("<II", self.buf, 96)

    def string(self, idx):
        off = struct.unpack_from("<I", self.buf, self.string_ids_off + 4 * idx)[0]
        _, off = uleb(self.buf, off)
        end = self.buf.index(0, off)
        return self.buf[off:end].decode("utf-8", "replace")

    def type_name(self, idx):
        return self.string(struct.unpack_from("<I", self.buf, self.type_ids_off + 4 * idx)[0])

    def method_name(self, idx):
        return self.string(struct.unpack_from("<I", self.buf, self.method_ids_off + 8 * idx + 4)[0])

    def methods(self, class_idx):
        for i in range(self.class_defs_size):
            off = self.class_defs_off + 32 * i
            if struct.unpack_from("<I", self.buf, off)[0] != class_idx:
                continue
            data_off = struct.unpack_from("<I", self.buf, off + 24)[0]
            if not data_off:
                return []
            pos = data_off
            static, pos = uleb(self.buf, pos)
            instance, pos = uleb(self.buf, pos)
            direct, pos = uleb(self.buf, pos)
            virtual, pos = uleb(self.buf, pos)
            for _ in range(static + instance):
                _, pos = uleb(self.buf, pos)
                _, pos = uleb(self.buf, pos)
            out = []
            for count in (direct, virtual):
                idx = 0
                for _ in range(count):
                    diff, pos = uleb(self.buf, pos)
                    idx += diff
                    _, pos = uleb(self.buf, pos)
                    code_off, pos = uleb(self.buf, pos)
                    out.append((idx, code_off))
            return out
        return []

    def find_type(self, name):
        for i in range(self.type_ids_size):
            if self.type_name(i) == name:
                return i
        return None


def patch_dex(raw):
    dex = Dex(raw)
    type_idx = dex.find_type(CLASS)
    if type_idx is None:
        raise SystemExit("class not found: " + CLASS)
    for method_idx, code_off in dex.methods(type_idx):
        if dex.method_name(method_idx) != METHOD or not code_off:
            continue
        _, _, _, tries, _, insns_size = struct.unpack_from("<HHHHII", dex.buf, code_off)
        if insns_size < 2:
            raise SystemExit("unexpected code size")
        if dex.buf[code_off + 16:code_off + 20] == STUB:
            print("already patched")
            return bytes(dex.buf)
        # Keep insns_size unchanged: the map_list lists code items sequentially,
        # so shrinking one would desync every following item for the verifier.
        dex.buf[code_off + 16:code_off + 16 + 2 * insns_size] = STUB + b"\x00" * (2 * (insns_size - 2))
        struct.pack_into("<H", dex.buf, code_off + 6, 0)  # tries_size
        dex.buf[12:32] = hashlib.sha1(dex.buf[32:]).digest()
        struct.pack_into("<I", dex.buf, 8, zlib.adler32(dex.buf[12:]) & 0xFFFFFFFF)
        print("patched %s.%s() -> return 0" % (CLASS, METHOD))
        return bytes(dex.buf)
    raise SystemExit("method not found: " + METHOD)


def rewrite_apk(src_path, dst_path, dex_bytes):
    src = zipfile.ZipFile(src_path)
    dst = zipfile.ZipFile(dst_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    for info in src.infolist():
        if info.filename.startswith(SKIP_META):
            continue
        data = dex_bytes if info.filename == "classes.dex" else src.read(info.filename)
        zi = zipfile.ZipInfo(info.filename, info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.create_system = info.create_system
        zi.flag_bits = 0x800
        if info.compress_type == 0:  # keep stored entries 4-byte aligned
            pad = (-(dst.fp.tell() + 30 + len(info.filename.encode("utf-8")))) % ALIGN
            if pad:
                pad += ALIGN if pad < 4 else 0
                zi.extra = struct.pack("<HH", 0xD935, pad - 4) + b"\x00" * (pad - 4)
        dst.writestr(zi, data)
    dst.close()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_dex_network_status.py <in.apk> <out.apk>")
    src, dst = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(src) as zf:
        dex = zf.read("classes.dex")
    patched = patch_dex(dex)
    rewrite_apk(src, dst, patched)
    print("written", dst, os.path.getsize(dst), "bytes (unsigned)")


if __name__ == "__main__":
    main()
