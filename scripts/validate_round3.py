from pathlib import Path
import sys,json,re,csv,struct,hashlib
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round3';model=root/'model'
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
source=base/'raw/lib/armeabi/libSrc.so';blob=source.read_bytes()
with source.open('rb') as fp:
    elf=ELFFile(fp);segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    code_regions=[(s['sh_addr'],s['sh_addr']+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read(address,size):
    for seg in segments:
        if seg['p_vaddr']<=address and address+size<=seg['p_vaddr']+seg['p_filesz']:
            off=seg['p_offset']+address-seg['p_vaddr'];return blob[off:off+size]
    return None
classes=json.loads((model/'classes.json').read_text());catalog=json.loads((model/'function_catalog.json').read_text())
assert len({r['address'] for r in catalog})==len(catalog)
for row in catalog:
    assert (base/row['source']).stat().st_size>100,row
    assert (base/row['readable_file']).stat().st_size>100,row
for item in classes:
    if item['registrations']:
        limit=max(int(r['registered_size'],16) for r in item['registrations'])
        for field in item['fields']:assert 0<=int(field['offset'],16)<limit,(item['name'],field)
    if not item['vtable']:continue
    gh=int(item['vtable_address'],16)
    assert struct.unpack('<II',read(gh-0x10000-8,8))==(0,0),item['name']
    for slot in item['vtable']:
        ptr=struct.unpack('<I',read(gh-0x10000+slot['slot']*4,4))[0]
        assert ptr and any(lo<=ptr&~1<hi for lo,hi in code_regions),(item['name'],slot)
        assert (ptr&~1)+0x10000==int(slot['address'],16),(item['name'],slot)
links=0
paths=[base/'反编译结果说明.md',base/'深入分析结果.md',base/'第三轮恢复结果.md',model/'类型目录.md',*list((model/'classes').glob('*.md'))]
if (model/'控制流待核对.md').exists():paths.append(model/'控制流待核对.md')
for path in paths:
    for target in re.findall(r'\]\((K:/[^)]+)\)',path.read_text(encoding='utf-8')):
        assert Path(target).is_file(),(path,target)
        links+=1
ir=json.loads((root/'expand/ir_results.json').read_text())
assert len(ir)==5 and all(r['status']=='ok' and not r['truncated'] for r in ir)
for row in ir:assert (root/'expand'/row['file']).stat().st_size>100
index_path=root/'full_library/functions.csv'
if not index_path.exists():index_path=root/'virtual_methods_final/functions.csv'
index=list(csv.DictReader(index_path.open(encoding='utf-8-sig')))
for row in index:assert int(row['address'],16)-int(row['elf_address'],16)==0x10000
sha=hashlib.file_digest((base/'PvZ2-LostCity-1.7.5.apk').open('rb'),'sha256').hexdigest()
assert sha=='1655512770c6968bd4216f0d66b8be955ce464c6e6881b5de6cbf776f245e1a4'
summary=json.loads((model/'summary.json').read_text())
fullpath=root/'full_library/summary.json'
if fullpath.exists():
    full=json.loads(fullpath.read_text())
    assert full['processed']==full['targets']==len(full['exports'])
    eligible={r['address'] for r in index if r['external']=='False' and r['thunk']=='False'}
    attempted={r['address'] for r in catalog}|{r['address'] for r in full['exports']}|set(full['existing_ir_only_addresses'])
    assert not eligible-attempted,sorted(eligible-attempted)
    summary.update(all_recognized_non_thunk_functions_attempted=True,recognized_non_thunk_functions=len(eligible),
                   full_pass_targets=full['targets'],full_pass_c_exports=full['exported_functions'],full_pass_c_errors=full['errors'])
auxpath=base/'native_analysis/auxiliary/summary.json'
if auxpath.exists():
    auxiliary=json.loads(auxpath.read_text())
    assert auxiliary['library_count']==6
    for library in auxiliary['libraries']:
        folder=base/library['directory'];rows=json.loads((folder/'summary.json').read_text())['exports']
        assert len(rows)==library['recognized_non_thunk_functions']
        for row in rows:
            if row['status']=='ok':assert (folder/row['file']).stat().st_size>80
    summary.update(auxiliary_libraries_attempted=6,auxiliary_c_exports=auxiliary['exported_functions'],auxiliary_c_errors=auxiliary['errors'])
summary.update(report_links_verified=links,class_documents_verified=len(classes),field_offsets_within_registered_sizes=True,
               vtable_headers_and_executable_pointers_verified=True,large_ir_files_verified=5,apk_sha256_unchanged=sha)
(base/'logs/round3_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
