"""Export captured original navigation results/cursors; expected values stay literal."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round22/rton_reader/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Original ARM indexed-reader results and cursor states.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 lines.append('{'+','.join([json.dumps(sc['label']),arr(sc['data']),arr(sc['indexed']),arr(sc['initial'])])+',{')
 for s in sc['steps']:lines.append('{'+','.join(['Operation::'+s['op'],str(s['a'])+'U',str(s['b'])+'U',arr(s['key']),arr(s['result']),arr(s['state'])])+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/rton_reader_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'indexed reader checkpoints')
