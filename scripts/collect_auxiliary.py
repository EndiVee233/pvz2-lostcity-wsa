from pathlib import Path
import json,shutil
base=Path(__file__).resolve().parents[1]
temp=Path((base/'logs/auxiliary_temp_path.txt').read_text(encoding='utf-8-sig').strip())
root=base/'native_analysis/auxiliary';rows=[]
for folder in sorted(temp.glob('*.so')):
    summary_path=folder/'summary.json'
    if not summary_path.exists():continue
    destination=root/folder.name
    shutil.copytree(folder,destination,dirs_exist_ok=True)
    summary=json.loads((destination/'summary.json').read_text(encoding='utf-8'))
    successful={Path(r['file']).name for r in summary['exports'] if r['status']=='ok'}
    for src in (destination/'functions').glob('*.c'):
        if src.name in successful:
            src.write_bytes(src.read_bytes().replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n'))
        else:
            failed=destination/'failed_outputs';failed.mkdir(exist_ok=True)
            target=failed/(src.stem+'.partial.txt')
            assert src.resolve().is_relative_to(base) and target.resolve().is_relative_to(base)
            src.replace(target)
    row={k:v for k,v in summary.items() if k!='exports'}
    irpath=destination/'ir_results.json'
    if irpath.exists():row['fallback_ir_successes']=sum(r['status']=='ok' for r in json.loads(irpath.read_text()))
    row['directory']=str(destination.relative_to(base));rows.append(row)
result={'libraries':rows,'library_count':len(rows),'exported_functions':sum(r['exported_functions'] for r in rows),
        'errors':sum(r['errors'] for r in rows)}
(root/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
