import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round24/reflection_chain/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
lines=['// Original factory/property/RTID chain states. No expected values computed in C++.','const std::vector<std::uint32_t> initial_state = '+arr(d['initial'])+';','const Step steps[] = {']
for s in d['steps']:
 nested=lambda values:'{'+','.join(arr(x) for x in values)+'}'
 lines.append('{'+','.join(['Operation::'+s['op'],str(s['type'])+'U',arr(s['name']),arr(s['data']),json.dumps(s['label']),nested(s['results']),nested(s['states'])])+'},')
lines.append('};')
(base/'native_recovered/tests/reflection_chain_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'reflection chain checkpoints')
