"""Disable only Board's present_newer spawner; retain ordinary zombie drops."""
import hashlib,json,struct
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

source=base/'native_analysis/offline_challenge/libSrc-offline-challenge.so'
original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='8e5d9a2afa70efb56a92012b13352770acaac56a32e56ecf7571e9096d6c73d6'
address=0x2304b0;offset=address-0x10000
assert original[offset:offset+4]==bytes.fromhex('f04b2de9')
replacement=bytes.fromhex('1eff2fe1') # bx lr, void spawner, before any allocation/counter update
blob=bytearray(original);blob[offset:offset+4]=replacement
cases=[]
for modified in (False,True):
 for valid in (0,1):
  for armed in (0,1):
   for wave in (None,2,3):
    for mode in (0,4,6):
     uc,_=machine()
     if modified:uc.mem_write(address,replacement)
     board,zombie,waves,obj=0x6000000,0x6001000,0x6002000,0x6003000
     def put(a,*v):uc.mem_write(a,struct.pack('<'+'I'*len(v),*v))
     put(board+0xc0,mode);uc.mem_write(board+0x899,bytes([armed]));put(board+0x89c,3)
     put(waves+0x1c,wave or 0);put(zombie+0x10,0x111,0x222,0x333);put(zombie+0x38,7)
     events=[]
     returns={0x24eeb8:valid,0x21221c:waves if wave is not None else 0,
              0x7c0328:obj,0x11e74b4:obj,0x1ea034:obj}
     observed={0x721c60:'kill_record',0x733bc8:'zombie_record',0x721960:'kill_count',0x22feec:'ordinary_drops'}
     def hook(cpu,pc,size,data):
      if pc==address and not modified:
       events.append('recharge_gift');cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
      elif pc in returns or pc in observed:
       if pc in observed:events.append(observed[pc])
       if pc in returns:cpu.reg_write(UC_ARM_REG_R0,returns[pc])
       cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
     uc.hook_add(UC_HOOK_CODE,hook)
     stack,end=0x4080000,0x5000100
     uc.reg_write(UC_ARM_REG_R0,board);uc.reg_write(UC_ARM_REG_R1,zombie)
     uc.reg_write(UC_ARM_REG_SP,stack);uc.reg_write(UC_ARM_REG_LR,end)
     uc.emu_start(0x2305f0,end,count=500)
     assert uc.reg_read(UC_ARM_REG_PC)==end and uc.reg_read(UC_ARM_REG_SP)==stack
     eligible=bool(valid and armed and wave==3)
     expected=[]
     if eligible and not modified:expected.append('recharge_gift')
     if valid:
      if mode!=6:expected+=['kill_record','zombie_record']
      if mode!=4:expected+=['kill_count']
      expected+=['ordinary_drops']
     assert events==expected,(modified,valid,armed,wave,mode,events,expected)
     assert bytes(uc.mem_read(board+0x899,1))==bytes([0 if eligible else armed])
     cases.append(dict(patched=modified,valid=valid,armed=armed,wave=wave,mode=mode,events=events))
out=base/'native_analysis/no_recharge_gift';out.mkdir(exist_ok=True)
target=out/'libSrc-no-recharge-gift.so';target.write_bytes(blob)
record=dict(source_sha256=hashlib.sha256(original).hexdigest(),patched_sha256=hashlib.sha256(blob).hexdigest(),
            ghidra_address=hex(address),file_offset=hex(offset),before=original[offset:offset+4].hex(),after=replacement.hex(),
            arm_cases_passed=len(cases),runtime_verified=False,cases=cases,
            scope='Original zombie-death callback executed; controlled eligibility, wave, profile and ordinary-drop boundaries. Only the void present_newer spawner entry returns early. Ordinary drop routine remains original and is still called; individual reward RNG not emulated.')
(out/'patch-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='cases'},indent=2))
