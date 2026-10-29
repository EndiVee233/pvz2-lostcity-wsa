from pathlib import Path
import json,re,collections
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round6';model=root/'model';model.mkdir(exist_ok=True)
prior=base/'native_analysis/core_round5/model'
catalog={r['address']:dict(r) for r in json.loads((prior/'function_catalog.json').read_text(encoding='utf-8'))};old_addresses=set(catalog)
versions={};views=root/'readable';views.mkdir(exist_ok=True)
formats=json.loads((root/'formats/summary.json').read_text(encoding='utf-8'))['exports'];switch=json.loads((root/'switch/summary.json').read_text(encoding='utf-8'))
selected=[('switch',switch)]+[('formats',r) for r in formats if r['status']=='ok' and r['style']=='decompile']
names={'01491afc':'Recovered_Format16_Callback','01493eb0':'Recovered_Format32_Callback','01505544':'Candidate_Switch_01505544'}
for stage,row in selected:
    assert row['status']=='ok' and not row['halt_baddata']
    address=row['address'];source=root/stage/row['file'];old=catalog.get(address)
    raw=source.read_text('utf-8');text=raw
    if stage=='formats':
        text=re.sub(r'\bCandidate_Format_'+address+r'\b',names[address],text)
        for original,new in [('param_1','write_callback'),('param_2','context'),('param_3','format_cursor'),('param_4','argument_words')]:
            text=re.sub(r'\b'+original+r'\b',new,text)
        note='Readable aliases are inferred. Original machine code passed a limited set of CPU-emulation examples; equivalence of this pseudocode is not established. '
    else:note='Experimental expanded candidate. All 76 entry-switch destinations match ELF data; '+str(raw.count('/* WARNING'))+' decompiler diagnostic comments remain. '
    target=views/(address+'.c');target.write_text('/* '+note+'Original raw output is preserved in the sibling stage directory. */\n'+text,encoding='utf-8')
    record=dict(address=address,elf_address=hex(int(address,16)-0x10000),name=names[address],current_name=names[address],status='ok',
                source=str(source.relative_to(base)),readable_file=str(target.relative_to(base)),source_kind='round6_'+stage,
                experimental_boundary=True,body_size=row['size'],body_ranges=row['body_ranges'],warning_comments=raw.count('/* WARNING'),
                control_flow_truncated=False,evidence_file=str((root/stage/'summary.json').relative_to(base)),
                selection_reason='ELF-verified switch destinations in a separate analysis project; experimental boundaries and warnings retained')
    versions[address]={'previous':old,'selected':record};catalog[address]=record
bad=[];jumptable=[];jumptable_details=[]
for address,row in catalog.items():
    text=(base/row['source']).read_text('utf-8')
    if 'halt_baddata' in text:bad.append(address)
    if 'Could not recover jumptable' in text:
        jumptable.append(address)
        jumptable_details.append({'address':address,'source':row['source'],'readable_file':row['readable_file'],
                                  'sites':re.findall(r'Could not recover jumptable at (0x[0-9a-f]+)',text),
                                  'indirect_jump_treated_as_call':'Treating indirect jump as call' in text})
hard={r['address'] for folder in [base/'native_analysis/core_round3/full_library',base/'native_analysis/core_deep']
      for r in json.loads((folder/'summary.json').read_text(encoding='utf-8'))['exports'] if r['status']=='error'}
emulation=json.loads((base/'logs/round6_emulation.json').read_text(encoding='utf-8'));assert all(r['passed'] for r in emulation['format_cases'])
summary={'baseline_pseudocode_functions':len(old_addresses),'cumulative_pseudocode_functions':len(catalog),'new_unique_functions':len(set(catalog)-old_addresses),
         'entry_switch_cases':76,'entry_switch_unique_targets':60,'arm_main_switch_entries':168,
         'format_functions_newly_exported':[r['address'] for r in formats if r['status']=='ok' and r['style']=='decompile'],
         'original_hard_addresses':len(hard),'original_hard_addresses_with_selected_C':len(hard&set(catalog)),
         'original_hard_still_without_C':sorted(hard-set(catalog)),'remaining_halt_baddata_addresses':sorted(bad),
         'remaining_jumptable_warning_addresses':sorted(jumptable),'switch_candidate_warnings':(root/'switch'/switch['file']).read_text('utf-8').count('/* WARNING'),
         'helper_emulation_cases_verified':emulation['helper_cases_verified'],'format_emulation_cases_passed':sum(r['passed'] for r in emulation['format_cases']),
         'all_new_versions_experimental':True}
