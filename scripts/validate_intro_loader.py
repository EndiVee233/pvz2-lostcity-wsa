"""Run the independently compiled data loader against saved original ARM graphs."""
import hashlib,json,subprocess,sys
from pathlib import Path
base=Path(__file__).resolve().parents[1];exe=base/'native_recovered/build/rton_load_objects.exe'
LEVEL='--level' in sys.argv
WAVE='--wave' in sys.argv or LEVEL
SEED='--seedbank' in sys.argv or WAVE
RAIL='--railcart' in sys.argv or SEED
out=base/('native_analysis/core_round29/level_reflection' if LEVEL else 'native_analysis/core_round28/wave_reflection' if WAVE else 'native_analysis/core_round27/seedbank_reflection' if SEED else 'native_analysis/core_round26/railcart_reflection' if RAIL else 'native_analysis/core_round25/intro_reflection');rows=[]
examples=[(out/'example','mixed-cycle',0),(out/'example','cowboy-dangerroom',0 if LEVEL else 3),(base/'native_analysis/core_round24/reflection_chain/example','cyclic',0)]
if RAIL:examples.append((out/'example','railcart-cycle',0))
if SEED:examples.extend([(out/'example','seedbank-cycle',0),*[(out/'example',f'resource-{n}',3) for n in [2,3,4]]])
if WAVE:examples.append((out/'example','wave-cycle',0))
if LEVEL:examples.append((out/'example','level-cycle',0))
for folder,name,expected_exit in examples:
 target=folder/(name+'.cpp.objects.json')
 result=subprocess.run([str(exe),str(folder/(name+'.raw.rton')),str(target),*([] if LEVEL else ['--wave-only'] if WAVE else ['--seedbank-only'] if SEED else ['--railcart-only'] if RAIL else ['--intro-only'])],capture_output=True,text=True)
 expected=json.loads((folder/(name+'.arm.objects.json')).read_text(encoding='utf-8'))
 actual=json.loads(target.read_text(encoding='utf-8'))
 assert result.returncode==expected_exit,(name,result.returncode,result.stderr)
 assert expected==actual,name
 rows.append(dict(example=name,exit_code=result.returncode,expected_exit_code=expected_exit,exact_arm_graph_match=True,created=sum(x is not None for x in actual['objects']),declarations=len(actual['objects']),output=str(target.relative_to(base)),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),stdout=result.stdout.strip(),stderr=result.stderr.strip()))
 if LEVEL and name=='cowboy-dangerroom':
  targets=[x['target'] for x in actual['objects'][0]['Modules']]
  assert targets==[2,None,None,None,None,1,3,4,None],targets
  def refs(value):
   if isinstance(value,dict):
    if all(k in value for k in ['package','name','target']):yield value
    else:
     for child in value.values():yield from refs(child)
   elif isinstance(value,list):
    for child in value:yield from refs(child)
  symbolic=[x for x in refs(actual) if x['package'] is not None]
  unresolved=sum(x['target'] is None for x in symbolic)
  rows[-1].update(local_module_targets=[x for x in targets if x is not None],unresolved_symbolic_references=unresolved)
  assert unresolved==16,unresolved
 if name=='cowboy-dangerroom' or name.startswith('resource-'):
  origin=json.loads((base/'native_analysis/core_round21/rton_normalizer/native-cli-validation.json').read_text(encoding='utf-8'))
  rows[-1]['source']=next(x['source'] for x in origin['resources'] if x['label']==('resource-1' if name=='cowboy-dangerroom' else name))
  assert hashlib.sha256((folder/(name+'.raw.rton')).read_bytes()).hexdigest()==rows[-1]['source']['plaintext_sha256']
 print('PASS',name,':',rows[-1]['created'],'/',rows[-1]['declarations'],'data objects, exit',result.returncode)
record=dict(executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),profile='default (round 29 eleven-class CurrentLevel profile)' if LEVEL else '--wave-only (round 28 ten-class profile)' if WAVE else '--seedbank-only (round 27 nine-class profile)' if SEED else '--railcart-only (round 26 eight-class profile)' if RAIL else '--intro-only (round 25 seven-class profile)',original_engine_library_required=False,data_only=True,game_behavior_executed=False,examples=rows,scope='Unchanged asset plaintexts and focused schema-derived graphs. Exit 0 means all declarations have supported factories; it does not assert all external references resolve or game behavior runs. Unsupported declarations remain null and CLI returns 3 for a partial load.')
(out/'native-cli-validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
