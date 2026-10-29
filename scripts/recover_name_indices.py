"""Original unsigned name trees, real-pool binding, and bank factory orchestration."""
import hashlib,itertools,json,random,shutil,struct
from native_emulation_support import base,machine
from unicorn import UC_HOOK_CODE,UcError
from unicorn.arm_const import *
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM

OUT=base/'native_analysis/core_round16/name_indices';OUT.mkdir(parents=True,exist_ok=True)
RAW,REG,STORE,SLOTS=0x6000000,0x6001000,0x6002000,0x6004000
KEY,KEY_REF,QUERY,VALUE,HANDLE,DEST=0x6005000,0x6005100,0x6006000,0x6007000,0x6007100,0x6007200
STACK,STOP=0x4080000,0x5000100
FUNCTIONS=dict(find=0x11ea54c,type_position=0x11ebbec,type_insert=0x11ebc9c,type_clear=0x11eab1c,
 object_position=0x11ed354,object_hint=0x11ed404,object_insert=0x11ed520,link=0x11ead38,
 object_clear=0x11ea120,bind=0x11ee270,ensure=0x11eefb0,reserve=0x11e7cb4,append=0x11eab5c,
 canonical=0x11e761c,resolve=0x1ea034,lookup=0x11e6a90)
SCENARIOS=[]
def step(op,key=0,a=0,b=0,d=(4,5,6),hint=None):return dict(op=op,key=key,a=a,b=b,d=list(d),hint=hint)
def sc(label,kind,steps,obj=False):SCENARIOS.append(dict(label=label,kind=kind,object=obj,steps=steps))
keys=[0,1,7,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
for obj in [False,True]:
 for order in itertools.permutations([0,1,7]):
  for deletion in [order,order[::-1]]:
   sc(f'order-{obj}-{order}-{deletion}','index',[step('put',k,a=i+9,d=(i,5,6)) for i,k in enumerate(order)]+[step('erase',k) for k in deletion],obj)
 sc(f'unsigned-{obj}','index',[step('put',k,a=i+9,d=(i,0xffffffff-i,6)) for i,k in enumerate(keys)]+[step('find',k) for k in keys+[2,8]]+[step('clear')],obj)
 for hint in [None,0,4,8,12]:
  for k in range(14):
   sc(f'hint-{obj}-{hint}-{k}','index',[step('put',i,a=i+3,d=(i,5,6)) for i in [0,4,8,12]]+[step('insert',k,a=99,d=(99,98,97),hint=hint),step('find',k),step('clear')],obj)
 sc(f'duplicates-{obj}','index',[step('put',7,a=1),step('insert',7,a=2,d=(7,8,9)),step('put',7,a=3,d=(1,2,3)),step('find',7),step('erase',7),step('erase',7)],obj)
rng=random.Random(0x4e414d45)
for obj in [False,True]:
 for n in range(6):
  live=set();steps=[]
  for i in range(140):
   k=rng.choice(keys+list(range(16)));op=rng.choice(['put','insert','erase','find'])
   hint=rng.choice(sorted(live)) if op=='insert' and live and rng.randrange(2) else None
   steps.append(step(op,k,a=i,d=(i,0x80000000+i,9),hint=hint))
   if op in ['put','insert']:live.add(k)
   elif op=='erase':live.discard(k)
  steps.append(step('clear'));sc(f'mixed-{obj}-{n}','index',steps,obj)
valid=[(0x10000,2<<17),(0x20001,2<<17),(0x30002,2<<17)]
for name in [0,2,3,7,8]:
 sc(f'bind-replace-{name}','binding',[step('bind',name,a=valid[0][0],b=valid[0][1]),step('lookup',name),step('canonical',name),step('resolve',name),step('bind',name,a=valid[1][0],b=valid[1][1]),step('lookup',name),step('bind',name,a=0x90000,b=2<<17),step('lookup',name),step('bind',name,a=valid[2][0],b=valid[2][1]),step('bind',name),step('lookup',name)],True)
sc('binding-reference-owner','binding',[step('bind',2,a=valid[0][0],b=valid[0][1]),step('drop_name',2),step('canonical',2),step('resolve',2),step('bind',2),step('lookup',2)],True)
sc('binding-wrong-type-removes-old','binding',[step('bind',2,a=valid[0][0],b=valid[0][1]),step('bind',2,a=valid[0][0],b=3<<17),step('lookup',2)],True)
for n in range(8):
 steps=[]
 for i in range(60):
  name=rng.randrange(2,9);which=rng.randrange(5)
  low,high=valid[which] if which<3 else (0,0) if which==3 else (0x90000,2<<17)
  steps.extend([step('bind',name,a=low,b=high),step(rng.choice(['lookup','canonical','resolve']),name)])
 steps.append(step('clear'));sc(f'binding-mixed-{n}','binding',steps,True)
sc('factory-bank-growth','factory',[step('ensure',k,a=i+101) for i,k in enumerate([0,0,15,16,1,31,32,0x2000,0x200f,0x2010,0x2000,0x2020,0x201f,32,48,0x2030])])
for n in range(4):
 sc(f'factory-mixed-{n}','factory',[step('ensure',rng.randrange(64)|(0x2000 if rng.randrange(2) else 0),a=i+501) for i in range(80)])

u,imports=machine();u.mem_map(0x8000000,0x2000000);u.mem_map(0xffff0000,0x1000)
cursor=0x8000000;kind='index';events=[];mock_pool=True;pool=0;stores={};tree=RAW
hits={k:0 for k in FUNCTIONS};core_hits={}
def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
def words(a,n=1):return list(struct.unpack('<'+'I'*n,u.mem_read(a,n*4)))
def wide(a):
 out=[]
 for i in range(0x10000):
  v=words(a+4*i)[0]
  if not v:return out
  out.append(v)
 raise AssertionError('unterminated text')
def alloc(size):
 global cursor
 a=cursor;cursor+=(size+63)&~63;assert cursor<0xa000000;u.mem_write(a,b'\xcc'*size);return a
def bank_slot(type):
 vector=REG if type&0x2000 else REG+12;index=type&~0x2000 if type&0x2000 else type
 begin,end=words(vector,2);return begin+index*4 if index<(end-begin)//4 else 0
def hook(uc,a,size,_):
 for name,entry in FUNCTIONS.items():
  if a==entry:hits[name]+=1
 r0,r1,r2=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
 name=imports.get(a)
 if a in [0x14e2d78,0x14e2e64,0x11f1e38,0x11f125c]:core_hits[f'{a:08x}']=core_hits.get(f'{a:08x}',0)+1
 if kind=='factory' and a==0x11ec764:
  serial=len(stores)+1;stores[r0]=(serial,r1)
  slot=bank_slot(r1);published=words(slot)[0] if slot else 0
  events.extend([0,serial,r1,r2,int(published!=0)])
  uc.mem_write(r0,bytes(0x184));put(r0,r1)
 elif kind=='factory' and a==0x11ee42c:
  matches=[(p,serial,type,off) for p,(serial,type) in stores.items() for off in [0x148,0x158,0x168,0x178] if r0==p+off]
  assert len(matches)==1
  p,serial,type,off=matches[0];offset=words(r1+4)[0]
  assert offset==[0x34,0x44,0x54,0x64][[0x148,0x158,0x168,0x178].index(off)]
  events.extend([1,serial,offset,int(words(bank_slot(type))[0]==p)])
  return # Observe but execute the original forwarder vector append.
 elif mock_pool and a==0x11f13a8:uc.reg_write(UC_ARM_REG_R0,0x6000800)
 elif mock_pool and a in [0x11f153c,0x11f14cc,0x11f1f08]:
  events.extend([{0x11f153c:0,0x11f14cc:1,0x11f1f08:2}[a],r1])
  if a==0x11f14cc:uc.reg_write(UC_ARM_REG_R0,0x16c5e40)
 elif a==0xffff0fc0:
  matched=words(r2)[0]==r0
  if matched:put(r2,r1)
  uc.reg_write(UC_ARM_REG_R0,0 if matched else 1)
 elif a==0x14d1a7c or name=='malloc':uc.reg_write(UC_ARM_REG_R0,alloc(r0))
 elif a==0x14d2e94 or name=='free':pass
 elif name in ['memcpy','memmove','wmemcpy','wmemmove']:
  n=r2*(4 if name.startswith('w') else 1);uc.mem_write(r0,bytes(uc.mem_read(r1,n)))
 elif name=='memset':uc.mem_write(r0,bytes([r1&255])*r2)
 elif name=='wmemset':uc.mem_write(r0,struct.pack('<I',r1)*r2)
 elif name=='wcslen':uc.reg_write(UC_ARM_REG_R0,len(wide(r0)))
 elif name=='wcscmp':
  x,y=wide(r0),wide(r1);uc.reg_write(UC_ARM_REG_R0,0 if x==y else 0xffffffff if x<y else 1)
 elif name:raise AssertionError('unexpected import '+name)
 else:return
 uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
def call(a,args):
 u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP)
 saved=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
 for i,r in enumerate(saved):u.reg_write(r,0xabc00000+i)
 for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],list(args)+[0]*4):u.reg_write(r,v)
 u.emu_start(a,STOP,count=1000000)
 assert u.reg_read(UC_ARM_REG_PC)==STOP and u.reg_read(UC_ARM_REG_SP)==STACK
 assert all(u.reg_read(r)==0xabc00000+i for i,r in enumerate(saved))
 return u.reg_read(UC_ARM_REG_R0)
