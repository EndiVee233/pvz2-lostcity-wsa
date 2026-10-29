from pathlib import Path
import json,re,hashlib,sys
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round5';model=root/'model'
catalog=json.loads((model/'function_catalog.json').read_text());addresses={r['address'] for r in catalog}
assert len(addresses)==len(catalog)
prior=json.loads((base/'native_analysis/core_round4/model/function_catalog.json').read_text());old={r['address'] for r in prior}
assert old<=addresses
for row in catalog:
    assert (base/row['source']).stat().st_size>100,row['address']
    assert (base/row['readable_file']).is_file(),row['address']
    if row['source_kind'].startswith('round5_'):
        assert 'halt_baddata' not in (base/row['source']).read_text('utf-8')
        if row.get('experimental_boundary'):assert row['body_size']>=4
classes=json.loads((model/'classes.json').read_text());previous=json.loads((base/'native_analysis/core_round4/model/classes.json').read_text())
assert {c['name'] for c in classes}=={c['name'] for c in previous}
before={c['name']:c for c in previous};fields=slots=0
for item in classes:
    old_item=before[item['name']]
    assert [(f['name'],f['offset']) for f in item['fields']]==[(f['name'],f['offset']) for f in old_item['fields']]
    assert item['vtable']==old_item['vtable']
    assert item.get('parent')==old_item.get('parent')
    for f in item['fields']:
        if item['registrations']:assert 0<=int(f['offset'],16)<max(int(r['registered_size'],16) for r in item['registrations'])
    fields+=len(item['fields']);slots+=len(item['vtable'])
repairs=json.loads((model/'control_flow_repairs.json').read_text());assert len({r['address'] for r in repairs})==len(repairs)
for r in repairs:
    assert 'halt_baddata' in (base/r['previous_source']).read_text('utf-8')
    assert 'halt_baddata' not in (base/r['new_source']).read_text('utf-8')
links=0
for p in [base/'第五轮恢复结果.md',*model.glob('*.md'),*(model/'classes').glob('*.md')]:
    for target in re.findall(r'\]\((K:/[^)]+)\)',p.read_text('utf-8')):
        if Path(target)==base/'logs/round5_validation.json':links+=1;continue
        assert Path(target).is_file(),(p,target);links+=1
sha=hashlib.file_digest((base/'PvZ2-LostCity-1.7.5.apk').open('rb'),'sha256').hexdigest()
assert sha=='1655512770c6968bd4216f0d66b8be955ce464c6e6881b5de6cbf776f245e1a4'
summary=json.loads((model/'round5_summary.json').read_text())
assert summary['cumulative_pseudocode_functions']==len(catalog)
assert summary['truncation_markers_removed']==len(repairs)
summary.update(class_field_records_verified=fields,vtable_slots_unchanged_and_previously_ELF_verified=slots,
               links_verified=links,apk_sha256_unchanged=sha,source_versions_and_no_truncation_markers_verified=True)
(base/'logs/round5_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
assert (base/'logs/round5_validation.json').is_file()
print(json.dumps(summary,ensure_ascii=False,indent=2))
