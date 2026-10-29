"""Export profile lifecycle evidence and check original ARM control flow.

Engine lookup, handle lifetime and sync calls are bounded stubs, not emulated
implementations. This script never reads or changes a player's save.
"""
from pathlib import Path
import struct,json,hashlib,shutil
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
out=base/'native_analysis/core_round8/profile_lifecycle';out.mkdir(parents=True,exist_ok=True)
names={0x7ba9f4:'SelectByName',0x7ba95c:'RenameByName',0x7c0b38:'PassesSubstringFilter',0x7ba7c8:'FindByName',0x7baa74:'SelectFirstAvailable',0x7bdeac:'DeleteByName',0x7be820:'CreateProfile',0x7c0bb0:'ValidateAndCreate',0x7c13d0:'ValidateAndRename',0x7b98dc:'GetCurrentProfile'}
blob=(base/'raw/lib/armeabi/libSrc.so').read_bytes();assert hashlib.sha256(blob).hexdigest()=='0892806592b0a6a1503d246020a9c69a634c85aa65d9baf2955106ad432420df'
folder=out/'pseudocode';folder.mkdir(exist_ok=True)
for a in names:
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)
(out/'verified-entry-disassembly.txt').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for a,n in [(0x7ba9f4,128),(0x7ba95c,152),(0x7c0b38,120)] for i in cs.disasm(blob[a-0x10000:a-0x10000+n],a)),encoding='utf-8')
cases=[]
def setup(entry):
 uc,_=machine();uc.reg_write(UC_ARM_REG_SP,0x4080000);uc.reg_write(UC_ARM_REG_LR,0x5000100)
 for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_FP):uc.reg_write(reg,0xabc000+reg)
 return uc
def finish(uc,entry):
 uc.emu_start(entry,0x5000100,count=1000)
 assert uc.reg_read(UC_ARM_REG_PC)==0x5000100 and uc.reg_read(UC_ARM_REG_SP)==0x4080000
 for reg in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_FP):assert uc.reg_read(reg)==0xabc000+reg
 return uc.reg_read(UC_ARM_REG_R0)
for entry in (0x7ba9f4,0x7ba95c):
 for state in ('missing','expired','valid'):
  uc=setup(entry);obj=0x6000000;player=0x6001000;oldname=0x6002000;newname=0x6002100;events=[];handle=None
  uc.mem_write(obj,b'\xa5'*0x98);uc.mem_write(player+0x1ec,struct.pack('<I',12345))
  uc.reg_write(UC_ARM_REG_R0,obj);uc.reg_write(UC_ARM_REG_R1,oldname);uc.reg_write(UC_ARM_REG_R2,newname)
  def hook(uc,a,size,user):
   global handle
   if a==0x7ba7c8:
    assert uc.reg_read(UC_ARM_REG_R1)==obj and uc.reg_read(UC_ARM_REG_R2)==oldname
    handle=uc.reg_read(UC_ARM_REG_R0);uc.mem_write(handle,struct.pack('<II',*( (0,0) if state=='missing' else (0x11223344,0x55667788))))
   elif a==0x11e74b4:uc.reg_write(UC_ARM_REG_R0,0x6003000)
   elif a==0x1ea034:
    assert uc.reg_read(UC_ARM_REG_R1)==handle
    assert bytes(uc.mem_read(handle,8))==struct.pack('<II',0x11223344,0x55667788)
    uc.reg_write(UC_ARM_REG_R0,player if state=='valid' else 0)
   elif a==0x721220:
    assert [uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1)]==[player,newname];events.append('rename')
   elif a==0x7b9ab0:
    assert [uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]==[obj,0,0];events.append('sync')
   elif a==0x1e9bb4:
    assert uc.reg_read(UC_ARM_REG_R0)==handle and uc.reg_read(UC_ARM_REG_R2)==0 and uc.reg_read(UC_ARM_REG_R3)==0;events.append('release')
   else:return
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  uc.hook_add(UC_HOOK_CODE,hook);result=finish(uc,entry)
  assert result==int(state=='valid')
  expected=bytearray(b'\xa5'*0x98)
  if entry==0x7ba9f4 and state=='valid':struct.pack_into('<I',expected,0x74,12345)
  assert bytes(uc.mem_read(obj,0x98))==expected
  assert events==(['rename','sync','release'] if entry==0x7ba95c and state=='valid' else ['release'])
  cases.append({'function':names[entry],'lookup_state':state,'result':result,'events':events,'object_memory_and_abi_verified':True})
for results in ([],[-1],[-1,-1],[0],[2],[-1,0],[-1,3,-1]):
 uc=setup(0x7c0b38);vec=0x6000000;arr=0x6000100;name=0x6000200;events=[]
 uc.mem_write(vec,struct.pack('<II',arr,arr+4*len(results)))
 for n in range(len(results)):
  token=0x6001000+n*0x100;uc.mem_write(arr+4*n,struct.pack('<I',token));uc.mem_write(token-12,struct.pack('<I',n+1))
 uc.reg_write(UC_ARM_REG_R0,name);uc.reg_write(UC_ARM_REG_R1,vec)
 def hook(uc,a,size,user):
  if a!=0x14f9b58:return
  n=len(events);assert [uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]==[name,0x6001000+n*0x100,0,n+1]
  events.append(results[n]);uc.reg_write(UC_ARM_REG_R0,results[n]&0xffffffff)
  uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 uc.hook_add(UC_HOOK_CODE,hook);result=finish(uc,0x7c0b38)
 assert result==int(all(r==-1 for r in results))
 assert len(events)==(next((i+1 for i,r in enumerate(results) if r!=-1),len(results)))
 cases.append({'function':'PassesSubstringFilter','find_results':results,'result':result,'calls_before_early_exit':len(events),'abi_verified':True})
record={'original_sha256':hashlib.sha256(blob).hexdigest(),'cases_passed':len(cases),'cases':cases,'scope':'Original ARM bodies of select/rename/filter; lookup, resolution, rename, sync, reference release and substring search mocked. Not full store/save validation.','source_fragment_compiled':False,'apk_changed':False,'function_map':{f'{a:08x}':n for a,n in names.items()}}
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
oldmap=base/'native_analysis/multiuser/recovered_function_map.json';m=json.loads(oldmap.read_text());m['functions']['007bdeac']='ProfileMgr.DeleteByName';m['functions']['007ba9f4']='ProfileMgr.SelectByName';oldmap.write_text(json.dumps(m,indent=2),encoding='utf-8')
print('Recovered 10 lifecycle pseudocode functions; original ARM cases passed:',len(cases))
