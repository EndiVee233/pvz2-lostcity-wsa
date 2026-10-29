"""Export original read results/positions, including captured writer inputs."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round20/rton_input/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Original ARM values, code units and cursor states, not calculated in C++.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 w=sc['writer'];writer='WriterKind::'+w['kind'] if w else 'WriterKind::none'
 lines.append('{'+','.join([json.dumps(sc['label']),arr(sc['data']),str(sc['mode'])+'U',writer,arr(w['value'] if w else [])])+',{')
 for s in sc['steps']:lines.append('{'+','.join(['Operation::'+s['op'],str(s['a'])+'U',arr(s['result']),arr(s['state'])])+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/rton_input_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'RTON input checkpoints')
