"""Run original intern pool, wide-string runtime, tree and handle operations.

Allocation, libc and the single-thread kuser atomic primitive are controlled. Pool IDs, reference counts,
entry recycling, pointer-table growth, COW string calls and tree operations run
as original instructions. Snapshot strings are UTF-32 words, not host wchar_t.
"""
import hashlib,json,random,shutil,struct
from native_emulation_support import base,machine
from unicorn import UC_HOOK_CODE,UcError
from unicorn.arm_const import *
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM

OUT=base/'native_analysis/core_round15/engine_intern';OUT.mkdir(parents=True,exist_ok=True)
QUERY,QUERY_REF,DEST=0x6002000,0x6003000,0x6003100
VALUES,HANDLES=0x6004000,0x6005000
REG,STORE,SLOTS=0x6008000,0x6009000,0x600a000
STACK,STOP=0x4080000,0x5000100
FUNCTIONS=dict(singleton=0x11f13a8,intern=0x11f2ed8,ensure=0x11f2d28,lookup=0x11f1df8,
 tree_lookup=0x11f1d88,retain=0x11f153c,retain_raw=0x11f125c,release=0x11f1f08,
 release_raw=0x11f1ed4,recycle=0x11f1e38,text=0x11f14cc,table_grow=0x11f2808,
 position=0x11f2aa8,insert=0x11f2b5c,acquire=0x594184,assign=0x158a20,drop=0x1589f0,
 handle=0x1e9bb4,canonical=0x11e761c,resolve=0x1ea034)
SCENARIOS=[]
def step(op,text=None,a=0,b=0,h=0,j=0):return dict(op=op,text=None if text is None else [ord(c) for c in text],a=a,b=b,h=h,j=j)
def scenario(label,steps):SCENARIOS.append(dict(label=label,steps=steps))
for text in ['', 'A','a','豌豆射手','植物大战僵尸','🍄🌻','é','e\u0301','prefix','prefix-long','A\0Z']:
 scenario('text-'+repr(text),[step('intern',text),step('lookup',text),step('acquire',text),step('text',h=0),step('retain',h=0),step('release',h=0),step('drop',h=0),step('lookup',text),step('acquire','复用',h=1),step('drop',h=1)])
scenario('null-empty',[step('intern'),step('acquire'),step('text'),step('retain'),step('release'),step('drop')])
scenario('duplicates',[step('acquire','同名',h=i) for i in range(3)]+[step('drop',h=i) for i in [1,0,2]])
scenario('reuse-last-freed',[step('acquire',f'name-{i}',h=i) for i in range(4)]+[step('drop',h=i) for i in [1,3,0,2]]+[step('intern',f'new-{i}') for i in range(4)])
scenario('table-growth',[step('acquire',f'项目-{i:02}',h=i) for i in range(33)]+[step('drop',h=i) for i in list(range(0,33,2))+list(range(1,33,2))])
scenario('assign-distinct',[step('acquire','旧名称',h=0),step('acquire','新名称',h=1),step('assign',h=0,j=1),step('drop',h=0),step('drop',h=1)])
scenario('assign-shared',[step('acquire','same',h=0),step('acquire','same',h=1),step('assign',h=0,j=1),step('drop',h=1),step('drop',h=0)])
scenario('assign-self-one-reference',[step('acquire','self',h=0),step('assign',h=0,j=0),step('lookup','self'),step('text',h=0)])
scenario('assign-from-zero',[step('acquire','old'),step('assign',h=0,j=1),step('text'),step('drop')])
for count in [0,1,2,0x7fffffff,0xfffffffe,0xffffffff]:
 scenario(f'count-wrap-{count:08x}',[step('acquire','count'),step('write_count',a=count),step('retain'),step('release'),step('text')])
