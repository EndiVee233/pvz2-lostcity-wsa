from pathlib import Path
import json,sys,struct
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'tools/python_libs'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from elftools.elf.elffile import ELFFile
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f:
    elf=ELFFile(f);segments=[dict(s.header) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    code=[(s['sh_addr']+0x10000,s['sh_addr']+0x10000+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read(address,size):
    va=address-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    raise ValueError(hex(address))
decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
helper=read(0x15eddfc,22);expected=bytes.fromhex('03b47146023189088000890008584018864603bcf746')
assert helper==expected
dispatch=read(0x150557c,4)
ins=list(decoder.disasm(dispatch,0x150557c));assert len(ins)==1 and ins[0].mnemonic=='bl' and ins[0].op_str=='#0x15eddfc'
assert read(0x150555c,2)==bytes.fromhex('4b2b') # CMP r3,#75 => 76 entries.
table=0x1505580;entries=[]
for index,offset in enumerate(struct.unpack('<76i',read(table,76*4))):
    target=(table+offset)&0xffffffff
    assert target%2==0 and any(lo<=target<hi for lo,hi in code)
    first=next(decoder.disasm(read(target,4),target),None);assert first
    entries.append({'case':index,'table_entry':f'{table+index*4:08x}','signed_offset':offset,'target':f'{target:08x}',
                    'first_instruction':first.mnemonic+' '+first.op_str,'target_bytes':read(target,4).hex()})
result={'function':'01505544','helper':'015eddfc','call_instruction':'0150557c','table_base':f'{table:08x}',
        'helper_bytes':helper.hex(),'helper_instructions':[f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in decoder.disasm(helper,0x15eddfc)],
        'entry_count':len(entries),'unique_targets':len({r['target'] for r in entries}),
        'formula':'target = align_down(LR + 2, 4) + signed32(table[index]); jump in Thumb mode',
        'entries':entries,'status':'Switch dispatch recovered; complete function pseudocode is still unresolved'}
model=base/'native_analysis/core_round5/model'
(model/'gnu_thumb_case_si_switch.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 最后一个截断点的定位','','`01505544` 的截断来自 Thumb 跳转表辅助函数，而不是本轮已经处理的异常返回路径。','',
       '已从原始 ELF 字节恢复 **76 个 case、60 个不同目标**。`0150555c` 比较输入值与 75，`0150557c` 调用辅助函数 `015eddfc`，表从 `01505580` 开始。','',
       '辅助函数实际执行“表基址加 32 位有符号偏移”，并保留调用前的 r0/r1：','','```asm',*result['helper_instructions'],'```','',
       '当前安装版本 Ghidra 的 ARM.cspec 中，`switch32_si_r0` 使用了偏移再乘 4 的表达式。这与该样本辅助函数的机器指令不匹配，需要在独立工程中进一步修正分析模型；本轮没有修改 Ghidra 安装文件或据此替换完整函数。','',
       '[完整表与指令证据]('+(model/'gnu_thumb_case_si_switch.json').as_posix()+')。表目标均落在 ELF 可执行区且能解码为 Thumb 指令，但这不等于各 case 的完整业务语义已恢复。','',
       '| case | 目标 | 首条指令 |','| ---: | --- | --- |']
for r in entries:lines.append('| '+str(r['case'])+' | `'+r['target']+'` | `'+r['first_instruction']+'` |')
(model/'最后一个截断点分析.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Switch entries:',len(entries),'unique targets:',result['unique_targets'])
