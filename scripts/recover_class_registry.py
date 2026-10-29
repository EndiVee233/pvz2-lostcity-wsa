from pathlib import Path
import sys,re,struct,json,csv,collections
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
source=base/'raw/lib/armeabi/libSrc.so';blob=source.read_bytes()
with source.open('rb') as fp:segments=[s for s in ELFFile(fp).iter_segments() if s['p_type']=='PT_LOAD']
def read(address,size):
    va=address-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    return None
def address(expression):
    expression=expression.strip()
    m=re.fullmatch(r'DAT_([0-9a-fA-F]{8})\s*\+\s*(0x[0-9a-fA-F]+)',expression)
    if not m:
        symbol=re.fullmatch(r'&?(?:FUN_|DAT_|LAB_|Recovered_\w+_)([0-9a-fA-F]{8})',expression)
        return int(symbol[1],16) if symbol else None
    raw=read(int(m[1],16),4)
    return (struct.unpack('<I',raw)[0]+int(m[2],16))&0xffffffff if raw else None
def string(expression):
    if expression.startswith('"'):
        try:return json.loads(expression)
        except ValueError:return None
    a=address(expression);raw=read(a,256) if a else None
    if not raw or b'\0' not in raw:return None
    raw=raw.split(b'\0',1)[0]
    try:return raw.decode('ascii')
    except UnicodeDecodeError:return None
root=base/'native_analysis/core_deep'
index_candidates=[root/'functions.csv',base/'native_analysis/core_round3/virtual_methods_final/functions.csv',base/'native_analysis/core_round3/full_library/functions.csv']
latest_index=next(p for p in reversed(index_candidates) if p.exists())
function_index={r['address']:r for r in csv.DictReader(latest_index.open(encoding='utf-8-sig'))}
pattern=r'DAT_[0-9a-fA-F]{8}\s*\+\s*0x[0-9a-fA-F]+'
string_pattern=r'(?:'+pattern+r'|"(?:[^"\\]|\\.)*")'
string_write_pattern=r'(?:'+string_pattern+r'|[A-Za-z_]\w*(?:\s*\+\s*(?:0x[0-9a-f]+|[A-Za-z_]\w*))?)'
callback_pattern=r'(?:'+pattern+r'|&?(?:FUN_|DAT_|LAB_|Recovered_\w+_)[0-9a-fA-F]{8})'
registrations=[];getters=[]
latest={}
for folder in [root/'functions',base/'native_analysis/core_round3/functions',base/'native_analysis/core_round3/expand/functions',
               base/'native_analysis/core_round3/virtual_methods/functions',base/'native_analysis/core_round3/virtual_methods_extra/functions',
               base/'native_analysis/core_round3/constructors/functions',base/'native_analysis/core_round3/virtual_methods_final/functions',
               base/'native_analysis/core_round3/full_library/functions']:
    for src in sorted(folder.glob('*.c')):latest[src.name.split('_',1)[0]]=src
for src in latest.values():
    code=src.read_text(encoding='utf-8',errors='replace')
    owner=src.name.split('_',1)[0]
    writes=[]
    for m in re.finditer(r'FUN_014fd0e0\(\s*&?([A-Za-z_]\w*)\s*,\s*('+string_write_pattern+r')\s*(?:,[^;]*?)?\);',code):
        text=string(m[2])
        writes.append((m.end(),m[1],text))
    for m in re.finditer(r'\(\*pcVar\d+\)\(piVar\d+,\s*&?(\w+),\s*('+callback_pattern+r'),\s*(0x[0-9a-f]+|[0-9]+),0\)',code):
        candidates=[w for w in writes if w[0]<m.start() and w[1]==m[1]]
        if not candidates:continue
        name=candidates[-1][2]
        if not name or not re.fullmatch(r'[A-Za-z_]\w{1,99}',name):continue
        callback=address(m[2]);key=f'{callback&~1:08x}' if callback else ''
        if key not in function_index:continue
        registrations.append({'class_name':name,'registration_function':owner,'callback':key,
                              'registered_size':hex(int(m[3],0)),'callback_thumb':bool(callback&1),
                              'source_file':str(src.relative_to(base)),'evidence_expression':m[2],
                              'role':'class registration callback; field registration role requires inspection'})
    if 'FUN_011f5efc()' in code and re.search(r'return (?:\*piVar\d+|DAT_[0-9a-f]+);',code):
        for m in re.finditer(r'\(\*pcVar\d+\)\(piVar\d+,\s*('+string_pattern+r'),\s*(uVar\d+),\s*('+callback_pattern+r'),',code):
            name=string(m[1])
            if name and re.fullmatch(r'[A-Za-z_]\w{1,99}',name):
                parents=list(re.finditer(re.escape(m[2])+r'\s*=\s*((?:FUN_|Recovered_\w+_)[0-9a-f]{8})\(\);',code[:m.start()]))
                callback=address(m[3])
                getters.append({'class_name':name,'address':owner,'source_file':str(src.relative_to(base)),
                                'parent_metadata_getter':f'{address(parents[-1][1]):08x}' if parents else None,
                                'type_callback':f'{callback&~1:08x}' if callback else None,
                                'role':'cached type metadata getter; inferred from allocation/name/return pattern'})
aliases=collections.defaultdict(list)
for row in registrations:aliases[row['callback']].append(('Registry',row['class_name'],row))
for row in getters:aliases[row['address']].append(('TypeMetadata',row['class_name'],row))
for row in getters:
    addr=row['type_callback']
    executable=addr and any(s['p_flags']&1 and s['p_vaddr']<=int(addr,16)-0x10000<s['p_vaddr']+s['p_filesz'] for s in segments)
    if executable:aliases[addr].append(('TypeCallback',row['class_name'],row))
names=[]
for addr,items in aliases.items():
    identities={(role,name) for role,name,row in items}
    if len(identities)!=1:continue
    role,name=next(iter(identities))
    names.append({'address':addr,'recovered_name':'Recovered_'+role+'_'+name+'_'+addr,
                  'class_name':name,'role':role,'evidence':items[0][2]})
out=base/'native_analysis/core_round3';out.mkdir(exist_ok=True)
(out/'class_registrations.json').write_text(json.dumps(registrations,indent=2),encoding='utf-8')
(out/'type_metadata_getters.json').write_text(json.dumps(getters,indent=2),encoding='utf-8')
(out/'recovered_name_candidates.json').write_text(json.dumps(names,indent=2),encoding='utf-8')
print('Class registration records:',len(registrations),'type metadata getters:',len(getters),'unambiguous role labels:',len(names))
for row in registrations:
    if row['class_name'] in ('Plant','Zombie','PlantPeashooter','PlantSunflower','Board'):
        print(row['class_name'],row['callback'],row['registered_size'])
