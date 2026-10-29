"""Record completed round-26 build and railcart ARM/CLI comparisons.

Run only after build.ps1 and validate_intro_loader.py --railcart succeed.
"""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];root=base/'native_recovered';manifest=root/'build-validation.json'
d=json.loads(manifest.read_text(encoding='utf-8'));folder=base/'native_analysis/core_round26/railcart_reflection'
r=json.loads((folder/'validation.json').read_text(encoding='utf-8'));cli=json.loads((folder/'native-cli-validation.json').read_text(encoding='utf-8'))
assert r['checkpoints']==80 and all(x['exact_arm_graph_match'] and x['exit_code']==x['expected_exit_code'] for x in cli['examples'])
actual=next(x for x in cli['examples'] if x['example']=='cowboy-dangerroom');assert actual['created']==2 and actual['declarations']==5 and actual['exit_code']==3
d.update(round=26,total_cpp_checks=44768+80,test_program_count=19,utility_program_count=3)
line='PASS 80 railcart/inherited reflection nested-record ARM full-state checkpoints'
if line not in d['observed_stdout']:d['observed_stdout'].append(line)
d['execution_exit_codes']['railcart_reflection_tests.exe']=0;d['artifacts']['build\\railcart_reflection_tests.exe']={}
for name in d['artifacts']:
 blob=(root/name).read_bytes();d['artifacts'][name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
d['test_scope']='All 19 programs compiled/passed with C++17 -Wall -Wextra -Werror; 3 tools linked. Eight selected concrete data classes, adding real RailcartProperties with nested RailcartRail/Location lists and narrow type text. 80 additional original ARM data-state comparisons cover defaults, resize/partial overwrite, malformed-list following-field fallbacks, mixed-class/cross-package references and actual Cowboy asset 2/5 partial load. Generic schemas, arbitrary value coercions, full malformed-context propagation, UID/text RTID, game/event runtime and Android/JNI/source-only APK remain incomplete.'
d['reflection_supported_data_classes']=[name for name in r['schemas'] if name!='RtObject']
d['reflection_scoped_entries']=[
 'Eight selected original factories: initialized reflected data fields only, no ARM vtable/game methods',
 '011ed5fc version1/no explicit UID/eight selected concrete data classes',
 '011ead94 and 011b9bb0 selected weak-reference/string-list/float/int/nested-record fields',
 '011b1de0 non-flags GroundEffectType narrow-text enum',
 '011b7180/011fb300/011f4c90 binary weak RTID reads 0..3, narrow text and bounded vector/record read paths',
 '011f9ae8 numeric/common narrow decimal float32 branches; wide/RTID/special-text excluded',
 '008a297c/008a1e30 plus growth helpers: logical record resize/defaults, not allocation capacity ABI']
d['reflection_bootstrap_boundary']='Explicit host metadata tokens/two logical system stores, nine class-directory entries after optional intro+railcart registration. Generic original reflection schema/symbol ABI is not restored. Original GameObject Serialize/event path executes against empty _INIT_134 event bus; host data adapter omits event bus/game callbacks, and event state is excluded.'
d['railcart_reflection_arm_cpp_full_state_checkpoints']=r['checkpoints'];d['railcart_reflection_original_operations']=r['operations']
d['railcart_reflection_function_entry_hits']=r['function_entry_hits'];d['railcart_reflection_schemas']=r['schemas'];d['railcart_reflection_scope']=r['scope']
d['all_reflection_arm_cpp_full_state_checkpoints']=54+50+80;d['railcart_native_cli_validation']=cli
d['intro_native_cli_validation']=json.loads((base/'native_analysis/core_round25/intro_reflection/native-cli-validation.json').read_text(encoding='utf-8'))
d['actual_cowboy_asset_data_objects_supported']=dict(created=2,declarations=5,remaining_classes=['LevelDefinition','WaveGeneratorProperties','SeedBankProperties'],origin=r['real_resource_source'],whole_level_supported=False)
d['full_game_source_build']=False
assert sum(int(line.split()[1]) for line in d['observed_stdout'])==d['total_cpp_checks']
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded round 26:',d['total_cpp_checks'],'checks;',len(d['artifacts']),'hashed artifacts; 8 concrete data classes; actual asset 2/5')
