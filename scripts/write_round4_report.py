from pathlib import Path
import json,csv,re,sys,struct
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round4';model=root/'model';r3=base/'native_analysis/core_round3'
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f:
    e=ELFFile(f);segments=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
    text_regions=[(s['sh_addr'],s['sh_addr']+s['sh_size']) for s in e.iter_sections() if s['sh_flags']&2 and not s['sh_flags']&5]
def string_at(gh):
    va=gh-0x10000
    if not any(lo<=va<hi for lo,hi in text_regions):return None
    for seg in segments:
        if seg['p_vaddr']<=va<seg['p_vaddr']+seg['p_filesz']:
            off=seg['p_offset']+va-seg['p_vaddr'];end=blob.find(b'\0',off,min(off+256,len(blob)))
            if end<0:return None
            value=blob[off:end]
            if not 2<=len(value)<=180 or any(c<32 or c>126 for c in value):return None
            return value.decode('ascii')
    return None
catalog={r['address']:r for r in json.loads((model/'function_catalog.json').read_text())}
classes=json.loads((model/'classes.json').read_text());summary=json.loads((model/'round4_summary.json').read_text())
methods=json.loads((model/'reflected_methods.json').read_text())
names={r['address']:r['name'] for r in csv.DictReader((root/'methods/functions.csv').open(encoding='utf-8-sig'))}
method_addresses={r['address'] for r in methods}
views=root/'readable';views.mkdir(exist_ok=True);annotated_strings=0
for address,row in catalog.items():
    if row.get('source_kind')=='round3_baseline' and address not in method_addresses:
        continue
    code=(base/row['source']).read_text(encoding='utf-8')
    def rename(m):
        n=names.get(m[1])
        return n if n and n.startswith(('Reflected_','Recovered_')) else 'FUN_'+m[1]
    code=re.sub(r'\b(?:func_0x|FUN_|Candidate_|Recovered_[A-Za-z0-9_]+_)([0-9a-f]{8})\b',rename,code)
    def annotate(m):
        global annotated_strings
        value=string_at(int(m[1],16))
        if value is None:return m[0]
        annotated_strings+=1
        return m[0]+' /* '+json.dumps(value).replace('*/','* /')+' */'
    code=re.sub(r'&(?:UNK_|DAT_)([0-9a-f]{8})',annotate,code)
    dest=views/(address+'.c')
    scope='Experimental fresh-import boundary/type candidate. ' if row.get('experimental_boundary') else ''
    dest.write_text('/* '+scope+'Readable aliases and string comments are navigation aids; original output is preserved. */\n'+code,encoding='utf-8')
    row['readable_file']=str(dest.relative_to(base));row['current_name']=names.get(address,row.get('name','FUN_'+address))
(model/'function_catalog.json').write_text(json.dumps(list(catalog.values()),indent=2),encoding='utf-8')
def link(path,label=None):
    path=Path(path);return '['+(label or path.name)+']('+path.as_posix()+')'
def fn(address):
    row=catalog.get(address)
    return link(base/row['readable_file'],address) if row else '`'+address+'`（待核对）'
