from pathlib import Path
import sys,json,re,struct,collections
base=Path(__file__).resolve().parents[1];r3=base/'native_analysis/core_round3';r4=base/'native_analysis/core_round4'
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f:
    elf=ELFFile(f);segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    code_regions=[(s['sh_addr'],s['sh_addr']+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read(gh,size):
    va=gh-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    return None
def constant(expr,pointer=False):
    expr=expr.strip()
    m=re.fullmatch(r'DAT_([0-9a-f]{8})\s*\+\s*(0x[0-9a-f]+)',expr)
    if m:
        raw=read(int(m[1],16),4)
        return (struct.unpack('<I',raw)[0]+int(m[2],16))&0xffffffff if raw else None
    m=re.search(r'(?:UNK_|DAT_|LAB_|FUN_|func_0x|Recovered_\w+_)([0-9a-f]{8})$',expr)
    if m:return int(m[1],16)
    m=re.fullmatch(r'(?:\([^()]*\)\s*)?(-?0x[0-9a-f]+|-?[0-9]+)',expr)
    return int(m[1],0)&0xffffffff if m else None
def string(expr):
    if expr.startswith('"'):
        try:return json.loads(expr)
        except ValueError:return None
    address=constant(expr,True);raw=read(address,256) if address else None
    if not raw or b'\0' not in raw:return None
    raw=raw.split(b'\0',1)[0]
    if not raw or any(c<32 or c>126 for c in raw):return None
    return raw.decode('ascii')
catalog={r['address']:dict(r,path=base/r['source']) for r in json.loads((r3/'model/function_catalog.json').read_text())}
for folder in [r4/'entries',r4/'isolated_v8',r4/'isolated_v7']:
    if not (folder/'summary.json').exists():continue
    for row in json.loads((folder/'summary.json').read_text())['exports']:
        if row['status']=='ok' and row['address'] not in catalog:catalog[row['address']]=dict(row,path=folder/row['file'])
registrations=json.loads((r3/'class_registrations.json').read_text());results=[]
str_expr=r'(?:"(?:[^"\\]|\\.)*"|&?[A-Za-z_]\w*(?:\s*\+\s*0x[0-9a-f]+)?)'
desc_expr=r'(?:0x[0-9a-f]+|&[A-Za-z_]+[0-9a-f]{8})'
for registration in registrations:
    source=catalog.get(registration['callback'])
    if not source:continue
    code=source['path'].read_text(encoding='utf-8',errors='replace');writes=[];globals=[]
    for m in re.finditer(r'(?:FUN_|func_0x)014fd0e0\(\s*&?(\w+),\s*('+str_expr+r')\s*(?:,[^;]*?)?\);',code):writes.append((m.end(),m[1],string(m[2])))
    for m in re.finditer(r'\b[A-Za-z_]+([0-9a-f]{8})\s*=\s*([^;]+);',code):globals.append((m.end(),int(m[1],16),constant(m[2],True),m[2]))
    for m in re.finditer(r'\(\*(pcVar\d+)\)\(param_1,param_2,\s*&?(\w+),\s*('+desc_expr+r'),\s*\w+,0\)',code):
        assignments=list(re.finditer(re.escape(m[1])+r'\s*=\s*([^;]+);',code[:m.start()]))
        if not assignments or not re.search(r'\*param_1 \+ 0x34\)',assignments[-1][1]):continue
        previous=[w for w in writes if w[0]<m.start() and w[1]==m[2]]
        if not previous or not previous[-1][2] or not re.fullmatch(r'[A-Za-z_]\w{0,100}',previous[-1][2]):continue
        name=previous[-1][2];desc=constant(m[3],True)
        if not desc:continue
        def descriptor_field(offset,is_pointer=False):
            seen=[w for w in globals if w[0]<m.start() and w[1]==desc+offset]
            if seen:return seen[-1][2]
            raw=read(desc+offset,4)
            if not raw:return None
            value=struct.unpack('<I',raw)[0]
            return value+0x10000 if is_pointer and value else value
        target=descriptor_field(4,True);flags=descriptor_field(8)
        if target is None or flags is None or flags&1:continue
        va=(target&~1)-0x10000
        if not any(lo<=va<hi for lo,hi in code_regions):continue
        record={'class_name':registration['class_name'],'method_name':name,'address':f'{target&~1:08x}',
                'elf_address':hex(va),'thumb':bool(target&1),'descriptor_address':hex(desc),'member_flags':flags,
                'registration_callback':registration['callback'],'evidence_source':str(source['path'].relative_to(base)),
                'evidence':'Reflection method slot 0x34, descriptor code pointer at +4 and nonvirtual flag at +8'}
        nearby=list(dict.fromkeys(w[2] for w in writes if previous[-1][0]<=w[0]<m.start() and w[1]!=m[2] and w[2]))
        record['nearby_type_strings']=nearby
        raw=read(target&~1,128);instructions=[]
        if raw and not target&1:
            for ins in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(raw,target&~1):
                instructions.append(ins)
                if ins.mnemonic=='bx' and ins.op_str=='lr':break
            loads=[i for i in instructions if i.mnemonic=='ldr' and re.fullmatch(r'r0, \[r0(?:, #(0x[0-9a-f]+|[0-9]+))?\]',i.op_str)]
            safe=instructions and instructions[-1].mnemonic=='bx' and instructions[-1].op_str=='lr' and len(loads)==1
            for ins in instructions:
                if ins.mnemonic.startswith('b') and not (ins.mnemonic=='bx' and ins.op_str=='lr'):safe=False
                if ins.mnemonic.startswith('str') and '[r0' in ins.op_str:safe=False
                if ins.op_str.split(',')[0]=='r0' and ins not in loads:safe=False
            if safe:
                match=re.fullmatch(r'r0, \[r0(?:, #(0x[0-9a-f]+|[0-9]+))?\]',loads[0].op_str)
                record['simple_getter_offset']=hex(int(match[1],0) if match[1] else 0)
                record['getter_evidence']=[f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in instructions]
        results.append(record)
dedup={(r['class_name'],r['method_name'],r['address']):r for r in results}
results=list(dedup.values());out=r4/'model';out.mkdir(exist_ok=True)
(out/'reflected_methods.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Reflected direct methods:',len(results),'distinct targets:',len({r['address'] for r in results}),'simple getters:',sum('simple_getter_offset' in r for r in results))
for row in results:
    if row['class_name'] in ['Zombie','Plant','Board']:print(row['class_name'],row['method_name'],row['address'],row.get('simple_getter_offset',''))
