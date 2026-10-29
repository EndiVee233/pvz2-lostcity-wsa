"""Round 32: original DangerRoomModuleProperties owned reference fields."""
import json,struct,hashlib
from reflection_emulation_support import h,seed
from unicorn import UC_HOOK_CODE
base=h.base;out=base/'native_analysis/core_round32/danger_module';out.mkdir(parents=True,exist_ok=True)
seed();h.u.mem_write(0x1843830,bytes(0x74));h.put(0x1843838,0x7fffffff,0x7fffffff);h.put(0x1843848,0x17a06a0)
for a in (0x1843850,0x1843890):h.put(a+8,a,a)
manager=h.call(0x11b10ec,[]);meta=h.call(0x2d1e8c,[]);h.call(0x11b15b4,[manager])
schema=h.words(meta+0x24)[0];b,e=h.words(schema+0x134,2)
fields=[dict(name=h.narrow(h.words(p+0x38)[0]).decode(),offset=h.words(p+0x48)[0]) for p in h.words(b,(e-b)//4)]
assert fields==[dict(name=n,offset=o) for n,o in [('m_thisPtr',8),('ResourceGroupNames',16),('WorldSpecificProperties',32),('LevelDesigners',40)]],fields
def vi(n):
 r=[]
 while n>=128:r.append((n&127)|128);n>>=7
 return bytes(r+[n])
def text(s):b=s.encode();return b'\x81'+vi(len(b))+b
def wide(s):b=s.encode();return vi(len(s))+vi(len(b))+b
def ref(n,p='.'):return b'\x83\x03'+wide(p)+wide(n)
def obj(p):return b''.join(text(k)+v for k,v in p)+b'\xff'
def array(xs):return b'\x86\xfd'+vi(len(xs))+b''.join(xs)+b'\xfe'
def decl(alias,props):return b'\x85'+obj([('objclass',text('DangerRoomModuleProperties')),('aliases',array([text(alias)])),('objdata',b'\x85'+obj(props))])
def doc(props):return b'RTON'+struct.pack('<I',1)+obj([('version',b'\x24\x01'),('objects',array([decl('DangerA',props),decl('DangerB',[])]))])+b'DONE'
ST,V,SER,SC=0x600c000,0x600c100,0x600c200,0x600d000
def reader(data):
 src=h.alloc(len(data));h.u.mem_write(src,data);dst=h.alloc(0x20000);h.u.mem_write(ST,bytes(0x100));h.put(ST,dst,0x20000,0,0,0,0,0x100)
 for off in (0x1c,0x34):h.put(ST+off+4,0,0,ST+off+4,ST+off+4,0)
 assert h.call(0x1202a74,[ST,src,len(data)])==1
 h.call(0x11f8818,[V,ST]);h.put(V+12,SC,SC,SC+0x1000);h.put(SER,V,0,1)
h.put(h.PARAM,0,0,0x16c5e40,0x194a588,0);h.put(h.QUERY,*map(ord,'local'),0);h.put(h.REF,h.QUERY);h.call(0x594184,[h.PARAM+4,h.REF]);name=h.words(h.PARAM+4)[0]
store=h.call(0x11eefb0,[h.REG,2,h.PARAM]);h.call(0x11f1f08,[h.pool,name]);vector=h.alloc(12);h.put(vector,0,0,0)
def handle_at(a,items):
 lo,hi=h.words(a,2)
 if not(lo|hi):return dict(package='',name='',target=-1)
 assert hi&0x80000000
 def txt(i):return ''.join(map(chr,h.wide(h.call(0x11f14cc,[h.pool,i]))))
 pkg=txt((lo>>31)|((hi&0x3fffffff)<<1));name=txt(lo&0x7fffffff)
 h.put(h.HANDLE,lo,hi);target=h.call(0x1ea034,[h.REG,h.HANDLE])
 return dict(package=pkg,name=name,target=items.index(target) if target in items else -1)
def state(address,items):
 b,e=h.words(address+40,2)
 return dict(world=handle_at(address+32,items),designers=[handle_at(p,items) for p in range(b,e,8)])
inputs=[('empty',[]),('cycle-and-missing',[('WorldSpecificProperties',ref('DangerB')),('LevelDesigners',array([ref('DangerB'),ref('DangerA'),ref('MissingDesigner'),b'\x83\0']))]),('partial-keeps-list',[('WorldSpecificProperties',ref('WorldConfig','OtherWorld'))]),('shrink',[('LevelDesigners',array([ref('DangerA')]))]),('grow',[('LevelDesigners',array([ref('DangerA'),ref('DangerB')]))]),('missing-preserves',[]),('clear',[('WorldSpecificProperties',b'\x83\0'),('LevelDesigners',array([]))]),('destroy-owned',[('WorldSpecificProperties',ref('WorldToRelease')),('LevelDesigners',array([ref('FirstToRelease'),ref('SecondToRelease')]))])]
cases=[];items=[]
for i,(label,props) in enumerate(inputs):
 data=doc(props);reader(data)
 if i==0:assert h.call(0x11ed5fc,[store,SER,vector])==1
 assert h.call(0x11ead94,[store,SER,vector])==1
 b,e=h.words(vector,2);items=h.words(b,(e-b)//4);assert len(items)==2 and all(items)
 cases.append(dict(label=label,raw_hex=data.hex(),state=state(items[0],items)))
# Trace the actual field-handle clearing order in original non-deleting dtor.
releases=[];tracking=True
def trace(u,a,size,unused):
 if a!=0x1e9bb4 or not tracking:return
 target=u.reg_read(h.UC_ARM_REG_R0);lo,hi=h.words(target,2)
 if hi&0x80000000:
  id=lo&0x7fffffff;begin=h.words(h.pool+24)[0];entry=h.words(begin+(id-1)*4)[0]
  releases.append(''.join(map(chr,h.wide(h.words(entry+12)[0]))))
h.u.hook_add(UC_HOOK_CODE,trace);h.call(0x2cff10,[items[0]]);tracking=False
assert releases==['FirstToRelease','SecondToRelease','WorldToRelease'],releases
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),metadata='002d1e8c',factory='002ce094',destructor='002cff10',allocation_bytes=56,fields=fields,cases=cases,destructor_reference_release_order=releases,scope='Real metadata/schema/factory, normalizer, both load passes, references and nondeleting destructor. Compare field text and resolved target identity, not full registry/pool state or arbitrary malformed inputs. No danger-room gameplay.')
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print('Captured',len(cases),'danger module states and destructor release order')
