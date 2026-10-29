import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round23/rton_scalars/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Original ARM non-RTID scalar results and cursor states.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 lines.append('{'+json.dumps(sc['label'])+','+arr(sc['data'])+',{')
 for s in sc['steps']:lines.append('{'+','.join(['Operation::'+s['op'],*[str(s[k])+'U' for k in ['offset','fallback','result','position']]])+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/rton_scalar_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'scalar checkpoints')
