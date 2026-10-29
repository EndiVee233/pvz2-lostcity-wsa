"""Recover core handle packing, slot validation and symbolic reference ordering."""
import struct,json,hashlib,shutil
from native_emulation_support import base,machine
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
out=base/'native_analysis/core_round11/engine_handles';out.mkdir(parents=True,exist_ok=True)
rows=[]
def put(u,a,*values):u.mem_write(a,struct.pack('<'+'I'*len(values),*values))
def setup(args):
 u,_=machine();u.reg_write(UC_ARM_REG_SP,0x4080000);u.reg_write(UC_ARM_REG_LR,0x5000100)
 for r,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(r,v)
 return u
def finish(u,a):
 u.emu_start(a,0x5000100,count=500)
 assert u.reg_read(UC_ARM_REG_PC)==0x5000100 and u.reg_read(UC_ARM_REG_SP)==0x4080000
 return u.reg_read(UC_ARM_REG_R0)
for wide in (False,True):
 for state in ('valid','wrong_type','out_of_range','stale'):
  store=0x6000000;slots=0x6001000;h=0x6002000;index=2 if state!='out_of_range' else 3;gen=0x12345678 if not wide else 0x123456
  lo=(index | ((gen&0xffff)<<16)) if not wide else index | ((gen&0xff)<<24)
  hi=((gen>>16) | (45<<17)) if not wide else (gen>>8) | 0x10000 | (45<<17)
  u=setup([store,h,0]);put(u,store,46 if state=='wrong_type' else 45,slots,3);put(u,h,lo,hi)
  put(u,slots+2*32+12,gen+int(state=='stale'))
  result=finish(u,0x11e62c8);assert result==(slots+64 if state=='valid' else 0)
  rows.append({'function':'lookup_slot','wide':wide,'state':state,'result_valid':result!=0,'low':lo,'high':hi,'generation':gen})
for encoded in (0,1,2,0x2000,0x2001,0x2002,0xffffffff):
 u=setup([0x6000000,encoded]);put(u,0x6000000,0x6001000,0x6001008,0x6001008,0x6002000,0x6002008,0x6002008)
 put(u,0x6001000,111,222);put(u,0x6002000,333,444)
 index=encoded&~0x2000 if encoded&0x2000 else encoded
 expected=([111,222] if encoded&0x2000 else [333,444])[index] if index<2 else 0
 assert finish(u,0x11e7538)==expected
 rows.append({'function':'registry_store','encoded':encoded,'result':expected})
handles=[(0,0),(0x12345678,45<<17),(0x80000007,0x80000002),(9,0xc0000003)]
for old in handles:
 for new in handles:
  dest=0x6000000;u=setup([dest,0,new[0],new[1]]);put(u,dest,*old);events=[]
  def hook(u,a,size,user):
   if a==0x11f13a8:u.reg_write(UC_ARM_REG_R0,0x6001000)
   elif a in (0x11f153c,0x11f1f08):events.append(('retain' if a==0x11f153c else 'release',u.reg_read(UC_ARM_REG_R1)))
   else:return
   u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
  u.hook_add(UC_HOOK_CODE,hook);finish(u,0x1e9bb4)
  expected=[]
  for action,h in [('retain',new),('release',old)]:
   if h[1]&0x80000000:expected.extend([(action,((h[0]>>31)|((h[1]&0x3fffffff)<<1))&0xffffffff),(action,h[0]&0x7fffffff)])
  assert events==expected and bytes(u.mem_read(dest,8))==struct.pack('<II',*new)
  rows.append({'function':'assign_handle','old':old,'new':new,'events':events})
for state,count in [('missing',0),('ready',2),('not_lazy',2),('lazy',0),('lazy',1),('lazy',2)]:
 store=0x6000000;h=0x6002000;slot=0x6003000;callbacks=0x6004000
 u=setup([store,h]);put(u,h,2,45<<17);put(u,slot+8,0x12345678 if state=='ready' else 0)
 put(u,slot+16,0x08000000 if state=='lazy' else 0);put(u,store+0x138,callbacks,callbacks+24*count)
 for i in range(count):put(u,callbacks+24*i+20,0x5000200+i*4)
 events=[]
 def hook(u,a,size,user):
  if a==0x11e62c8:u.reg_write(UC_ARM_REG_R0,0 if state=='missing' else slot)
  elif a in (0x5000200,0x5000204):
   i=(a-0x5000200)//4
   assert u.reg_read(UC_ARM_REG_R0)==callbacks+24*i and u.reg_read(UC_ARM_REG_R1)==h
   events.append(i);put(u,slot+8,0x12345678+i)
  else:return
  u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook);result=finish(u,0x11e6620)
 expected=0x12345678 if state=='ready' else 0x12345678+count-1 if state=='lazy' and count else 0
 assert result==expected and events==(list(range(count)) if state=='lazy' else [])
 rows.append({'function':'resolve_object','state':state,'callback_count':count,'result':result,'events':events})
folder=out/'pseudocode';folder.mkdir(exist_ok=True)
for a in ('011e62c8','011e7538','001e9bb4','001ea034','011e761c','011e6620'):
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(a+'_*.c'):shutil.copy2(p,folder/p.name)
record={'original_sha256':hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),'cases_passed':len(rows),'cases':rows,'scope':'Original ARM for slot lookup, bank lookup, handle assignment and lazy callback iteration. Intern pool access, slot lookup inside resolve_object and callback implementations mocked. Actual resource loading and object creation/destruction not emulated.'}
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print('PASS',len(rows),'original ARM engine handle checks')
