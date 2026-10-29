"""Run the real store constructor/reset/destructor with real intern/name trees.

No store-constructor stub. Control allocator/libc/kuser primitives and external
object/registry callback bodies. Package ID remains zero in this bounded owner.
"""
import hashlib,json,random,shutil,struct
from native_emulation_support import base,machine
from unicorn import UC_HOOK_CODE,UcError
from unicorn.arm_const import *
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
OUT=base/'native_analysis/core_round17/owned_stores';OUT.mkdir(parents=True,exist_ok=True)
REG,PARAM,QUERY,REF,VALUE,HANDLE,DEST,DESC=0x6000000,0x6001000,0x6003000,0x6003100,0x6003200,0x6003300,0x6003400,0x6003500
OBJECT=0x600a000;STACK,STOP=0x4080000,0x5000100
FUNCTIONS=dict(construct=0x11ec764,remove=0x11ec274,reset=0x11ea17c,ensure=0x11eefb0,
 forward=0x11e5c80,package=0x11ebe2c,create=0x11ed120,bind=0x11ee270,
 resolve=0x1ea034,release=0x11e6450,retain=0x11e6424,drain=0x11e6b0c)
SCENARIOS=[]
def config(reserve=0,name=None,display='',fixed=0,system=0):return dict(reserve=reserve,name=None if name is None else [ord(c) for c in name],display=list(display.encode('utf-8')),fixed=fixed,system=system)
def step(op,type=2,a=0,b=0,c=0,h=0,name=0,d=(7,8,9)):return dict(op=op,type=type,a=a,b=b,c=c,h=h,name=name,d=list(d))
def scenario(label,configs,steps):SCENARIOS.append(dict(label=label,configs=configs,steps=steps))
for type in [0,2,15,16,0x2000,0x2001,0x2010]:
 scenario(f'default-{type}',[],[step('ensure',type,a=0xffffffff),step('ensure',type,a=0xffffffff),step('reset',type,a=0),step('reset',type,a=1),step('remove',type),step('remove',type),step('ensure',type,a=0xffffffff),step('remove',type)])
for name in ['', '植物','same','$already','🍄']:
 scenario('named-'+repr(name),[config(3,name,'显示名称 / UTF-8',255,129)],
  [step('ensure',a=0),step('reset',a=1),step('remove')])
scenario('constructor-ignores-new-config-on-reuse',[config(1,'first','one',1,2),config(4,'second','two',3,4)],
 [step('ensure',a=0),step('ensure',a=1),step('remove'),step('ensure',a=1),step('remove')])
scenario('duplicate-name-unregister',[config(2,'same')],[step('ensure',2,a=0),step('ensure',3,a=0),step('remove',2),step('remove',3)])
scenario('provided-name-ref-release',[config(2,'old')],[step('ensure',a=0),step('drop_config',a=0),step('remove')])
for mode in [0,1,2]:
 for hard in [0,1]:
  scenario(f'object-reset-{mode}-{hard}',[config(4,'objects')],[step('ensure',a=0),
   step('create',a=1,b=mode,h=0),step('create',a=2,b=0,h=1,d=(10,11,12)),step('retain',h=0),
   step('bind',h=0,name=0),step('resolve',name=0),step('reset',a=hard),step('resolve',name=0),
   step('create',a=3,b=0,h=2),step('bind',h=2,name=0),step('resolve',name=0),step('remove')])
scenario('deferred-then-hard-reset',[config(3,'deferred')],[step('ensure',a=0),step('create',a=1,b=1),step('release'),step('reset',a=1),step('remove')])
scenario('null-and-nonowned',[config(3,'mixed')],[step('ensure',a=0),step('create',a=0,b=0),step('create',a=2,b=2,h=1),step('reset',a=1),step('remove')])
scenario('multiple-banks-remove-order',[config(1,'bank')],[step('ensure',t,a=0) for t in [0x2002,1,0x2000,3]]+[step('remove',t) for t in [0x2000,0x2002,1,3]])
for type in [2,0x2001]:
 scenario(f'default-descriptor-{type}',[config(3,'default-desc')],[step('ensure',type,a=0),step('create_default',type,a=1),step('bind',type),step('resolve',type),step('reset',type),step('remove',type)])