symbol_low,symbol_high=0x80000002,0x80000000
scenario('symbolic-handle-real-pool',[step('acquire','类型',h=0),step('acquire','对象',h=1),step('handle',a=symbol_low,b=symbol_high),step('drop',h=0),step('drop',h=1),step('canonical'),step('resolve'),step('handle',a=symbol_low,b=symbol_high),step('handle'),step('lookup','类型'),step('lookup','对象')])
scenario('symbolic-same-name',[step('acquire','类型',h=0),step('handle',a=0x80000001,b=0x80000000),step('drop',h=0),step('canonical'),step('handle')])
rng=random.Random(0x494e5445)
texts=['alpha','beta','gamma','A','a','植物','僵尸','🌻','豌豆','prefix','prefix-more','é']
for number in range(8):
 occupied=set();steps=[]
 for i in range(100):
  empty=sorted(set(range(8))-occupied)
  choices=['lookup','intern']+(['acquire']*3 if empty else [])+(['drop','text','retain_pair']*2 if occupied else [])+(['assign'] if len(occupied)>1 else [])
  op=rng.choice(choices)
  if op=='acquire':
   h=rng.choice(empty);occupied.add(h);steps.append(step(op,rng.choice(texts),h=h))
  elif op=='drop':
   h=rng.choice(sorted(occupied));occupied.remove(h);steps.append(step(op,h=h))
  elif op=='assign':
   h,j=rng.sample(sorted(occupied),2);steps.append(step(op,h=h,j=j))
  elif op=='retain_pair':
   h=rng.choice(sorted(occupied));steps.extend([step('retain',h=h),step('release',h=h)])
  elif op=='text':steps.append(step(op,h=rng.choice(sorted(occupied))))
  else:steps.append(step(op,rng.choice(texts)))
 steps.extend(step('drop',h=h) for h in sorted(occupied))
 scenario(f'mixed-{number}',steps)

u,imports=machine();u.mem_map(0x8000000,0x1000000);u.mem_map(0xffff0000,0x1000)
cursor=0x8000000;pool=0;hits={k:0 for k in FUNCTIONS};string_assign_hits=0
def put(a,*v):u.mem_write(a,struct.pack('<'+'I'*len(v),*v))
def words(a,n=1):return list(struct.unpack('<'+'I'*n,u.mem_read(a,n*4)))
def wide(a):
 out=[]
 for i in range(0x10000):
  v=words(a+4*i)[0]
  if not v:return out
  out.append(v)
 raise AssertionError('unterminated string')
def alloc(size):
 global cursor
 result=cursor;cursor+=(size+63)&~63
 assert cursor<0x9000000
 u.mem_write(result,b'\xcc'*size);return result
def hook(uc,a,size,_):
 global string_assign_hits
 for name,entry in FUNCTIONS.items():
  if a==entry:hits[name]+=1
 if a==0x14fa6fc:string_assign_hits+=1
 name=imports.get(a)
 r0,r1,r2=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
 if a==0xffff0fc0:
  matched=words(r2)[0]==r0
  if matched:put(r2,r1)
  uc.reg_write(UC_ARM_REG_R0,0 if matched else 1)
 elif a==0x14d1a7c or name=='malloc':uc.reg_write(UC_ARM_REG_R0,alloc(r0))
 elif a==0x14d2e94 or name=='free':pass
 elif name in ('memcpy','memmove','wmemcpy','wmemmove'):
  length=r2*(4 if name.startswith('w') else 1);uc.mem_write(r0,bytes(uc.mem_read(r1,length)))
 elif name=='memset':uc.mem_write(r0,bytes([r1&255])*r2)
 elif name=='wmemset':uc.mem_write(r0,struct.pack('<I',r1)*r2)
 elif name=='wcslen':uc.reg_write(UC_ARM_REG_R0,len(wide(r0)))
 elif name=='wcscmp':
  x,y=wide(r0),wide(r1);uc.reg_write(UC_ARM_REG_R0,0 if x==y else 0xffffffff if x<y else 1)
 elif name:raise AssertionError(f'unexpected import {name}')
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
def entry_address(id):return words(words(pool+0x18)[0]+(id-1)*4)[0]
def fixture_registry():
 put(REG,REG+0x100,REG+0x100,REG+0x100,REG+0x110,REG+0x11c,REG+0x11c)
 put(REG+0x110,0,0,STORE);put(REG+0x24,REG+0x200)
 put(REG+0x200,1,REG+0x20,0,0,1,2)
 put(STORE,2,SLOTS,1);put(SLOTS,0,0,0x12345678,1,1,4,5,6)
 put(STORE+0xec,STORE+0x200);put(STORE+0x200,1,STORE+0xe8,0,0,4,5,6,0,0x10000,2<<17)
 put(STORE+0x104,STORE+0x300);put(STORE+0x300,1,STORE+0x100,0,0,2,0,4,5,6)
