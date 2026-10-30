"""Remove only the original speed button's local feature-20 gate."""
from pathlib import Path
import hashlib
import json
import struct
from native_emulation_support import machine, base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

source=base/'native_analysis/worldmap_entries/libSrc-no-worldmap-entries.so'
original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='0176f226b382f55b39fdff151e862c0789c6d3f33511345b6d7d9205d06557d6'
address=0x9037c4;offset=address-0x10000
assert original[offset:offset+4]==bytes.fromhex('304cf8eb') # BL profile.HasFeature(0x14)
replacement=bytes.fromhex('0100a0e3') # Only this call site: mov r0,#1
blob=bytearray(original);blob[offset:offset+4]=replacement
out=base/'native_analysis/original_speed_button'
cases=[]
for modified in (False,True):
 for speed in (0x3f800000,0x40000000):
  for trial in (False,True):
   for profile in ('absent','locked','unlocked'):
    uc,_=machine()
    if modified:uc.mem_write(address,replacement)
    obj,controller,player,manager,node,vector=0x6000000,0x6000100,0x6000200,0x6000300,0x6000500,0x6000600
    def put(a,*values):uc.mem_write(a,struct.pack('<'+'I'*len(values),*values))
    put(0x1840528,controller);put(controller+0x30,speed)
    put(obj+0xf0,0);uc.mem_write(obj+0xee,bytes([int(trial)]))
    put(player+0x60,player+0x80,player+0x80+(4 if profile=='unlocked' else 0))
    put(player+0x80,0x14)
    put(0x1833050,manager);put(manager+0xc,0);put(manager+0x40,0)
    put(node+0x14,vector,vector+0x18)
    put(vector+0x14,0x5000200)
    events=[];modal=[]
    def hook(cpu,pc,size,user):
     if pc==0x15ef05c: # low-level soft-float equality boundary
      cpu.reg_write(UC_ARM_REG_R0,int(cpu.reg_read(UC_ARM_REG_R0)==cpu.reg_read(UC_ARM_REG_R1)))
      cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     elif pc==0x7c0328:
      cpu.reg_write(UC_ARM_REG_R0,0 if profile=='absent' else player)
      cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     elif pc==0x1f1314: # controlled event-bus map lookup/insertion
      cpu.reg_write(UC_ARM_REG_R0,node);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     elif pc==0x34f688:
      cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     elif pc==0x5000200: # observe the original handler's speed-change event argument
      factor=cpu.reg_read(UC_ARM_REG_R1);events.append(factor)
      put(controller+0x30,factor)
      cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     elif pc==0x9037d0:
      modal.append(True);cpu.emu_stop()
    uc.hook_add(UC_HOOK_CODE,hook)
    stack,end=0x4080000,0x5000100
    uc.reg_write(UC_ARM_REG_R0,obj);uc.reg_write(UC_ARM_REG_SP,stack);uc.reg_write(UC_ARM_REG_LR,end)
    uc.reg_write(UC_ARM_REG_R4,0x12345678)
    uc.emu_start(0x903588,end,count=3000)
    denied=not modified and not trial and profile=='locked'
    target=0x40000000 if speed==0x3f800000 else 0x3f800000
    assert bool(modal)==denied
    assert events==([] if denied else [target]),events
    if not denied:
     assert uc.reg_read(UC_ARM_REG_PC)==end and uc.reg_read(UC_ARM_REG_SP)==stack
     assert uc.reg_read(UC_ARM_REG_R4)==0x12345678
    assert bytes(uc.mem_read(player+0x60,8))==struct.pack('<II',player+0x80,player+0x80+(4 if profile=='unlocked' else 0))
    assert struct.unpack('<I',uc.mem_read(player+0x80,4))[0]==0x14
    cases.append(dict(patched=modified,input_speed_bits=hex(speed),trial=trial,profile=profile,
                      pay_modal=bool(modal),speed_events=[hex(v) for v in events],feature_list_preserved=True))
target=out/'libSrc-original-speed-unlocked.so';target.write_bytes(blob)
record=dict(source_sha256=hashlib.sha256(original).hexdigest(),patched_sha256=hashlib.sha256(blob).hexdigest(),
            ghidra_address=hex(address),file_offset=hex(offset),before='304cf8eb',after=replacement.hex(),
            arm_cases_passed=len(cases),cases=cases,runtime_verified=False,
            scope='Execute original SpeedChange click handler and original feature lookup; soft-float comparison, player accessor and event-bus boundaries controlled. Only the button-local feature-20 call is replaced; no purchase records, currency or global entitlement function changed.')
(out/'unlock-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='cases'},indent=2))
