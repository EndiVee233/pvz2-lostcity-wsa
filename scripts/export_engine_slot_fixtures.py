"""Export original ARM slot traces without deriving expected outcomes in C++."""
import json
from pathlib import Path
base = Path(__file__).resolve().parents[1]
d = json.loads((base / 'native_analysis/core_round13/engine_slots/validation.json').read_text())

def values(v):
    return '{' + ','.join(str(i) + 'U' for i in v) + '}'

lines = ['// Generated from original ARM state checkpoints; do not edit expected outcomes.',
         'const Scenario scenarios[] = {']
for sc in d['scenarios']:
    lines.append('{' + ','.join([json.dumps(sc['label']), str(sc['capacity']) + 'U',
        str(sc['seed']) + 'U', str(sc['type']) + 'U', '0x' + sc['initial']['normalized_fnv1a64'] + 'ULL']) + ',{')
    for s in sc['steps']:
        parts = ['Operation::' + s['op'], *[str(s[k]) + 'U' for k in ['a', 'b', 'c', 'h']],
                 values(s['d']), values(s['result']), values(s['events']),
                 '0x' + s['snapshot']['normalized_fnv1a64'] + 'ULL']
        lines.append('{' + ','.join(parts) + '},')
    lines.append('}},')
lines.append('};')
(base / 'native_recovered/tests/engine_slot_fixtures.inc').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Exported', d['checkpoints'], 'ARM slot checkpoints')
