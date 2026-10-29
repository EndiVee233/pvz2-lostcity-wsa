"""Suppress offline cloud-network prompts and both retained announcement screens.

Applied only to the isolated offline v4 native library; not a general dialog hook.
"""
from pathlib import Path
import hashlib,json,sys,shutil
from native_emulation_support import machine,base
from unicorn.arm_const import *

source=base/'native_analysis/multiuser/fixes/libSrc-multiuser-fixed.so'
blob=bytearray(source.read_bytes())
assert hashlib.sha256(blob).hexdigest()=='f58e6ac5a5be1470aea6aa51653693556884ad8287d3e68ea9ae0d4f75e1711b'
out=base/'native_analysis/startup_dialogs';out.mkdir(exist_ok=True)
patches=[];cases=[]
for address,name in [(0x41e944,'CloudNetworkFailurePrompt'),(0x412700,'FirstGameAnnouncement'),(0x4127bc,'ActivityGameAnnouncement')]:
 offset=address-0x10000
 old=bytes(blob[offset:offset+8])
 # All three originals begin with an ARM callee-save push. Return before
 # allocating a modal, hiding menu widgets, pausing gameplay or playing sounds.
 assert old==bytes.fromhex({0x41e944:'f04f2de9b8a29fe5',0x412700:'78482de9153ca0e3',0x4127bc:'78482de94d5da0e3'}[address])
 new=bytes.fromhex('0000a0e31eff2fe1') # mov r0,#0; bx lr
 blob[offset:offset+8]=new
 patches.append({'ghidra_address':hex(address),'file_offset':hex(offset),'name_inferred':name,'original':old.hex(),'patched':new.hex()})
 for arg in (0,0x6000000):
  uc,_=machine();uc.mem_write(address,new)
  stack=0x4080000;end=0x5000100
  for reg,val in [(UC_ARM_REG_R0,arg),(UC_ARM_REG_R1,0x6000100),(UC_ARM_REG_R2,0x6000200),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,end),(UC_ARM_REG_R4,0x12345678)]:uc.reg_write(reg,val)
  uc.emu_start(address,end,count=3)
  assert uc.reg_read(UC_ARM_REG_R0)==0 and uc.reg_read(UC_ARM_REG_PC)==end
  assert uc.reg_read(UC_ARM_REG_SP)==stack and uc.reg_read(UC_ARM_REG_R4)==0x12345678
  cases.append({'function':name,'argument':hex(arg),'returns_zero':True,'stack_and_callee_register_preserved':True})
 folder=out/'recovered_functions';folder.mkdir(exist_ok=True)
 for f in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(f,folder/f.name)
target=out/'libSrc-no-startup-dialogs.so';target.write_bytes(blob)
record={'source_v4_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(blob).hexdigest(),'patches':patches,'bounded_arm_cases':cases,'runtime_verified':False,
 'scope':'Isolated offline package only. Return zero without constructing these dialogs; generic dialogs, profile-delete confirmation and network status are unchanged. Emulator checks only patched exits; WSA verification is separate.'}
(out/'patch-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