rng=random.Random(0x53544f52)
for n in range(6):
 steps=[step('ensure',a=0)]
 for i in range(8):
  steps += [step('create',a=1+i,b=rng.randrange(3),h=i,d=(i+1,5,6)),step('bind',h=i,name=i%3),step('resolve',name=i%3)]
  if i in [2,5]:steps.append(step('reset',a=rng.randrange(2)))
 steps += [step('reset',a=1),step('remove')]
 scenario(f'mixed-lifecycle-{n}',[config(4,'random')],steps)

u,imports=machine();u.mem_map(0x8000000,0x4000000);u.mem_map(0xffff0000,0x1000)
cursor=0x8000000;pool=0;records=[];events=[];hits={k:0 for k in FUNCTIONS};alias_ids=[]
def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
def words(a,n=1):return list(struct.unpack('<'+'I'*n,u.mem_read(a,n*4)))
def wide(a):
 out=[]
 for i in range(0x10000):
  v=words(a+4*i)[0]
  if not v:return out
  out.append(v)
 raise AssertionError('unterminated wide text')
def narrow(a):
 out=bytearray()
 for i in range(0x10000):
  b=bytes(u.mem_read(a+i,1))[0]
  if not b:return bytes(out)
  out.append(b)
 raise AssertionError('unterminated narrow text')
def alloc(size):
 global cursor
 a=cursor;cursor+=(size+63)&~63;assert cursor<0xc000000;u.mem_write(a,b'\xcc'*size);return a
def bank_slot(type):
 v=REG if type&0x2000 else REG+12;i=type&~0x2000 if type&0x2000 else type
 begin,end=words(v,2);return begin+i*4 if i<(end-begin)//4 else 0
def store_for(type):
 p=bank_slot(type);return words(p)[0] if p else 0
def find_key(t,key):
 n=words(t+8)[0];candidate=t+4
 while n:
  if words(n+16)[0]<key:n=words(n+12)[0]
  else:candidate=n;n=words(n+8)[0]
 return candidate if candidate!=t+4 and words(candidate+16)[0]==key else 0
def event_registry(offset,s):
 serial=next(i+1 for i,r in enumerate(records) if r['address']==s)
 type=words(s)[0];name=words(s+0xc4)[0];alias=find_key(REG+0x1c,name)
 events.extend([0,offset,serial,words(s+0xc0)[0],words(s+8)[0],*[words(s+x)[0] for x in [0x50,0x2c,0x74,0x98]],words(s+0xf8)[0],words(s+0x110)[0],int(bool(alias)),words(alias+20)[0] if alias else 0,int(store_for(type)==s)])
