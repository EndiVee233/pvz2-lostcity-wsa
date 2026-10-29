import json
from pathlib import Path
base=Path(__file__).resolve().parents[1];r=json.loads((base/'native_analysis/core_round30/sundropper/validation.json').read_text())
rows=['{"'+c['raw_hex']+'", {'+','.join(str(x)+'U' for x in c['bits'])+'}}' for c in r['cases']]
(base/'native_recovered/tests/sundropper_fixtures.inc').write_text('// Captured original ARM field states.\nconst Case cases[] = {'+','.join(rows)+'};\n',encoding='utf-8')
