import json
from pathlib import Path
base=Path(__file__).resolve().parents[1];r=json.loads((base/'native_analysis/core_round32/danger_module/validation.json').read_text());rows=[]
def ref(v):return '{'+json.dumps(v['package'])+','+json.dumps(v['name'])+','+str(v['target'])+'}'
for c in r['cases']:rows.append('{"'+c['raw_hex']+'",'+ref(c['state']['world'])+',{'+','.join(ref(v) for v in c['state']['designers'])+'}}')
(base/'native_recovered/tests/danger_module_fixtures.inc').write_text('// Original ARM field texts and resolved identities.\nconst Case cases[] = {'+','.join(rows)+'};\n',encoding='utf-8')
