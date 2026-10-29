from pathlib import Path
import sys, struct, re, json, csv
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
src=base/'raw/lib/armeabi/libSrc.so'
data=src.read_bytes()
with src.open('rb') as fp:
    elf=ELFFile(fp)
    loads=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    executable=[(s['p_vaddr'],s['p_vaddr']+s['p_memsz']) for s in loads if s['p_flags']&1]
    def string_at(va):
        for s in loads:
            if s['p_vaddr']<=va<s['p_vaddr']+s['p_filesz']:
                off=s['p_offset']+va-s['p_vaddr'];end=data.find(b'\0',off,min(off+512,len(data)))
                if end<0:return None
                try:return data[off:end].decode('ascii')
                except UnicodeDecodeError:return None
        return None
    entries=[]
    for section in elf.iter_sections():
        if not section['sh_flags']&2 or section['sh_flags']&4 or section['sh_type']=='SHT_NOBITS':continue
        start=section['sh_offset'];end=start+section['sh_size']
        for pos in range(start,end-11,4):
            nameptr,sigptr,func=struct.unpack_from('<III',data,pos)
            if not any(lo<=func&~1<hi for lo,hi in executable):continue
            sig=string_at(sigptr)
            if not sig or not re.fullmatch(r'\([BCDFIJSZVL\[;/a-zA-Z0-9_$]*\)[BCDFIJSZVL\[;/a-zA-Z0-9_$]+',sig):continue
            name=string_at(nameptr)
            if not name or not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]{1,100}',name):continue
            entries.append({'name':name,'signature':sig,'elf_address':hex(func&~1),'thumb':bool(func&1),
                            'table_address':hex(section['sh_addr']+pos-start),'section':section.name})
out=base/'native_analysis/libSrc'
(out/'jni_tables.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
with (out/'jni_tables.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['name','signature','elf_address','thumb','table_address','section']);w.writeheader();w.writerows(entries)
print('Recovered JNI table candidates:',len(entries))
for entry in entries[:35]:print(entry['elf_address'],entry['name'],entry['signature'])
