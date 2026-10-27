#!/usr/bin/env python3
"""Patch dynamic.rsb: switch UIChangeSpeedButton from Arena (PvP) to original SpeedChange."""
import hashlib
import struct
import sys

sys.path.insert(0, r"K:\pvz2-tools")
import rsbtool
from py3rijndael import RijndaelCbc, ZeroPadding

KEY = hashlib.md5(b"com_popcap_pvz2_magento_product_2013_05_05").hexdigest().encode()
IV = KEY[4:28]
CBC = RijndaelCbc(KEY, IV, ZeroPadding(24), block_size=24)

PATCHES = [
    (b"\x90\x16ArenaChangeSpeedButton", b"\x90\x0bSpeedChange"),
    (b"\x90\x26IMAGE_UI_HUD_INGAME_ARENA_CHANGE_SPEED", b"\x90\x19IMAGE_UI_HUD_INGAME_SPEED"),
    (b"\x81\x16ArenaChangeSpeedButton", b"\x81\x0bSpeedChange"),
    (b"\x81\x26IMAGE_UI_HUD_INGAME_ARENA_CHANGE_SPEED", b"\x81\x19IMAGE_UI_HUD_INGAME_SPEED"),
]


def decrypt(blob):
    assert blob[:2] == b"\x10\x00", blob[:2]
    return CBC.decrypt(blob[2:])


def encrypt(pt):
    ct = CBC.encrypt(pt)
    return b"\x10\x00" + ct


def main(src, dst):
    data = bytearray(open(src, "rb").read())
    h = rsbtool.parse_head(data)
    infos = rsbtool.read_rsgp_info(data, h["rsgpInfo_BeginOffset"], h["rsgp_Number"],
                                   h["rsgpInfo_EachLength"])
    pack = [it for it in infos if it["ID"] == "Packages"][0]
    base = pack["fields"][0]
    p0_off = struct.unpack_from("<I", data, base + 0x18)[0]
    fl_len = struct.unpack_from("<I", data, base + 0x48)[0]
    fl_off = struct.unpack_from("<I", data, base + 0x4c)[0]
    files = rsbtool.read_string_list(data, base + fl_off, fl_len, 1)

    changed = 0
    for idx, (name, extra) in enumerate(files):
        typ, off, size = extra
        start = base + p0_off + off
        blob = bytes(data[start:start + size])
        if blob[:2] != b"\x10\x00":
            continue
        pt = decrypt(blob)
        if b"UIChangeSpeedButton" not in pt:
            continue
        before_len = len(pt)
        new = pt
        total = 0
        for old, repl in PATCHES:
            c = new.count(old)
            total += c
            new = new.replace(old, repl)
        if total == 0:
            print(f"[{idx}] {name!r}: no arena strings (already patched?)")
            continue
        n_cls = n_img = total
        # keep the same plaintext length so the ciphertext keeps its size
        if len(new) < before_len:
            new = new + b"\x00" * (before_len - len(new))
        elif len(new) > before_len:
            print(f"[{idx}] {name!r}: WARNING grew")
        ct = encrypt(new)
        if len(ct) != size:
            print(f"[{idx}] {name!r}: size mismatch {len(ct)} != {size}, skipping")
            continue
        data[start:start + size] = ct
        changed += 1
        print(f"[{idx}] {name!r}: patched class x{n_cls}, image x{n_img} (size {size})")

    open(dst, "wb").write(data)
    print("patched", changed, "packages ->", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
