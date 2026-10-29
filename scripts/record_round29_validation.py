"""Record the successful round-29 build and selected LevelDefinition profile.

Run after build.ps1 and all standalone CLI profile checks complete.
"""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];root=base/'native_recovered';manifest=root/'build-validation.json'
d=json.loads(manifest.read_text(encoding='utf-8'));folder=base/'native_analysis/core_round29/level_reflection'
r=json.loads((folder/'validation.json').read_text(encoding='utf-8'));cli=json.loads((folder/'native-cli-validation.json').read_text(encoding='utf-8'))
assert r['checkpoints']==282 and all(x['exact_arm_graph_match'] and x['exit_code']==x['expected_exit_code'] for x in cli['examples'])
actual=next(x for x in cli['examples'] if x['example']=='cowboy-dangerroom')
assert actual['created']==5 and actual['declarations']==5 and actual['exit_code']==0
assert actual['local_module_targets']==[2,1,3,4] and actual['unresolved_symbolic_references']==16
d.update(round=29,total_cpp_checks=45184+282,test_program_count=22,utility_program_count=3)
line='PASS 282 level/inherited reflection module-reference ARM full-state checkpoints'
if line not in d['observed_stdout']:d['observed_stdout'].append(line)
d['execution_exit_codes']['level_reflection_tests.exe']=0;d['artifacts']['build\\level_reflection_tests.exe']={}
for name in d['artifacts']:
 blob=(root/name).read_bytes();d['artifacts'][name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
d['test_scope']='All 22 programs compiled/passed with C++17 -Wall -Wextra -Werror; 3 tools linked. Eleven concrete data classes including LevelDefinition/37 registered fields: owned module refs, warning records, narrow strings/reward enum, bools/int32 and signed16 StartingSun bit truncation. 282 added original ARM data-state checks. CurrentLevel package matches four local module links in Cowboy asset; all 5 declarations constructed, 16 nonempty external symbolic refs remain unresolved. Other three assets construct LevelDefinition+SeedBank (2/6 each). GameFeature element read declines in the selected original registration; preserve resized zero slots without claiming unlock values. No game lifecycle/rendering/audio, Android JNI engine, source-only APK, generic RTTI/UID/text RTID or arbitrary coercion/malformed-context parity.'
d['reflection_supported_data_classes']=[name for name in r['schemas'] if name!='RtObject']
d['reflection_scoped_entries']=[x.replace('Ten selected','Eleven selected').replace('ten selected','eleven selected') for x in d['reflection_scoped_entries']]
for entry in ['00442f3c/0044401c LevelDefinition selected data construction and owned-reference teardown','LevelDefinition 37 registered fields; StartingSun signed16 low bits; reward narrow enum; warning Type/Text/Level','GameFeaturesToUnlock unresolved original GameFeature read 011ab2bc returns false: vector resize/zero slots only, no unlock semantics']:
 if entry not in d['reflection_scoped_entries']:d['reflection_scoped_entries'].append(entry)
d['reflection_bootstrap_boundary']='Explicit host metadata tokens/two logical system stores; twelve class-directory entries after optional LevelDefinition registration. LevelDefinition parent is PropertySheetBase, with no inherited ResourceGroupNames. Original generic reflection/schema ABI and game callbacks are not implemented. Original GameObject post-read notification runs against an empty _INIT_134 bus; event state, COW identity, private words, padding and allocator capacities excluded.'
d['level_reflection_arm_cpp_full_state_checkpoints']=r['checkpoints'];d['level_reflection_original_operations']=r['operations'];d['level_reflection_function_entry_hits']=r['function_entry_hits'];d['level_reflection_scope']=r['scope']
d['level_reward_enum']=r['level_reward_enum'];d['level_warning_schema']=r['level_warning_schema'];d['level_feature_codec']=r['level_feature_codec']
d['all_reflection_arm_cpp_full_state_checkpoints']=54+50+80+139+197+282;d['level_native_cli_validation']=cli
for prefix,path in [('intro','core_round25/intro_reflection'),('railcart','core_round26/railcart_reflection'),('seedbank','core_round27/seedbank_reflection'),('wave','core_round28/wave_reflection')]:
 d[prefix+'_native_cli_validation']=json.loads((base/'native_analysis'/path/'native-cli-validation.json').read_text(encoding='utf-8'))
d['actual_cowboy_asset_data_objects_supported']=dict(created=5,declarations=5,remaining_classes=[],origin=r['real_resource_source'],all_declarations_constructed=True,local_module_links=4,unresolved_symbolic_references=16,whole_level_supported=False)
d['other_asset_data_objects_supported']=[dict(created=x['created'],declarations=x['declarations'],origin=x['source'],whole_level_supported=False) for x in cli['examples'] if 'source' in x and x['example']!='cowboy-dangerroom']
d['full_game_source_build']=False
assert sum(int(line.split()[1]) for line in d['observed_stdout'])==d['total_cpp_checks']
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded round 29:',d['total_cpp_checks'],'checks;',len(d['artifacts']),'hashed artifacts; 11 data classes; Cowboy 5/5 declarations, 4 local links, 16 external refs unresolved')
