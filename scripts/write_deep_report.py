from pathlib import Path
import json,csv
base=Path(__file__).resolve().parents[1]
root=base/'native_analysis/core_deep'
summary=json.loads((root/'summary.json').read_text(encoding='utf-8'))
refs=json.loads((root/'string_references.json').read_text(encoding='utf-8'))
jni=json.loads((base/'native_analysis/libSrc/jni_java_map.json').read_text(encoding='utf-8'))
recovery=json.loads((base/'java_recovery/results.json').read_text(encoding='utf-8'))
fallback=json.loads((base/'java_recovery/fallback_results.json').read_text(encoding='utf-8'))
annotations=json.loads((root/'resolved_string_expressions.json').read_text(encoding='utf-8'))
layouts=json.loads((root/'property_offset_candidates.json').read_text(encoding='utf-8'))
files={p.name.split('_',1)[0]:p for p in (root/'annotated').glob('*.c')}
def link(path,label=None):
    path=Path(path)
    return '['+(label or path.name)+']('+path.as_posix()+')'
def function_link(address):
    return link(files[address],address) if address in files else '`'+address+'`（见函数索引）'
lines=['# 第二轮深入反编译结果','',
       '主游戏库已从最初的 7 个 JNI 函数扩展到大量函数入口索引和精选伪代码，并补出了 Java 失败方法的简化/指令输出。原始 APK 与上一轮导出文件均保留。','',
       '## 本轮结果','',
       '- 主库识别出 **'+format(summary['recognized_functions'],',')+' 个函数入口**，其中 '+format(summary['non_thunk_internal_functions'],',')+' 个为非外部、非跳板函数。这些是自动识别结果，不代表原始源码中的准确函数总数。',
       '- 本轮精选导出 **'+str(summary['exported_functions'])+' 个主库函数伪代码**；另有 '+str(summary['export_errors'])+' 个导出失败记录。',
       '- 恢复 **27 条动态 JNI 方法注册记录**，方法名均能在已导出的 PopCap Java 代码中找到对应声明；同名支付回调可能对应不同类，不能只凭方法名确定所属类。',
       '- 建立 **'+format(summary['strings_with_function_references'],',')+' 条字符串到函数的引用索引**。',
       '- 在注释版伪代码中解析了 **'+format(sum(len(x['resolved_strings']) for x in annotations),',')+' 处字符串地址表达式**，保留原始表达式并附上可读字符串。',
       '- 针对原先含 367 处失败占位的 237 个 Java 类，连同相关内部类，导出 **'+format(sum(x['exported_files'] for x in recovery),',')+' 份简化输出**。简化输出仍有 '+str(sum(x['remaining_method_stubs'] for x in recovery))+' 处占位，对应类另外导出了 '+str(sum(x['exported_files'] for x in fallback))+' 份底层指令输出，未再出现同类占位。这个统计只说明指令可查看，不意味着 Java 语义或可编译性已恢复。','',
       '## 优先查看','',
       '- '+link(root/'functions.csv','全部函数入口、ELF 地址、Ghidra 地址和大小索引'),
       '- '+link(root/'string_references.json','植物、僵尸、伤害等字符串的函数引用'),
       '- '+link(root/'summary.json','本轮函数导出清单、调用路径与错误记录'),
       '- '+link(base/'native_analysis/libSrc/jni_tables.csv','恢复的 JNI 注册表'),
       '- '+link(base/'native_analysis/libSrc/jni_java_map.json','JNI 与 Java 声明对应关系'),
       '- '+link(root/'property_offset_candidates.json','属性注册偏移候选表'),
       '- '+link(base/'java_recovery/results.json','Java 简化导出统计'),
       '- '+link(base/'java_recovery/fallback_results.json','Java 指令导出统计'),'','## 游戏主循环入口','',
       'Java 的 `AndroidSurfaceView` 调用 `Native_onDrawFrame()`。该 JNI 的 ELF 地址为 `0x132a0a0`，在本次 Ghidra 工程中为 `0133a0a0`。伪代码串接多个引擎调用、读取时间值，并根据计时结果重复调用 `FUN_01338258`，随后调用 `FUN_01337860`。这为后续定位更新与绘制逻辑提供了入口；内部函数的精确语义仍需汇编和运行证据确认。','',
       '- 每帧 JNI：'+function_link('0133a0a0'),
       '- 循环内调用：'+function_link('01338258'),
       '- 后续引擎调用：'+function_link('01337860'),
       '- 应用初始化：'+function_link('01340678'),'','## 按游戏对象定位','',
       '下面是字符串引用证据对应的函数，常见用途为类型、反射或序列化注册；不能据此直接把函数当作对象的行为实现。地址为本次 Ghidra 工程地址。','',
       '| 线索字符串 | 函数入口 |','| --- | --- |']
