"""Round 22: original indexed RTON navigation over real normalized documents."""
import hashlib,json,shutil
import recover_owned_stores as h
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base
OUT=base/'native_analysis/core_round22/rton_reader';OUT.mkdir(parents=True,exist_ok=True)
STREAM,READER,KEY=0x6008000,0x6008100,0x6008200
FUNCTIONS=dict(peek=0x11f87d8,key_text=0x11f884c,value=0x11f8920,narrow_text=0x11fa28c,
 is_object=0x11fc08c,first=0x11fc0c0,next=0x11fc124,is_array=0x11fc208,count=0x11fc23c,element=0x11fc2ac,find=0x11fdd64)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
source=json.loads((base/'native_analysis/core_round21/rton_normalizer/validation.json').read_text(encoding='utf-8'))
labels={'empty','narrow-cache-order','wide-cache-order','mixed-keys','nested-40','nested-65','array-253-0','array-253-3','array-253-33','array-253-128','all-tags-129','all-tags-130','all-tags-1','all-tags-32','random-document-0','random-document-1','random-document-2','random-document-3'}
inputs=[s for s in source['scenarios'] if s['label'] in labels or s['source']]
scenarios=[];checks=0
def state():return [h.words(STREAM+20)[0],h.words(READER+8)[0]]
for original in inputs:
 for mode in [0,1]:
  h.cursor=0x8000000;h.records=[];h.u.mem_write(0x6000000,bytes(0x20000));h.put(0x18cbf94,0);h.put(0x18cbf98,0);h.pool=h.call(0x11f13a8,[])
  raw=bytes(original['data']);src=h.alloc(len(raw)+64);h.u.mem_write(src,raw+bytes(64));output=h.alloc(0x200000)
  h.put(STREAM,output,0x200000,0,0,0,0,0x100)
  for off in [0x1c,0x34]:h.put(STREAM+off+4,0,0,STREAM+off+4,STREAM+off+4,0)
  assert h.call(0x1202a74,[STREAM,src,len(raw)])==1
  size=h.words(STREAM+20)[0];indexed=bytes(h.u.mem_read(output,size));assert indexed==bytes(original['output'])
  if mode:h.put(STREAM,0,0,output,output+size,output+size)
  h.call(0x11f8818,[READER,STREAM])
  sc=dict(label=original['label']+'-mode'+str(mode),data=original['data'],mode=mode,indexed=list(indexed),initial=state(),steps=[],source=original['source']);scenarios.append(sc)
  def op(name,a=0,b=0,key=b''):
   global checks
   key=key.encode('utf-8') if isinstance(key,str) else bytes(key)
   if name=='seek':h.put(STREAM+20,a);result=[]
   elif name=='find':
    h.u.mem_write(h.QUERY,key+b'\0');h.put(KEY,0x194a588);h.call(0x14fc3f9,[KEY,h.QUERY,len(key)])
    result=[h.call(FUNCTIONS[name],[READER,a,KEY])]
   elif name=='peek':result=[h.call(FUNCTIONS[name],[READER])]
   else:
    value=h.call(FUNCTIONS[name],[READER,a,b])
    if name in ['key_text','narrow_text']:
     if value:assert output<=value<output+size;value-=output
    result=[value]
   sc['steps'].append(dict(op=name,a=a,b=b,key=list(key),result=result,state=state()))
   if name!='seek':checks+=1
   return result[0] if result else 0
  root=h.words(READER+8)[0];op('peek')
  for name in FUNCTIONS:
   if name=='peek':continue
   op('seek',13);op(name,0,0,b'not-global')
  visited=set()
  def text(offset,wide=False):
   return ''.join(chr(c) for c in h.wide(output+offset)).encode('utf-8') if wide else h.narrow(output+offset)
  def walk(offset,depth=0):
   if not offset or offset in visited:return
   assert depth<100;visited.add(offset)
   is_object=op('is_object',offset);is_array=op('is_array',offset);op('count',offset);op('narrow_text',offset)
   op('first',offset);op('element',offset,0);op('element',offset,0xffffffff)
   if is_object:
    field=op('first',offset);fields=[]
    while field:
     pointer=op('key_text',field);value=op('value',field);fields.append((field,pointer,value))
     name=text(pointer,indexed[field] in [0xb6,0xb7]);op('find',offset,key=name)
     field=op('next',field)
    for key in [b'not-global',b'',b'key',b'objects',b'objclass',b'A\0B',b'same']:
     op('seek',root);op('find',offset,key=key)
    for field,pointer,value in fields:walk(value,depth+1)
   elif is_array:
    count=op('count',offset);assert count<1000
    for i in range(count):walk(op('element',offset,i),depth+1)
    op('element',offset,count);op('element',offset,count+1)
  walk(root)
  def member(obj,name):return op('value',op('find',obj,key=name))
  def value_text(value):
   pointer=op('narrow_text',value);return h.narrow(output+pointer).decode('utf-8') if pointer else ''
  if sc['source']:
   summary=dict(root_fields=[],object_count=0,objects=[])
   field=op('first',root)
   while field:
    pointer=op('key_text',field);value=op('value',field)
    summary['root_fields'].append(dict(key=h.narrow(output+pointer).decode('utf-8'),key_offset=field,value_offset=value,tag=indexed[value]))
    field=op('next',field)
   objects=member(root,'objects');count=op('count',objects);summary['object_count']=count
   for i in range(count):
    obj=op('element',objects,i);aliases=member(obj,'aliases');names=[]
    for j in range(op('count',aliases)):names.append(value_text(op('element',aliases,j)))
    summary['objects'].append(dict(index=i,objclass=value_text(member(obj,'objclass')),aliases=names))
   sc['summary']=summary
  assert bytes(h.u.mem_read(output,size))==indexed,'navigation mutated indexed document'
  print('Captured',sc['label'],len(sc['steps']),'operations',flush=True)
assert all(h.hits[n] for n in FUNCTIONS),h.hits
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
for label,a,b in [('navigation',0x11fc08c,0x11fc348),('lookup',0x11fdd64,0x11fdec0)]:
 (OUT/(label+'.asm')).write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
record=dict(original_sha256=source['original_sha256'],scenarios_passed=len(scenarios),checkpoints=checks,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=scenarios,
 scope='Real original normalization/cache trees and indexed reader header/navigation/lookup execute. External-buffer and vector-backed modes. Return pointers normalized to document byte offsets. Compare every returned value and exact cursor/root, indexed bytes unchanged. Seek steps are controlled fixture preparation and excluded from checkpoint count. Valid indexed documents and offsets; no malformed link cycles/out-of-bounds policy equivalence, scalar coercions, RTTI/object construction, original pointer/COW ABI or concurrent shared-stream semantics. Resource summaries use recovered navigation and narrow C-string views, not object deserialization.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(scenarios),'original indexed reader scenarios;',checks,'return/cursor checkpoints')
