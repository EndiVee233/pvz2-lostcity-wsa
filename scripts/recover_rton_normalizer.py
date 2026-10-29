"""Round 21: execute the real raw->indexed RTON conversion, no converter stubs."""
import hashlib,json,random,shutil,struct,sys
import recover_owned_stores as h
from unicorn import UC_HOOK_CODE
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base
OUT=base/'native_analysis/core_round21/rton_normalizer';OUT.mkdir(parents=True,exist_ok=True)
STREAM=0x6008000
FUNCTIONS=dict(normalize=0x1202a74,container=0x12028a0,token=0x1201398,reference_wire=0x11f4394)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
input_stream=0
def trace(uc,address,size,unused):
 global input_stream
 if address==0x11f83b0 and not input_stream:input_stream=uc.reg_read(h.UC_ARM_REG_R0)
h.u.hook_add(UC_HOOK_CODE,trace)
def vi(n):
 result=[]
 while n>=128:result.append((n&127)|128);n>>=7
 return bytes(result+[n])
def narrow(s,tag=0x81):
 data=s.encode() if isinstance(s,str) else bytes(s)
 return bytes([tag])+vi(len(data))+data
def wide_payload(s):
 data=s.encode('utf-8');return vi(len(s))+vi(len(data))+data
def wide(s,tag=0x82):return bytes([tag])+wide_payload(s)
def obj(pairs):return b''.join(k+v for k,v in pairs)+b'\xff'
def array(values,subtype=0xfd):return b'\x86'+bytes([subtype])+vi(len(values))+b''.join(values)+b'\xfe'
def document(body):return b'RTON'+struct.pack('<HH',1,0)+body+b'DONE'
scenarios=[]
def scenario(label,data,source=None):scenarios.append(dict(label=label,data=list(data),source=source))
def single(label,value,key=None):scenario(label,document(obj([(narrow('key') if key is None else key,value)])))
scenario('empty',document(b'\xff'))
for magic,v,f in [(b'NOPE',1,0),(b'RTON',0,0),(b'RTON',2,0),(b'RTON',1,1),(b'RTON',1,2)]:scenario('bad-header-'+magic.decode()+str(v)+str(f),magic+struct.pack('<HH',v,f)+b'\xffDONE')
scenario('bad-trailer',document(obj([(narrow('x'),b'\x01')]))[:-4]+b'FAIL')
scenario('trailing-bytes',document(b'\xff')+b'ignored')
rng=random.Random(0x4e4f524d)
fixed={8:1,10:1,0x10:2,0x12:2,0x20:4,0x22:4,0x26:4,0x40:8,0x42:8,0x46:8}
zero={9,11,0x11,0x13,0x21,0x23,0x27,0x41,0x43,0x47}
payloads={tag:bytes(rng.randrange(256) for i in range(n)) for tag,n in fixed.items()}
payloads.update({tag:b'' for tag in zero})
payloads.update({0:b'',1:b'',2:b'',0x24:vi(0x80000000),0x25:vi(0xffffffff),0x28:vi(0xffffffff),0x44:vi(0xfedcba9876543210),0x45:vi(0xffffffffffffffff),0x48:vi(0x8000000000000000),0x81:vi(3)+b'A\0B',0x82:wide_payload('植物🍄'),0x83:b'\0',0x84:b'',0x85:b'\xff',0x86:b'\xfd\0\xfe',0x87:b'\0'+vi(3)+b'bin'+vi(3)+b'A\0B',0x90:vi(3)+b'foo',0x91:vi(0),0x92:wide_payload('缓存'),0x93:vi(0)})
for tag in range(256):
 if tag in [0x91,0x93]:
  first=narrow('foo',0x90) if tag==0x91 else wide('缓存',0x92)
  scenario('all-tags-'+str(tag),document(obj([(narrow('seed'),first),(narrow('key'),bytes([tag])+payloads[tag])])))
 else:single('all-tags-'+str(tag),bytes([tag])+payloads.get(tag,b''))
