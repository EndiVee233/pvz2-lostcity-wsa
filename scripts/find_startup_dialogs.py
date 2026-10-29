from pathlib import Path
import sys,struct,re,json
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f: segments=[dict(s.header) for s in ELFFile(f).iter_segments() if s['p_type']=='PT_LOAD']
def offset(a):
 for s in segments:
  if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']: return s['p_offset']+a-s['p_vaddr']
def address(o):
 for s in segments:
  if s['p_offset']<=o<s['p_offset']+s['p_filesz']:return s['p_vaddr']+o-s['p_offset']+0x10000
keys={}
for m in re.finditer(rb'(?:[\x20-\x7e]\x00\x00\x00){8,}',blob):
 t=m.group().decode('utf-32le')
 if re.search('NETWORK|ICLOUD|NOTICE|ANNOUNC',t): keys[address(m.start())]=t
hits=[]
for f in (base/'native_analysis/core_round3/full_library/functions').glob('*.c'):
 text=f.read_text(errors='replace')
 for m in re.finditer(r'(?:DAT|UNK)_([0-9a-f]{8})',text):
  target=int(m[1],16)
  if target in keys:hits.append({'function':f.stem,'string':keys[target],'target':hex(target),'expression':m[0]})
 for m in re.finditer(r'DAT_([0-9a-f]{8})\s*\+\s*0x([0-9a-f]+)',text):
  o=offset(int(m[1],16)-0x10000)
  if o is None:continue
  target=(struct.unpack_from('<I',blob,o)[0]+int(m[2],16))&0xffffffff
  if target in keys:hits.append({'function':f.stem,'string':keys[target],'target':hex(target),'expression':m[0]})
out=base/'native_analysis/startup_dialogs';out.mkdir(exist_ok=True)
(out/'string-xrefs.json').write_text(json.dumps(hits,indent=2),encoding='utf-8')
print(json.dumps(hits,indent=2))
