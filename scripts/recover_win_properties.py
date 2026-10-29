"""Original metadata/schema/factory evidence for ZombiesDeadWinConProperties."""
import json
from reflection_emulation_support import h,seed
seed();manager=h.call(0x11b10ec,[]);meta=h.call(0xb78a90,[]);h.call(0x11b15b4,[manager]);schema=h.words(meta+0x24)[0]
b,e=h.words(schema+0x134,2)
fields=[dict(name=h.narrow(h.words(p+0x38)[0]).decode(),offset=h.words(p+0x48)[0]) for p in h.words(b,(e-b)//4)]
assert fields==[dict(name='m_thisPtr',offset=8),dict(name='ResourceGroupNames',offset=16)]
parent=h.words(meta+8)[0];parent_name=h.narrow(h.words(parent+4)[0]).decode();assert parent_name=='LevelModuleProperties'
p=h.call(0xb78784,[]);defaults=h.words(p+8,5);assert defaults==[0]*5
out=h.base/'native_analysis/core_round31/win_condition';out.mkdir(parents=True,exist_ok=True)
(out/'factory-validation.json').write_text(json.dumps(dict(metadata='00b78a90',factory='00b78784',parent=parent_name,allocation_bytes=32,fields=fields,default_reference_and_vector_words=defaults,scope='Real metadata/schema registration and factory. Inherited fields only; no runtime instance/event wiring.'),indent=2),encoding='utf-8');print('Confirmed win property factory and inherited-only schema')