for keyword in ['Plant','Zombie','Board','Projectile','PlantPeashooter','PeashooterProps','PlantSunflower','LostCityStageProperties','Hitpoints','Cost','PacketCooldown','BaseDamage']:
    matches=[r for r in refs if r['text']==keyword]
    addresses=[]
    for row in matches:
        for ref in row['references']:
            if ref['function'] not in addresses:addresses.append(ref['function'])
    addresses.sort(key=lambda a:(a not in files,a))
    if addresses:lines.append('| `'+keyword+'` | '+'、'.join(function_link(a) for a in addresses[:2])+' |')
lines+=['','## 植物属性注册示例','',
        '函数 '+function_link('00515428')+' 中，可以从字符串构造和紧随其后的注册调用读出以下属性及偏移候选。它们用于辅助恢复类布局，尚未验证为运行时对象的完整结构。','',
        '| 属性 | 注册偏移候选 |','| --- | --- |']
for item in layouts:
    if item['function_file'].startswith('00515428') and item['property'] in ['Cost','Hitpoints','MinLevel','MaxLevel','PacketCooldown','StartingCooldown','PlantFoodDurationSeconds','PlantFoodPlayCount','GridWidth','GridHeight']:
        lines.append('| `'+item['property']+'` | `'+item['candidate_offset']+'` |')
lines+=['','## Java 补救输出','',
        '`java_recovery/simple/` 按 DEX 分目录存放含显式跳转的简化输出；`java_recovery/fallback/` 为仍有困难的类提供更底层的指令输出。相关内部类单独导出，阅读时需要同时查找同名前缀的文件。这些输出用于与原 Java/Smali 交叉检查，保留了无法恢复的控制流，不是可直接编译的 Java 工程。','',
        '单独增加线程栈大小的 RTON 重试仍遇到工具内部的区域结构限制，日志保留在 `logs/java_recovery_rton.log`。主 Java 导出目录没有被这些实验覆盖。','',
        '另外在 `assets/ltayx.mn.ltplugin_v2000.pl` 内找到一个额外 DEX，解出 '+str(len(list((base/'embedded_code/ltayx_java').rglob('*.java'))))+' 份 Java 文件，位于 `embedded_code/ltayx_java/`，工具仍报告 2 项错误。它属于支付插件，不是主游戏逻辑。其他内嵌 SDK JAR 中仍有无法按 ZIP/DEX 直接读取的数据，见 `native_analysis/embedded_archives.json`。','',
        '## 验证与边界','',
        '- 本轮主库自动分析运行 300 秒后达到时限，已保留分析出的入口、引用及导出结果，不能称为全库分析完成。',
        '- 自动分析与反编译出现部分无效指令、控制流和类型恢复警告，详见 `logs/ghidra_deep.log`。有些函数可能包含错误边界、不可达代码或未解析调用。',
        '- 原始伪代码在 `native_analysis/core_deep/functions/`；字符串注释版在 `native_analysis/core_deep/annotated/`。注释解析基于文件内 PC 相对常量表达式，未改写指令或原始 C 语句。',
        '- `property_offset_candidates.json` 是启发式结果：同名字段可能出现多个偏移，也可能误配，不能直接用于修改内存。',
        '- 本次 Ghidra 基址为 `0x10000`，工程地址通常比 ELF 原始地址高 `0x10000`；Thumb 地址最低位另作模式标记。',
        '- Ghidra 工程仍为 `native_analysis/ghidra_project/pvz2_lostcity.gpr`，可以从现在的识别结果继续分析。',
        '- 未完成所有约 5 万个函数的伪代码导出，也未恢复原始 C++ 工程、验证重新编译或游戏运行。','']
(base/'深入分析结果.md').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote 深入分析结果.md')