def page(name):return model/'classes'/('class_'+re.sub(r'\W','_',name)+'.md')
by_class={}
for row in methods:by_class.setdefault(row['class_name'],[]).append(row)
(model/'classes').mkdir(exist_ok=True)
for item in classes:
    lines=['# '+item['name'],'','部分结构来自反射登记和代码指针；推导名称、实验边界与类型仍需人工核对。','']
    if item.get('parent'):lines.append('父类型线索：'+link(page(item['parent']),item['parent'])+'。')
    for r in item['registrations']:lines.append('登记大小 `'+r['registered_size']+'`；注册回调 '+fn(r['callback'])+'。')
    if item.get('type_callback'):lines.append('对象创建/类型回调 '+fn(item['type_callback'])+'。')
    lines+=['','## 字段','']
    if item['fields']:
        lines+=['类型为注册数据中的候选类型；偏移已核对登记大小，但未在运行中的游戏验证。','','| 字段 | 偏移 | 类型线索 |','| --- | --- | --- |']
        for field in sorted(item['fields'],key=lambda r:int(r['offset'],16)):
            typ=field.get('candidate_type_name','')
            if not typ and 'type_tag' in field:typ='tag '+str(field['type_tag'])+' / '+str(field['type_size'])+' bytes'
            lines.append('| `'+field['name']+'` | `'+field['offset']+'` | '+typ.replace('|','\\|')+' |')
    else:lines.append('本轮尚未提取字段记录。')
    reflected=by_class.get(item['name'],[])
    if reflected:
        lines+=['','## 原生反射登记的方法','',
                '名称来自注册字符串；目标来自方法描述符的直接代码指针。登记到某类型不保证它是原始 C++ 定义中的唯一所属类。','',
                '| 登记名称 | 代码入口 | 描述符 |','| --- | --- | --- |']
        for row in reflected:lines.append('| `'+row['method_name']+'` | '+fn(row['address'])+' | `'+row['descriptor_address']+'` |')
    lines+=['','## 虚函数槽位','']
    if item['vtable']:
        lines+=['表地址 `'+item['vtable_address']+'`，'+str(len(item['vtable']))+' 个槽位。','','| 槽位 | 代码入口 | 与父类型的关系 |','| ---: | --- | --- |']
        for slot in item['vtable']:
            relation={'inherited':'共用','overridden':'替换','new_slot':'新增'}.get(slot.get('relation_to_parent'),'未比对')
            lines.append('| '+str(slot['slot'])+' | '+fn(slot['address'])+' | '+relation+' |')
    else:lines.append('本轮尚未定位可验证的表。')
    page(item['name']).write_text('\n'.join(lines)+'\n',encoding='utf-8')
