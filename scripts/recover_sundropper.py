"""Round 30: original SunDropperProperties factory and two-pass data loads."""
import json,struct,hashlib
from reflection_emulation_support import h,seed
base=h.base;out=base/'native_analysis/core_round30/sundropper';out.mkdir(parents=True,exist_ok=True)
seed()
# Match the evidenced empty GameObject post-read event bus from round 25.
h.u.mem_write(0x1843830,bytes(0x74));h.put(0x1843838,0x7fffffff,0x7fffffff);h.put(0x1843848,0x17a06a0)
for a in (0x1843850,0x1843890):h.put(a+8,a,a)
manager=h.call(0x11b10ec,[]);meta=h.call(0x959cd0,[]);h.call(0x11b15b4,[manager])
schema=h.words(meta+0x24)[0];b,e=h.words(schema+0x134,2)
fields=[dict(name=h.narrow(h.words(p+0x38)[0]).decode(),offset=h.words(p+0x48)[0]) for p in h.words(b,(e-b)//4)]
names=['InitialSunDropDelay','SunCountdownBase','SunCountdownRange','SunCountdownMax','SunCountdownIncreasePerSun']
assert fields==[dict(name='m_thisPtr',offset=8),dict(name='ResourceGroupNames',offset=16)]+[dict(name=n,offset=28+4*i) for i,n in enumerate(names)],fields
p=h.call(0x9597c8,[]);defaults=h.words(p+28,5);assert defaults==[0]*5
def vi(n):
 r=[]
 while n>=128:r.append((n&127)|128);n>>=7
 return bytes(r+[n])
def text(s):b=s.encode();return b'\x81'+vi(len(b))+b
def obj(p):return b''.join(text(k)+v for k,v in p)+b'\xff'
def array(xs):return b'\x86\xfd'+vi(len(xs))+b''.join(xs)+b'\xfe'
def doc(props):return b'RTON'+struct.pack('<I',1)+obj([('version',b'\x24\x01'),('objects',array([b'\x85'+obj([('objclass',text('SunDropperProperties')),('aliases',array([text('DefaultSunDropper')])),('objdata',b'\x85'+obj(props))])]))])+b'DONE'
ST,V,SER,SC=0x600c000,0x600c100,0x600c200,0x600d000
def reader(data):
 src=h.alloc(len(data));h.u.mem_write(src,data);dst=h.alloc(0x20000);h.u.mem_write(ST,bytes(0x100));h.put(ST,dst,0x20000,0,0,0,0,0x100)
 for off in (0x1c,0x34):h.put(ST+off+4,0,0,ST+off+4,ST+off+4,0)
 assert h.call(0x1202a74,[ST,src,len(data)])==1
 h.call(0x11f8818,[V,ST]);h.put(V+12,SC,SC,SC+0x1000);h.put(SER,V,0,1)
h.put(h.PARAM,0,0,0x16c5e40,0x194a588,0);store=h.call(0x11eefb0,[h.REG,2,h.PARAM])
vector=h.alloc(12);h.put(vector,0,0,0)
cases=[]
inputs=[('defaults',[]),('real-levelmodules',[(n,b'\x42'+struct.pack('<d',v)) for n,v in zip(names,[2,4.25,2.75,9.5,0.1])]),('partial-preserves-others',[(names[1],b'\x42'+struct.pack('<d',8.5))]),('negative-zero',[(names[0],b'\x22'+struct.pack('<f',-0.0))]),('unknown-ignored',[('UnknownSunField',b'\x24\x09')])]
for i,(label,props) in enumerate(inputs):
 data=doc(props);reader(data)
 if i==0:assert h.call(0x11ed5fc,[store,SER,vector])==1
 assert h.call(0x11ead94,[store,SER,vector])==1
 start,end=h.words(vector,2);assert end-start==4;address=h.words(start)[0];bits=h.words(address+28,5)
 cases.append(dict(label=label,raw_hex=data.hex(),bits=bits))
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),metadata='00959cd0',factory='009597c8',fields=fields,default_bits=defaults,cases=cases,scope='Real reflection manager, metadata/schema registration, factory, normalizer and two-pass load/property reads. Empty game event bus and controlled low-level primitives. Five float fields only; no sun spawning gameplay, resources scheduling or complete graph equivalence claimed.')
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print('Captured',len(cases),'SunDropper original ARM data states')
