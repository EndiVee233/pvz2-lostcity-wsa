import json
from pathlib import Path
base=Path(__file__).resolve().parents[1];r=json.loads((base/'native_analysis/core_round33/brain_properties/validation.json').read_text())
(base/'native_recovered/tests/brain_properties_fixtures.inc').write_text('// Original ARM float field states.\nconst Case cases[] = {'+','.join('{"'+c['raw_hex']+'",'+str(c['bits'])+'U}' for c in r['cases'])+'};\n',encoding='utf-8')