index=['# 第四轮类型目录','','按类型浏览字段、反射方法和虚函数槽位。','','| 类型 | 字段 | 反射方法 | 虚表槽位 |','| --- | ---: | ---: | ---: |']
for item in sorted(classes,key=lambda r:r['name'].lower()):index.append('| '+link(page(item['name']),item['name'])+' | '+str(len(item['fields']))+' | '+str(len(by_class.get(item['name'],[])))+' | '+str(len(item['vtable']))+' |')
(model/'类型目录.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
methodlines=['# 反射方法对应表','','根据反射登记槽 0x34、方法描述符 +4 的代码指针和 +8 的非虚调用标志提取。不能仅据此恢复所有参数、原始 C++ 声明或唯一所属类。','','| 类型 | 登记方法 | 代码 |','| --- | --- | --- |']
for row in sorted(methods,key=lambda r:(r['class_name'],r['method_name'])):methodlines.append('| '+row['class_name']+' | `'+row['method_name']+'` | '+fn(row['address'])+' |')
(model/'反射方法目录.md').write_text('\n'.join(methodlines)+'\n',encoding='utf-8')
hp=next(r for r in methods if r['class_name']=='Zombie' and r['method_name']=='GetHitpoints')
proof=['# Zombie.GetHitpoints 的证据','',
       '反射登记名为 `GetHitpoints`，其方法描述符为 `'+hp['descriptor_address']+'`。描述符的代码指针指向 '+fn(hp['address'])+'，非虚成员标志为 `'+str(hp['member_flags'])+'`。',
       '登记附近的类型字符串为 `'+', '.join(hp.get('nearby_type_strings',[]))+'`。Zombie 字段登记还把 `m_hitpoints` 置于 `0x138`，类型标记为 8、宽度为 4 字节。','',
       '该入口的 ARM 指令如下：','','```asm',*hp['getter_evidence'],'```','',
       '代码把对象偏移 `0x138` 的 32 位内容载入返回寄存器。结合反射中的 `float` 类型与字段登记，可以将其理解为读取 `m_hitpoints`；这是静态证据复原，尚未通过游戏运行验证。','',
       '同一字段表中还有 `m_maxHitpoints`（`0x13c`）和 `m_damageScale`（`0x140`）。详见 '+link(page('Zombie'),'Zombie 结构记录')+'。','']
(model/'Zombie_GetHitpoints_证据.md').write_text('\n'.join(proof),encoding='utf-8')
baseline_bad=set()
baseline_bad={Path(s).stem for s in (base/'logs/round3_truncated_paths.txt').read_text(encoding='utf-8-sig').splitlines() if s.strip()}
current_bad={a for a in baseline_bad if a in catalog and catalog[a].get('source_kind')=='round3_baseline'}
for a,row in catalog.items():
    if row.get('source_kind')!='round3_baseline' and row.get('control_flow_truncated',False):current_bad.add(a)
summary.update(reflected_method_records=len(methods),reflected_target_addresses=len(method_addresses),
               zombie_registered_fields=len(next(x for x in classes if x['name']=='Zombie')['fields']),
               current_control_flow_truncation_records=len(current_bad),annotated_string_pointers=annotated_strings,
               class_records=len(classes))
(model/'round4_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
lines=['# 第四轮恢复结果','',
       '主库累计有 **'+format(len(catalog),',')+' 个不同地址的函数伪代码**，较第三轮新增 '+format(summary['new_unique_functions'],',')+' 个。新增目录包含 '+str(summary['selected_isolated_candidates'])+' 个从独立工程导出的实验候选，来源和旧版本均保留。','',
       '- '+link(model/'类型目录.md','类型目录：字段、方法、虚函数槽位'),
       '- '+link(page('Zombie'),'Zombie：补出的 79 个字段登记'),
       '- '+link(model/'Zombie_GetHitpoints_证据.md','GetHitpoints：登记名称、字段偏移与指令证据'),
       '- '+link(model/'反射方法目录.md','214 条反射方法对应记录'),
       '- '+link(model/'function_catalog.json','统一函数目录'),
       '- '+link(model/'source_versions.json','候选与历史来源'),
       '- '+link(model/'unselected_candidates.json','未采用的实验候选与原因'),'','## 本轮变化','',
       '| 项目 | 结果 |','| --- | ---: |',
       '| 新增不同地址的伪代码 | '+str(summary['new_unique_functions'])+' |',
       '| 原 28 个未纳入 C 输出的条目，本轮已纳入 | '+str(summary['original_no_C_now_with_C'])+' |',
       '| 原条目中仍未纳入的数量 | '+str(len(summary['original_no_C_still_without_C']))+' |',
       '| 基线虚表指针中已有 C 输出 | '+str(summary['virtual_pointer_addresses_with_C'])+' / '+str(summary['baseline_virtual_pointer_addresses'])+' |',
       '| 原生反射登记记录 | '+str(len(methods))+' |',
       '| Zombie 字段登记 | '+str(summary['zombie_registered_fields'])+' |','',
       '修正了 3 个已有反编译结果的 UTF-8 保存错误。原先 5 个大型函数现在均有 C 候选输出；其中 Zombie 的注册回调还恢复出 `m_hitpoints`、`m_maxHitpoints`、`m_damageScale` 等 79 个字段登记。','',
       '新入口由虚函数表或原生方法描述符中的代码指针支持。对落在其它函数内部的入口，另建工程试验边界，原主工程的旧函数边界保留。库的 ELF 属性标记 ARM v7，因此额外使用 ARM v7 解码设置与原 ARM v8 默认设置对照。','',
       '## 尚未解决的部分','',
       '对旧的 415 个控制流截断输出进行了独立工程对照。按函数范围、警告及截断标记的保守规则，本轮自动采用的替换数为 '+str(summary['selected_control_flow_repairs'])+'；更好看的输出也可能来自错误边界，实验文件不等于验证通过。','',
       '以下原困难条目仍未纳入主目录：'+', '.join('`'+a+'`' for a in summary['original_no_C_still_without_C'])+'。其中 `00a1580c` 有实验 C 输出，但覆盖范围与基线差异过大，留待人工核对。','',
       '目前统一目录还有 '+str(len(current_bad))+' 个带控制流截断标记的输出（包括本轮新增候选），并有类型、间接调用等未验证之处。新旧原始输出分别保存在各批次目录；这不是可直接编译的原始游戏工程。原 APK 未修改。','']
(base/'第四轮恢复结果.md').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote round4 report;',len(catalog),'function entries;',len(classes),'class pages')
