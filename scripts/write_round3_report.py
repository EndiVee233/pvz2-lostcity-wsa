from pathlib import Path
import json,csv,re,collections
base=Path(__file__).resolve().parents[1]
root=base/'native_analysis/core_round3';model=root/'model'
classes=json.loads((model/'classes.json').read_text())
catalog={r['address']:r for r in json.loads((model/'function_catalog.json').read_text())}
summary=json.loads((model/'summary.json').read_text())
indexes=[root/'functions.csv',root/'expand/functions.csv',root/'virtual_methods/functions.csv',root/'virtual_methods_extra/functions.csv',root/'constructors/functions.csv',root/'virtual_methods_final/functions.csv',root/'full_library/functions.csv']
last=next(p for p in reversed(indexes) if p.exists())
function_rows=list(csv.DictReader(last.open(encoding='utf-8-sig')))
names={r['address']:r['name'] for r in function_rows}
containing={}
for folder in ['virtual_methods','virtual_methods_extra','virtual_methods_final']:
    path=root/folder/'summary.json'
    if not path.exists():continue
    for record in json.loads(path.read_text())['exports']:
        match=re.search(r'inside existing function ([0-9a-f]{8})',record.get('error',''))
        if match:containing[record['address']]=match[1]
ir_catalog={}
for folder in [root/'expand',root/'full_library']:
    path=folder/'ir_results.json'
    if not path.exists():continue
    for record in json.loads(path.read_text()):
        if record['status']=='ok':ir_catalog[record['address']]=dict(record,source=str((folder/record['file']).relative_to(base)))
(model/'ir_catalog.json').write_text(json.dumps(list(ir_catalog.values()),indent=2),encoding='utf-8')
readable=root/'readable';readable.mkdir(exist_ok=True)
warning_outputs=0;truncated_control_flow_outputs=0;truncated_functions=[]
for address,row in catalog.items():
    src=base/row['source']
    alternate=src.parent.parent/'annotated'/src.name
    if src.parent.parent.name=='core_deep' and alternate.exists():src=alternate
    code=src.read_text(encoding='utf-8',errors='replace')
    warning_outputs+=('/* WARNING:' in code)
    truncated_control_flow_outputs+=('halt_baddata' in code)
    if 'halt_baddata' in code:truncated_functions.append(address)
    def replace_name(match):
        name=names.get(match[1]);return name if name and name.startswith('Recovered_') else match[0]
    code=re.sub(r'\b(?:FUN_|Recovered_[A-Za-z0-9_]+_)([0-9a-f]{8})\b',replace_name,code)
    dest=readable/(address+'.c')
    dest.write_text('/* Navigation view: recovered role/slot aliases are inferred; original source and method names are not restored. */\n'+code,encoding='utf-8')
    row['readable_file']=str(dest.relative_to(base));row['current_name']=names.get(address,row.get('name'))
(model/'function_catalog.json').write_text(json.dumps(list(catalog.values()),indent=2),encoding='utf-8')
def link(path,label=None):
    path=Path(path);return '['+(label or path.name)+']('+path.as_posix()+')'
def fn(address):
    row=catalog.get(address)
    if row:return link(base/row['readable_file'],address)
    if address in ir_catalog:return link(base/ir_catalog[address]['source'],address+'（p-code）')
    owner=catalog.get(containing.get(address))
    if owner:return link(base/owner['readable_file'],address+'（函数内部入口）')
    owner_ir=ir_catalog.get(containing.get(address))
    if owner_ir:return link(base/owner_ir['source'],address+'（内部入口 p-code）')
    if address not in names:return '`'+address+'`（尚未识别为独立函数）'
    return '`'+address+'`（未生成 C；见函数索引）'
