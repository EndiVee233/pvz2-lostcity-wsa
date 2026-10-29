from pathlib import Path
import json,re,difflib,html
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round5';model=root/'model'
catalog={r['address']:r for r in json.loads((model/'function_catalog.json').read_text())}
classes=json.loads((model/'classes.json').read_text());summary=json.loads((model/'round5_summary.json').read_text())
methods=json.loads((model/'reflected_methods.json').read_text());repairs=json.loads((model/'control_flow_repairs.json').read_text())
def link(path,label):return '['+label+']('+Path(path).as_posix()+')'
def fn(address):
    row=catalog.get(address);return link(base/row['readable_file'],address) if row else '`'+address+'`（尚无选定 C 输出）'
def page(name):return model/'classes'/('class_'+re.sub(r'\W','_',name)+'.md')
by_class={}
for m in methods:by_class.setdefault(m['class_name'],[]).append(m)
(model/'classes').mkdir(exist_ok=True)
for item in classes:
    lines=['# '+item['name'],'','反射字段、继承关系和代码指针来自静态分析；类型和函数名线索仍需核对。','']
    if item.get('parent'):lines.append('父类型：'+link(page(item['parent']),item['parent'])+'。')
    for r in item['registrations']:lines.append('登记大小 `'+r['registered_size']+'`；注册回调 '+fn(r['callback'])+'。')
    if item.get('type_callback'):lines.append('类型/创建回调 '+fn(item['type_callback'])+'。')
    lines+=['','## 字段','','| 名称 | 偏移 | 类型线索 |','| --- | --- | --- |']
    for field in sorted(item['fields'],key=lambda r:int(r['offset'],16)):
        typ=field.get('candidate_type_name','') or ('tag '+str(field.get('type_tag','?'))+' / '+str(field.get('type_size','?'))+' bytes')
        lines.append('| `'+field['name']+'` | `'+field['offset']+'` | '+typ.replace('|','\\|')+' |')
    if by_class.get(item['name']):
        lines+=['','## 反射方法','','| 登记名 | 代码入口 |','| --- | --- |']
        for m in by_class[item['name']]:lines.append('| `'+m['method_name']+'` | '+fn(m['address'])+' |')
    if item['vtable']:
        lines+=['','## 虚函数槽位','','| 槽位 | 代码入口 | 与父类型关系 |','| ---: | --- | --- |']
        for slot in item['vtable']:
            relation={'inherited':'共用','overridden':'替换','new_slot':'新增'}.get(slot.get('relation_to_parent'),'未比对')
            lines.append('| '+str(slot['slot'])+' | '+fn(slot['address'])+' | '+relation+' |')
    page(item['name']).write_text('\n'.join(lines)+'\n',encoding='utf-8')
