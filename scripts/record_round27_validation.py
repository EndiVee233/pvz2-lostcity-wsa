"""Record completed round-27 build and SeedBank original ARM/CLI comparisons.

Run after build.ps1 and validate_intro_loader.py --seedbank succeed.
"""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];root=base/'native_recovered';manifest=root/'build-validation.json'
d=json.loads(manifest.read_text(encoding='utf-8'));folder=base/'native_analysis/core_round27/seedbank_reflection'
r=json.loads((folder/'validation.json').read_text(encoding='utf-8'));cli=json.loads((folder/'native-cli-validation.json').read_text(encoding='utf-8'))
assert r['checkpoints']==139 and all(x['exact_arm_graph_match'] and x['exit_code']==x['expected_exit_code'] for x in cli['examples'])
actual=next(x for x in cli['examples'] if x['example']=='cowboy-dangerroom');assert actual['created']==3 and actual['declarations']==5 and actual['exit_code']==3
assets=[x for x in cli['examples'] if 'source' in x];assert len(assets)==4
d.update(round=27,total_cpp_checks=44848+139,test_program_count=20,utility_program_count=3)
line='PASS 139 seedbank/inherited reflection enum/bool/string-list ARM full-state checkpoints'
if line not in d['observed_stdout']:d['observed_stdout'].append(line)
d['execution_exit_codes']['seedbank_reflection_tests.exe']=0;d['artifacts']['build\\seedbank_reflection_tests.exe']={}
for name in d['artifacts']:
 blob=(root/name).read_bytes();d['artifacts'][name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
d['test_scope']='All 20 programs compiled/passed with C++17 -Wall -Wextra -Werror; 3 tools linked. Nine selected concrete data classes including SeedBankProperties enum/three booleans/three narrow string lists/BlackListLiftedBy. 139 additional original ARM complete data-state comparisons include actual Cowboy asset 3/5 and SeedBank 1/6 in each of three other assets. Partial data profiles only: generic schemas, numeric/wide enum and arbitrary string coercion, UID/text RTID, full malformed-context propagation, event/game runtime and Android/JNI/source-only APK remain incomplete.'
d['reflection_supported_data_classes']=[name for name in r['schemas'] if name!='RtObject']
d['reflection_scoped_entries']=[
 'Nine selected original factories: initialized reflected fields, no ARM vtable/game behavior',
 '011ed5fc version1/no explicit UID/nine selected concrete data classes',
 '011ead94 and 011b9bb0 selected weak-reference/string-list/float/int/boolean/nested-record fields',
 '011b1de0 non-flags GroundEffectType and SeedBank SelectionMethod narrow-text enums; decimal fallback within signed32',
 '011b7180/011fb300/011f4c90 binary weak RTID reads 0..3 and bounded vector/string/record reads',
 '011f8a24 non-reference boolean coercion used by three SeedBank bool properties',
 '011f9ae8 numeric/common narrow decimal float32 branches; wide/RTID/special-text excluded',
 '008a297c/008a1e30 record resize/defaults, not allocation capacity ABI']
d['reflection_bootstrap_boundary']='Explicit host metadata tokens/two logical system stores; ten class-directory entries with optional SeedBank registration. Original generic reflection schema/symbol ABI is not restored. Original GameObject Serialize/event path executes with empty _INIT_134 event bus; host data adapter omits game callbacks/events, and event state is excluded.'
d['seedbank_reflection_arm_cpp_full_state_checkpoints']=r['checkpoints'];d['seedbank_reflection_original_operations']=r['operations']
d['seedbank_reflection_function_entry_hits']=r['function_entry_hits'];d['seedbank_reflection_schemas']=r['schemas'];d['seedbank_reflection_scope']=r['scope']
d['seedbank_selection_enum']=r['seedbank_selection_enum'];d['all_reflection_arm_cpp_full_state_checkpoints']=54+50+80+139;d['seedbank_native_cli_validation']=cli
for prefix,path in [('intro','core_round25/intro_reflection'),('railcart','core_round26/railcart_reflection')]:
 d[prefix+'_native_cli_validation']=json.loads((base/'native_analysis'/path/'native-cli-validation.json').read_text(encoding='utf-8'))
d['actual_cowboy_asset_data_objects_supported']=dict(created=3,declarations=5,remaining_classes=['LevelDefinition','WaveGeneratorProperties'],origin=r['real_resource_source'],whole_level_supported=False)
d['other_asset_data_objects_supported']=[dict(created=x['created'],declarations=x['declarations'],origin=x['source'],whole_level_supported=False) for x in assets if x['example']!='cowboy-dangerroom']
d['full_game_source_build']=False
assert sum(int(line.split()[1]) for line in d['observed_stdout'])==d['total_cpp_checks']
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded round 27:',d['total_cpp_checks'],'checks;',len(d['artifacts']),'hashed artifacts; 9 concrete data classes; Cowboy asset 3/5')