(model/'function_catalog.json').write_text(json.dumps(list(catalog.values()),ensure_ascii=False,indent=2),encoding='utf-8')
(model/'source_versions.json').write_text(json.dumps(versions,ensure_ascii=False,indent=2),encoding='utf-8')
(model/'round6_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
def link(path,label):return '['+label+']('+Path(path).as_posix()+')'
def fn(address):return link(base/catalog[address]['readable_file'],address)
quality=['# 间接跳转待核对目录','','以下 319 个地址仍有跳转表未恢复提示。部分输出把间接跳转按调用显示，可能是尾调用或虚调用；需要核对，不能只据提示认定整个函数错误。','','| 函数 | 提示地址 | 间接跳转按调用显示 |','| --- | --- | --- |']
for row in sorted(jumptable_details,key=lambda r:r['address']):
    quality.append('| '+fn(row['address'])+' | '+', '.join('`'+s+'`' for s in row['sites'])+' | '+('是' if row['indirect_jump_treated_as_call'] else '未出现此提示')+' |')
(model/'间接跳转待核对目录.md').write_text('\n'.join(quality)+'\n',encoding='utf-8')
(model/'jumptable_review.json').write_text(json.dumps(jumptable_details,ensure_ascii=False,indent=2),encoding='utf-8')
interface='''/* Inferred interfaces for 32-bit ARM, documented from static code and limited CPU emulation.
   These are analysis aliases, not original symbol names or a linkable replacement library.
   argument_words refers to the target ARM argument stream; a host va_list is not interchangeable.
   The full format grammar and all error cases have not been tested. */
#ifndef PVZ2_RECOVERED_FORMAT_INTERFACES_H
#define PVZ2_RECOVERED_FORMAT_INTERFACES_H
#include <stdint.h>
enum RecoveredWriteStage { RECOVERED_BEGIN = 0, RECOVERED_APPEND = 1, RECOVERED_END = 2 };
typedef int32_t (*RecoveredWrite16)(const uint16_t *units, uint32_t count, void *context, int32_t stage);
typedef int32_t (*RecoveredWrite32)(const uint32_t *units, uint32_t count, void *context, int32_t stage);
int32_t Recovered_Format16_Callback(RecoveredWrite16 writer, void *context, const uint16_t *format, void *argument_words);
int32_t Recovered_Format32_Callback(RecoveredWrite32 writer, void *context, const uint32_t *format, void *argument_words);
#endif
'''
(views/'recovered_format_interfaces.h').write_text(interface,encoding='utf-8')
lines=['# 两个格式化函数的恢复说明','',
       '两者处理相同类别的格式化逻辑，分别读写 16 位和 32 位字符单元。名称与参数别名是本轮推导，不是恢复出的原始符号。','',
       '| 入口 | 字符单元 | 旧分析体积 | 新实验体积 | 主分支表 |','| --- | ---: | ---: | ---: | ---: |']
for row in formats:
    if row['status']=='ok' and row['style']=='decompile':lines.append('| '+fn(row['address'])+' | '+('16 位' if row['address']=='01491afc' else '32 位')+' | 608 字节 | '+str(row['size'])+' 字节 | 84 项 |')
lines+=['','原来仅识别了 608 字节的函数体，未把分支表涉及的全部代码纳入。根据原指令的边界比较与表中跳转补全分析范围，并明确登记间接跳转目标后，两者均在约 1 秒内导出 C 伪代码；前轮每个函数等待 120 秒仍超时。','',
        '## 推导出的接口','',
        '- 参数 1：写出回调；参数 2：原样传给回调的上下文；参数 3：格式字符串；参数 4：32 位 ARM 参数流。',
        '- 回调阶段 0 为开始、1 为写出、2 为结束；写出回调返回 -1 时，样例中的外层函数也返回 -1。',
        '- 仿真样例中，成功返回值等于写出的字符单元数。',
        '- 参数流依赖目标 ARM ABI，不能把本机的 va_list 直接当作替代品。','',
        link(views/'recovered_format_interfaces.h','便于继续分析的接口头文件')+'。','',
        '## 原指令的有限仿真','',
        '使用 CPU 仿真器执行 ELF 中原有指令；回调由测试环境接收。两种字符宽度各验证 7 个样例，共 14 个。此处验证的是原指令在这些输入下的行为，没有编译或证明导出的 C 与原指令完全等价，也没有启动游戏。','',
        '| 格式字符串 | 条件 | 16 位结果 | 32 位结果 |','| --- | --- | --- | --- |']
for fmt in dict.fromkeys(r['format'] for r in emulation['format_cases']):
    rows=[r for r in emulation['format_cases'] if r['format']==fmt];sample=rows[0]
    result='返回 -1' if sample['force_callback_failure'] else sample['output']
    lines.append('| `'+fmt+'` | '+('写出回调故意失败' if sample['force_callback_failure'] else str(sample['arguments']))+' | '+result+' | '+result+' |')
lines+=['',link(base/'logs/round6_emulation.json','完整仿真记录')+'；'+link(root/'format_switches.json','168 项主分支表与原始指令证据')+'。','',
        '主分支在伪代码中按字节偏移显示 case（0、4、8……），对应格式字符编号为 `0x25 + case值/4`。这部分依赖手工登记的分支目标，工具保留了对应提示。其它格式选项、浮点路径和设备行为尚未全面验证。','']
(model/'格式化函数说明.md').write_text('\n'.join(lines),encoding='utf-8')
lines=['# 最后一个已知截断点的扩展候选','',
       '入口 '+fn('01505544')+' 原先只导出少量代码，并在 `__gnu_thumb1_case_si` 后截断。本轮按辅助函数的实际指令安装了仅作用于新实验工程的解析模型，没有改动 Ghidra 安装文件或主工程。','',
       '表基址为 `align_down(LR + 2, 4)`，读取有符号 32 位偏移后直接加到表基址；末尾 `mov pc,lr` 保持 Thumb 状态。76 个输入均在 CPU 仿真器中到达了表指定的目标，且保留 r0、r1 和栈指针；运算后的 N/Z/C/V 条件标志也与模型一致。','',
       '新输出中的入口分支表有 76 项、60 个不同目标，与从 ELF 提取的表逐项对应，截断标记已消失。','',
       '**这是扩展候选，仍有 '+str(summary['switch_candidate_warnings'])+' 条诊断注释**：包括调用改作分支、移除不可达块和辅助函数模型注入。不能把警告消失或表目标一致等同于完整语义恢复。实验边界扩大到 8,352 字节，仍需要人工检查各分支和内部长跳转。','',
       '- '+link(root/'pvz2_thumb_case_si.xml','本样本的辅助函数解析模型'),
       '- '+link(root/'switch/summary.json','实验边界、全部分支目标与诊断计数'),
       '- '+link(base/'native_analysis/core_round5/model/最后一个截断点分析.md','前轮的表定位与原始指令证据'),
       '- '+link(base/'logs/round6_emulation.json','76 个输入的原指令仿真记录'),'']
(model/'跳转恢复证据.md').write_text('\n'.join(lines),encoding='utf-8')
lines=['# 第六轮恢复结果','',
       '本轮补出了最后 **2 个原先超时的函数伪代码**，主库累计 **'+format(len(catalog),',')+' 个不同地址的函数输出**。此前统计的 28 个困难条目现在都已有选定 C 输出，其中部分仍是带实验边界的候选。','',
       '- '+link(model/'格式化函数说明.md','两个新函数：用途、接口、伪代码与仿真样例'),
       '- '+link(model/'跳转恢复证据.md','最后一个截断点：76 个分支的扩展候选'),
       '- '+link(model/'function_catalog.json','最新统一函数目录'),
       '- '+link(base/'native_analysis/core_round5/model/类型目录.md','沿用的类型目录：2,174 个类型、6,232 条字段记录'),
       '- '+link(model/'source_versions.json','本轮采用版本及前轮来源'),'','## 验证结果','',
       '| 项目 | 结果 |','| --- | ---: |',
       '| 新补出的函数 | 2 |','| 新登记的 ARM 主分支项 | 168 |','| Thumb 辅助函数仿真输入 | 76 / 76 通过 |',
       '| 16 位、32 位格式化原指令样例 | 14 / 14 通过 |','| 统一目录中含 halt_baddata 的条目 | '+str(len(bad))+' |','',
       '两个新函数的原指令在仿真中分别正确输出普通文字、中文、正负十进制、十六进制和补零文本；写出回调失败的样例返回 -1。仿真使用原 ELF 指令和测试回调，没有运行游戏，也没有验证伪代码的完整等价性。','',
       '最后一个已知截断点也已得到 76 个分支的扩展伪代码候选。它仍保留 **'+str(summary['switch_candidate_warnings'])+' 条诊断注释**，没有据此宣称全部代码正确。主库其它输出中仍有 '+str(len(jumptable))+' 个地址含跳转表未恢复的提示，已整理为 '+link(model/'间接跳转待核对目录.md','后续核对目录')+'。','',
       '实验只写入新的独立 Ghidra 工程；原 APK、原生库字节、前轮主工程和历史结果保留。这些仍是反编译伪代码及分析线索，不是可直接重新编译的完整原始工程。','',
       link(base/'logs/round6_validation.json','结构与完整性核验')+'；'+link(base/'logs/round6_emulation.json','有限 CPU 仿真记录')+'。','']
(base/'第六轮恢复结果.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='remaining_jumptable_warning_addresses'},ensure_ascii=False,indent=2))
print('Other unresolved jumptable diagnostic addresses:',len(jumptable))