def init_tree(t):put(t+4,0,0,t+4,t+4);put(t+20,0)
def lookup(t,key):
 put(KEY,key);return call(FUNCTIONS['find'],[t,KEY])
def tree_state(t,obj):
 color,root,minimum,maximum=words(t+4,4);nodes=[]
 def visit(n):
  if n:visit(words(n+8)[0]);nodes.append(n);visit(words(n+12)[0])
 visit(root);ranks={0:0xffffffff,t+4:0xfffffffe,**{n:i for i,n in enumerate(nodes)}}
 out=[color,ranks[root],ranks[minimum],ranks[maximum],words(t+20)[0]]
 assert len(nodes)==out[-1]
 for n in nodes:
  v=words(n,9 if obj else 6);out.extend([v[0],ranks[v[1]],ranks[v[2]],ranks[v[3]],v[4],*(v[6:9] if obj else v[5:6])])
 return out
def pool_state():
 begin,end,cap=words(pool+24,3);count=(end-begin)//4;entries=words(begin,count) if count else []
 tags={pool+0x24:0xfffffffe,pool+0x38:0xffffffff,**{p:i for i,p in enumerate(entries)}}
 out=[count,(cap-begin)//4,words(pool+20)[0]]
 for off in [0x24,0x38]:out.extend(tags[p] for p in words(pool+off,2))
 for e in entries:
  v=words(e,5);text=wide(v[3]);out.extend([tags[v[0]],tags[v[1]],v[2],v[4],len(text),*text])
 nodes=[]
 def visit(n):
  if n:visit(words(n+8)[0]);nodes.append(n);visit(words(n+12)[0])
 c,r,l,h=words(pool+4,4);visit(r);ranks={0:0xffffffff,pool+4:0xfffffffe,**{n:i for i,n in enumerate(nodes)}}
 out.extend([c,ranks[r],ranks[l],ranks[h],len(nodes)])
 for n in nodes:
  v=words(n,6);out.extend([v[0],ranks[v[1]],ranks[v[2]],ranks[v[3]],v[5]])
 return out
def state(obj):
 if kind=='factory':
  out=[]
  for t in [REG,REG+12]:
   begin,end,cap=words(t,3);n=(end-begin)//4;out.extend([n,(cap-begin)//4]);out.extend(stores[p][0] if p else 0 for p in (words(begin,n) if n else []))
  return out
 t=tree_state(tree,obj)
 return [len(t),*t,*pool_state()] if kind=='binding' else t
def setup_binding():
 global pool
 pool=call(0x11f13a8,[])
 for i in range(1,9):
  text=[ord(c) for c in f'名称-{i}'];put(QUERY,*text,0);put(KEY_REF,QUERY)
  call(0x594184,[VALUE+(i-1)*8,KEY_REF]);assert words(VALUE+(i-1)*8)[0]==i
 put(REG,0,0,0,REG+0x100,REG+0x10c,REG+0x10c);put(REG+0x100,0,0,STORE)
 put(REG+0x24,REG+0x200);put(REG+0x200,1,REG+0x20,0,0,1,2)
 put(STORE,2,SLOTS,3)
 descriptors=[(4,5,6),(7,8,9),(0,0,0)]
 for i,d in enumerate(descriptors):put(SLOTS+i*32,0,0,0x12345678+i,i+1,1,*d)
 init_tree(STORE+0xe4);put(STORE+0xec,STORE+0x400)
 for i,slot in enumerate([0,2,1]):
  n=STORE+0x400+i*0x40;left=STORE+0x440 if i==0 else 0;right=STORE+0x480 if i==0 else 0
  put(n,1 if i==0 else 0,STORE+0xe8 if i==0 else STORE+0x400,left,right,*descriptors[slot],0,((slot+1)<<16)|slot,2<<17)
 init_tree(STORE+0xfc)
checkpoints=0
for scenario in SCENARIOS:
 kind=scenario['kind'];obj=scenario['object'];mock_pool=kind!='binding';cursor=0x8000000;stores={};events=[]
 u.mem_write(0x6000000,bytes(0x20000));put(0x18cbf94,0);put(0x18cbf98,0);put(0x18cbf70,REG);put(0x18cbf74,REG)
 tree=STORE+0xfc if kind=='binding' else RAW
 init_tree(tree)
 if kind=='binding':setup_binding()
 scenario['initial']=state(obj)
 for number,s in enumerate(scenario['steps']):
  events=[];op,key,a,b=s['op'],s['key'],s['a'],s['b'];result=[]
  try:
   if kind=='factory':
    call(FUNCTIONS['ensure'],[REG,key,a]);p=words(bank_slot(key))[0];result=[stores[p][0]]
   elif kind=='binding':
    put(KEY,key)
    if op=='bind':put(HANDLE,a,b);result=[call(FUNCTIONS[op],[STORE,KEY,HANDLE])]
    elif op=='lookup':call(FUNCTIONS[op],[DEST,STORE,KEY]);result=words(DEST,2)
    elif op in ['canonical','resolve']:
     put(HANDLE,0x80000000|key,0x80000000)
     if op=='canonical':call(FUNCTIONS[op],[DEST,REG,HANDLE]);result=words(DEST,2)
     else:result=[call(FUNCTIONS[op],[REG,HANDLE])]
    elif op=='drop_name':call(0x11f1f08,[pool,key])
    elif op=='clear':call(FUNCTIONS['object_clear'],[tree,words(tree+8)[0]]);init_tree(tree)
   else:
    before=words(tree+20)[0];found=lookup(tree,key);exists=found!=tree+4
    if op=='find':result=[1,*words(found+24,3)] if obj and exists else [1,words(found+20)[0]] if exists else [0]
    elif op=='erase':
     result=[int(exists)]
     if exists:
      node=call(0x14e2e65,[found,tree+4])
      if obj:call(0x11f13a8,[]);call(0x11f1f08,[0x6000800,words(node+16)[0]])
      call(0x14d2e95,[node]);put(tree+20,before-1)
    elif op=='clear':call(FUNCTIONS['object_clear' if obj else 'type_clear'],[tree,words(tree+8)[0]]);init_tree(tree)
    else:
     if op=='put' and exists:node=found
     else:
      hint=found if op=='put' else tree+4 if s['hint'] is None else lookup(tree,s['hint'])
      put(KEY,key);put(KEY_REF,KEY);node=call(FUNCTIONS['object_insert' if obj else 'type_insert'],[tree,hint,0,KEY_REF])
     inserted=words(tree+20)[0]!=before
     if op=='put' or inserted:put(node+(24 if obj else 20),*(s['d'] if obj else [a]))
     if op=='insert':result=[int(inserted)]
   s['result']=result;s['events']=events;s['state']=state(obj);checkpoints+=1
  except (UcError,AssertionError) as error:raise RuntimeError(f"{scenario['label']}/{number}/{op} PC={u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
assert all(hits.values()),hits
for name,a,b in [('object_names',0x11ed354,0x11ed5fc),('binding',0x11ee270,0x11ee42c),('type_names',0x11ebbec,0x11ebe2c),('factory',0x11eefb0,0x11ef350)]:
 md=Cs(CS_ARCH_ARM,CS_MODE_ARM);(OUT/(name+'.asm')).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for address in list(FUNCTIONS.values())+[0x11ec764]:
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(SCENARIOS),checkpoints=checkpoints,function_entry_hits=hits,core_entry_hits=core_hits,scenarios=SCENARIOS,
 scope='Name tree ARM writes and Thumb balancing execute. Raw tree cases control intern retain/text/release boundaries and compare their call order. Binding cases run real intern pool and actual canonical/object lookup with prepared slots/descriptors. Factory cases control only store constructor body; original bank reserve/resize and forwarder append execute. Allocation/libc/single-thread kuser CAS controlled; no complete store constructor, RTTI, package-name normalization, concurrency, failures or reentrancy.')
(OUT/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('PASS',len(SCENARIOS),'original ARM name-index/binding/factory scenarios;',checkpoints,'full-state checkpoints')
