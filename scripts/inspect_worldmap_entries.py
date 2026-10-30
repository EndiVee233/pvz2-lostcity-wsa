"""Locate original world-map draw calls and verify class-specific vtable slots."""
from pathlib import Path
import sys
import struct
base = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base / 'tools/python_libs'))
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
path = base / 'raw/lib/armeabi/libSrc.so'
blob = path.read_bytes()
with path.open('rb') as fp:
    elf = ELFFile(fp)
    segments = [dict(s.header) for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
def off(gh):
    va = gh - 0x10000
    for seg in segments:
        if seg['p_vaddr'] <= va < seg['p_vaddr'] + seg['p_filesz']:
            return seg['p_offset'] + va - seg['p_vaddr']
    raise ValueError(hex(gh))
for name, vtable in [('Lottery',0x17d7a60),('PlantAdventure',0x17c5738),
                     ('Gemreturn',0x1808620),('GemBank',0x17d7ea0)]:
    print(name, 'vtable', hex(vtable), 'slots',
          {i: hex(struct.unpack_from('<I',blob,off(vtable)+i*4)[0]+0x10000) for i in (15,21,47,48)})
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
calls = []
for ins in md.disasm(blob[off(0xa31ecc):off(0xa31ecc)+0xa00],0xa31ecc):
    if ins.mnemonic == 'bl' and ins.op_str == '#0x11794c8':
        calls.append(hex(ins.address))
        print('GemBank image draw call',hex(ins.address),ins.bytes.hex())
print('Image call count',len(calls))
