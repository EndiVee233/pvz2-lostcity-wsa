"""Export original byte-path outputs and package-aware owner states."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round18/store_packages/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(f'{x}U' for x in v)+'}'
lines=['// Captured original ARM package/path states; do not calculate expected values in C++.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 configs=[]
 for c in sc['configs']:
  configs.append('{'+','.join([f'{c["reserve"]}U',str(c['name'] is None).lower(),arr(c['name'] or []),arr(c['display']),f'{c["fixed"]}U',f'{c["system"]}U'])+'}')
 paths='{'+','.join(arr(p) for p in sc['paths'])+'}'
 lines.append('{'+','.join([json.dumps(sc['label']),str(sc['kind']=='path').lower(),paths,'{'+','.join(configs)+'}',arr(sc['initial'])])+',{')
 for s in sc['steps']:
  parts=['Operation::'+s['op'],*[f'{s[k]}U' for k in ['type','a','b','c','h','name']],arr(s['d']),arr(s['result']),arr(s['events']),arr(s['state'])]
  lines.append('{'+','.join(parts)+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/store_package_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'package/path ARM checkpoints')
