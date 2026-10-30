"""Exercise retained attempt deduction for each mode, count and obfuscation key."""
import json,struct
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
uc,imports=machine();player,manager=0x6000000,0x6001000
def put(a,v):uc.mem_write(a,struct.pack('<I',v&0xffffffff))
def get(a):return struct.unpack('<I',uc.mem_read(a,4))[0]
def encode(value,key):
 shift=key&31;value^=key
 return ((value<<shift)|(value>>(32-shift)))&0xffffffff
def decode(raw,key):
 shift=key&31
 return (((raw>>shift)|(raw<<(32-shift)))&0xffffffff)^key
put(0x18400a4,manager)
def hook(cpu,pc,size,user):
 if pc in (0x7210c4,0x71a924,0x7b8ed0):
  cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 elif pc in imports:raise AssertionError(('unexpected import',imports[pc]))
uc.hook_add(UC_HOOK_CODE,hook)
cases=[]
for mode in range(3):
 for count in (0,1,3):
  for key in (0,13,0x1234567f):
   for offset in (0x334,0x33c,0x344):put(player+offset,encode(count,key));put(player+offset+4,key)
   put(player+4,0xbf800000)
   stack,end=0x4080000,0x5000100
   for reg,val in ((UC_ARM_REG_R0,player),(UC_ARM_REG_R1,mode),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,end)):
    uc.reg_write(reg,val)
   uc.emu_start(0x721e88,end,count=5000)
   assert uc.reg_read(UC_ARM_REG_PC)==end and uc.reg_read(UC_ARM_REG_SP)==stack
   values=[decode(get(player+offset),key) for offset in (0x334,0x33c,0x344)]
   expected=[count]*3;expected[mode]=max(0,count-1)
   assert values==expected,(mode,count,key,values)
   cases.append(dict(mode=mode,initial_count=count,key=key,after_counts=values))
record=dict(arm_cases_passed=len(cases),cases=cases,
 scope='Original victory-side attempt deduction only; no synthetic victory or runtime memory writes.')
(base/'native_analysis/offline_challenge/attempt-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({'arm_cases_passed':len(cases)}))
