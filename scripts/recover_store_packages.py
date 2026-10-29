"""Round 18: original package setter, byte paths, aliases and nonempty teardown."""
import hashlib,json,shutil
import recover_owned_stores as h
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base
OUT=base/'native_analysis/core_round18/store_packages';OUT.mkdir(parents=True,exist_ok=True)
NARROW_OBJ,WIDE_OBJ,OUT_OBJ,BACK_OBJ=0x6006000,0x6006100,0x6006200,0x6006300
PATH_VALUES=0x6005000
FUNCTIONS=dict(normalize=0x11e71c4,filename=0x11e6f10,effective=0x11e63b4,
 directory=0x11450b8,basename=0x11473ac,base_pointer=0x11471cc,last_set=0x113ffdc,
 narrow=0x1141e38,widen=0x1141d80,package=0x11ebe2c)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
SCENARIOS=[]
def step(op,type=2,a=0,b=0,c=0,h=0,name=0,d=(7,8,9)):return dict(op=op,type=type,a=a,b=b,c=c,h=h,name=name,d=list(d))
def sc(label,paths,steps,configs=None,kind='owner'):
 SCENARIOS.append(dict(label=label,kind=kind,paths=[[ord(c) for c in p] for p in paths],configs=configs or [],steps=steps))
paths=['','foo','foo.rton','foo.RTON','foo.part.json','packages/foo.rton','PACKAGES/Foo.JSON','Packages\\Foo.ext',
 'dir/file.rton','dir\\file.rton','PACKAGES\\dir\\Mixed.ext','packages/','/','\\','\\\\server','\\\\server\\share',
 '\\\\server\\share\\file.rton','C:foo.ext','C:\\dir\\file.ext','dir.with.dot/file','dir/.hidden','.','..',
 'packages/foo..json','packages//foo.rton','../packages/../foo.ext','a/../b.rton','植物/豌豆.rton','🍄.rton',
 'Ā','xĀy.rton','packages/xĀy.rton','Ŝfolder/file.rton','dir/colon:name.ext','packages\\.hidden','double..',
 'trailing/','foo?query.rton','packages/UPPER','packagesx/foo.rton']
for i,path in enumerate(paths):
 sc(f'byte-path-{i}',[path],[step('convert'),step('normalize'),step('filename')],kind='path')
 sc(f'package-owner-{i}',[path],[step('ensure',a=0),step('set_package',a=0),step('effective'),step('query_alias'),step('set_package',a=0xffffffff),step('remove')],[h.config(3,'owner')])
sc('same-canonical-keeps-first-filename',['PACKAGES/Foo.json','packages/Foo.rton','Foo.yaml','packages\\Foo.zzz','foo.rton','packages/foo.RTON'],
 [step('ensure',a=0)]+[step('set_package',a=i) for i in range(6)]+[step('remove')],[h.config(2,'same')])
sc('package-alias-collision',['packages/foo.rton','foo.json','foo.ext'],[
 step('ensure',2,a=0),step('ensure',3,a=1),step('set_package',2,a=0),step('set_package',3,a=1),step('query_alias',2),
 step('set_package',3,a=0xffffffff),step('query_alias',2),step('set_package',2,a=2),step('query_alias',2),step('remove',2),step('remove',3)],
 [h.config(2,'A'),h.config(2,'B')])
sc('alias-equals-store-name',['$owner'],[step('ensure',a=0),step('set_package',a=0),step('query_alias'),step('set_package',a=0xffffffff),step('query_effective'),step('remove')],[h.config(2,'owner')])
sc('alias-equals-another-store-name',['$B'],[step('ensure',2,a=0),step('ensure',3,a=1),step('set_package',2,a=0),step('query_effective',3),step('set_package',2,a=0xffffffff),step('query_effective',3),step('remove',3),step('remove',2)],[h.config(2,'A'),h.config(2,'B')])
for type in [2,0x2001]:
 for hard in [0,1]:
  sc(f'package-object-lifecycle-{type}-{hard}',['packages/levels/test.rton'],[step('ensure',type,a=0),step('create',type,a=1),
   step('bind',type),step('set_package',type,a=0),step('resolve_package',type),step('reset',type,a=hard),step('resolve_package',type),
   step('create',type,a=2,h=1),step('bind',type,h=1),step('resolve_package',type),step('remove',type)],[h.config(3,'objects')])
