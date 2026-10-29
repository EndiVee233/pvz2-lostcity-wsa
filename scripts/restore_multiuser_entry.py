"""Reconnect the retained Chinese player-list screen; preserve the baseline ELF."""
from pathlib import Path
import sys,struct,json,hashlib
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

source=base/'raw/lib/armeabi/libSrc.so'
out=base/'native_analysis/multiuser';out.mkdir(exist_ok=True)
original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='0892806592b0a6a1503d246020a9c69a634c85aa65d9baf2955106ad432420df'
offset=0x460d54;entry=offset+0x10000;target=0x474770
assert original[offset:offset+4]==bytes.fromhex('190000ea')
# Case 3 was B epilogue. BL existing OpenProfilesList, then fall through to
# the next table word (case 4), which is still B epilogue. No code cave needed.
instruction=struct.pack('<I',0xeb000000|(((target-entry-8)//4)&0xffffff))
patched=bytearray(original);patched[offset:offset+4]=instruction
cases=[]
for enabled in (True,False):
 for button in (3,4,5,6,7,8,9,11):
  for modified in (False,True):
   uc,_=machine();calls=[];obj=0x6000000;stack=0x4080000
   if modified:uc.mem_write(entry,instruction)
   uc.mem_write(obj+0xd0,bytes([0 if enabled else 1]))
   uc.reg_write(UC_ARM_REG_R0,obj);uc.reg_write(UC_ARM_REG_R1,button)
   uc.reg_write(UC_ARM_REG_SP,stack);uc.reg_write(UC_ARM_REG_LR,0x5000100)
   def hook(uc,address,size,user):
    if address==0x5000100:uc.emu_stop()
    elif address==target:
     assert uc.reg_read(UC_ARM_REG_R0)==obj
     calls.append(address);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
   uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x470d18,0,count=100)
   assert len(calls)==int(modified and enabled and button==3)
   assert uc.reg_read(UC_ARM_REG_PC)==0x5000100 and uc.reg_read(UC_ARM_REG_SP)==stack
   cases.append({'menu_enabled':enabled,'button':button,'patched':modified,'open_list_calls':len(calls)})
(out/'libSrc-multiuser.so').write_bytes(patched)
record={'original_sha256':hashlib.sha256(original).hexdigest(),'patched_sha256':hashlib.sha256(patched).hexdigest(),
 'file_offset':hex(offset),'ghidra_address':hex(entry),'old_bytes':original[offset:offset+4].hex(),'new_bytes':instruction.hex(),
 'existing_open_list_function':'0x00474770','existing_list_constructor':'0x00474470',
 'changed_bytes':sum(a!=b for a,b in zip(original,patched)),'emulation_cases_passed':len(cases),'cases':cases,
 'scope':'Original ARM dispatcher, list opening mocked at original target; actual list/create/switch/delete still require WSA verification.'}
(out/'entry-patch-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='cases'},indent=2))
