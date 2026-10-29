"""Run a bounded set of original ARM/Thumb instructions in a CPU emulator."""
from pathlib import Path
import sys,json,struct,collections
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'tools/python_libs'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UcError
from unicorn.arm_const import *
from elftools.elf.elffile import ELFFile
root=base/'native_analysis/core_round6'
path=base/'raw/lib/armeabi/libSrc.so';blob=path.read_bytes()
with path.open('rb') as fp:
    elf=ELFFile(fp);segments=[dict(s.header) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    symbols=[dict(s.entry,name=s.name) for s in elf.get_section_by_name('.dynsym').iter_symbols()]
    relocations=[dict(r.entry) for section in elf.iter_sections() if section['sh_type']=='SHT_REL' for r in section.iter_relocations()]
def machine():
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    lo=min(s['p_vaddr']+0x10000 for s in segments)&~4095
    hi=max(s['p_vaddr']+0x10000+s['p_memsz'] for s in segments);hi=(hi+4095)&~4095
    uc.mem_map(lo,hi-lo)
    for seg in segments:uc.mem_write(seg['p_vaddr']+0x10000,blob[seg['p_offset']:seg['p_offset']+seg['p_filesz']])
    imports={};external=0x7000000;uc.mem_map(external,0x10000)
    for r in relocations:
        address=r['r_offset']+0x10000;kind=r['r_info_type']
        if kind==23:
            value=struct.unpack('<I',uc.mem_read(address,4))[0];uc.mem_write(address,struct.pack('<I',(value+0x10000)&0xffffffff))
        elif kind in (2,21,22):
            symbol=symbols[r['r_info_sym']]
            if symbol['st_shndx']=='SHN_UNDEF':
                target=external+r['r_info_sym']*4;imports[target]=symbol['name'];uc.mem_write(target,bytes.fromhex('1eff2fe1'))
            else:target=symbol['st_value']+0x10000
            if kind==2:target+=struct.unpack('<I',uc.mem_read(address,4))[0]
            uc.mem_write(address,struct.pack('<I',target&0xffffffff))
    uc.mem_map(0x4000000,0x100000);uc.mem_map(0x5000000,0x1000);uc.mem_map(0x6000000,0x20000)
    return uc,imports

switch=json.loads((base/'native_analysis/core_round5/model/gnu_thumb_case_si_switch.json').read_text(encoding='utf-8'))
uc,_=machine();helper_results=[];state={}
def helper_hook(uc,address,size,user):
    if address==state.get('expected'):uc.emu_stop()
uc.hook_add(UC_HOOK_CODE,helper_hook)
for entry in switch['entries']:
    target=int(entry['target'],16);state['expected']=target
    uc.reg_write(UC_ARM_REG_CPSR,0x30);uc.reg_write(UC_ARM_REG_SP,0x4080000)
    uc.reg_write(UC_ARM_REG_R0,entry['case']);uc.reg_write(UC_ARM_REG_R1,0x1234abcd)
    uc.reg_write(UC_ARM_REG_LR,0x1505581)
    uc.emu_start(0x15eddfd,0,count=30)
    assert uc.reg_read(UC_ARM_REG_PC)==target
    assert uc.reg_read(UC_ARM_REG_CPSR)&0x20
    assert uc.reg_read(UC_ARM_REG_R0)==entry['case'] and uc.reg_read(UC_ARM_REG_R1)==0x1234abcd
    assert uc.reg_read(UC_ARM_REG_SP)==0x4080000
    table=0x1505580;unsigned_offset=entry['signed_offset']&0xffffffff
    carry=int(table+unsigned_offset>0xffffffff)
    overflow=int(bool((~(table^unsigned_offset)&(table^target))&0x80000000))
    expected_nzcv=((target>>31)<<3)|(int(target==0)<<2)|(carry<<1)|overflow
    assert (uc.reg_read(UC_ARM_REG_CPSR)>>28)&15==expected_nzcv
    helper_results.append({'case':entry['case'],'target':entry['target'],'thumb_preserved':True,'r0_r1_sp_preserved':True,'nzcv':expected_nzcv,'nzcv_matches_model':True})

format_results=[]
for entry,width in [(0x1491afc,2),(0x1493eb0,4)]:
    for fmt,args,expected,force_failure in [
        ('PvZ2 test',[],'PvZ2 test',False),('植物',[],'植物',False),
        ('value=%d',[42],'value=42',False),('negative=%d',[-7],'negative=-7',False),
        ('hex=%x',[0x2a],'hex=2a',False),('pad=%08x',[0x2a],'pad=0000002a',False),
        ('callback-failure',[],'',True)]:
        uc,imports=machine();events=[];error=[];tail=collections.deque(maxlen=20)
        encoding='utf-16le' if width==2 else 'utf-32le'
        uc.mem_write(0x6000000,(fmt+'\0').encode(encoding));uc.mem_write(0x6010000,b''.join(struct.pack('<I',v&0xffffffff) for v in args)+b'\0'*64)
        uc.reg_write(UC_ARM_REG_SP,0x40f0000);uc.reg_write(UC_ARM_REG_LR,0x5000100)
        uc.reg_write(UC_ARM_REG_R0,0x5000000);uc.reg_write(UC_ARM_REG_R1,0x12345678)
        uc.reg_write(UC_ARM_REG_R2,0x6000000);uc.reg_write(UC_ARM_REG_R3,0x6010000)
        def hook(uc,address,size,user):
            tail.append(f'{address:08x}')
            if address==0x5000100:uc.emu_stop();return
            if address==0x5000000:
                ptr=uc.reg_read(UC_ARM_REG_R0);length=uc.reg_read(UC_ARM_REG_R1);stage=uc.reg_read(UC_ARM_REG_R3)
                text=bytes(uc.mem_read(ptr,length*width)).decode(encoding) if ptr and length else ''
                accepted=not (force_failure and stage==1)
                events.append({'stage':stage,'text':text,'length':length,'context':uc.reg_read(UC_ARM_REG_R2),'accepted':accepted})
                uc.reg_write(UC_ARM_REG_R0,length if accepted else 0xffffffff);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
            if address in imports:
                name=imports[address]
                if name in ('memcpy','memmove'):
                    dst=uc.reg_read(UC_ARM_REG_R0);src=uc.reg_read(UC_ARM_REG_R1);size=uc.reg_read(UC_ARM_REG_R2)
                    uc.mem_write(dst,bytes(uc.mem_read(src,size)));uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
                if name=='memset':
                    dst=uc.reg_read(UC_ARM_REG_R0);value=uc.reg_read(UC_ARM_REG_R1);size=uc.reg_read(UC_ARM_REG_R2)
                    uc.mem_write(dst,bytes([value&255])*size);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
                error.append('Unsupported imported function: '+name);uc.emu_stop()
        uc.hook_add(UC_HOOK_CODE,hook)
        try:uc.emu_start(entry,0,count=200000)
        except (UcError,UnicodeError) as e:error.append(str(e))
        output=''.join(e['text'] for e in events if e['accepted'])
        retval=uc.reg_read(UC_ARM_REG_R0);expected_return=0xffffffff if force_failure else len(expected.encode(encoding))//width
        passed=not error and uc.reg_read(UC_ARM_REG_PC)==0x5000100 and output==expected and retval==expected_return
        format_results.append({'address':f'{entry:08x}','candidate_character_width':width,'format':fmt,'arguments':args,'expected':expected,
                               'output':output,'return_value':retval,'expected_return_value':expected_return,'force_callback_failure':force_failure,
                               'events':events,'passed':passed,'errors':error,'last_addresses':list(tail) if not passed else []})
result={'emulator':'Unicorn 2.1.4','scope':'Original native code in a bounded CPU emulator; not a game or device runtime test',
        'helper_cases_verified':len(helper_results),'helper_cases':helper_results,'format_cases':format_results}
(base/'logs/round6_emulation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Helper cases verified:',len(helper_results))
for r in format_results:print(r['address'],r['format'],'passed='+str(r['passed']),'output='+repr(r['output']),r['errors'])
