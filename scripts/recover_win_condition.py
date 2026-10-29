"""Round 31: bounded original ZombiesDeadWinCon predicate, not a full board."""
import json,struct,hashlib
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
out=base/'native_analysis/core_round31/win_condition';out.mkdir(parents=True,exist_ok=True)
def put(u,a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
scenarios=[([],[]),([0],[]),([1,4],[]),([2],[]),([0,2],[3]),([3],[3]),([],[0]),([],[1]),([],[2]),([],[3]),([],[4]),([],[3,4]),([],[4,3]),([0,1],[0,1,2,3]),([0,4],[3,3])]
# registry fixture codes: 0 null handle, 1 missing bank, 2 expired object,
# 3 live object predicate false, 4 live object predicate true.
rows=[]
for flags,kinds in scenarios:
 u,_=machine();app=0x6000000;board=0x6001000;entities=0x6003000;vector=board+0x9ec;handles=0x6004000;registry=0x6005000;store=0x6006000;copy=0x6008000;events=[]
 put(u,0x1846b60,app);put(u,app+0x6bc,board);put(u,0x18400a8,registry)
 put(u,vector,entities,entities+len(flags)*4)
 for i,f in enumerate(flags):p=0x6009000+i*0x40;put(u,entities+i*4,p);put(u,p+0x1c,f)
 for i,k in enumerate(kinds):put(u,handles+i*8,0 if k==0 else i+1,0 if k==0 else 0x25<<17)
 last=None;visits=[]
 def hook(u,a,size,user):
  global last
  r=[u.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
  if a==0x14d1a7c:
   assert r[0]==len(flags)*4;u.reg_write(UC_ARM_REG_R0,copy);events.append('allocate-snapshot')
  elif a==0x1577a0:u.mem_write(r[0],bytes(u.mem_read(r[1],r[2])));events.append('copy-snapshot')
  elif a==0x14d2e94:assert r[0]==copy;events.append('free-snapshot')
  elif a==0x874970:
   assert r[1:3]==[registry,0x25];put(u,r[0],0,0,handles,handles+len(kinds)*8);events.append('enumerate-0x25')
  elif a==0x1e9bb4:put(u,r[0],r[2],r[3])
  elif a==0x11e74b4:u.reg_write(UC_ARM_REG_R0,registry)
  elif a==0x11e761c:
   lo,hi=struct.unpack('<II',u.mem_read(r[2],8));put(u,r[0],lo,hi)
   last=(lo-1 if lo else None);visits.append(last)
  elif a==0x11e7538:
   assert r[1]==0x25;events.append('find-bank-'+str(last));u.reg_write(UC_ARM_REG_R0,0 if kinds[last]==1 else store)
  elif a==0x11e6620:
   events.append('resolve-'+str(last))
   k=kinds[last];p=0x600b000+last*0x100;vt=0x600d000+last*0x100
   put(u,p,vt);put(u,vt+0xd4,0x5000200);u.reg_write(UC_ARM_REG_R0,0 if k==2 else p)
  elif a==0x5000200:events.append('predicate-'+str(last));u.reg_write(UC_ARM_REG_R0,int(kinds[last]==4))
  elif a==0x11e99e4:events.append('release-enumeration')
  else:return
  u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 u.reg_write(UC_ARM_REG_SP,0x4080000);u.reg_write(UC_ARM_REG_LR,0x5000100)
 regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_FP]
 for reg in regs:u.reg_write(reg,0x123000+reg)
 u.emu_start(0xb78c70,0x5000100,count=3000)
 assert u.reg_read(UC_ARM_REG_PC)==0x5000100 and u.reg_read(UC_ARM_REG_SP)==0x4080000
 for reg in regs:assert u.reg_read(reg)==0x123000+reg
 result=u.reg_read(UC_ARM_REG_R0);assert result==int(not any(f&2 for f in flags) and 4 not in kinds)
 if flags:assert events[-1]=='free-snapshot'
 if not any(f&2 for f in flags):assert 'release-enumeration' in events
 rows.append(dict(entity_flags=flags,registry_kinds=kinds,result=result,events=events,visited=visits,abi_verified=True))
r=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),entry='00b78c70',entity_flag_test='0024eeb8',board_vector='0021a1c0 => Board+0x9ec',cases=rows,scope='Original predicate and real entity flag read; allocation/copy, registry enumeration, handle normalization/resolution, virtual predicate and cleanup helpers controlled. No full Board, zombie lifecycle or victory event dispatch.')
(out/'validation.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print('PASS',len(rows),'original ARM win predicate cases')
