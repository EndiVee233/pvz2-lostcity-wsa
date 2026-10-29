from pathlib import Path
import json,sys
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'tools/python_libs'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f:
    elf=ELFFile(f);segments=[dict(s.header) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
def read(address,size):
    va=address-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    raise ValueError(hex(address))
dec=Cs(CS_ARCH_ARM,CS_MODE_ARM);functions=[]
for entry,branch,end,width in [(0x1491afc,0x1491c80,0x149287c,2),(0x1493eb0,0x1494034,0x1494c58,4)]:
    bound=list(dec.disasm(read(branch-4,4),branch-4))[0]
    dispatch=list(dec.disasm(read(branch,4),branch))[0]
    assert bound.mnemonic=='cmp' and bound.op_str=='r3, #0x53'
    assert dispatch.mnemonic=='addls' and dispatch.op_str=='pc, pc, r3, lsl #2'
    entries=[]
    for index in range(84):
        address=branch+8+index*4;ins=list(dec.disasm(read(address,4),address))[0]
        assert ins.mnemonic=='b'
        target=int(ins.op_str.removeprefix('#'),16);assert entry<=target<end
        entries.append({'index':index,'format_code':index+0x25,'format_character':chr(index+0x25),
                        'instruction_address':f'{address:08x}','instruction_bytes':bytes(ins.bytes).hex(),'target':f'{target:08x}'})
    functions.append({'address':f'{entry:08x}','switch_address':f'{branch:08x}','next_known_function':f'{end:08x}',
                      'candidate_character_width':width,'entries':entries})
root=base/'native_analysis/core_round6';(root/'format_switches.json').write_text(json.dumps({'functions':functions},indent=2),encoding='utf-8')
print('Verified ARM branch-table entries:',sum(len(f['entries']) for f in functions))
