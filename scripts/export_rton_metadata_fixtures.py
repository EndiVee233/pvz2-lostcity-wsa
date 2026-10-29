"""Export captured original bytes/cache states without recomputing outputs."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round19/rton_metadata/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Captured original ARM writes; expected bytes are never calculated by C++.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 c=sc['config'] or dict(type=2,reserve=0,name=None,display=[],fixed=0,system=0)
 config='{'+','.join([str(c['type'])+'U',str(c['reserve'])+'U',str(c['name'] is None).lower(),arr(c['name'] or []),arr(c['display']),str(c['fixed'])+'U',str(c['system'])+'U'])+'}'
 lines.append('{'+','.join([json.dumps(sc['label']),str(sc['config'] is not None).lower(),config,arr(sc['path']),arr(sc['initial'])])+',{')
 for s in sc['steps']:lines.append('{'+','.join(['Operation::'+s['op'],str(s['number'])+'U',arr(s['key']),arr(s['value']),str(s['cached']).lower(),arr(s['state'])])+'},')
 lines.append('}},')
lines.append('};')
(base/'native_recovered/tests/rton_metadata_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'RTON byte/cache checkpoints')
