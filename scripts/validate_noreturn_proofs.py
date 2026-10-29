"""Independently check Ghidra's no-return proof against ELF bytes and Capstone."""
from pathlib import Path
import json,sys,struct
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB,CS_GRP_CALL,CS_GRP_JUMP
from capstone.arm import ARM_OP_IMM,ARM_CC_AL,ARM_CC_INVALID
from elftools.elf.elffile import ELFFile
root=base/'native_analysis/core_round5'
proof=json.loads((root/'noreturn/noreturn_audit.json').read_text())
path=base/'raw/lib/armeabi/libSrc.so';blob=path.read_bytes()
with path.open('rb') as fp:
    elf=ELFFile(fp);segments=[dict(s.header) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    symbols={s.name:dict(s.entry) for s in elf.get_section_by_name('.dynsym').iter_symbols()}
    dyn=elf.get_section_by_name('.dynsym')
    relocations={r['r_offset']+0x10000:dyn.get_symbol(r['r_info_sym']).name for r in elf.get_section_by_name('.rel.plt').iter_relocations()}
def read(address,size):
    va=address-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            return blob[s['p_offset']+va-s['p_vaddr']:s['p_offset']+va-s['p_vaddr']+size]
    raise AssertionError(('unbacked address',hex(address),size))
decoders={0:Cs(CS_ARCH_ARM,CS_MODE_ARM),1:Cs(CS_ARCH_ARM,CS_MODE_THUMB)}
for d in decoders.values():d.detail=True

def check_import_thunk(address,name,visited=None):
    visited=set() if visited is None else visited
    assert address not in visited;visited.add(address)
    ins=list(decoders[0].disasm(read(address,12),address))
    # ARM ELF PLT: ADD ip,pc,#imm; ADD ip,ip,#imm; LDR pc,[ip,#imm]!
    if [i.mnemonic for i in ins]==['add','add','ldr']:
        a,b,c=ins
        assert a.reg_name(a.operands[0].reg)=='ip' and a.reg_name(a.operands[1].reg)=='pc'
        assert b.reg_name(b.operands[0].reg)=='ip' and b.reg_name(b.operands[1].reg)=='ip'
        assert c.reg_name(c.operands[0].reg)=='pc' and c.reg_name(c.operands[1].mem.base)=='ip'
        slot=address+8+a.operands[2].imm+b.operands[2].imm+c.operands[1].mem.disp
        assert relocations[slot]==name,(hex(address),name,hex(slot));return
    # ARM-to-ARM veneer: LDR ip,[pc]; ADD pc,pc,ip; signed relative literal.
    if [i.mnemonic for i in ins[:2]]==['ldr','add']:
        a,b=ins[:2]
        assert a.reg_name(a.operands[0].reg)=='ip' and a.reg_name(a.operands[1].mem.base)=='pc'
        assert b.reg_name(b.operands[0].reg)=='pc' and b.reg_name(b.operands[1].reg)=='pc' and b.reg_name(b.operands[2].reg)=='ip'
        literal=struct.unpack('<i',read(address+8+a.operands[1].mem.disp,4))[0]
        check_import_thunk((address+12+literal)&0xffffffff,name,visited);return
    raise AssertionError(('unknown import thunk',hex(address),name))

known=set();seed_evidence=[]
for seed in proof['seeds']:
    address=int(seed['address'],16);name=seed['name'];sym=symbols[name]
    if sym['st_shndx']!='SHN_UNDEF':
        assert address==(sym['st_value']&~1)+0x10000
        kind='defined dynamic symbol'
    elif seed['size']==1:
        # Ghidra's synthetic linkage entries lie outside the ELF load segments.
        assert seed['symbol_source'] in ('DEFAULT','IMPORTED')
        target=seed.get('resolved_thunk');assert target and target['external'] and target['name']==name
        kind='undefined dynamic symbol / synthetic external linkage'
    elif 'resolved_thunk' in seed:
        target=seed['resolved_thunk'];assert target['external'] and target['name']==name
        check_import_thunk(address,name);kind='ELF PLT relocation or veneer'
    else:
        # The synthetic external function is a Ghidra linkage artifact, not code.
        assert seed['size']==1 and seed['symbol_source']=='IMPORTED'
        kind='undefined dynamic symbol / synthetic external linkage'
    known.add(seed['address']);seed_evidence.append({'address':seed['address'],'name':name,'verified_via':kind})

instruction_count=0;conditional_count=0
for wrapper in proof['proven_wrappers']:
    rows=sorted(wrapper['instructions'],key=lambda r:int(r['address'],16));decoded={};runs=[]
    for row in rows:
        address=int(row['address'],16);data=bytes.fromhex(row['bytes']);assert read(address,len(data))==data
        if runs and runs[-1]['end']==address and runs[-1]['thumb']==row['thumb']:
            runs[-1]['bytes']+=data;runs[-1]['end']+=len(data)
        else:runs.append({'start':address,'end':address+len(data),'thumb':row['thumb'],'bytes':data})
    for run in runs:
        for ins in decoders[run['thumb']].disasm(run['bytes'],run['start']):decoded[f'{ins.address:08x}']=ins
    graph={};terminal_instructions=set()
    for row in rows:
        key=row['address'];ins=decoded[key];instruction_count+=1
        assert ins.bytes==bytes.fromhex(row['bytes'])
        conditional=ins.cc not in (ARM_CC_AL,ARM_CC_INVALID) or ins.mnemonic.startswith(('cbz','cbnz'))
        branch=CS_GRP_JUMP in ins.groups;call=CS_GRP_CALL in ins.groups
        if call or branch:
            targets=[f'{o.imm&~1:08x}' for o in ins.operands if o.type==ARM_OP_IMM]
            assert targets==row['targets'],(key,ins.mnemonic,targets,row['targets'])
            if conditional:assert row['conditional'],(key,'lost ARM predicate');conditional_count+=1
        else:assert row['flow']=='FALL_THROUGH',(key,ins.mnemonic,row['flow'])
        nextkey=f'{ins.address+ins.size:08x}';edges=[]
        if call:
            if len(row['targets'])==1 and row['targets'][0] in known:
                terminal_instructions.add(key)
                if conditional:edges.append(nextkey)
            else:edges.append(nextkey)
        elif branch:
            assert row['targets'],(key,'unresolved jump')
            for target in row['targets']:
                if target in known:terminal_instructions.add(key)
                else:edges.append(target)
            if conditional:edges.append(nextkey)
        else:edges.append(nextkey)
        graph[key]=edges
    seen=set();active=set()
    def visit(key):
        if key in seen:return
        assert key not in active,('unproven loop',key)
        assert key in graph,('unproven path',key)
        active.add(key)
        assert graph[key] or key in terminal_instructions,('unproven terminal',key)
        for successor in graph[key]:visit(successor)
        active.remove(key);seen.add(key)
    visit(wrapper['address']);assert len(seen)==len(graph)
    assert terminal_instructions
    known.add(wrapper['address'])
result={'verified_seed_records':len(proof['seeds']),'verified_wrappers':len(proof['proven_wrappers']),
        'verified_instruction_bytes_and_control_flow':instruction_count,'conditional_transfers_checked':conditional_count,'seed_evidence':seed_evidence}
(base/'logs/round5_noreturn_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='seed_evidence'},indent=2))
