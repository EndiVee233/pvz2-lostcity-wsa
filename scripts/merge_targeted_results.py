from pathlib import Path
import json,shutil
base=Path(__file__).resolve().parents[1]
temp=Path((base/'logs/deep_native_temp_path.txt').read_text(encoding='utf-8-sig').strip())
root=base/'native_analysis/core_deep'
results=json.loads((temp/'targeted_results.json').read_text(encoding='utf-8'))
shutil.copytree(temp/'functions',root/'functions',dirs_exist_ok=True)
summary=json.loads((root/'summary.json').read_text(encoding='utf-8'))
summary.setdefault('initial_exported_functions',summary['exported_functions'])
summary.setdefault('initial_export_errors',summary['export_errors'])
merged={row['address']:row for row in summary['exports']}
for row in results:
    row['elf_address']=row['elf_address'].rstrip('L')
    merged[row['address']]=row
summary['exports']=list(merged.values())
summary['exported_functions']=sum(r['status']=='ok' for r in merged.values())
summary['export_errors']=sum(r['status']=='error' for r in merged.values())
summary['targeted_followup_attempts']=len(results)
(root/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(root/'targeted_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Merged targeted results:',summary['exported_functions'],'exported;',summary['export_errors'],'still failed')