def hook(uc,a,size,_):
 for name,entry in FUNCTIONS.items():
  if a==entry:hits[name]+=1
 r0,r1,r2,r3=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
 name=imports.get(a)
 if a==0x11ec764:
  records.append(dict(address=r0,alive=True));return # Execute the REAL constructor.
 if a in [0x5000400,0x5000404]:event_registry(0x34 if a==0x5000400 else 0x44,r1)
 elif a==0x5000500:
  matches=[]
  for serial,r in enumerate(records,1):
   if not r['alive']:continue
   s=r['address'];slots,cap=words(s+4,2)
   for i in range(cap):
    slot=slots+i*32
    if words(slot+8)[0]==r0:matches.append((serial,s,i,slot))
  assert matches
  serial,s,i,slot=matches[0];v=words(slot,8)
  events.extend([1,r0,serial,i,v[3],v[4],v[5],words(s+0x50)[0],words(s+0x74)[0],words(s+0xf8)[0],words(s+0x110)[0]])
 elif a==0xffff0fc0:
  ok=words(r2)[0]==r0
  if ok:put(r2,r1)
  uc.reg_write(UC_ARM_REG_R0,0 if ok else 1)
 elif a==0x14d1a7c or name=='malloc':uc.reg_write(UC_ARM_REG_R0,alloc(r0))
 elif a==0x14d2e94 or name=='free':pass
 elif name in ['memcpy','memmove','wmemcpy','wmemmove']:
  n=r2*(4 if name.startswith('w') else 1);uc.mem_write(r0,bytes(uc.mem_read(r1,n)))
 elif name=='memset':uc.mem_write(r0,bytes([r1&255])*r2)
 elif name=='wmemset':uc.mem_write(r0,struct.pack('<I',r1)*r2)
 elif name=='wcslen':uc.reg_write(UC_ARM_REG_R0,len(wide(r0)))
 elif name=='strlen':uc.reg_write(UC_ARM_REG_R0,len(narrow(r0)))
 elif name in ['wcscmp','strcmp','strncmp','strncasecmp']:
  x,y=(wide(r0),wide(r1)) if name=='wcscmp' else (narrow(r0),narrow(r1))
  if name in ['strncmp','strncasecmp']:x,y=x[:r2],y[:r2]
  if name=='strncasecmp':x,y=x.lower(),y.lower()
  uc.reg_write(UC_ARM_REG_R0,0 if x==y else 0xffffffff if x<y else 1)
 elif name=='wmemcmp':
  x,y=words(r0,r2),words(r1,r2);uc.reg_write(UC_ARM_REG_R0,0 if x==y else 0xffffffff if x<y else 1)
 elif name=='memcmp':
  x,y=bytes(uc.mem_read(r0,r2)),bytes(uc.mem_read(r1,r2));uc.reg_write(UC_ARM_REG_R0,0 if x==y else 0xffffffff if x<y else 1)
 elif name=='memchr':
  found=bytes(uc.mem_read(r0,r2)).find(bytes([r1&255]));uc.reg_write(UC_ARM_REG_R0,0 if found<0 else r0+found)
 elif name=='sprintf':
  assert narrow(r1)==b'%d';value=r2 if r2<0x80000000 else r2-0x100000000;data=str(value).encode();uc.mem_write(r0,data+b'\0');uc.reg_write(UC_ARM_REG_R0,len(data))
 elif name:raise AssertionError('unexpected import '+name)
 else:return
 uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
def call(a,args,extras=()):
 u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP)
 saved=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
 for i,r in enumerate(saved):u.reg_write(r,0xabc00000+i)
 for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(r,v)
 if extras:put(STACK,*extras)
 u.emu_start(a,STOP,count=2000000)
 assert u.reg_read(UC_ARM_REG_PC)==STOP and u.reg_read(UC_ARM_REG_SP)==STACK
 assert all(u.reg_read(r)==0xabc00000+i for i,r in enumerate(saved))
 return u.reg_read(UC_ARM_REG_R0)
def tree_state(t,mode):
 color,root,lo,hi=words(t+4,4);nodes=[]
 def visit(n):
  if n:visit(words(n+8)[0]);nodes.append(n);visit(words(n+12)[0])
 visit(root);rank={0:0xffffffff,t+4:0xfffffffe,**{n:i for i,n in enumerate(nodes)}}
 out=[color,rank[root],rank[lo],rank[hi],words(t+20)[0]];assert len(nodes)==out[-1]
 for n in nodes:
  v=words(n,10 if mode=='descriptor' else 9 if mode=='object' else 6)
  out.extend([v[0],rank[v[1]],rank[v[2]],rank[v[3]],*v[4:7],*v[8:10]] if mode=='descriptor' else [v[0],rank[v[1]],rank[v[2]],rank[v[3]],v[4],*(v[6:9] if mode=='object' else v[5:6])])
 return out