for path in ['foo','packages/foo.rton','植物/豌豆.rton']:
 sc('drop-path-owner-'+str(len(path)),[path],[step('ensure',a=0),step('set_package',a=0),step('release_path',a=0),step('effective'),step('set_package',a=0xffffffff),step('remove')],[h.config(2,'owned')])
sc('zero-canonical-with-stored-filename',['foo','.','..'],[step('ensure',a=0),step('set_package',a=0),step('set_package',a=1),step('effective'),step('set_package',a=0xffffffff),step('set_package',a=2),step('remove')],[h.config(2,'dots')])

def logical_narrow(ptr):return list(bytes(h.u.mem_read(ptr,h.words(ptr-12)[0])))
def logical_wide(ptr):return h.words(ptr,h.words(ptr-12)[0])
def snapshot():
 out=h.snapshot()
 for r in h.records:
  out.append(int(r['alive']))
  if r['alive']:
   s=r['address'];p=h.words(s+0xdc)[0];filename=logical_wide(p)
   selected=h.call(FUNCTIONS['effective'],[s]);out.extend([h.words(s+0xd4)[0],len(filename),*filename,h.words(selected)[0]])
 return out
def seed(sc):
 h.cursor=0x8000000;h.records=[];h.events=[];h.alias_ids=[]
 h.u.mem_write(0x6000000,bytes(0x20000));h.put(0x18cbf94,0);h.put(0x18cbf98,0);h.put(0x18cbf70,h.REG);h.put(0x18cbf74,h.REG)
 # Constant 9 is assigned by original _INIT_1265; executing that whole initializer
 # would also register unrelated RTTI. Set its evidenced prefix parameter here.
 h.put(0x18cbf6c,9)
 h.put(h.REG+0x18,0x87654321);h.put(h.REG+0x20,0,0,h.REG+0x20,h.REG+0x20)
 for offset,buffer,target in [(0x34,0x6004000,0x5000400),(0x44,0x6004100,0x5000404)]:
  h.put(h.REG+offset+4,buffer,buffer+24,buffer+24);h.put(buffer+20,target)
 h.pool=h.call(0x11f13a8,[])
 if sc['kind']=='path':return []
 for i in range(3):
  h.put(h.QUERY,*[ord(c) for c in f'别名-{i}'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[h.VALUE+i*8,h.REF]);h.alias_ids.append(h.words(h.VALUE+i*8)[0])
 for i,cfg in enumerate(sc['configs']):
  p=h.PARAM+i*64;h.put(p,cfg['reserve'],0,0x16c5e40,0x194a588,0)
  if cfg['name'] is not None:
   h.put(h.QUERY,*cfg['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[p+4,h.REF])
  raw=bytes(cfg['display']);h.u.mem_write(h.QUERY,raw+b'\0');h.call(0x14fc3f9,[p+12,h.QUERY,len(raw)])
  h.u.mem_write(p+16,bytes([cfg['fixed'],cfg['system']]))
 ids=[]
 for i,text in enumerate(sc['paths']):
  h.put(h.QUERY,*text,0);h.put(h.REF,h.QUERY);h.call(0x594184,[PATH_VALUES+i*8,h.REF]);ids.append(h.words(PATH_VALUES+i*8)[0])
 for i in range(1,128):h.put(h.OBJECT+i*32,0x600bf00)
 h.put(0x600bf00+20,0x5000500)
 return ids
checkpoints=0
for sc in SCENARIOS:
 ids=seed(sc);handles=[[0,0] for _ in range(32)];sc['initial']=[] if sc['kind']=='path' else snapshot()
 for number,s in enumerate(sc['steps']):
  op,type,a,b,c,k,name=[s[x] for x in ['op','type','a','b','c','h','name']];result=[];h.events=[]
  try:
   if sc['kind']=='path':
    text=sc['paths'][0]
    if op=='convert':
     h.put(h.QUERY,*text,0);h.call(0x14fb451,[WIDE_OBJ,h.QUERY,0]);h.call(FUNCTIONS['narrow'],[NARROW_OBJ,WIDE_OBJ,0]);raw=logical_narrow(h.words(NARROW_OBJ)[0]);h.call(FUNCTIONS['widen'],[BACK_OBJ,NARROW_OBJ]);wide=logical_wide(h.words(BACK_OBJ)[0]);result=[len(raw),*raw,len(wide),*wide]
    else:
     raw=bytes([v&255 for v in text]);h.u.mem_write(h.QUERY,raw+b'\0');h.put(NARROW_OBJ,0x194a588);h.call(0x14fc3f9,[NARROW_OBJ,h.QUERY,len(raw)])
     h.call(FUNCTIONS[op],[OUT_OBJ,0,NARROW_OBJ]);raw=logical_narrow(h.words(OUT_OBJ)[0]);result=[len(raw),*raw]
   else:
    store=h.store_for(type)
    if op=='ensure':
     h.call(h.FUNCTIONS['ensure'],[h.REG,type,0 if a==0xffffffff else h.PARAM+a*64]);store=h.store_for(type);result=[next(i+1 for i,r in enumerate(h.records) if r['address']==store)]
    elif op=='set_package':h.put(h.REF,0 if a==0xffffffff else ids[a]);h.call(FUNCTIONS['package'],[store,h.REF])
    elif op=='effective':result=[h.words(h.call(FUNCTIONS['effective'],[store]))[0]]
    elif op in ['query_alias','query_effective']:
     id=h.words(store+0xd4)[0] if op=='query_alias' else h.words(h.call(FUNCTIONS['effective'],[store]))[0]
     h.put(h.REF,id);p=h.call(0x11e7570,[h.REG,h.REF]);result=[next(i+1 for i,r in enumerate(h.records) if r['address']==p) if p else 0]
    elif op=='release_path':h.call(0x11f1f08,[h.pool,ids[a]])
    elif op=='remove':
     result=[int(bool(store))]
     if store:h.call(h.FUNCTIONS['remove'],[store]);h.call(0x14d2e95,[store]);next(r for r in h.records if r['address']==store)['alive']=False
    elif op=='reset':h.call(h.FUNCTIONS['reset'],[store,a])
    elif op=='create':
     h.put(h.DESC,*s['d']);h.call(h.FUNCTIONS['create'],[h.DEST,store,h.OBJECT+a*32 if a else 0,b],[c,h.DESC]);handles[k]=h.words(h.DEST,2);result=handles[k]
    elif op=='bind':h.put(h.REF,h.alias_ids[name]);h.put(h.HANDLE,*handles[k]);result=[h.call(h.FUNCTIONS['bind'],[store,h.REF,h.HANDLE])]
    elif op=='resolve_package':
     id=h.words(h.call(FUNCTIONS['effective'],[store]))[0];h.put(h.HANDLE,h.alias_ids[name]|((id&1)<<31),0x80000000|(id>>1));result=[h.call(h.FUNCTIONS['resolve'],[h.REG,h.HANDLE])]
    else:raise AssertionError(op)
   s['result']=result;s['events']=h.events;s['state']=[] if sc['kind']=='path' else snapshot();checkpoints+=1
  except Exception as error:raise RuntimeError(f"{sc['label']}/{number}/{op} PC={h.u.reg_read(h.UC_ARM_REG_PC):08x}: {error}") from error
assert all(h.hits[n] for n in FUNCTIONS),h.hits
for label,a,b in [('package_setter',0x11ebe2c,0x11ec274),('package_paths',0x11e6f10,0x11e73e0)]:
 md=Cs(CS_ARCH_ARM,CS_MODE_ARM);(OUT/(label+'.asm')).write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(SCENARIOS),checkpoints=checkpoints,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=SCENARIOS,
 scope='Real original nonempty package setter, path helpers, low-byte conversion, constructor/reset/destructor, pools and indices execute. Prefix length 9 seeded from _INIT_1265 evidence, without unrelated RTTI initializer. Successful allocation/libc/single-thread kuser CAS and external callback/destructor bodies controlled. Compare logical string lengths including embedded zero bytes; no original pointer/COW ABI, arbitrary prefix configuration, failures, reentrancy or concurrency.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(SCENARIOS),'original package/path/lifecycle scenarios;',checkpoints,'state checkpoints')
