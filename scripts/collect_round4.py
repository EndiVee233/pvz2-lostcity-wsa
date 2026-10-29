from pathlib import Path
import json,shutil,collections,re
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round4'
stages=[('entries','round4_temp_path.txt'),('methods','round4_methods_temp_path.txt'),('isolated_v8','round4_isolated_temp_path.txt'),('isolated_v7','round4_armv7_temp_path.txt')]
for stage,logfile in stages:
    temp=Path((base/'logs'/logfile).read_text(encoding='utf-8-sig').strip())
    dest=root/stage;dest.mkdir(exist_ok=True)
    for filename in ['summary.json','functions.csv']:
        if (temp/filename).exists():shutil.copy2(temp/filename,dest/filename)
    shutil.copytree(temp/'functions',dest/'functions',dirs_exist_ok=True)
    summary=json.loads((dest/'summary.json').read_text())
    if summary['processed']!=summary['requested']:raise RuntimeError(stage+' is still processing')
    valid={Path(r['file']).name for r in summary['exports'] if r['status']=='ok'}
    for src in (dest/'functions').glob('*.c'):
        if src.name not in valid:
            partial=dest/'incomplete_outputs';partial.mkdir(exist_ok=True)
            src.replace(partial/(src.stem+'.partial.txt'))
        else:src.write_bytes(src.read_bytes().replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n'))

r3=base/'native_analysis/core_round3'
baseline=json.loads((r3/'model/function_catalog.json').read_text())
catalog={r['address']:dict(r,source_kind='round3_baseline') for r in baseline}
baseline_addresses=set(catalog);baseline_bad={}
for row in baseline:
    text=(base/row['source']).read_text(encoding='utf-8',errors='replace')
    if 'halt_baddata' in text:baseline_bad[row['address']]={'size':row.get('size',0),'warnings':text.count('/* WARNING:'),'characters':len(text)}
versions=collections.defaultdict(list)
entry_summary=json.loads((root/'entries/summary.json').read_text())
for row in entry_summary['exports']:
    if row['status']!='ok':continue
    record=dict(row,source=str((root/'entries'/row['file']).relative_to(base)),source_kind='primary_vtable_or_encoding_repair')
    catalog[row['address']]=record;versions[row['address']].append(record)
for row in json.loads((root/'methods/summary.json').read_text())['exports']:
    if row['status']!='ok':continue
    record=dict(row,source=str((root/'methods'/row['file']).relative_to(base)),source_kind='reflected_method_descriptor')
    versions[row['address']].append(record)
    if row['address'] not in catalog:catalog[row['address']]=record

repaired=[];unselected=[];candidate_rows=[]
for stage in ['isolated_v8','isolated_v7']:
    summary=json.loads((root/stage/'summary.json').read_text())
    for row in summary['exports']:
        if row['status']!='ok':continue
        candidate=dict(row,source=str((root/stage/row['file']).relative_to(base)),source_kind=stage,experimental_boundary=True)
        versions[row['address']].append(candidate);candidate_rows.append(candidate)
ranked=collections.defaultdict(list)
for row in candidate_rows:
    if row.get('body_size',0)<4:
        unselected.append(dict(row,selection_reason='No complete ARM instruction in modeled body'));continue
    if row.get('baseline_size',0)>0:
        n=row['baseline_size'];m=row['body_size']
        if m>max(n*2,n+512) or m<max(4,n//2):
            unselected.append(dict(row,selection_reason='Modeled body differs substantially from baseline; retained for manual review'));continue
    ranked[row['address']].append(row)
for address,rows in ranked.items():
    rows.sort(key=lambda r:(r.get('control_flow_truncated',True),r.get('warning_comments',999),r['source_kind']!='isolated_v7'))
    candidate=rows[0]
    if address not in catalog:
        catalog[address]=dict(candidate,selection_reason='New output for a previously unresolved entry; experimental import')
    elif address in baseline_bad and not candidate.get('control_flow_truncated',True):
        code=(base/candidate['source']).read_text(encoding='utf-8')
        hard_markers=['Could not recover jumptable','Bad instruction','Unimplemented pcodeop']
        if candidate.get('warning_comments',999)<=baseline_bad[address]['warnings'] and not any(m in code for m in hard_markers):
            catalog[address]=dict(candidate,selection_reason='Truncation marker removed and body size/diagnostic counts remained within conservative limits')
            repaired.append(address)
        else:unselected.append(dict(candidate,selection_reason='Candidate diagnostics do not meet conservative replacement criteria'))
    else:unselected.append(dict(candidate,selection_reason='Baseline or primary output retained'))

model=root/'model';model.mkdir(exist_ok=True)
(model/'function_catalog.json').write_text(json.dumps(list(catalog.values()),indent=2),encoding='utf-8')
(model/'source_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
(model/'unselected_candidates.json').write_text(json.dumps(unselected,indent=2),encoding='utf-8')
(model/'control_flow_repairs.json').write_text(json.dumps(repaired,indent=2),encoding='utf-8')
old_hard={r['address'] for folder in [r3/'full_library',base/'native_analysis/core_deep'] for r in json.loads((folder/'summary.json').read_text())['exports'] if r['status']=='error'}
virtuals=json.loads((r3/'model/virtual_methods.json').read_text())
summary={'baseline_pseudocode_functions':len(baseline_addresses),'cumulative_pseudocode_functions':len(catalog),
         'new_unique_functions':len(set(catalog)-baseline_addresses),'original_no_C_addresses':len(old_hard),
         'original_no_C_now_with_C':len(old_hard&set(catalog)),
         'original_no_C_still_without_C':sorted(old_hard-set(catalog)),
         'selected_control_flow_repairs':len(repaired),'baseline_virtual_pointer_addresses':len(virtuals),
         'virtual_pointer_addresses_with_C':sum(a in catalog for a in virtuals),
         'remaining_virtual_pointer_addresses':sorted(a for a in virtuals if a not in catalog),
         'selected_isolated_candidates':sum(r.get('experimental_boundary',False) for r in catalog.values())}
(model/'round4_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
