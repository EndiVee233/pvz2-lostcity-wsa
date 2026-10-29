"""Round 20: original byte/varint/string/UTF8/header input primitives.

All read and decoder functions execute original instructions. Input memory is
bounded by the stream length for UTF8; raw read cases satisfy original caller
preconditions. No raw-Rton to indexed-Rton transcoder is claimed here.
"""
import hashlib,json,random,shutil,struct
import recover_owned_stores as h
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
base=h.base
OUT=base/'native_analysis/core_round20/rton_input';OUT.mkdir(parents=True,exist_ok=True)
STREAM,READER,DEST,TEXT,PTR,VALUE=0x6008000,0x6008100,0x6008200,0x6008300,0x6008400,0x6008500
FUNCTIONS=dict(read=0x11f83b0,var32=0x11f83f0,var64=0x11f8440,zig32=0x11f84b4,zig64=0x11f84d0,
 narrow=0x11f8508,wide=0x11f8554,codepoint=0x11f85a0,utf8=0x11f8624,decode=0x1141fb4,header=0x11f873c)
h.FUNCTIONS.update(FUNCTIONS)
for k in FUNCTIONS:h.hits.setdefault(k,0)
scenarios=[]
def step(op,a=0):return dict(op=op,a=a)
def scenario(label,data,steps,modes=(0,1)):
 for mode in modes:scenarios.append(dict(label=label+'-'+str(mode),data=list(data),mode=mode,writer=None,steps=[dict(s) for s in steps]))
def varint(n):
 out=[]
 while n>=128:out.append((n&127)|128);n>>=7
 return bytes(out+[n])
def packwide(text):return struct.pack('<'+'I'*len(text),*text)
rng=random.Random(0x52454144)
values32=[0,1,2,63,64,127,128,129,8191,8192,16383,16384,2097151,2097152,0x7fffffff,0x80000000,0xffffffff]+[rng.randrange(1<<32) for _ in range(80)]
values64=[0,1,127,128,0xffffffff,0x100000000,0x7fffffffffffffff,0x8000000000000000,0xffffffffffffffff]+[rng.randrange(1<<64) for _ in range(80)]
for op,values in [('var32',values32),('zig32',values32),('var64',values64),('zig64',values64)]:
 scenario(op+'-boundaries',b''.join(varint(n) for n in values),[step(op) for n in values])
for count in [2,5,6,9,10,11,32,37,38,40,74,150]:
 payload=bytes([0xff]*(count-1)+[127])
 scenario('overlong-'+str(count),payload*4,[step(op) for op in ['var32','var64','zig32','zig64']])
 for kind,payload in [('tail',bytes([128]*(count-1)+[1])),('mixed',bytes([rng.randrange(128)|128 for _ in range(count-1)]+[rng.randrange(128)]))]:
  scenario('overlong-'+kind+'-'+str(count),payload*4,[step(op) for op in ['var32','var64','zig32','zig64']])
scenario('byte-copies',bytes(range(256))*2,[step('read',n) for n in [0,1,7,16,128,256,104]])
byte_strings=[b'',b'x',b'A\0B\xff',bytes(range(256)),bytes([255])*128,b'last']
scenario('logical-narrow-strings',b''.join(varint(len(s))+s for s in byte_strings),[step('narrow') for s in byte_strings])
wide_strings=[[],[0],[0x4e00,0,0x1f344,0xffffffff],[i*0x10001 for i in range(128)]]
scenario('logical-wide-strings',b''.join(varint(len(s))+packwide(s) for s in wide_strings),[step('wide') for s in wide_strings])

# Cover every first byte, valid legacy 2..5-byte sequences, forbidden codepoints,
# overlong encodings and each truncated continuation/invalid-continuation place.
utf_cases=[bytes([i]) for i in range(256)]
utf_cases += [b'',b'A\0B',b'\xc2\x80',b'\xdf\xbf',b'\xe0\xa0\x80',b'\xed\x9f\xbf',b'\xed\xa0\x80',b'\xed\xbf\xbf',b'\xee\x80\x80',b'\xef\xbf\xbd',b'\xef\xbf\xbe',b'\xef\xbf\xbf',b'\xf0\x90\x80\x80',b'\xf4\x8f\xbf\xbf',b'\xf4\x90\x80\x80',b'\xf7\xbf\xbf\xbf',b'\xf8\x88\x80\x80\x80',b'\xfb\xbf\xbf\xbf\xbf',b'\xfc\x84\x80\x80\x80\x80',b'\xc0\x80',b'\xc1\xbf',b'\xe0\x9f\xbf',b'\xf0\x8f\xbf\xbf',b'\xf8\x87\xbf\xbf\xbf']
for valid in [b'\xc2\xa0',b'\xe1\x88\xb4',b'\xf1\x80\x88\xb4',b'\xf9\x80\x80\x88\xb4']:
 for n in range(1,len(valid)):utf_cases.append(valid[:n])
 for n in range(1,len(valid)):
  for invalid in [0,65,0xc0,255]:utf_cases.append(valid[:n]+bytes([invalid])+valid[n+1:])
for n,data in enumerate(utf_cases):scenario('utf8-case-'+str(n),data,[step('decode'),step('codepoint'),step('codepoint')],modes=(n%2,))
for n in [0,1,7,8,9,15,16,17,32,128]:
 text='植物🍄'*n;payload=text.encode('utf-8');count=len(text)
 scenario('utf8-string-'+str(n),varint(count)+varint(len(payload))+payload,[step('utf8')])
for n,payload in enumerate([b'A\0B',b'A\xc0\x80B',b'\xed\xa0\x80',b'\xff',b'',b'\xf9\x80\x80\x88\xb4']):
 # Deliberately incorrect declared byte size: original ignores this field.
 scenario('utf8-invalid-string-'+str(n),varint(5)+varint(999)+payload,[step('utf8')])