def classfile(name):return model/'classes'/('class_'+re.sub(r'\W','_',name)+'.md')
review=['# 控制流待核对函数','','这些输出带有 halt_baddata 标记，表示部分控制流未恢复；点击地址查看对应伪代码。','']
review+=['- '+fn(a) for a in sorted(truncated_functions)]
(model/'控制流待核对.md').write_text('\n'.join(review)+'\n',encoding='utf-8')
(model/'classes').mkdir(exist_ok=True)
lookup={x['name']:x for x in classes}
for item in classes:
    lines=['# '+item['name'],'','这是从类型注册、对象分配和函数表提取的分析记录，包含推导信息，尚未恢复完整 C++ 类定义。','']
    if item.get('parent'):lines.append('父类型线索：'+link(classfile(item['parent']),item['parent'])+'。')
    elif item.get('parent_getter'):lines.append('父类型元数据入口：'+fn(item['parent_getter'])+'，名称暂未对应。')
    if item.get('metadata_getter'):lines.append('类型元数据：'+fn(item['metadata_getter'])+'。')
    if item.get('type_callback'):lines.append('类型回调：'+fn(item['type_callback'])+'。')
    if item.get('constructor_candidate'):lines.append('构造辅助函数候选：'+fn(item['constructor_candidate'])+'。')
    for registration in item['registrations']:
        lines.append('登记大小：`'+registration['registered_size']+'`；登记函数 '+fn(registration['registration_function'])+'；字段/类型注册回调 '+fn(registration['callback'])+'。')
    if item.get('allocation_size'):lines.append('工厂分配大小：`'+item['allocation_size']+'`。')
    lines+=['','## 字段注册记录','']
    if item['fields']:
        lines+=['偏移来自反射注册调用，类型列为邻近类型字符串候选；尚未验证运行时布局。','','| 字段 | 偏移 | 类型候选 |','| --- | --- | --- |']
        for field in sorted(item['fields'],key=lambda r:int(r['offset'],16)):
            type_name=field.get('candidate_type_name','')
            if not type_name and 'type_tag' in field:type_name='tag '+str(field['type_tag'])+' / '+str(field['type_size'])+' bytes'
            lines.append('| `'+field['name']+'` | `'+field['offset']+'` | '+type_name.replace('|','\\|')+' |')
    else:lines.append('本轮未提取到可解析的字段注册记录。')
    lines+=['','## 虚函数槽位','']
    if item['vtable']:
        lines.append('表地址：`'+item['vtable_address']+'`；'+str(len(item['vtable']))+' 个连续代码指针；表前两字均为零，指针均落在 ELF 可执行代码节。')
        if item.get('vtable_walk_capped'):lines.append('扫描达到上限，当前表可能不完整。')
        lines+=['','槽位反映函数指针关联，原始方法名称尚未恢复。关系列由与父类型同一槽位的指针比较得出。','','| 槽位 | 表内偏移 | 函数 | 与父类型的关系 |','| ---: | --- | --- | --- |']
        for slot in item['vtable']:
            relation={'inherited':'共用','overridden':'替换','new_slot':'新增'}.get(slot.get('relation_to_parent'),'未比对')
            lines.append('| '+str(slot['slot'])+' | `'+slot['vtable_byte_offset']+'` | '+fn(slot['address'])+' | '+relation+' |')
    else:lines.append('本轮尚未定位到可验证的虚函数表。')
    classfile(item['name']).write_text('\n'.join(lines)+'\n',encoding='utf-8')

index=['# 类型目录','','按名称浏览本轮的类型注册、字段和虚函数槽位记录。条目是从二进制证据提取的部分结构。','','| 类型 | 父类型线索 | 字段记录 | 虚函数槽位 |','| --- | --- | ---: | ---: |']
for item in sorted(classes,key=lambda x:x['name'].lower()):
    index.append('| '+link(classfile(item['name']),item['name'])+' | '+(item.get('parent') or '')+' | '+str(len(item['fields']))+' | '+str(len(item['vtable']))+' |')