def snapshot():
 start,end,cap=words(pool+0x18,3);count=(end-start)//4;capacity=(cap-start)//4
 entries=words(start,count) if count else []
 tags={pool+0x24:0xfffffffe,pool+0x38:0xffffffff,**{e:i for i,e in enumerate(entries)}}
 state=[count,capacity,words(pool+0x14)[0]]
 for offset in [0x24,0x38]:state.extend(tags[p] for p in words(pool+offset,2))
 for e in entries:
  v=words(e,5);text=wide(v[3]);state.extend([tags[v[0]],tags[v[1]],v[2],v[4],len(text),*text])
 nodes=[]
 def visit(n):
  if n:visit(words(n+8)[0]);nodes.append(n);visit(words(n+12)[0])
 color,root,minimum,maximum=words(pool+4,4);visit(root)
 ranks={0:0xffffffff,pool+4:0xfffffffe,**{n:i for i,n in enumerate(nodes)}}
 state.extend([color,ranks[root],ranks[minimum],ranks[maximum],len(nodes)])
 assert len(nodes)==words(pool+0x14)[0]
 for n in nodes:
  v=words(n,6);state.extend([v[0],ranks[v[1]],ranks[v[2]],ranks[v[3]],v[5]])
 return state
checkpoints=0
for sc in SCENARIOS:
 cursor=0x8000000;u.mem_write(0x6000000,bytes(0x20000));put(0x18cbf94,0);put(0x18cbf98,0)
 pool=call(FUNCTIONS['singleton'],[]);assert call(FUNCTIONS['singleton'],[])==pool
 fixture_registry();sc['initial']=snapshot()
 for number,s in enumerate(sc['steps']):
  op,a,b,h,j=[s[k] for k in ['op','a','b','h','j']]
  text=s['text'];query=0 if text is None else QUERY
  if text is not None:put(QUERY,*text,0)
  put(QUERY_REF,query);value=VALUES+h*8;source=VALUES+j*8
  id=words(value)[0];result=[]
  try:
   if op=='intern':result=[call(FUNCTIONS[op],[pool,query])]
   elif op=='lookup':
    e=call(FUNCTIONS[op],[pool,query]);result=[words(e+8)[0]+1 if e else 0]
   elif op=='acquire':
    assert call(FUNCTIONS[op],[value,QUERY_REF])==value
    id,p=words(value,2);result=[id,len(wide(p)),*wide(p)]
   elif op=='assign':
    call(FUNCTIONS[op],[value,source]);id,p=words(value,2);result=[id,len(wide(p)),*wide(p)]
   elif op=='drop':result=[call(FUNCTIONS[op],[value])]
   elif op=='retain':call(FUNCTIONS[op],[pool,id])
   elif op=='release':result=[call(FUNCTIONS[op],[pool,id])]
   elif op=='text':
    p=call(FUNCTIONS[op],[pool,id]);t=wide(p);result=[len(t),*t]
   elif op=='write_count':put(entry_address(id)+16,a)
   elif op=='handle':
    call(FUNCTIONS[op],[HANDLES,0,a,b]);result=words(HANDLES,2)
   elif op=='canonical':
    assert call(FUNCTIONS[op],[DEST,REG,HANDLES])==DEST;result=words(DEST,2)
   elif op=='resolve':result=[call(FUNCTIONS[op],[REG,HANDLES])]
   else:raise AssertionError(op)
   s['result']=result;s['state']=snapshot();checkpoints+=1
  except (UcError,AssertionError) as error:
   raise RuntimeError(f"{sc['label']}/{number}/{op} PC={u.reg_read(UC_ARM_REG_PC):08x}: {error}") from error
assert all(hits.values()),hits
for name,a,b in [('intern_core',0x11f1d88,0x11f1f34),('intern_create',0x11f2808,0x11f2f0c),('intern_access',0x11f13a8,0x11f1568)]:
 md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
 (OUT/(name+'.asm')).write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(SCENARIOS),checkpoints=checkpoints,function_entry_hits=hits,original_wide_assign_calls=string_assign_hits,scenarios=SCENARIOS,
 state_format='Entry count/capacity/tree size, free/live next/prev indices; entries: next,prev,index,refs,text length,text UTF-32 words; tree header color/root/min/max ranks/size, then ordered color/parent/left/right/entry-index nodes. Free sentinel=fffffffe, live=ffffffff. Actual string pointers/storage capacities excluded.',
 scope='Original intern singleton/access/count/create/recycle/vector/string-tree operations and real symbolic handle assignment/canonical/object chain. Original COW wide-string assignment executes; allocator, libc wide/memory primitives and single-thread ARM kuser compare-exchange controlled. Valid null-terminated Unicode input, successful allocation, valid nonzero IDs, no concurrency or reentrancy. Text-address comparisons normalize to entry IDs/content, not original pointers.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(SCENARIOS),'original ARM intern scenarios;',checkpoints,'full-state checkpoints')
print('Original wide-string assignments executed:',string_assign_hits)