for tag in fixed:
 for data in [bytes(fixed[tag]),bytes([255])*fixed[tag],bytes([128])+bytes(fixed[tag]-1)]:single('fixed-bits-'+str(tag)+'-'+data.hex(),bytes([tag])+data)
for tag in [0x24,0x25,0x28,0x44,0x45,0x48]:
 for n in [0,1,127,128,16383,16384,0xffffffff]:single('varint-'+str(tag)+'-'+str(n),bytes([tag])+vi(n))
scenario('narrow-cache-order',document(obj([(narrow('key',0x90),narrow('same',0x90)),(narrow('key',0x90),narrow('same',0x90)),(b'\x91\0',b'\x91\x03'),(narrow(b'A\0B'),narrow(b'A\0B'))])))
scenario('wide-cache-order',document(obj([(wide('键',0x92),wide('值',0x92)),(wide('键',0x92),wide('值',0x92)),(b'\x93\0',b'\x93\x03'),(narrow('key'),wide('键'))])))
scenario('mixed-keys',document(obj([(wide('植物'),wide('植物')),(narrow('植物'),narrow('植物')),(b'\x02',b'\x02')])) )
for length in [0,1,7,8,9,16,17,31,32,33,128]:
 single('wide-length-'+str(length),wide('🍄中'*length))
for subtype in [0,1,0xfd,255]:
 for count in [0,1,3,32,33,128]:single('array-'+str(subtype)+'-'+str(count),array([b'\x24'+vi(i) for i in range(count)],subtype))
for declared,values in [(0xffffffff,[]),(0xffffffff,[b'\x01']),(0xffffffff,[b'\x01',b'\x24\x80\x01',narrow('value')]),(0,[b'\x01',b'\x00',b'\x01']),(7,[b'\x01',b'\x00'])]:
 single('array-backpatch-'+str(declared)+'-'+str(len(values)),b'\x86\xfd'+vi(declared)+b''.join(values)+b'\xfe')
for depth in [1,7,8,31,32,33,40,65]:
 value=b'\x01'
 for i in range(depth):value=b'\x85'+obj([(narrow('key'),value)]) if i%2 else array([value])
 single('nested-'+str(depth),value)
for kind in [0,1,2,3,4,255]:
 for pkg,name in [('', ''),('.', ''),('.', 'pea'),('levels/植物','plant'),('.\0x',''),('pkg\0tail','name\0tail')]:
  data=bytes([kind])
  if kind==1:data+=vi(1)+vi(2)+struct.pack('<I',0xaabbccdd)
  elif kind==2:data+=wide_payload(pkg)+vi(0)+vi(0)+struct.pack('<I',0)
  elif kind==3:data+=wide_payload(pkg)+wide_payload(name)
  single('reference-'+str(kind)+'-'+pkg+'-'+name,b'\x83'+data)
for skip in [0,1,255]:
 for name in [b'',b'blob',b'A\0B']:
  single('blob-'+str(skip)+'-'+name.hex(),b'\x87'+bytes([skip])+vi(len(name))+name+vi(5)+bytes([0,1,128,254,255]))
def random_value(depth):
 if depth>0:
  choice=rng.randrange(6)
  if choice==0:return array([random_value(depth-1) for i in range(rng.randrange(5))])
  if choice==1:return b'\x85'+obj([(narrow('k'+str(i)),random_value(depth-1)) for i in range(rng.randrange(5))])
 tag=rng.choice([0,1,2,0x21,0x24,0x25,0x40,0x81,0x82,0x84])
 if tag in [0x24,0x25]:return bytes([tag])+vi(rng.randrange(1<<32))
 if tag==0x40:return bytes([tag])+struct.pack('<Q',rng.randrange(1<<64))
 if tag==0x81:return narrow(rng.choice(['','same','plant','A\0B']))
 if tag==0x82:return wide(rng.choice(['','植物🍄','same']))
 return bytes([tag])
for n in range(30):scenario('random-document-'+str(n),document(obj([(narrow('field'+str(i)),random_value(4)) for i in range(8)])))