def pool_state():
 begin,end,cap=words(pool+24,3);count=(end-begin)//4;entries=words(begin,count) if count else []
 tags={pool+0x24:0xfffffffe,pool+0x38:0xffffffff,**{p:i for i,p in enumerate(entries)}}
 out=[count,(cap-begin)//4,words(pool+20)[0]]
 for off in [0x24,0x38]:out.extend(tags[p] for p in words(pool+off,2))
 for e in entries:
  v=words(e,5);text=wide(v[3]);out.extend([tags[v[0]],tags[v[1]],v[2],v[4],len(text),*text])
 # Intern tree values are entry indices (key pointers are normalized away).
 color,root,lo,hi=words(pool+4,4);nodes=[]
 def visit(n):
  if n:visit(words(n+8)[0]);nodes.append(n);visit(words(n+12)[0])
 visit(root);rank={0:0xffffffff,pool+4:0xfffffffe,**{n:i for i,n in enumerate(nodes)}}
 out.extend([color,rank[root],rank[lo],rank[hi],len(nodes)])
 for n in nodes:
  v=words(n,6);out.extend([v[0],rank[v[1]],rank[v[2]],rank[v[3]],v[5]])
 return out
def slot_state(s):
 slots,cap=words(s+4,2);tags={s+off:0xfffffffc+i for i,off in enumerate([0xc,0x30,0x54,0x78])}
 def norm(p):
  if p in tags:return tags[p]
  assert slots<=p<slots+cap*32 and (p-slots)%32==0
  return (p-slots)//32
 out=[cap,*[words(s+x)[0] for x in [0x2c,0x50,0x74,0x98]]]
 for off in [0xc,0x30,0x54,0x78]:out.extend(norm(p) for p in words(s+off,2))
 for i in range(cap):
  v=words(slots+i*32,8);out.extend([norm(v[0]),norm(v[1]),*v[2:]])
 return out
def append(out,part):out.extend([len(part),*part])
def snapshot():
 out=[];serials={r['address']:i+1 for i,r in enumerate(records)}
 bank=[]
 for v in [REG,REG+12]:
  b,e,c=words(v,3);n=(e-b)//4;bank.extend([n,(c-b)//4]);bank.extend(serials[p] if p else 0 for p in (words(b,n) if n else []))
 append(out,bank);append(out,tree_state(REG+0x1c,'type'));append(out,pool_state());out.append(len(records))
 for r in records:
  out.append(int(r['alive']))
  if not r['alive']:continue
  s=r['address'];display=list(narrow(words(s+0xcc)[0]));flags=bytes(u.mem_read(s+0xd0,2))
  data=[words(s)[0],words(s+0xc0)[0],words(s+0xc4)[0],flags[0],flags[1],len(display),*display]
  append(data,slot_state(s));append(data,tree_state(s+0xe4,'descriptor'));append(data,tree_state(s+0xfc,'object'))
  data.extend((words(s+off+4)[0]-words(s+off)[0])//24 for off in [0x148,0x158,0x168,0x178])
  append(out,data)
 return out
def run():
 global cursor,pool,records,events,alias_ids
 checkpoints=0
 for sc in SCENARIOS:
  cursor=0x8000000;records=[];events=[];alias_ids=[]
  u.mem_write(0x6000000,bytes(0x20000));put(0x18cbf94,0);put(0x18cbf98,0);put(0x18cbf70,REG);put(0x18cbf74,REG)
  put(REG+0x18,0x87654321);put(REG+0x20,0,0,REG+0x20,REG+0x20)
  for offset,buffer,target in [(0x34,0x6004000,0x5000400),(0x44,0x6004100,0x5000404)]:
   put(REG+offset+4,buffer,buffer+24,buffer+24);put(buffer+20,target)
  pool=call(0x11f13a8,[])
  for i in range(3):
   text=[ord(c) for c in f'别名-{i}'];put(QUERY,*text,0);put(REF,QUERY);call(0x594184,[VALUE+i*8,REF]);alias_ids.append(words(VALUE+i*8)[0])
  for i,cfg in enumerate(sc['configs']):
   p=PARAM+i*64;put(p,cfg['reserve'],0,0x16c5e40,0x194a588,0)
   if cfg['name'] is not None:
    put(QUERY,*cfg['name'],0);put(REF,QUERY);call(0x594184,[p+4,REF])
   raw=bytes(cfg['display']);u.mem_write(QUERY,raw+b'\0');call(0x14fc3f9,[p+12,QUERY,len(raw)])
   u.mem_write(p+16,bytes([cfg['fixed'],cfg['system']]))
  for i in range(1,128):put(OBJECT+i*32,0x600bf00)
  put(0x600bf00+20,0x5000500)
  handles=[[0,0] for _ in range(32)];sc['initial']=snapshot()
  for number,s in enumerate(sc['steps']):
   op,type,a,b,c,h,name=[s[k] for k in ['op','type','a','b','c','h','name']];events=[];result=[]
   try:
    store=store_for(type)
    if op=='ensure':
     call(FUNCTIONS[op],[REG,type,0 if a==0xffffffff else PARAM+a*64]);store=store_for(type)
     result=[next(i+1 for i,r in enumerate(records) if r['address']==store)]
    elif op=='remove':
     result=[int(bool(store))]
     if store:
      call(FUNCTIONS[op],[store]);call(0x14d2e95,[store]);next(r for r in records if r['address']==store)['alive']=False
    elif op=='drop_config':call(0x11f1f08,[pool,words(PARAM+a*64+4)[0]])
    elif op=='reset':call(FUNCTIONS[op],[store,a])
    elif op in ['create','create_default']:
     put(DESC,*s['d']);call(FUNCTIONS['create'],[DEST,store,OBJECT+a*32 if a else 0,b],[c,DESC if op=='create' else 0]);handles[h]=words(DEST,2);result=handles[h]
    elif op in ['retain','release']:
     put(HANDLE,*handles[h]);r=call(FUNCTIONS[op],[store,HANDLE]);result=[r] if op=='release' else []
    elif op=='bind':
     put(REF,alias_ids[name]);put(HANDLE,*handles[h]);result=[call(FUNCTIONS[op],[store,REF,HANDLE])]
    elif op=='resolve':
     type_name=words(store+0xc4)[0];put(HANDLE,alias_ids[name]|((type_name&1)<<31),0x80000000|(type_name>>1));result=[call(FUNCTIONS[op],[REG,HANDLE])]
    s['result']=result;s['events']=events;s['state']=snapshot();checkpoints+=1
   except (UcError,AssertionError) as error:raise RuntimeError(f"{sc['label']}/{number}/{op} PC={u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
 assert all(hits.values()),hits
 for label,a,b in [('constructor',0x11ec764,0x11ecc78),('destructor',0x11ec274,0x11ec614),('reset',0x11ea17c,0x11ea4e0)]:
  md=Cs(CS_ARCH_ARM,CS_MODE_ARM);(OUT/(label+'.asm')).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
 folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
 for address in FUNCTIONS.values():
  for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
 record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(SCENARIOS),checkpoints=checkpoints,function_entry_hits=hits,scenarios=SCENARIOS,
  scope='Real original 011ec764 constructor, 011ec274 teardown, 011ea17c soft/hard reset, factory, intern/name/descriptor/slot/string code execute together. No constructor/reset stub. Allocator/libc/single-thread kuser CAS and external object/registry callback bodies controlled. Nonempty package mutation, arbitrary object classes, RTTI, allocation failures, zero-reference active slots, callback mutation/reentrancy/concurrency and original COW ABI not covered.')
 (OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
 print('PASS',len(SCENARIOS),'real original store lifecycle scenarios;',checkpoints,'full-state checkpoints')

if __name__ == "__main__":
 run()
