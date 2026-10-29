"""Export captured ARM intern states; no expected results are recomputed."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round15/engine_intern/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(f'{x}U' for x in v)+'}'
lines=['// Generated from original ARM intern pool and handle-chain execution.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 lines.append('{'+json.dumps(sc['label'],ensure_ascii=False)+','+arr(sc['initial'])+',{')
 for s in sc['steps']:
  fields=['Operation::'+s['op'],str(s['text'] is None).lower(),arr(s['text'] or []),*[f'{s[k]}U' for k in ['a','b','h','j']],arr(s['result']),arr(s['state'])]
  lines.append('{'+','.join(fields)+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/engine_intern_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'ARM intern states')