# Reuse the existing local resource-decryption preparation, without modifying
# encrypted assets or implementing/deeming it a recovered native decryption path.
sys.path.insert(0,str(base/'tools/python_libs'))
from py3rijndael import RijndaelCbc,ZeroPadding
key=hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
cipher=RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24)
seen=set()
for path in sorted((base/'apktool_out/assets').rglob('*.RTON'),key=lambda p:p.stat().st_size):
 data=path.read_bytes();data=cipher.decrypt(data[2:]) if data[:2]==b'\x10\0' else data
 digest=hashlib.sha256(data).hexdigest()
 if digest in seen:continue
 seen.add(digest);scenario('resource-'+str(len(seen)),data,dict(path=str(path.relative_to(base)),plaintext_sha256=digest))
 if len(seen)==4:break

def table(offset,wide=False):
 nodes=[]
 def visit(n):
  if n:visit(h.words(n+8)[0]);nodes.append(n);visit(h.words(n+12)[0])
 visit(h.words(STREAM+offset+8)[0]);assert len(nodes)==h.words(STREAM+offset+20)[0]
 result=[]
 for n in nodes:
  p=h.words(n+16)[0];size=h.words(p-12)[0];text=h.words(p,size) if wide else list(bytes(h.u.mem_read(p,size)))
  result.append(dict(text=text,offset=h.words(n+20)[0]))
 return result
for number,sc in enumerate(scenarios):
 h.cursor=0x8000000;h.records=[];h.u.mem_write(0x6000000,bytes(0x20000));h.put(0x18cbf94,0);h.put(0x18cbf98,0)
 h.pool=h.call(0x11f13a8,[]);input_stream=0
 data=bytes(sc['data']);src=h.alloc(len(data)+64);h.u.mem_write(src,data+bytes(64));output=h.alloc(0x200000)
 h.put(STREAM,output,0x200000,0,0,0,0,0x100)
 for off in [0x1c,0x34]:h.put(STREAM+off+4,0,0,STREAM+off+4,STREAM+off+4,0)
 try:
  success=h.call(FUNCTIONS['normalize'],[STREAM,src,len(data)])
  size=h.words(STREAM+20)[0];assert size<0x200000
  sc.update(success=success,consumed=h.words(input_stream+20)[0],output=list(bytes(h.u.mem_read(output,size))),narrow=table(0x1c),wide=table(0x34,True))
  assert bytes(h.u.mem_read(src,len(data)))==data
  if sc['source']:
   folder=OUT/'resources';folder.mkdir(exist_ok=True)
   (folder/(sc['label']+'.raw.rton')).write_bytes(data)
   (folder/(sc['label']+'.arm.indexed.rton')).write_bytes(bytes(sc['output']))
 except Exception as e:raise RuntimeError(f"{number}/{sc['label']} PC={h.u.reg_read(h.UC_ARM_REG_PC):08x}: {e}") from e
 if number%100==0:print('Captured',number+1,'/',len(scenarios),flush=True)
assert all(h.hits[n] for n in FUNCTIONS),h.hits
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for a in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
(OUT/'normalizer.asm').write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(h.u.mem_read(0x1201398,0x1202b34-0x1201398)),0x1201398))+'\n',encoding='utf-8')
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(scenarios),checkpoints=len(scenarios),function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=scenarios,
 scope='Real original document/token/container conversion, string cache trees, bit vectors, reference wire parser/emitter and intern pool execute. Fresh fixed caller output buffer, no high-level converter stubs. Compare all output bytes, success, input consumption and logical sorted string/offset maps, not cache tree topology or global intern-pool side effects. Raw reads and string object keys are caller preconditions. Include ffffffff and mismatching declared array counts, preserving original backpatch overwrite behavior rather than asserting navigability. Existing Python decryption only prepares four asset plaintext inputs; not native decryption recovery. Allocator/libc/single-thread kuser controlled. No field navigation, game class creation or full engine runtime.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(scenarios),'original RTON normalization byte/table checkpoints')
