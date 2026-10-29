"""Export original conversion bytes and string/offset maps, no recomputation."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round21/rton_normalizer/validation.json').read_text(encoding='utf-8'))
def arr(v):return '{'+','.join(str(x)+'U' for x in v)+'}'
def table(entries):return '{'+','.join('{'+arr(e['text'])+','+str(e['offset'])+'U}' for e in entries)+'}'
lines=['// Captured original ARM conversion outputs and logical maps.','const Scenario scenarios[] = {']
for sc in d['scenarios']:
 lines.append('{'+','.join([json.dumps(sc['label'].replace('\0','[NUL]')),arr(sc['data']),str(bool(sc['success'])).lower(),str(sc['consumed'])+'U',arr(sc['output']),table(sc['narrow']),table(sc['wide'])])+'},')
lines.append('};')
(base/'native_recovered/tests/rton_normalizer_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',d['checkpoints'],'RTON normalizer checkpoints')
