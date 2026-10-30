"""Remove four requested world-map entry points from the isolated offline build."""
from pathlib import Path
import gc
import hashlib
import json
import struct
import sys
from native_emulation_support import machine, base
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from unicorn.arm_const import *

source = base / 'native_analysis/startup_dialogs/libSrc-no-startup-dialogs.so'
original = source.read_bytes()
assert hashlib.sha256(original).hexdigest() == '496a73a0b624a3b77586e3933f94c1224db5e52d1da53aacce5f621aca717891'
blob = bytearray(original)
out = base / 'native_analysis/worldmap_entries'
out.mkdir(exist_ok=True)
with source.open('rb') as fp:
    elf = ELFFile(fp)
    segments = [dict(s.header) for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
    relocs = {r['r_offset']:r['r_info_type'] for section in elf.iter_sections()
              if section['sh_type'] == 'SHT_REL' for r in section.iter_relocations()}

def offset(address):
    va = address - 0x10000
    for seg in segments:
        if seg['p_vaddr'] <= va < seg['p_vaddr'] + seg['p_filesz']:
            return seg['p_offset'] + va - seg['p_vaddr']
    raise ValueError(hex(address))

patches = []
def patch(address, data, role, expected=None, relocation=False):
    pos = offset(address)
    before = bytes(blob[pos:pos+len(data)])
    if expected is not None: assert before == expected, (role,before.hex())
    blob[pos:pos+len(data)] = data
    patches.append(dict(ghidra_address=hex(address), file_offset=hex(pos), role=role,
                        before=before.hex(), after=data.hex(), relative_relocation=relocation))

ret0 = bytes.fromhex('0000a0e31eff2fe1')
widgets = [
    ('Lottery',0x17d7a60,0xa2bf74,0xa2bbb0),
    ('PlantTrial',0x1808c80,0xe83de8,0xe83c74),
    ('Gemreturn',0x1808620,0xe6facc,0xe6f7f0),
]
exits = []
for name, table, draw, click in widgets:
    assert struct.unpack_from('<I',blob,offset(table+15*4))[0]+0x10000 == draw
    assert struct.unpack_from('<I',blob,offset(table+47*4))[0]+0x10000 == click
    for entry, role in [(draw,'draw'),(click,'click')]:
        code = original[offset(entry):offset(entry)+8]
        assert list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(code,entry))[0].mnemonic.startswith('push')
        patch(entry,ret0,name+' '+role)
        exits.append((name+' '+role,entry))
    slot = table+21*4
    assert relocs[slot-0x10000] == 23  # R_ARM_RELATIVE: loader adds the image base.
    patch(slot,struct.pack('<I',draw-0x10000),name+' hit-test',
          struct.pack('<I',0x98680c-0x10000),True)

# WorldMap_GemBank draws its background, gem, recharge button, then numeric text.
# Keep the first two image calls and numeric text; remove only the third image call.
draw = 0xa31ecc
calls = [ins.address for ins in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(
         original[offset(draw):offset(draw)+0xa00],draw)
         if ins.mnemonic == 'bl' and ins.op_str == '#0x11794c8']
assert calls == [0xa31fe0,0xa320f8,0xa3221c]
patch(calls[2],bytes.fromhex('0000a0e1'),'GemBank recharge image only',bytes.fromhex('a91c1deb'))
slot = 0x17d7ea0+21*4
assert relocs[slot-0x10000] == 23
patch(slot,struct.pack('<I',0xa2bf74-0x10000),'GemBank read-only hit-test',
      struct.pack('<I',0x367498-0x10000),True)
patch(0xa313f8,ret0,'GemBank recharge click')
exits.append(('GemBank recharge click',0xa313f8))

# Every changed byte must belong to one of the explicit patch ranges.
allowed = {i for p in patches for i in range(int(p['file_offset'],16),
              int(p['file_offset'],16)+len(bytes.fromhex(p['after'])))}
assert len(original) == len(blob)
assert all(a == b or i in allowed for i,(a,b) in enumerate(zip(original,blob)))
for address in calls[:2]:
    pos = offset(address)
    assert blob[pos:pos+4] == original[pos:pos+4]
# PlantAdventure is a distinct feature; the requested Chinese icon is PlantTrial.
for address,size in [(0x7068d4,8),(0x706678,8),(0x17c5738+21*4,4)]:
    pos=offset(address)
    assert blob[pos:pos+size] == original[pos:pos+size]

# Bounded original ARM execution verifies patched exits and per-class hit dispatch.
cases = []
uc, _ = machine()
for item in patches:
    value = bytes.fromhex(item['after'])
    if item['relative_relocation']:
        value = struct.pack('<I',struct.unpack('<I',value)[0]+0x10000)
    uc.mem_write(int(item['ghidra_address'],16),value)
stack, end = 0x4080000, 0x5000100
preserved = [UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
             UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
def run(name, address, arg, x, y):
    uc.reg_write(UC_ARM_REG_R0,arg)
    uc.reg_write(UC_ARM_REG_R1,x&0xffffffff)
    uc.reg_write(UC_ARM_REG_R2,y&0xffffffff)
    uc.reg_write(UC_ARM_REG_R3,0)
    uc.reg_write(UC_ARM_REG_SP,stack)
    uc.reg_write(UC_ARM_REG_LR,end)
    for i,reg in enumerate(preserved):uc.reg_write(reg,0x12345000+i)
    uc.emu_start(address,end,count=4)
    assert uc.reg_read(UC_ARM_REG_PC)==end and uc.reg_read(UC_ARM_REG_R0)==0
    assert uc.reg_read(UC_ARM_REG_SP)==stack
    assert all(uc.reg_read(reg)==0x12345000+i for i,reg in enumerate(preserved))
    cases.append(dict(role=name, entry=hex(address), returns_zero=True, preserves_callee_state=True))
for name,address in exits:
    for arg in (0,0x6000000,0xffffffff):run(name,address,arg,42,53)
for name,table in [(n,t) for n,t,_,_ in widgets]+[('GemBank',0x17d7ea0)]:
    address = struct.unpack('<I',uc.mem_read(table+21*4,4))[0]
    for x,y in [(-1,-1),(0,0),(40,50),(9999,9999)]:run(name+' hit-test',address,0,x,y)
del uc
gc.collect()

target = out / 'libSrc-no-worldmap-entries.so'
target.write_bytes(blob)
record = dict(source_sha256=hashlib.sha256(original).hexdigest(),
              patched_sha256=hashlib.sha256(blob).hexdigest(),patches=patches,
              bounded_arm_cases=cases,arm_cases_passed=len(cases),
              gem_background_and_icon_draw_calls_preserved=True,
              game_assets_changed=False, runtime_verified=False,
              scope='Only isolated offline world-map entry rendering and hit/click handlers. No currency/save changes; no gameplay rewards or store purchase logic changed. Full WSA UI verification is separate.')
(out/'patch-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ('patches','bounded_arm_cases')},indent=2))
