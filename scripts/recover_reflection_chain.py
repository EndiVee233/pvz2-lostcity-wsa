"""Round 24: real factories, full original two-pass loader and property calls.

GroundEffect is a real registered class, not a demonstration test class. No
factory, reflection registration, property dispatcher or reference resolver is
stubbed. Low-level single-thread/C-library boundaries are documented separately.
"""
import hashlib,json,shutil,struct
from reflection_emulation_support import h,seed
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base;OUT=base/'native_analysis/core_round24/reflection_chain';OUT.mkdir(parents=True,exist_ok=True)
FUNCTIONS=dict(register=0x11f761c,lookup=0x11f6120,ancestry=0x11f595c,factory=0x254bf8,
 create_pass=0x11ed5fc,fill_pass=0x11ead94,properties=0x11b9bb0,enum_read=0x11b1de0,
 reference_property=0x11b7180,reference_read=0x11f4c90,resolve=0x1ea034)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
ST,V,SER,SC=0x600c000,0x600c100,0x600c200,0x600d000
def vi(n):
 r=[]
 while n>=128:r.append((n&127)|128);n>>=7
 return bytes(r+[n])
def text(s):b=s.encode();return b'\x81'+vi(len(b))+b
def wide(s):b=s.encode();return vi(len(s))+vi(len(b))+b
def obj(pairs):return b''.join(text(k)+v for k,v in pairs)+b'\xff'
def array(values):return b'\x86\xfd'+vi(len(values))+b''.join(values)+b'\xfe'
def ref(name='',pkg='.',kind=3,descriptor=(0,1,0xffffffff)):
 if kind==0 or kind>3:return b'\x83'+bytes([kind])
 if kind==3:return b'\x83\x03'+wide(pkg)+wide(name)
 a,b,c=descriptor;return b'\x83'+bytes([kind])+(wide(pkg) if kind==2 else b'')+vi(a)+vi(b)+struct.pack('<I',c)
def declaration(aliases=(),props=(),cls='EntityComponent_GroundEffect',data_mode=1):
 pairs=[('objclass',text(cls)),('aliases',array([text(x) for x in aliases]))]
 if data_mode:pairs.append(('objdata',b'\x85'+obj(props) if data_mode==1 else b'\x24\x07'))
 return b'\x85'+obj(pairs)
def document(values,version=1):return b'RTON\x01\0\0\0'+obj([('version',b'\x24'+vi(version)),('objects',array(values))])+b'DONE'
operations=[]
def add(op,type=2,name='',data=b'',label=''):
 operations.append(dict(op=op,type=type,name=[ord(c) for c in name],data=list(data),label=label))
add('ensure',2,'local');add('ensure',3,'remote');add('package',2,'packages/local.rton');add('package',3,'packages/remote.rton')
cycle=document([declaration(['Alpha'],[('m_type',text('tide_gargantuar')),('m_effect',ref('Beta'))]),declaration(['Beta'],[('m_type',text('stuck_into_ground')),('m_effect',ref('Alpha'))])])
add('load',data=cycle,label='forward-and-cyclic-names')
add('populate',data=document([declaration(['ignored'],[('m_type',text(' rise ')),('m_effect',ref('',kind=0))]),declaration([],[])]),label='overwrite-one-preserve-missing')
add('load',data=document([declaration(['Alpha'],[('m_effect',ref('Target','remote'))])]),label='cross-package-before-target')
add('load',3,data=document([declaration(['Target'],[('m_type',text('surf')),('m_effect',ref('Alpha','local'))])]),label='cross-package-after-target')
add('load',data=document([declaration(['Ghost'],[],cls='UnknownClass'),declaration(['Good'],[('m_effect',ref('Ghost'))])]),label='unknown-factory-hole')
add('load',data=document([declaration(['Abstract'],[],cls='RtObject'),declaration(['Good'],[])]),label='abstract-factory-hole')
add('load',data=document([declaration(['Same',''],[('m_type',text('tide')),('m_effect',ref('Same'))]),declaration(['Same'],[('m_type',text('tide_with_tail')),('m_effect',ref('Same'))])]),label='duplicate-alias-first-wins')
add('load',data=document([declaration(['Self'],[('m_effect',ref(kind=1))])]),label='descriptor-reference-current-store')
add('load',data=document([declaration(['Other'],[('m_effect',ref(kind=2,pkg='remote'))])]),label='descriptor-reference-package')
add('load',data=document([declaration(['Other'],[('m_effect',ref(kind=2,pkg='missing'))])]),label='descriptor-missing-package')
for name in ['tide',' tide_gargantuar\t','rise','surf','stuck_under_ground','stuck_into_ground','unknown','-1','99','']:
 add('load',data=document([declaration(['Enum'],[('m_type',text(name)),('m_effect',ref(kind=4))])]),label='enum-'+repr(name))
