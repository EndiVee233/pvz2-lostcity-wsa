from pathlib import Path
import sys,re,struct,json

base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
source=base/'raw/lib/armeabi/libSrc.so'
blob=source.read_bytes()
with source.open('rb') as fp:
    segments=[s for s in ELFFile(fp).iter_segments() if s['p_type']=='PT_LOAD']
def read_ghidra(addr,size):
    va=addr-0x10000
    for seg in segments:
        if seg['p_vaddr']<=va and va+size<=seg['p_vaddr']+seg['p_filesz']:
            offset=seg['p_offset']+va-seg['p_vaddr']
            return blob[offset:offset+size]
    return None
def resolve(expression):
    m=re.fullmatch(r'DAT_([0-9a-fA-F]{8})\s*\+\s*(0x[0-9a-fA-F]+)',expression)
    if not m:return None
    raw=read_ghidra(int(m[1],16),4)
    if not raw:return None
    target=(struct.unpack('<I',raw)[0]+int(m[2],16))&0xffffffff
    raw=read_ghidra(target,256)
    if not raw or b'\0' not in raw:return None
    text=raw.split(b'\0',1)[0]
    if not 3<=len(text)<=180 or any(c<32 or c>126 for c in text):return None
    if not any(chr(c).isalpha() for c in text):return None
    return text.decode('ascii'),target

root=base/'native_analysis/core_deep'
out=root/'annotated';out.mkdir(exist_ok=True)
allrows=[];layouts=[]
pattern=r'DAT_[0-9a-fA-F]{8}\s*\+\s*0x[0-9a-fA-F]+'
for src in sorted((root/'functions').glob('*.c')):
    code=src.read_text(encoding='utf-8',errors='replace')
    refs=[]
    def annotate(match):
        found=resolve(match.group())
        if not found:return match.group()
        text,target=found
        refs.append({'expression':match.group(),'text':text,'ghidra_address':hex(target)})
        return match.group()+' /* '+json.dumps(text).replace('*/','* /')+' */'
    annotated=re.sub(pattern,annotate,code)
    (out/src.name).write_text(annotated,encoding='utf-8')
    allrows.append({'function_file':src.name,'resolved_strings':refs})
    # Candidate property offsets are derived from the string constructor and a
    # subsequent registration call using the same local string variable.
    writes=[]
    for m in re.finditer(r'FUN_[0-9a-f]+\(\s*&?([A-Za-z_]\w*)\s*,\s*('+pattern+r')\s*,[^;]+;',code):
        found=resolve(m[2])
        if found:writes.append((m.end(),m[1],found[0]))
    for m in re.finditer(r'\(\*pcVar\d+\)\(param_1,param_2,\s*&?([A-Za-z_]\w*)\s*,\s*(0x[0-9a-fA-F]+|[0-9]+)\s*,',code):
        prior=[w for w in writes if w[0]<m.start() and w[1]==m[1]]
        if not prior:continue
        _,variable,name=prior[-1]
        layouts.append({'function_file':src.name,'property':name,'candidate_offset':m[2],
                        'evidence':'Name-string construction followed by registration call; inferred, not verified runtime layout'})
(root/'resolved_string_expressions.json').write_text(json.dumps(allrows,indent=2),encoding='utf-8')
(root/'property_offset_candidates.json').write_text(json.dumps(layouts,indent=2),encoding='utf-8')
print('Annotated functions',len(allrows),'resolved string expressions',sum(len(r['resolved_strings']) for r in allrows),'property offset candidates',len(layouts))
