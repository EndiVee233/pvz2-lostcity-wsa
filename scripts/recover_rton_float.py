"""Round 25: original float32 getter, numeric and narrow decimal branches.

The original ARM soft-float helpers execute. Decimal strtod is the controlled
host C runtime; hex/NaN/infinity text, wide swscanf, RTID and cross-libc
special-text/locale parity excluded.
"""
import hashlib,json,random,shutil,struct
from reflection_emulation_support import h
base=h.base;OUT=base/'native_analysis/core_round25/rton_float';OUT.mkdir(parents=True,exist_ok=True)
STREAM,READER,BUFFER=0x6008000,0x6008100,0x6009000
h.FUNCTIONS['f32']=0x11f9ae8;h.hits['f32']=0
old=json.loads((base/'native_analysis/core_round23/rton_scalars/validation.json').read_text(encoding='utf-8'))
cases=[dict(label=s['label'].removesuffix('-mode0'),data=s['data'],offset=s['steps'][0]['offset']) for s in old['scenarios'] if s['mode']==0 and not s['label'].startswith('wide-') and s['label'] not in ['narrow-inline-9-mode0','narrow-reference-9-mode0']]
header=b'RTON\x01\0\x01\0\xb8\xffDONE\0\0'
def case(label,tag,payload):cases.append(dict(label=label,data=list(header+bytes([tag])+payload),offset=16))
rng=random.Random(0x464c5432)
for tag in [0x40,0x46]:
 for bits in [rng.getrandbits(64) for _ in range(160)]+[(1<<n)+delta for n in [24,25,31,32,53,62,63] for delta in [-1,0,1,2,3,7,255,256,257]]:
  case('integer64-'+hex(tag)+'-'+hex(bits),tag,struct.pack('<Q',bits))
for n in [-150,-149,-148,-127,-126,-125,0,1,23,24,127,128]:
 for number in [2.0**n,-2.0**n,(1.0+2**-24)*2.0**n,(1.0+2**-24+2**-52)*2.0**n]:
  case('double-boundary-'+number.hex(),0x42,struct.pack('<d',number))
for s in ['1.25','-0',' \t-12.75tail','6.022e23','1e-45','3.4028235e38','1e39','-1e39','1e-400','1.000000059604644775390625','junk']:
 b=s.encode()+b'\0';case('decimal-'+s,0xb0,struct.pack('<I',len(b))+b)
scenarios=[]
for c in cases:
 for mode in [0,1]:
  h.cursor=0x8000000;h.u.mem_write(STREAM,bytes(0x200));data=bytes(c['data']);h.u.mem_write(BUFFER,data+bytes(64))
  if mode==0:h.put(STREAM,BUFFER,len(data),0,0,0,0,0)
  else:h.put(STREAM,0,0,BUFFER,BUFFER+len(data),BUFFER+len(data),0,0)
  h.call(0x11f8818,[READER,STREAM]);h.put(STREAM+20,13)
  result=h.call(0x11f9ae8,[READER,c['offset'],0x87654321])
  scenarios.append(dict(**c,mode=mode,fallback=0x87654321,result=result,position=h.words(STREAM+20)[0]))
folder=OUT/'pseudocode';folder.mkdir(exist_ok=True)
for p in (base/'native_analysis/core_round3/full_library/functions').glob('011f9ae8_*.c'):shutil.copy2(p,folder/p.name)
record=dict(original_sha256=hashlib.sha256((base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),checkpoints=len(scenarios),function_entry_hits=h.hits['f32'],scenarios=scenarios,scope=__doc__)
(OUT/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['// Original ARM float getter return bits and exact cursor; no host expected-value calculation.','const FloatCase float_cases[] = {']
for s in scenarios:lines.append('{'+','.join([json.dumps(s['label']),'{'+','.join(str(x)+'U' for x in s['data'])+'}',*[str(s[k])+'U' for k in ['offset','fallback','result','position']]])+'},')
lines.append('};');(base/'native_recovered/tests/rton_float_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('PASS',len(scenarios),'original numeric/narrow-decimal float bits/cursor checkpoints',flush=True)
