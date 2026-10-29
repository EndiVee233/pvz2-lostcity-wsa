from pathlib import Path
import json,csv,collections,shutil
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round5';model=root/'model';model.mkdir(exist_ok=True)
verification=json.loads((base/'logs/round5_noreturn_verification.json').read_text())
assert verification['verified_wrappers']>0
prior=base/'native_analysis/core_round4'
catalog={r['address']:dict(r) for r in json.loads((prior/'model/function_catalog.json').read_text())}
baseline=set(catalog);versions=collections.defaultdict(list);repairs=[];unselected=[]
primary={r['address']:r for r in csv.DictReader((prior/'methods/functions.csv').open(encoding='utf-8-sig'))}
for stage in ['noreturn','hard','assert_fix','isolated_fix']:
    summary=json.loads((root/stage/'summary.json').read_text())
    assert summary['processed']==summary['requested'],stage
    for row in summary['exports']:
        if row['status']!='ok':unselected.append(dict(row,stage=stage));continue
        address=row['address'];source=root/stage/row['file'];text=source.read_text('utf-8')
        isolated=stage=='isolated_fix'
        if isolated:assert row['size']==catalog[address]['body_size'],(address,'experimental boundary changed')
        else:assert row['size']==int(primary[address]['size']),(address,'primary boundary changed')
        candidate=dict(row,source=str(source.relative_to(base)),source_kind='round5_'+stage,
                       control_flow_truncated='halt_baddata' in text,experimental_boundary=isolated,
                       selection_reason='Existing '+('experimental' if isolated else 'primary')+' boundary; no-return metadata supported by static instruction proofs')
        if isolated:candidate['body_size']=row['size']
        versions[address].append(candidate)
        if 'halt_baddata' in text:
            unselected.append(dict(candidate,selection_reason='Truncation remains'));continue
        previous=catalog.get(address)
        if previous:
            previous_text=(base/previous['source']).read_text('utf-8')
            if 'halt_baddata' in previous_text:
                repairs.append({'address':address,'previous_source':previous['source'],'new_source':candidate['source'],
                                'old_characters':len(previous_text),'new_characters':len(text),
                                'other_jumptable_warning':('Could not recover jumptable' in text)})
        catalog[address]=candidate
for row in catalog.values():
    if row['address'] not in versions:continue
    target=root/'readable'/(row['address']+'.c');target.parent.mkdir(exist_ok=True)
    target.write_text((base/row['source']).read_text('utf-8'),encoding='utf-8');row['readable_file']=str(target.relative_to(base))
bad=[]
for row in catalog.values():
    text=(base/row['source']).read_text('utf-8')
    if 'halt_baddata' in text:bad.append(row['address'])
old_hard=json.loads((prior/'model/round4_summary.json').read_text())['original_no_C_still_without_C']
for name,data in [('function_catalog.json',list(catalog.values())),('source_versions.json',versions),('control_flow_repairs.json',repairs),('unselected_candidates.json',unselected)]:
    (model/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(prior/'model/reflected_methods.json',model/'reflected_methods.json')
summary={'baseline_pseudocode_functions':len(baseline),'cumulative_pseudocode_functions':len(catalog),'new_unique_functions':len(set(catalog)-baseline),
         'truncation_markers_removed':len(repairs),'remaining_truncation_addresses':sorted(bad),'previous_hard_now_with_C':[a for a in old_hard if a in catalog],
         'previous_hard_still_without_C':[a for a in old_hard if a not in catalog],
         'selected_new_versions':sum(a in versions for a in catalog),'verified_noreturn_wrappers':verification['verified_wrappers'],
         'verified_noreturn_instructions':verification['verified_instruction_bytes_and_control_flow']}
(model/'round5_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
