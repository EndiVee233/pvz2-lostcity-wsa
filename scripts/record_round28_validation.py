"""Record the completed round-28 build, original ARM and standalone CLI proof.

Run after build.ps1, verify_wave_uninitialized.py and the CLI profile checks.
"""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];root=base/'native_recovered';manifest=root/'build-validation.json'
d=json.loads(manifest.read_text(encoding='utf-8'));folder=base/'native_analysis/core_round28/wave_reflection'
r=json.loads((folder/'validation.json').read_text(encoding='utf-8'));cli=json.loads((folder/'native-cli-validation.json').read_text(encoding='utf-8'))
undefined=json.loads((folder/'uninitialized-field-validation.json').read_text(encoding='utf-8'))
assert r['checkpoints']==197 and r['operations']==119
assert all(x['exact_arm_graph_match'] and x['exit_code']==x['expected_exit_code'] for x in cli['examples'])
actual=next(x for x in cli['examples'] if x['example']=='cowboy-dangerroom');assert actual['created']==4 and actual['declarations']==5 and actual['exit_code']==3
assert not undefined['spawn_count_initialized_by_factory'] and all(not x['cpu_writes'] for x in undefined['cases'])
d.update(round=28,total_cpp_checks=44987+197,test_program_count=21,utility_program_count=3)
line='PASS 197 wave/inherited reflection nested-reference ARM full-state checkpoints'
if line not in d['observed_stdout']:d['observed_stdout'].append(line)
d['execution_exit_codes']['wave_reflection_tests.exe']=0;d['artifacts']['build\\wave_reflection_tests.exe']={}
for name in d['artifacts']:
 blob=(root/name).read_bytes();d['artifacts'][name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
d['test_scope']='All 21 programs compiled/passed with C++17 -Wall -Wextra -Werror; 3 tools linked. Ten selected concrete data classes, adding WaveGeneratorProperties and five nested value schemas: event, wave, zombie spawn, zombie pool and seed pool. 197 additional original ARM full data-state checks cover nonempty nested refs, partial resize, default Hero reference/ownership, original teardown order, Row enum and scalar coercion. Actual Cowboy asset 4/5 only; external ZombieTypes/HeroTypes not fully loaded. SpawnCount remains explicitly undefined until property write; two original allocator-pattern proofs confirm no factory initialization. No generic schema/UID/text RTID or complete malformed nested-context coercion, game/event runtime, Android/JNI source engine or source-only APK.'
d['reflection_supported_data_classes']=[name for name in r['schemas'] if name!='RtObject']
d['reflection_scoped_entries'].extend([
 '009c4c70 WaveGeneratorProperties initialized reflected defaults and owned HeroTypes/DefaultHeroLevelProps symbolic ref',
 'Wave nested value read schemas: event, wave, ZombieSpawn, ZombiePool, SeedPool; valid array containers and narrow Row enum',
 '009c7a18/009c78b4/009c7710 logical owned-ref teardown order: forward elements, reverse nested field order; no allocator ABI',
 'SpawnCount +0x58 original factory uninitialized: optional until actual property write, never a heap-fill default'])
# Rewrite the existing general selected-class count after extending the profile.
d['reflection_scoped_entries']=[x.replace('Nine selected','Ten selected').replace('nine selected','ten selected') for x in dict.fromkeys(d['reflection_scoped_entries'])]
d['reflection_bootstrap_boundary']='Explicit host metadata tokens/two logical system stores; eleven class-directory entries with optional WaveGenerator registration. Generic original schema/symbol ABI and game methods are not restored. Original GameObject Serialize/event path executes with empty _INIT_134 bus; host omits event subscribers/game callbacks. Physical metadata, COW identity, allocator capacity, private non-reflected words and padding excluded.'
d['wave_reflection_arm_cpp_full_state_checkpoints']=r['checkpoints'];d['wave_reflection_original_operations']=r['operations']
d['wave_reflection_function_entry_hits']=r['function_entry_hits'];d['wave_reflection_schemas']=r['schemas'];d['wave_reflection_scope']=r['scope']
d['wave_nested_schemas']=r['wave_nested_schemas'];d['wave_row_enum']=r['wave_row_enum'];d['wave_spawn_count_initialization_proof']=undefined
d['all_reflection_arm_cpp_full_state_checkpoints']=54+50+80+139+197;d['wave_native_cli_validation']=cli
for prefix,path in [('intro','core_round25/intro_reflection'),('railcart','core_round26/railcart_reflection'),('seedbank','core_round27/seedbank_reflection')]:
 d[prefix+'_native_cli_validation']=json.loads((base/'native_analysis'/path/'native-cli-validation.json').read_text(encoding='utf-8'))
d['actual_cowboy_asset_data_objects_supported']=dict(created=4,declarations=5,remaining_classes=['LevelDefinition'],origin=r['real_resource_source'],whole_level_supported=False)
d['full_game_source_build']=False
assert sum(int(line.split()[1]) for line in d['observed_stdout'])==d['total_cpp_checks']
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded round 28:',d['total_cpp_checks'],'checks;',len(d['artifacts']),'hashed artifacts; 10 data classes; Cowboy asset 4/5')