index=['# 第五轮类型目录','','链接已指向第五轮采用的函数版本；未改进的函数继续引用前轮输出。','','| 类型 | 字段 | 虚表槽位 |','| --- | ---: | ---: |']
for item in sorted(classes,key=lambda r:r['name'].lower()):index.append('| '+link(page(item['name']),item['name'])+' | '+str(len(item['fields']))+' | '+str(len(item['vtable']))+' |')
(model/'类型目录.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
changes=['# 控制流修正目录','','本表统计截断标记被消除的函数，并不表示参数、局部变量类型、异常展开语义或全部间接跳转均已恢复。','','| 地址 | 旧输出 | 新输出 | 其它间接跳转诊断 |','| --- | --- | --- | --- |']
for r in sorted(repairs,key=lambda r:r['address']):
    changes.append('| `'+r['address']+'` | '+link(base/r['previous_source'],'旧版')+' | '+fn(r['address'])+' | '+('仍需核对' if r['other_jumptable_warning'] else '未出现此诊断')+' |')
(model/'控制流修正目录.md').write_text('\n'.join(changes)+'\n',encoding='utf-8')
proofs=json.loads((root/'noreturn/noreturn_audit.json').read_text())
prooflines=['# 不返回函数的静态证据','','从 ABI 声明和 ELF 动态符号/PLT 重定位开始，沿机器指令检查所有可达分支。普通调用保留返回路径；有循环、未知跳转、返回指令或越过函数范围的候选不予采用。已用独立反汇编器检查字节、ARM/Thumb 模式、条件分支与目标地址。','',
            '| 函数 | 已检查指令数 | 终止调用/尾跳转目标 |','| --- | ---: | --- |']
for r in proofs['proven_wrappers']:prooflines.append('| `'+r['address']+'` '+r['name']+' | '+str(len(r['instructions']))+' | '+', '.join('`'+t['callee']+'`' for t in r['terminals'])+' |')
prooflines+=['','## ABI 声明依据','',
 '- [Android C++ ABI：throw、rethrow、pure virtual](https://android.googlesource.com/platform/external/libcxxabi/+/refs/heads/master/include/cxxabi.h)',
 '- [Android libc：abort、exit](https://android.googlesource.com/platform/bionic/+/main/libc/include/stdlib.h)',
 '- [Android libc：_exit](https://android.googlesource.com/platform/bionic/+/f45bc14d5497c30bd43e22d025e3b88812b2baa4/libc/include/unistd.h)',
 '- [Android 日志断言：__android_log_assert](https://android.googlesource.com/platform/system/core/+/6584d0a35ab7722bdc6590525dee29f72f0ec576/include/android/log.h)',
 '',link(root/'noreturn/noreturn_audit.json','完整指令证据')+'；'+link(base/'logs/round5_noreturn_verification.json','独立核验结果')+'。','']
(model/'不返回函数证据.md').write_text('\n'.join(prooflines),encoding='utf-8')
example=next(r for r in repairs if r['address']=='0064fc6c')
before=(base/example['previous_source']).read_text('utf-8');after=(base/example['new_source']).read_text('utf-8')
diff=difflib.HtmlDiff(wrapcolumn=110).make_file(before.splitlines(),after.splitlines(),fromdesc='旧分析：错误跟随异常调用的返回路径',todesc='修正后：异常分支不再返回',context=True,numlines=5)
(model/'异常分支修正对照.html').write_text(diff,encoding='utf-8')
lines=['# 第五轮恢复结果','',
       '本轮主要修正异常处理造成的控制流误判：消除 **'+str(summary['truncation_markers_removed'])+' 个函数的截断标记**，另新增 **'+str(summary['new_unique_functions'])+' 个不同地址的函数伪代码**。主库累计 **'+format(summary['cumulative_pseudocode_functions'],',')+' 个**。','',
       '- '+link(model/'类型目录.md','最新类型目录：字段、方法和虚函数入口'),
       '- '+link(model/'控制流修正目录.md','控制流修正清单及前后版本'),
       '- '+link(model/'异常分支修正对照.html','示例：误读相邻函数的内容如何被移除'),
       '- '+link(model/'不返回函数证据.md','机器指令、ABI 声明与独立核验证据'),
       '- '+link(model/'最后一个截断点分析.md','最后一个截断点：已恢复 76 个分支入口'),
       '- '+link(model/'function_catalog.json','统一函数目录'),
       '- '+link(base/'第四轮恢复结果.md','第四轮结果与反射方法证据'),'','## 修正原因','',
       '此前分析遗漏了一批“不返回”属性。调用抛出异常、终止程序等函数后，工具仍沿虚构的返回路径继续读取，甚至把相邻函数和常量解读为当前函数的内容。',
       '本轮先核对已知 ABI 函数的 ELF 动态符号、PLT 重定位或导入跳板，再证明 '+str(summary['verified_noreturn_wrappers'])+' 个封装函数的全部已知路径均终止于不返回调用。修改的仅是分析工程中的属性；没有修改 APK 或原生库字节。',
       '对 '+str(summary['verified_noreturn_instructions'])+' 条指令另外使用独立反汇编器核对字节、模式、分支目标和条件执行。主工程导出沿用旧边界；另有 4 个入口沿用第四轮独立工程的实验边界，标记仍保留，未修改主工程边界。历史输出保留。',
       '修正后部分伪代码明显变短，这是误读的相邻代码被移除。不能据此推断源程序本身缩短，也不能仅据警告减少认定恢复完整。','',
       '## 仍需继续恢复','',
       '前轮剩余 5 个未纳入 C 输出的困难条目，本轮补出 '+str(len(summary['previous_hard_now_with_C']))+' 个；仍未选定 C 输出的地址：'+', '.join('`'+a+'`' for a in summary['previous_hard_still_without_C'])+'。',
       '累计目录中仍含截断标记的地址：'+', '.join('`'+a+'`' for a in summary['remaining_truncation_addresses'])+'。此外，未出现截断标记的输出仍可能有未知类型、错误参数、跳转表警告或实验函数边界。',
       '这些成果仍是静态反编译与结构线索，不是完整可重新编译的原始源码，尚未经过游戏运行验证。','',
       link(base/'logs/round5_validation.json','本轮完整性核验')+'。','']
(base/'第五轮恢复结果.md').write_text('\n'.join(lines),encoding='utf-8')
print('Round 5 report and',len(classes),'class pages written')
