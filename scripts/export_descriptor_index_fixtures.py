"""Export complete original ARM/Thumb tree states for compiled C++ checks."""
import json
from pathlib import Path
base = Path(__file__).resolve().parents[1]
source = base / 'native_analysis/core_round14/descriptor_index/validation.json'
d = json.loads(source.read_text())

def array(values):
    return '{' + ','.join(f'{v}U' for v in values) + '}'

lines = ['// Captured original ARM/Thumb node states; expected values are not generated in C++.',
         'const IndexScenario index_scenarios[] = {']
for sc in d['scenarios']:
    lines.append('{' + json.dumps(sc['label']) + ',' + array(sc['initial']) + ',{')
    for s in sc['steps']:
        lines.append('{' + ','.join(['Operation::' + s['op'], array(s['key']), array(s['value']),
            str(s['hint'] is not None).lower(), array(s['hint'] or [0, 0, 0]),
            array(s['result']), array(s['state'])]) + '},')
    lines.append('}},')
lines.append('};')
(base / 'native_recovered/tests/descriptor_index_fixtures.inc').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Exported', d['checkpoints'], 'complete ARM/Thumb descriptor states')
