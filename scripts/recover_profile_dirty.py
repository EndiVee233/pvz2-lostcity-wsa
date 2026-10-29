"""Check original ARM dirty/timestamp/save-dispatch functions with bounded hooks."""
import struct,json,shutil,hashlib
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
out=base/'native_analysis/core_round10/profile_dirty';out.mkdir(parents=True,exist_ok=True)
cases=[]
def put(uc,a,v):uc.mem_write(a,struct.pack('<I',v&0xffffffff))
def run(entry,mode,**kw):
 uc,_=machine();p=0x6000000;m=0x6001000;clock=0x6002000;controller=0x6003000;writer=0x6004000;vt=0x6005000;callback=0x5000200;events=[]
 initial=bytearray(b'\xa5'*0x4d8)
 if mode=='dirty':struct.pack_into('<f',initial,4,kw['pending'])
 uc.mem_write(p,bytes(initial));uc.mem_write(m,b'\xa5'*0x98)
 put(uc,m+4,controller);uc.mem_write(m+0x81,bytes([kw.get('blocked',0)]));uc.mem_write(0x18cbe98,bytes([kw.get('global_blocked',0)]))
 put(uc,0x1840528,clock);uc.mem_write(clock+0x24,struct.pack('<f',10.0));put(uc,0x18400a4,m)
 put(uc,writer,vt);put(uc,vt+0x10,callback)
 uc.reg_write(UC_ARM_REG_R0,m if mode=='dispatch' else p);uc.reg_write(UC_ARM_REG_R1,777)
 uc.reg_write(UC_ARM_REG_SP,0x4080000);uc.reg_write(UC_ARM_REG_LR,0x5000100)
 regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_FP]
 for r in regs:uc.reg_write(r,0xabc000+r)
 def hook(uc,a,size,user):
  if a==0x15ef070:
   def f(r):return struct.unpack('<f',struct.pack('<I',uc.reg_read(r)))[0]
   uc.reg_write(UC_ARM_REG_R0,int(f(UC_ARM_REG_R0)<f(UC_ARM_REG_R1)))
  elif a==0x71a924 and mode in ('dirty','setter'):
   assert uc.reg_read(UC_ARM_REG_R0)==p;events.append('timestamp')
  elif a==0x7b8ed0 and mode in ('dirty','setter'):
   assert uc.reg_read(UC_ARM_REG_R0)==m;events.append('dispatch')
  elif a==0xf854ac:events.append('clock-service')
  elif a==0xf8530c:uc.reg_write(UC_ARM_REG_R0,kw['service_time']&0xffffffff)
  elif a==0x157824:
   assert uc.reg_read(UC_ARM_REG_R0)==0;events.append('system-time');uc.reg_write(UC_ARM_REG_R0,123456)
  elif a==0x2ec77c:
   assert uc.reg_read(UC_ARM_REG_R0)==controller;events.append('get-writer');uc.reg_write(UC_ARM_REG_R0,writer)
  elif a==callback:
   assert uc.reg_read(UC_ARM_REG_R0)==writer;events.append('request-save')
  else:return
  uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(entry,0x5000100,count=300)
 assert uc.reg_read(UC_ARM_REG_PC)==0x5000100 and uc.reg_read(UC_ARM_REG_SP)==0x4080000
 for r in regs:assert uc.reg_read(r)==0xabc000+r
 expected=bytearray(initial)
 if mode=='dirty':
  changed=kw['pending']<0 or kw['pending']<10
  if changed:struct.pack_into('<f',expected,4,-1)
  assert events==(['timestamp','dispatch'] if changed else [])
 elif mode=='timestamp':
  value=kw['service_time'] if kw['service_time']>0 else 123456
  struct.pack_into('<i',expected,0x4d4,value)
  assert events==(['clock-service']+([] if kw['service_time']>0 else ['system-time']))
 elif mode=='dispatch':
  expected_manager=bytearray(b'\xa5'*0x98);struct.pack_into('<I',expected_manager,4,controller);expected_manager[0x81]=kw['blocked'];expected_manager[0x80]=1
  assert bytes(uc.mem_read(m,0x98))==expected_manager
  assert events==(['get-writer','request-save'] if not kw['blocked'] and not kw['global_blocked'] else [])
 elif mode=='setter':
  struct.pack_into('<I',expected,0x1ec,777);struct.pack_into('<f',expected,4,-1)
  assert events==['timestamp','dispatch']
 assert bytes(uc.mem_read(p,len(expected)))==expected
 cases.append({'entry':hex(entry),'mode':mode,'inputs':{k:str(v) for k,v in kw.items()},'events':events,'memory_and_abi_verified':True})
for pending in (-1.0,0.0,9.0,10.0,11.0,float('nan'),float('inf'),-float('inf')):run(0x7210c4,'dirty',pending=pending)
for t in (-1,0,999):run(0x71a924,'timestamp',service_time=t)
for a in (0,1):
 for b in (0,1):run(0x7b8ed0,'dispatch',blocked=a,global_blocked=b)
# Setter tail-calls mark-dirty; negative initial bits trigger the dirty branch.
run(0x721ce4,'setter')
folder=out/'pseudocode';folder.mkdir(exist_ok=True)
for address in ('007210c4','0071a924','007b8ed0','00721ce4'):
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(address+'_*.c'):shutil.copy2(p,folder/p.name)
record={'original_sha256':hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),'cases_passed':len(cases),'cases':cases,'scope':'Original ARM functions; initialized manager and clock singleton paths only. Float comparison, time services and storage access mocked. No save serialization or disk write tested.'}
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print('PASS',len(cases),'original ARM dirty-state checks')
