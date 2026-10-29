"""Export captured ARM name-tree, binding and registry-bank states."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round16/name_indices/validation.json').read_text())
def arr(values):return '{'+','.join(f'{v}U' for v in values)+'}'
lines=['// Captured original ARM states; do not regenerate expected outputs in C++.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 lines.append('{'+','.join([json.dumps(sc['label']),'Kind::'+sc['kind'],str(sc['object']).lower(),arr(sc['initial'])])+',{')
 for s in sc['steps']:
  lines.append('{'+','.join(['Operation::'+s['op'],*[f'{s[k]}U' for k in ['key','a','b']],arr(s['d']),str(s['hint'] is not None).lower(),f'{s["hint"] or 0}U',arr(s['result']),arr(s['events']),arr(s['state'])])+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/name_index_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'ARM name/index/bank checkpoints')