for magic,version,format in [(b'RTON',1,1),(b'RTON',1,0),(b'RTON',0,1),(b'RTON',2,1),(b'NOPE',1,1),(b'RTON',1,2)]:
 scenario('header-'+magic.decode()+'-'+str(version)+'-'+str(format),magic+struct.pack('<HH',version,format)+b'root',[step('read',2),step('header'),step('header')])

# Capture previous round's ORIGINAL writer output, then feed the real reader.
# C++ also reproduces these bytes through RtonWriter before reading them.
for kind,value in [('varuint',[0,127,128,0xffffffff]),('narrow',[65,0,66,128,255]),('utf8',[ord(c) for c in '植物🍄/test'])]:
 h.cursor=0x8000000;h.u.mem_write(STREAM,bytes(0x1000));out=h.alloc(0x10000);h.put(STREAM,out,0,0,0,0,0,0)
 writer=READER;h.put(writer,STREAM)
 for off in [24,52]:h.put(writer+off+4,0,0,writer+off+4,writer+off+4,0,0)
 h.put(PTR,0x194a588)
 if kind=='varuint':
  for v in value:h.call(0x11fd650,[STREAM,v])
  steps=[step('var32') for v in value]
 elif kind=='narrow':
  h.u.mem_write(DEST,bytes(value)+b'\0');h.put(TEXT,0x194a588);h.call(0x14fc3f9,[TEXT,DEST,len(value)])
  h.call(0x1200230,[writer,PTR,TEXT,0]);steps=[step('read',1),step('narrow')]
 else:
  h.put(DEST,*value,0);h.call(0x1205280,[writer,PTR,DEST,0]);steps=[step('read',1),step('utf8')]
 data=bytes(h.u.mem_read(out,h.words(STREAM+20)[0]));scenario('writer-to-reader-'+kind,data,steps)
 for sc in scenarios[-2:]:sc['writer']=dict(kind=kind,value=value)

checkpoints=0
for sc in scenarios:
 h.cursor=0x8000000;h.u.mem_write(0x6008000,bytes(0x1000));data=bytes(sc['data']);buffer=h.alloc(len(data)+64);h.u.mem_write(buffer,data+bytes(64))
 if sc['mode']==0:h.put(STREAM,buffer,len(data),0,0,0,0,0)
 else:h.put(STREAM,0,0,buffer,buffer+len(data),buffer+len(data),0,0)
 h.put(READER,STREAM,0,0,0,0,0);h.put(TEXT,0x194a588)
 # Decode output marker exposes failure leaving the caller's value untouched.
 for s in sc['steps']:
  op=s['op'];result=[]
  try:
   if op=='read':h.call(FUNCTIONS[op],[STREAM,DEST,s['a']]);result=list(bytes(h.u.mem_read(DEST,s['a'])))
   elif op in ['var32','zig32','var64','zig64']:
    value=h.call(FUNCTIONS[op],[STREAM]);result=[value]
    if op in ['var64','zig64']:result.append(h.u.reg_read(h.UC_ARM_REG_R1))
   elif op in ['narrow','wide','utf8']:
    h.put(TEXT,0x194a588 if op=='narrow' else 0x194a578);h.call(FUNCTIONS[op],[STREAM,TEXT]);p=h.words(TEXT)[0];n=h.words(p-12)[0]
    result=list(bytes(h.u.mem_read(p,n))) if op=='narrow' else h.words(p,n)
   elif op=='codepoint':result=[h.call(FUNCTIONS[op],[STREAM])]
   elif op=='decode':
    offset=h.words(STREAM+20)[0];h.put(PTR,buffer+offset);h.put(VALUE,0xdecafbad)
    consumed=h.call(FUNCTIONS[op],[PTR,len(data)-offset,VALUE]);result=[consumed,h.words(VALUE)[0],h.words(PTR)[0]-(buffer+offset)]
   elif op=='header':result=[h.call(FUNCTIONS[op],[READER])]
   else:raise AssertionError(op)
   assert bytes(h.u.mem_read(buffer,len(data)))==data,'input mutated'
   s['result']=result;s['state']=[h.words(STREAM+20)[0],h.words(READER+8)[0],bytes(h.u.mem_read(STREAM+25,1))[0]];checkpoints+=1
  except Exception as error:raise RuntimeError(f"{sc['label']}/{op} PC={h.u.reg_read(h.UC_ARM_REG_PC):08x}: {error}") from error
assert all(h.hits[n] for n in FUNCTIONS),h.hits
for label,a,b in [('input_primitives',0x11f83b0,0x11f87d8),('utf8_decoder',0x1141fb4,0x1142148)]:
 md=Cs(CS_ARCH_ARM,CS_MODE_ARM);(OUT/(label+'.asm')).write_text('\n'.join(f'{x.address:08x}: {x.mnemonic:8} {x.op_str}' for x in md.disasm(bytes(h.u.mem_read(a,b-a)),a))+'\n',encoding='utf-8')
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for address in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{address:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(scenarios),checkpoints=checkpoints,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=scenarios,
 scope='Original byte/varint32/64/zigzag/raw narrow/raw UTF32/UTF8 decoding and normalized-header functions execute. Fixed external buffer and vector-backed input, original COW strings retained. Compare all returned code units and exact position/root/header flag; input unchanged. Raw reads obey original caller bounds; bounded malformed UTF8 and terminated overlong varints tested. Allocator/libc controlled, no transcoder/indexed document navigation/object reader/file IO/concurrency or Android COW ABI.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(scenarios),'original RTON input scenarios;',checkpoints,'value/position checkpoints')
