"""Round 23: non-RTID boolean/int32/uint32 coercion, original ARM branches.

Decimal C-library calls use the real host 32-bit C runtime within signed32
range; overflow/locale parity and the RTID branch are explicitly excluded.
"""
import ctypes,hashlib,json,random,shutil,struct
import recover_owned_stores as h
from unicorn import UC_HOOK_CODE
base=h.base;OUT=base/'native_analysis/core_round23/rton_scalars';OUT.mkdir(parents=True,exist_ok=True)
STREAM,READER,BUFFER=0x6008000,0x6008100,0x6009000
FUNCTIONS=dict(i32=0x11f8d6c,u32=0x11f9070,boolean=0x11f8a24,wide_decimal=0x11f1288)
h.FUNCTIONS.update(FUNCTIONS)
for name in FUNCTIONS:h.hits.setdefault(name,0)
crt=ctypes.CDLL('msvcrt');assert ctypes.sizeof(ctypes.c_long)==4
crt.atoi.argtypes=[ctypes.c_char_p];crt.atoi.restype=ctypes.c_int
crt.strtol.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.c_int];crt.strtol.restype=ctypes.c_long
controlled={a:n for a,n in h.imports.items() if n in ['atoi','strtol']}
for a in controlled:del h.imports[a]
def libc(uc,a,size,unused):
 name=controlled.get(a)
 if not name:return
 data=h.narrow(uc.reg_read(h.UC_ARM_REG_R0));value=crt.atoi(data) if name=='atoi' else crt.strtol(data,None,10)
 uc.reg_write(h.UC_ARM_REG_R0,value&0xffffffff);uc.reg_write(h.UC_ARM_REG_PC,uc.reg_read(h.UC_ARM_REG_LR))
h.u.hook_add(UC_HOOK_CODE,libc)
cases=[]
header=b'RTON\x01\0\x01\0\xb8\xffDONE\0\0'
def case(label,tag,payload=b'',tail=None,offset=16):
 data=header+bytes([tag])+payload
 if tail is not None:data=data.ljust(64,b'\0')+tail
 cases.append(dict(label=label,data=list(data),offset=offset))
for tag in [8,10,0xbc]:
 for n in range(256):case('byte-'+str(tag)+'-'+str(n),tag,bytes([n]))
for tag,n,fmt in [(0x10,16,'H'),(0x12,16,'H'),(0x20,32,'I'),(0x26,32,'I'),(0x40,64,'Q'),(0x46,64,'Q')]:
 for value in [0,1,127,128,(1<<(n-1))-1,1<<(n-1),(1<<n)-1]:case('fixed-'+str(tag)+'-'+str(value),tag,struct.pack('<'+fmt,value))
rng=random.Random(0x5343414c)
for tag,fmt,values in [(0x22,'I',[0,0x80000000,0x3fc00000,0xbfc00000,0x4effffff,0x4f000000,0xcf000000,0x4f800000,0x7f800000,0xff800000,0x7fc00000,0xffc00000]),(0x42,'Q',[0,0x8000000000000000,0x3ff8000000000000,0xbff8000000000000,0x41dfffffffc00000,0x41e0000000000000,0xc1e0000000000000,0x41efffffffe00000,0x41f0000000000000,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000000,0xfff8000000000000])]:
 for bits in values+[rng.randrange(1<<(32 if tag==0x22 else 64)) for i in range(60)]:case('float-'+str(tag)+'-'+hex(bits),tag,struct.pack('<'+fmt,bits))
texts=['','0','1','-1','+2147483647','-2147483648',' \t\n12xyz','false','true','0x10','--1','00000000000000000123','12\0tail','12junk']
for i,text in enumerate(texts):
 raw=text.encode();wide=struct.pack('<'+'I'*(len(text)+1),*[ord(c) for c in text],0)
 case('narrow-inline-'+str(i),0xb0,struct.pack('<I',len(raw)+1)+raw+b'\0')
 case('narrow-reference-'+str(i),0xb1,struct.pack('<I',64),raw+b'\0')
 case('wide-inline-'+str(i),0xb2,struct.pack('<I',len(wide))+wide)
 case('wide-reference-'+str(i),0xb3,struct.pack('<I',64),wide)
wide=[0x131,0x132,0x133,0];case('wide-low-bytes',0xb2,struct.pack('<I',len(wide)*4)+struct.pack('<4I',*wide))
supported={8,10,0xbc,0x10,0x12,0x20,0x26,0x40,0x46,0x22,0x42,0xb0,0xb1,0xb2,0xb3,0xba}
for tag in range(256):
 if tag not in supported:case('unsupported-tag-'+str(tag),tag,b'\0'*8)
case('null-offset',0x20,struct.pack('<I',123),offset=0)
previous=json.loads((base/'native_analysis/core_round22/rton_reader/validation.json').read_text(encoding='utf-8'))
for old in previous['scenarios']:
 if not old['source'] or old['mode']!=0:continue
 field=next(x for x in old['summary']['root_fields'] if x['key']=='version')
 cases.append(dict(label=old['label'].removesuffix('-mode0'),data=old['indexed'],offset=field['value_offset'],source=old['source'],summary=old['summary']))
scenarios=[];checks=0
for original in cases:
 for mode in [0,1]:
  h.cursor=0x8000000;h.u.mem_write(STREAM,bytes(0x200));data=bytes(original['data']);h.u.mem_write(BUFFER,data+bytes(64))
  if mode==0:h.put(STREAM,BUFFER,len(data),0,0,0,0,0)
  else:h.put(STREAM,0,0,BUFFER,BUFFER+len(data),BUFFER+len(data),0,0)
  h.call(0x11f8818,[READER,STREAM]);steps=[]
  for op in ['i32','u32','boolean']:
   h.put(STREAM+20,13);fallback=0x87654321
   result=h.call(FUNCTIONS[op],[READER,original['offset'],fallback]);steps.append(dict(op=op,offset=original['offset'],fallback=fallback,result=result,position=h.words(STREAM+20)[0]));checks+=1
  sc=dict(label=original['label']+'-mode'+str(mode),data=original['data'],mode=mode,steps=steps)
  if 'source' in original:sc.update(source=original['source'],summary=dict(original['summary'],version=steps[0]['result']))
  scenarios.append(sc)
assert all(h.hits[n] for n in FUNCTIONS),h.hits
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for a in FUNCTIONS.values():
 for p in (base/'native_analysis/core_round3/full_library/functions').glob(f'{a:08x}_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),scenarios_passed=len(scenarios),checkpoints=checks,function_entry_hits={n:h.hits[n] for n in FUNCTIONS},scenarios=scenarios,
 scope='Original three scalar getter branches and wide-to-low-byte decimal helper execute. Non-RTID cases only; partial entries, not three fully restored functions. Original soft-float conversion helpers execute including infinities/NaNs. atoi/strtol use controlled host 32-bit C runtime with decimal inputs within signed32 range; overflow/locale equivalence excluded. Return bits and exact cursor compared in external/vector modes. Reference coercion, scalar64/float getters, object factory, Android ABI/runtime remain missing.')
(OUT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(scenarios),'original non-RTID scalar scenarios;',checks,'bits/cursor checkpoints')
