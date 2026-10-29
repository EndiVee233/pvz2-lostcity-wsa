"""Export original real-constructor/store-lifecycle states for C++ replay."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round17/owned_stores/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(f'{x}U' for x in v)+'}'
lines=['// Captured original constructor/reset/destructor states; do not derive expectations in C++.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 configs=[]
 for c in sc['configs']:
  configs.append('{'+','.join([f'{c["reserve"]}U',str(c['name'] is None).lower(),arr(c['name'] or []),arr(c['display']),f'{c["fixed"]}U',f'{c["system"]}U'])+'}')
 lines.append('{'+json.dumps(sc['label'],ensure_ascii=False)+',{'+','.join(configs)+'},'+arr(sc['initial'])+',{')
 for s in sc['steps']:
  fields=['Operation::'+s['op'],*[f'{s[k]}U' for k in ['type','a','b','c','h','name']],arr(s['d']),arr(s['result']),arr(s['events']),arr(s['state'])]
  lines.append('{'+','.join(fields)+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/owned_store_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'real store lifecycle ARM states')
