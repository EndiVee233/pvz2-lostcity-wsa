import json
from pathlib import Path
base=Path(__file__).resolve().parents[1];d=json.loads((base/'native_analysis/core_round31/win_condition/validation.json').read_text());rows=[]
for c in d['cases']:
 ints=lambda v:'{'+','.join(str(x)+'U' for x in v)+'}'
 strings=lambda v:'{'+','.join(json.dumps(x) for x in v)+'}'
 rows.append('{'+ints(c['entity_flags'])+','+ints(c['registry_kinds'])+','+str(c['result'])+','+str(2*len(c['visited']))+','+strings([x for x in c['events'] if x.startswith(('predicate-','find-bank-','resolve-')) or x in ('enumerate-0x25','release-enumeration')])+'}')
(base/'native_recovered/tests/win_condition_fixtures.inc').write_text('// Original ARM branch outcomes and callback order.\nconst Case cases[] = {'+','.join(rows)+'};\n',encoding='utf-8')