(model/'类型目录.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
virtuals=json.loads((model/'virtual_methods.json').read_text())
covered_virtuals=sum(a in catalog for a in virtuals)
ir=json.loads((root/'expand/ir_results.json').read_text())
named=sum(r['name'].startswith('Recovered_') for r in function_rows)
summary.update(recognized_function_entries=len(function_rows),named_with_recovered_role_aliases=named,
               cumulative_unique_pseudocode_functions=len(catalog),new_unique_since_round2=len(catalog)-1005,
               virtual_method_addresses_with_pseudocode=covered_virtuals,large_functions_with_ir=sum(r['status']=='ok' for r in ir))
summary.update(c_outputs_with_warning_comments=warning_outputs,c_outputs_with_halt_baddata=truncated_control_flow_outputs)
(model/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
main=['# 第三轮恢复结果','',
      '主库已累计导出 **'+format(len(catalog),',')+' 个不同地址的函数伪代码**，上一轮为 1,005 个。本轮新增 '+format(len(catalog)-1005,',')+' 个。文件按函数地址去重，未把重复导出和纯指令中间表示计为新的 C 函数。','',
      '## 直接查看','',
      '- '+link(model/'类型目录.md','类型目录：按类名浏览字段、继承和虚函数槽位'),
      '- '+link(classfile('PlantPeashooter'),'豌豆射手 PlantPeashooter'),
      '- '+link(classfile('PlantSunflower'),'向日葵 PlantSunflower'),
      '- '+link(classfile('Plant'),'Plant 基础类型'),
      '- '+link(classfile('Zombie'),'Zombie 基础类型'),
      '- '+link(classfile('Board'),'Board 战场类型'),
      '- '+link(model/'function_catalog.json','统一函数目录：地址、当前名称、原始输出和可读视图路径'),
      '- '+link(model/'ir_catalog.json','未生成 C 的函数中间表示目录'),
      '- '+link(last,'最新 Ghidra 函数入口索引'),'','## 本轮提取的结构','',
      '| 内容 | 数量 |','| --- | ---: |',
      '| 索引中的函数入口 | '+format(len(function_rows),',')+' |',
      '| 可读伪代码中的不同函数地址 | '+format(len(catalog),',')+' |',
      '| 使用 Recovered 前缀角色名称的函数 | '+format(named,',')+' |',
      '| 类型条目 | '+str(len(classes))+' |',
      '| 已对应父类型的关系 | '+str(summary['parent_links'])+' |',
      '| 含字段注册记录的类型 | '+str(summary['classes_with_registered_fields'])+' |',
      '| 字段偏移记录 | '+format(summary['field_offset_records'],',')+' |',
      '| 已提取虚函数表的类型 | '+str(summary['classes_with_factory_and_vtable'])+' |',
      '| 虚表中不同的函数地址 | '+format(len(virtuals),',')+' |',
      '| 其中已有伪代码的函数地址 | '+format(covered_virtuals,',')+' |','',
      '类型条目来自注册字符串和元数据入口，不等同于完整恢复的 C++ 类。`Recovered_Registry_*`、`Recovered_TypeMetadata_*`、`Recovered_TypeCallback_*`、`Recovered_CtorCandidate_*` 和 `Recovered_VSlot_*` 是带地址的分析代称。槽位函数可能被多个类型共用，代称不代表已恢复原始方法名或唯一所属类。','',
      '虚函数表由创建对象时写入的表指针，或创建流程中单个辅助调用里的表指针推导；逐项检查指针落在 ELF 可执行代码节。字段只收录反射字段登记槽 `0x2c` 中可解析的名字和偏移，遇到无法解析的新字符串写入时会丢弃旧名称，减少误配。','',
      '## 具体进展','']
fullpath=root/'full_library/summary.json'
if fullpath.exists():
    full=json.loads(fullpath.read_text())
    main+=['','已对其余 '+format(full['targets'],',')+' 个已识别的非外部、非跳板函数完成全量导出尝试：'+format(full['exported_functions'],',')+' 个生成 C 伪代码，'+str(full['errors'])+' 个未生成 C；其中 '+str(full['fallback_ir_successes'])+' 个另有中间表示。详见 '+link(fullpath,'全量尝试记录')+'。','']
    if truncated_control_flow_outputs:
        main+=['其中 '+format(truncated_control_flow_outputs,',')+' 个 C 输出带有 `halt_baddata` 控制流截断标记。这些是可供定位的部分伪代码，不能按完整函数实现使用。'+link(model/'控制流待核对.md','逐函数清单')+'。','']
auxpath=base/'native_analysis/auxiliary/summary.json'
aux_lines=[]
if auxpath.exists():
    auxiliary=json.loads(auxpath.read_text())
    aux_lines+=['','## 其它原生库','',
           'APK 的 `lib/armeabi/` 下另有 6 个库，本轮均进行了自动分析和已识别函数的导出尝试；首轮的 Hook 库保留在 `native_analysis/pseudocode/libHookPVZ2.so.c`。下表数量含运行库和依赖库函数，自动生成的伪代码仍可能有控制流警告。','',
           '| 库 | 已识别非跳板函数 | C 伪代码 | 未生成 C |','| --- | ---: | ---: | ---: |']
    for row in auxiliary['libraries']:
        aux_lines.append('| '+link(base/row['directory']/'summary.json',row['library'])+' | '+str(row['recognized_non_thunk_functions'])+' | '+str(row['exported_functions'])+' | '+str(row['errors'])+' |')
for name in ['PlantPeashooter','PlantSunflower']:
    item=lookup[name]
    main.append('- '+name+'：已关联 '+str(len(item['vtable']))+' 个槽位，其中 '+str(len(item.get('overridden_slots',[])))+' 个与父类型的同槽指针不同，'+str(item.get('inherited_slot_count',0))+' 个共用。'+('另有 '+str(sum(s.get('relation_to_parent')=='new_slot' for s in item['vtable']))+' 个新增槽位。' if any(s.get('relation_to_parent')=='new_slot' for s in item['vtable']) else ''))
main+=['- 已把 Plant 与 Zombie 的创建流程、对象大小、类型注册回调和虚函数表对应起来。Zombie 的大型注册回调仍未生成 C 输出，字段模型因此仍有空缺。','']
main+=aux_lines
main+=['','## 5 个大型函数的中间表示','',
       '上轮的 5 个超时函数这轮均保存了 normalized high p-code。它是反编译器的中间表示，可用于追踪调用和数据流；这些输出没有计入 C 伪代码数量。','',
       '| 函数地址 | 当前名称 | P-code 操作条目 | 文件 |','| --- | --- | ---: | --- |']
for row in ir:
    if row['status']=='ok':main.append('| `'+row['address']+'` | `'+row['name']+'` | '+str(row['operations'])+' | '+link(root/'expand'/row['file'],'p-code')+' |')
main+=['','## 文件位置与限制','',
       '- `native_analysis/core_round3/readable/`：统一可读视图，函数名按当前角色标签显示；原始输出仍保存在各批次的 `functions/` 下。',
       '- `native_analysis/core_round3/model/`：类型目录、每个类型的文档、类模型、槽位关系和统一函数目录。',
       '- `native_analysis/core_round3/expand/large_function_ir/`：5 个大型函数的中间表示；`large_function_assembly/` 保留对应指令列表。',
       '- `native_analysis/ghidra_project/pvz2_lostcity.gpr`：已保存新增入口与角色标签，可继续在 Ghidra 中分析。',
       '- 批次日志位于 `logs/ghidra_round3*.log`。部分入口落在已识别函数内部，本轮记录并跳过，没有强行拆分函数边界；伪代码中仍存在类型、间接调用和控制流警告。',
       '- 本轮尚未导出整个主库的所有函数，也没有恢复原始工程、原始类/方法名称、全部类型或可直接重新编译的游戏源码。原 APK 保持不变。','']
if fullpath.exists():
    main=[line.replace('本轮尚未导出整个主库的所有函数，也没有恢复原始工程、原始类/方法名称、全部类型或可直接重新编译的游戏源码。','本轮已尝试当前已识别的非外部、非跳板函数；未识别的代码、错误的边界和未解析的间接调用仍可能存在。尚未恢复原始工程、原始类/方法名称、全部类型或可直接重新编译的游戏源码。') for line in main]
(base/'第三轮恢复结果.md').write_text('\n'.join(main),encoding='utf-8')
print('Wrote round3 report,',len(classes),'class pages,',len(catalog),'readable function views')
