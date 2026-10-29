"""Record the completed round-25 Zig build and original-ARM comparisons.

Run after native_recovered/build.ps1 succeeds and validate_intro_loader.py.
This records evidence; it does not substitute for compiling or running tests.
"""
import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];root=base/'native_recovered'
manifest=root/'build-validation.json';d=json.loads(manifest.read_text(encoding='utf-8'))
evidence=base/'native_analysis/core_round25'
f=json.loads((evidence/'rton_float/validation.json').read_text(encoding='utf-8'))
r=json.loads((evidence/'intro_reflection/validation.json').read_text(encoding='utf-8'))
cli=json.loads((evidence/'intro_reflection/native-cli-validation.json').read_text(encoding='utf-8'))
assert f['checkpoints']==3462 and r['checkpoints']==50
assert all(x['exact_arm_graph_match'] and x['exit_code']==x['expected_exit_code'] for x in cli['examples'])
d.update(round=25,total_cpp_checks=41256+f['checkpoints']+r['checkpoints'],test_program_count=18,utility_program_count=3)
for line in ['PASS 3462 RTON numeric/narrow-decimal float ARM bits/cursor checkpoints','PASS 50 inherited reflection factory/property/list/reference ARM full-state checkpoints']:
 if line not in d['observed_stdout']:d['observed_stdout'].append(line)
for name in ['rton_float_tests.exe','intro_reflection_tests.exe']:
 d['execution_exit_codes'][name]=0;d['artifacts']['build\\'+name]={}
for name in d['artifacts']:
 p=root/name;blob=p.read_bytes();d['artifacts'][name]=dict(bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
d['test_scope']='All 18 test programs compiled and passed with C++17 -Wall -Wextra -Werror; 3 tools linked. Adds 3462 float return/cursor checks and 50 selected inherited reflection full-state checkpoints. Seven concrete data schemas, mixed-class cycles and actual Cowboy DangerRoom partial load (1/5) match saved original ARM. Data only; generic reflection builder, remaining classes/UID/text RTID, event subscribers/game behavior, Android/JNI replacement and full source APK remain incomplete.'
d['reflection_supported_data_classes']=[name for name in r['schemas'] if name!='RtObject']
d['reflection_scoped_entries']=[
 '00254bf8 and six inherited factory initialized reflected data fields; no vtable/game methods',
 '011ed5fc version1/no explicit UID/seven selected concrete data classes',
 '011ead94 and 011b9bb0 selected inherited weak-reference/string-list/float/int read fields',
 '011b1de0 non-flags GroundEffectType narrow-text enum',
 '011b7180/011fb300/011f4c90 binary weak RTID read branches 0..3',
 '011f9ae8 numeric and common narrow decimal branches, float32 bits; wide/RTID/special-text excluded']
d['reflection_bootstrap_boundary']='Explicit host metadata tokens and two logical system stores, eight class-directory entries after optional intro registration. Original ARM executes real manager/schema initialization; host generic schema/symbol ABI is not restored. Original GameObject post-read event path executes against an empty bus seeded from _INIT_134; host data adapter has no event bus/game callbacks and event state is not compared.'
d['intro_reflection_arm_cpp_full_state_checkpoints']=r['checkpoints']
d['intro_reflection_original_operations']=r['operations']
d['intro_reflection_function_entry_hits']=r['function_entry_hits']
d['intro_reflection_schemas']=r['schemas']
d['intro_reflection_scope']=r['scope']
d['all_reflection_arm_cpp_full_state_checkpoints']=54+r['checkpoints']
d['rton_float_arm_cpp_bits_cursor_checkpoints']=f['checkpoints']
d['rton_float_partial_entry']='011f9ae8 numeric/narrow-decimal float32 getter; not counted as another completely restored function'
d['rton_float_scope']=f['scope']
d['intro_native_cli_validation']=cli
d['full_game_source_build']=False
manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sum(int(line.split()[1]) for line in d['observed_stdout'])==d['total_cpp_checks']
print('Recorded round',d['round'],':',d['total_cpp_checks'],'checks;',len(d['artifacts']),'hashed artifacts; 7 concrete data classes; actual level 1/5')