add('load',data=document([declaration(['Missing'],data_mode=0),declaration(['Wrong'],data_mode=2)]),label='missing-and-nonobject-data')
add('load',data=document([declaration(['ShouldNotLoad'])],version=2),label='wrong-version-preserves-store')
add('load',data=document([]),label='empty-object-list')
add('load',data=cycle,label='rebuild-after-clear')
for name in ['EntityComponent_GroundEffect','RtObject','UnknownClass','entitycomponent_groundeffect']:
 add('lookup',name=name,label='class-name-'+name)

seed();manager=h.call(0x11b10ec,[]);ground=h.call(0x255520,[]);h.call(0x11b15b4,[manager])
type_begin,type_end=h.words(0x18cbfa4,2);types=h.words(type_begin,(type_end-type_begin)//4);assert len(types)==2
schema=h.words(ground+0x24)[0];start,end=h.words(schema+0x134,2)
properties=[]
for p in h.words(start,(end-start)//4):properties.append(dict(name=h.narrow(h.words(p+0x38)[0]).decode(),offset=h.words(p+0x48)[0]))
assert properties==[dict(name='m_type',offset=8),dict(name='m_effect',offset=16)]
object_addresses=[];vectors={};checks=0
def serial(address):return object_addresses.index(address)+1 if address else 0
def snapshot():
 out=[]
 # Class metadata/name vector, normalized parent identity and factory role.
 out.append(len(types))
 for p in types:
  name=h.narrow(h.words(p+4)[0]);parent=h.words(p+8)[0]
  out.extend([len(name),*name,types.index(parent)+1 if parent else 0,int(p==ground)])
 for a in [0,types[0],ground]:
  for b in [0,types[0],ground]:out.append(h.call(FUNCTIONS['ancestry'],[a,b]))
 h.append(out,h.pool_state())
 alive=set()
 for type in [2,3]:
  store=h.store_for(type);out.append(int(bool(store)))
  if not store:continue
  out.extend([h.words(store+0xc4)[0],h.words(store+0xd4)[0]])
  slots=h.slot_state(store);count=slots[0]
  for i in range(count):
   offset=13+i*8+2;address=slots[offset]
   if address:alive.add(address);slots[offset]=serial(address)
  h.append(out,slots);h.append(out,h.tree_state(store+0xe4,'descriptor'));h.append(out,h.tree_state(store+0xfc,'object'))
 out.append(len(object_addresses))
 for address in object_addresses:
  out.append(int(address in alive))
  if address not in alive:continue
  effect=h.words(address+16,2);h.put(h.HANDLE,*effect);resolved=h.call(FUNCTIONS['resolve'],[h.REG,h.HANDLE])
  out.extend([bytes(h.u.mem_read(address+4,1))[0],h.words(address+8)[0],*effect,serial(resolved)])
 return out
def read_document(data):
 src=h.alloc(len(data));h.u.mem_write(src,data);dst=h.alloc(0x20000);h.u.mem_write(ST,bytes(0x100))
 h.put(ST,dst,0x20000,0,0,0,0,0x100)
 for off in [0x1c,0x34]:h.put(ST+off+4,0,0,ST+off+4,ST+off+4,0)
 assert h.call(0x1202a74,[ST,src,len(data)])==1
 h.call(0x11f8818,[V,ST]);h.put(V+12,SC,SC,SC+0x1000);h.put(SER,V,0,1)
initial=snapshot()
for operation in operations:
 op,type=operation['op'],operation['type'];results=[];states=[];store=h.store_for(type)
 if op=='ensure':
  p=h.PARAM;h.put(p,0,0,0x16c5e40,0x194a588,0);h.put(h.QUERY,*operation['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[p+4,h.REF]);name=h.words(p+4)[0]
  h.call(0x11eefb0,[h.REG,type,p]);h.call(0x11f1f08,[h.pool,name]);results.append([]);states.append(snapshot())
 elif op=='package':
  h.put(h.QUERY,*operation['name'],0);h.put(h.REF,h.QUERY);h.call(0x594184,[h.VALUE,h.REF]);name=h.words(h.VALUE)[0]
  h.put(h.REF,name);h.call(0x11ebe2c,[store,h.REF]);h.call(0x11f1f08,[h.pool,name]);results.append([]);states.append(snapshot())
 elif op=='lookup':
  data=''.join(chr(c) for c in operation['name']).encode();h.u.mem_write(h.QUERY,data+b'\0');value=h.call(FUNCTIONS['lookup'],[h.QUERY]);results.append([types.index(value)+1 if value else 0]);states.append(snapshot())
 else:
  read_document(bytes(operation['data']))
  if op=='load':
   vector=h.alloc(12);h.put(vector,0,0,0);created=h.call(FUNCTIONS['create_pass'],[store,SER,vector]);vectors[type]=vector
   b,e=h.words(vector,2);addresses=h.words(b,(e-b)//4)
   for p in addresses:
    if p and p not in object_addresses:object_addresses.append(p)
   results.append([created,*[serial(p) for p in addresses]]);states.append(snapshot())
   if created:
    filled=h.call(FUNCTIONS['fill_pass'],[store,SER,vector]);results.append([filled]);states.append(snapshot())
  else:
   filled=h.call(FUNCTIONS['fill_pass'],[store,SER,vectors[type]]);results.append([filled]);states.append(snapshot())
 operation['results']=results;operation['states']=states;checks+=len(states)
 if operation['label']=='forward-and-cyclic-names':
  folder=OUT/'example';folder.mkdir(exist_ok=True);(folder/'cyclic.raw.rton').write_bytes(bytes(operation['data']))
  vector=vectors[type];b,e=h.words(vector,2);addresses=h.words(b,(e-b)//4);rows=[]
  for i,address in enumerate(addresses):
   effect=h.words(address+16,2);h.put(h.HANDLE,*effect);resolved=h.call(FUNCTIONS['resolve'],[h.REG,h.HANDLE])
   cls=h.call(h.words(h.words(address)[0])[0],[address]);name=h.narrow(h.words(cls+4)[0]).decode()
   rows.append(dict(index=i,objclass=name,m_type=h.words(address+8)[0],m_effect_target=addresses.index(resolved) if resolved else None))
  (folder/'cyclic.arm.objects.json').write_text(json.dumps(dict(data_only=True,success=True,objects=rows),indent=2)+'\n',encoding='utf-8')
 print('Captured',operation['label'] or op,flush=True)
assert all(h.hits[n] for n in FUNCTIONS),h.hits
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for a in [*FUNCTIONS.values(),0x2555a0,0x255520,0x11f6288]:
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
for name,a,b in [('ancestry',0x11f595c,0x11f59ac),('ground_factory',0x254bf8,0x254c48),('class_publication',0x11f761c,0x11f77bc)]:
 (OUT/(name+'.asm')).write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:8} {i.op_str}' for i in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),operations=len(operations),checkpoints=checks,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},properties=properties,initial=initial,steps=operations,
 scope='Actual original reflection manager registration/finalization, real EntityComponent_GroundEffect factory, full original create/fill passes, property dispatcher, enum and weak-reference codecs, intern/name/descriptor/slot trees and resolver execute. No high-level factory/property/reference stubs. Host port intentionally supports only this data class, narrow enum text/ASCII aliases, no explicit UID; global reflection metadata/symbol-table ABI and game methods not reproduced. Compare class order/inheritance, entire intern state, complete two game-store slot/index state, initialized object fields and resolved identities. Low-level allocator/libc/single-thread pthread/ASCII ctype controlled. Broader reflection classes/protocols, RTID text parser, runtime/Android still incomplete.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',checks,'real reflection factory/property/reference full-state checkpoints')
