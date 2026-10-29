"""Read-only inventory of actual APK dependencies and source-build milestones."""
import hashlib,json,re,struct,zipfile
from pathlib import Path
base=Path(__file__).resolve().parents[1]
out=base/'native_analysis/source_build_audit';out.mkdir(parents=True,exist_ok=True)
build=json.loads((base/'rebuild_project/validation.json').read_text(encoding='utf-8'))
native=json.loads((base/'native_recovered/build-validation.json').read_text(encoding='utf-8'))
apk=base/build['signed_apk']
with zipfile.ZipFile(apk) as z:
 libs=[];dex=[]
 original_apk=base/'PvZ2-LostCity-1.7.5.apk'
 resource_table_match=None
 if original_apk.is_file():
  with zipfile.ZipFile(original_apk) as original_zip:resource_table_match=hashlib.sha256(z.read('resources.arsc')).digest()==hashlib.sha256(original_zip.read('resources.arsc')).digest()
 for info in z.infolist():
  if info.filename.startswith('lib/') and info.filename.endswith('.so'):
   blob=z.read(info);original=base/'raw'/info.filename
   digest=hashlib.sha256(blob).hexdigest()
   libs.append(dict(path=info.filename,bytes=len(blob),sha256=digest,matches_original=original.is_file() and digest==hashlib.sha256(original.read_bytes()).hexdigest()))
  if re.fullmatch(r'classes\d*\.dex',info.filename):
   with z.open(info) as f:header=f.read(112)
   dex.append(dict(path=info.filename,classes=struct.unpack_from('<I',header,96)[0]))
sources={};classes={}
for folder in ['bootstrap','game_bridge']:
 sources[folder]=len(list((base/'rebuild_project/src'/folder).rglob('*.java')))
classes['bootstrap']=len(list((base/'rebuild_project/build/bootstrap-classes').rglob('*.class')))
classes['bridge']=len(list((base/'rebuild_project/build/bridge-classes').rglob('*.class')))
managed=sum(x['classes'] for x in dex);source_classes=sum(classes.values())
texts=[p.read_text(encoding='utf-8-sig') for p in (base/'rebuild_project/src/game_bridge').rglob('*.java')]
native_decls=sum(len(re.findall(r'(?m)^\s*(?:(?:public|private|protected|static|final|synchronized)\s+)*native\s+[^;]+;',t)) for t in texts)
loaders=[]
for p in (base/'rebuild_project/src').rglob('*.java'):
 for no,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
  if 'System.load' in line:loaders.append(dict(path=str(p.relative_to(base)),line=no,text=line.strip()))
cpps=list((base/'native_recovered/src').glob('*.cpp'));jni=[]
for p in cpps:
 for no,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if re.search(r'JNIEXPORT|JNI_OnLoad|Java_com_|ANativeActivity_onCreate',line):jni.append(dict(path=str(p.relative_to(base)),line=no,text=line.strip()))
full=json.loads((base/'native_analysis/core_round3/full_library/summary.json').read_text(encoding='utf-8'))
report=dict(apk=str(apk.relative_to(base)),apk_bytes=apk.stat().st_size,read_only=True,dex=dex,total_apk_classes=managed,source_java_files=sources,compiled_source_class_files=classes,compiled_source_classes=source_classes,source_class_inventory_percent=round(source_classes/managed*100,4),source_class_percent_scope='Class-count inventory only; not functional coverage or whole-game source completion. Third-party classes can be rebuilt/replaced rather than hand-restored.',popcap_namespace_from_validated_build=dict(total=build['popcap_namespace_total_classes'],source=build['popcap_namespace_source_compiled_classes']),native_method_declarations=native_decls,loaders=loaders,native_libraries=libs,original_native_libraries_retained=sum(x['matches_original'] for x in libs),original_libraries_replaced_by_recovered_build=0,native_cpp_translation_units=len(cpps),native_jni_entry_definitions=jni,native_host_build=dict(target=native['target'],checks=native['total_cpp_checks'],test_programs=native['test_program_count'],utilities=native['utility_program_count']),native_android_source_library_built=False,recovered_native_modules_packaged_into_apk=False,source_only_engine_boot_verified=False,source_only_level_run_verified=False,resource_table_compiled_from_xml=build['resource_table_compiled_from_xml'],binary_resource_table_matches_original=resource_table_match,decompiler_material=dict(targets=full['targets'],pseudocode_exports=full['exported_functions'],not_compilable_source=True),overall_completion_percent=None,overall_percent_reason='No validated function-weighted inventory of gameplay/renderer/audio/resource/RTTI systems; semantic operation counts and assertion counts cannot be divided by decompiler targets to infer completion.',milestones=dict(host_native_modules_build=True,plaintext_rton_navigation=True,android_engine_abi=False,original_libSrc_replaced=False,gameplay_renderer_audio_from_source=False,complete_source_apk=False))
report['bounded_reflection_data_classes']=native.get('reflection_supported_data_classes',[])
report['milestones']['bounded_factory_property_reference_chain']=bool(report['bounded_reflection_data_classes'])
report['bounded_object_scope']='Selected data-schema factory/properties/references only; no game methods or full-level object coverage'
report['bounded_resource_data_coverage']=native.get('actual_cowboy_asset_data_objects_supported')
(out/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('APK:',managed,'classes;',source_classes,'compiled source class files;',sum(sources.values()),'Java sources')
print('Native binaries:',len(libs),'; original-identical:',report['original_native_libraries_retained'],'; native declarations:',native_decls)
print('JNI definitions in recovered C++:',len(jni),'; actual library replacements: 0; Android source-only engine boot: not verified')
