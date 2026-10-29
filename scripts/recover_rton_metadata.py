"""Round 19: execute original RTON field writer and store metadata serializer.

Original string cache trees, COW strings and byte writes execute. Use a fixed
output stream buffer to exclude file IO and the not-yet-recovered stream growth
ABI. No high-level writer/serializer function is replaced by a stub.
"""
import hashlib,json,random,shutil
import recover_owned_stores as h
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base
OUT=base/'native_analysis/core_round19/rton_metadata';OUT.mkdir(parents=True,exist_ok=True)
WRITER,STREAM,KEY,VAL,WIDE=0x6008000,0x6008100,0x6008200,0x6008300,0x6008400
FUNCTIONS=dict(metadata=0x11e6b70,integer=0x1200a88,string=0x1200230,cached=0x12000d4,wide=0x1205280,
 varuint=0x11fd650,raw_string=0x11fdb58,raw_wide=0x11fd9d4,codepoint=0x11fd77c,append=0x11fd5c8)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
scenarios=[]
def step(op,number=0,key='',value=(),cached=False):
 return dict(op=op,number=number,key=list(key.encode()) if isinstance(key,str) else key,value=list(value.encode()) if isinstance(value,str) else list(value),cached=cached)
def scenario(label,steps,cfg=None,path=''):
 scenarios.append(dict(label=label,steps=steps,config=cfg,path=[ord(c) for c in path]))
rng=random.Random(0x52544f4e)
numbers=[0,1,63,64,127,128,8191,8192,16383,16384,1048575,1048576,2097151,2097152,0x7fffffff,0x80000000,0xffffffff,0xffffffc0,0xffffffbf,0xffffe000,0xfff00000]+[rng.randrange(1<<32) for _ in range(80)]
scenario('unsigned-varint',[step('varuint',n) for n in numbers])
scenario('integer-tag-choice',[step('integer',n,key='value' if i%2 else '') for i,n in enumerate(numbers)])
scenario('string-cache-and-binary',[step('string',key=k,value=v,cached=c) for k,v,c in [
 ('alpha','x',False),('alpha','x',True),('beta','x',True),('','',True),('alpha','',True),('alpha','alpha',True),
 ('binary',[0,128,255,0,65],False),([0,255,0],'value',True),([0,255,0],'value',True),('beta','x',False)]])
scenario('large-cache-reference',[step('string',key='k'+str(i),value='v'+str(i),cached=True) for i in range(140)]+[step('string',key='k139',value='v139',cached=True),step('string',key='k0',value='v0',cached=True)])
wide_values=[[],[0],[65,0,66],[0x7f,0x80,0x7ff,0x800,0xd7ff,0xd800,0xdfff,0xffff,0x10000,0x10ffff,0x110000,0xffffffff]]
for n in [1,7,8,9,15,16,17,23,24,25,31,32,33,128]:wide_values.append([0x4e00+(i%20) if i%3 else 0x1f344 for i in range(n)])
scenario('wide-byte-length-and-loop',[step('wide',key='wide',value=v) for v in wide_values])
for n in range(18):
 cfg=h.config(n%3,[None,'','植物🍄','$x','ĀŜ'][n%5],'' if n%3==0 else '显示 / UTF-8',255 if n%2 else 0,[0,1,2,129,255][n%5]);cfg['type']=[2,0x2001,0x2000][n%3]
 if n==17:cfg['display']=[65,0,66,255]
 scenario('metadata-'+str(n),[step('metadata'),step('package',1),step('metadata'),step('metadata'),step('package',0),step('metadata')],cfg,['packages/levels/test.rton','PACKAGES/植物.rton','xĀy.json'][n%3])

def narrow_object(obj,data):
 h.u.mem_write(h.QUERY,bytes(data)+b'\0');h.put(obj,0x194a588);h.call(0x14fc3f9,[obj,h.QUERY,len(data)])
