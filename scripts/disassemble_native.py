from pathlib import Path
import sys, csv
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB,CS_MODE_LITTLE_ENDIAN
for name in ['libHookPVZ2','libSrc']:
    symbols=list(csv.DictReader((base/'native_analysis'/name/'symbols.csv').open(encoding='utf-8-sig')))
    selected=[s for s in symbols if s['defined']=='True' and s['type']=='STT_FUNC' and int(s['size'])>0
              and (name=='libHookPVZ2' or s['name']=='JNI_OnLoad' or s['name'].startswith('Java_'))]
    with (base/'raw/lib/armeabi'/(name+'.so')).open('rb') as src:
        elf=ELFFile(src)
        with (base/'native_analysis'/name/'disassembly.asm').open('w',encoding='utf-8') as dst:
            for sym in selected:
                address=int(sym['address'],16);start=address & ~1
                for segment in elf.iter_segments():
                    if segment['p_type']=='PT_LOAD' and segment['p_vaddr']<=start<segment['p_vaddr']+segment['p_filesz']:
                        fileoff=segment['p_offset']+start-segment['p_vaddr'];break
                else:continue
                src.seek(fileoff);code=src.read(int(sym['size']))
                md=Cs(CS_ARCH_ARM,(CS_MODE_THUMB if address&1 else CS_MODE_ARM)|CS_MODE_LITTLE_ENDIAN)
                dst.write('\n; '+sym['name']+' @ '+hex(address)+'\n')
                for ins in md.disasm(code,start):dst.write(f'{ins.address:08x}: {ins.mnemonic:10} {ins.op_str}\n')
    print(name,'exported disassembly for',len(selected),'functions')