def state():
 length=h.words(STREAM+20)[0];out=[length,*bytes(h.u.mem_read(output,length))]
 nodes=[]
 def visit(n):
  if n:visit(h.words(n+8)[0]);nodes.append(n);visit(h.words(n+12)[0])
 visit(h.words(WRITER+32)[0]);out.extend([len(nodes),h.words(WRITER+48)[0]])
 assert len(nodes)==h.words(WRITER+44)[0]
 for node in nodes:
  p=h.words(node+16)[0];size=h.words(p-12)[0];out.extend([size,*bytes(h.u.mem_read(p,size)),h.words(node+20)[0]])
 return out
checks=0
for sc in scenarios:
 h.cursor=0x8000000;h.records=[];h.events=[];h.alias_ids=[]
 h.u.mem_write(0x6000000,bytes(0x20000));h.put(0x18cbf94,0);h.put(0x18cbf98,0);h.put(0x18cbf70,h.REG);h.put(0x18cbf74,h.REG);h.put(0x18cbf6c,9)
 h.put(h.REG+0x18,0x87654321);h.put(h.REG+0x20,0,0,h.REG+0x20,h.REG+0x20)
 h.pool=h.call(0x11f13a8,[]);store=0
 cfg=sc['config']
 if cfg:
  p=h.PARAM;h.put(p,cfg['reserve'],0,0x16c5e40,0x194a588,0)
  if cfg['name'] is not None:h.put(h.QUERY,*cfg['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[p+4,h.REF])
  narrow_object(p+12,cfg['display']);h.u.mem_write(p+16,bytes([cfg['fixed'],cfg['system']]))
  h.call(h.FUNCTIONS['ensure'],[h.REG,cfg['type'],p]);store=h.store_for(cfg['type'])
  h.put(h.QUERY,*sc['path'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[h.VALUE,h.REF]);path_id=h.words(h.VALUE)[0]
 output=h.alloc(0x10000);h.put(STREAM,output,0,0,0,0,0,0);h.put(WRITER,STREAM)
 for off in [24,52]:h.put(WRITER+off+4,0,0,WRITER+off+4,WRITER+off+4,0,0)
 sc['initial']=state()
 for s in sc['steps']:
  op=s['op'];h.events=[]
  try:
   if op=='metadata':
    before=h.snapshot();h.call(FUNCTIONS[op],[store,WRITER]);assert before==h.snapshot(),'metadata mutated owned state'
   elif op=='package':h.put(h.REF,path_id if s['number'] else 0);h.call(h.FUNCTIONS['package'],[store,h.REF])
   elif op=='varuint':h.call(FUNCTIONS[op],[STREAM,s['number']])
   else:
    narrow_object(KEY,s['key'])
    if op=='integer':h.call(FUNCTIONS[op],[WRITER,KEY,s['number']])
    elif op=='string':narrow_object(VAL,s['value']);h.call(FUNCTIONS[op],[WRITER,KEY,VAL,int(s['cached'])])
    elif op=='wide':h.put(WIDE,*s['value'],0);h.call(FUNCTIONS[op],[WRITER,KEY,WIDE,0])
    else:raise AssertionError(op)
   s['state']=state();checks+=1
  except Exception as e:raise RuntimeError(f"{sc['label']}/{checks}/{op} PC={h.u.reg_read(h.UC_ARM_REG_PC):08x}: {e}") from e
 if store:h.call(h.FUNCTIONS['remove'],[store])
assert all(h.hits[n] for n in FUNCTIONS),h.hits
for label,a,b in [('metadata',0x11e6b70,0x11e6f10),('wide',0x11fd77c,0x11fdb58),('integer',0x1200a88,0x1200b94)]:
 md=Cs(CS_ARCH_ARM,CS_MODE_ARM);(OUT/(label+'.asm')).write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for a in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(scenarios),checkpoints=checks,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=scenarios,
 scope='Actual original metadata, integer selection, narrow cache tree, varint, UTF8 codepoint loops and byte append execute. Fixed caller output buffer; no stream expansion/file IO/document root/object payload, wide cache mode, allocation failures or concurrent execution. Cache compared as logical sorted key/index entries, not original tree topology. Allocator/libc/single-thread kuser and external callbacks controlled. Metadata verified not to change owner/intern state.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(scenarios),'original RTON metadata scenarios;',checks,'byte/cache checkpoints')
