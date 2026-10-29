from pathlib import Path
import zipfile,struct,hashlib,json,re,time
from validate_bridge_api import validate as validate_bridge
from build_dex_reference_jar import Dex
base=Path(__file__).resolve().parents[1];project=base/'rebuild_project'
original=base/'PvZ2-LostCity-1.7.5.apk';built=project/'output/PvZ2-LostCity-1.7.5-rebuilt.apk'
def u32(data,offset):return struct.unpack_from('<I',data,offset)[0]
def uleb(data,offset):
    result=shift=0
    while True:
        value=data[offset];offset+=1;result|=(value&127)<<shift
        if value<128:return result,offset
        shift+=7
def dex_info(data):
    assert data[:4]==b'dex\n' and u32(data,32)==len(data)
    count=u32(data,56);off=u32(data,60);strings=[]
    for i in range(count):
        loc=u32(data,off+i*4);_,start=uleb(data,loc);end=data.index(0,start)
        strings.append(data[start:end].replace(b'\xc0\x80',b'\x00').decode('utf-8','surrogatepass'))
    types=[strings[u32(data,u32(data,68)+i*4)] for i in range(u32(data,64))]
    classes={types[u32(data,u32(data,100)+i*32)] for i in range(u32(data,96))}
    return {'classes':classes,'class_count':len(classes),'type_count':len(types),'method_ids':u32(data,88),'field_ids':u32(data,80),'version':data[4:7].decode()}
def stream_hash(archive,name):
    with archive.open(name) as f:return hashlib.file_digest(f,'sha256').hexdigest()
def resource_packages(data):
    kind,header,total=struct.unpack_from('<HHI',data,0);assert kind==2
    packages=[];offset=header
    while offset<total:
        kind,size_header,size=struct.unpack_from('<HHI',data,offset);assert size>=size_header and size>0
        if kind==0x200:
            name=data[offset+12:offset+268].decode('utf-16le').split('\0',1)[0]
            packages.append({'package':name,'id':hex(u32(data,offset+8))})
        offset+=size
    return packages
started=time.time();dex_records=[];unchanged=[];libraries=[];bridge=validate_bridge();popcap_classes=set();bootstrap_classes=set()
with zipfile.ZipFile(original) as src,zipfile.ZipFile(built) as dst:
    assert len(dst.namelist())==len(set(dst.namelist()))
    assert dst.testzip() is None
    for name in sorted(n for n in src.namelist() if re.fullmatch(r'classes\d*\.dex',n)):
        before=dex_info(src.read(name));after=dex_info(dst.read(name));assert before['classes']==after['classes'],name
        popcap_classes.update(c for c in before['classes'] if c.startswith('Lcom/popcap/'))
        if name=='classes8.dex':bootstrap_classes=after['classes']
        if name=='classes.dex':
            assert before['field_ids']==after['field_ids']
            a=set(Dex(src.read(name)).methods);b=set(Dex(dst.read(name)).methods)
            allowed=set()
            for record in bridge['classes']:
                owner='L'+record['class'].removesuffix('.smali')+';'
                for method in record.get('compiler_added_private_methods',[])+record.get('intentional_added_methods',[]):
                    signature=method.rsplit(' ',1)[-1];pos=signature.index('(')
                    allowed.add((owner,signature[:pos],signature[pos:]))
            assert a<=b and b-a==allowed,('unexpected method ID changes',b-a,a-b)
            constants=[]
            for data in (src.read(name),dst.read(name)):
                values={}
                for cls in Dex(data).classes():
                    if cls['name'].startswith('Lcom/popcap/pvz2cmhd/R$') or cls['name']=='Lcom/popcap/pvz2cmhd/BuildConfig;':
                        for (owner,field,typ),flags,value,_ in cls['fields']:
                            if flags&0x18==0x18 and typ in ('Z','B','C','S','I','J','Ljava/lang/String;'):
                                values[(owner,field,typ)]=value if value is not None or typ.startswith('L') else 0
                constants.append(values)
            assert constants[0]==constants[1], 'R/BuildConfig constant values changed'
            generated_resource_constants_checked=len(constants[0])
        elif name!='classes8.dex':
            assert before['method_ids']==after['method_ids'] and before['field_ids']==after['field_ids'],name
        dex_records.append({'name':name,'class_count':after['class_count'],'class_descriptors_preserved':True,
                            'original_method_ids':before['method_ids'],'rebuilt_method_ids':after['method_ids'],
                            'original_version':before['version'],'rebuilt_version':after['version']})
    for info in src.infolist():
        name=info.filename
        if info.is_dir() or re.fullmatch(r'classes\d*\.dex',name):continue
        if re.fullmatch(r'META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))',name,re.I):continue
        assert name in dst.namelist(),name
        a=stream_hash(src,name);b=stream_hash(dst,name);assert a==b,name
        unchanged.append(name)
        if name.startswith('lib/') and name.endswith('.so'):libraries.append({'file':name,'sha256':b,'compiled_from_source':False})
    resources=dst.read('resources.arsc');packages=resource_packages(resources)
    assert {p['id'] for p in packages}=={'0x66','0x7f'}
    assert dst.getinfo('resources.arsc').compress_type==zipfile.ZIP_STORED
    assert src.read('AndroidManifest.xml')==dst.read('AndroidManifest.xml')
    assert dst.read('classes8.dex')!=src.read('classes8.dex')
def read_log(path):
    raw=path.read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace')
verify=read_log(project/'logs/apksigner-verify.log')
for scheme in ['v1 scheme (JAR signing)','v2 scheme (APK Signature Scheme v2)','v3 scheme (APK Signature Scheme v3)']:
    assert f'Verified using {scheme}: true' in verify
console=read_log(project/'logs/windows-powershell-build.log')
assert 'Built and verified:' in console
apk_sha=hashlib.file_digest(original.open('rb'),'sha256').hexdigest();assert apk_sha=='1655512770c6968bd4216f0d66b8be955ce464c6e6881b5de6cbf776f245e1a4'
runtime_path=project/'wsa-runtime-validation.json'
runtime=json.loads(runtime_path.read_text(encoding='utf-8')) if runtime_path.exists() else {}
built_sha=hashlib.file_digest(built.open('rb'),'sha256').hexdigest()
runtime_matches=runtime.get('source_apk_sha256')==built_sha
runtime_payload_matches=False
runtime_tag=runtime.get('test_variant_tag','v3')
assert re.fullmatch(r'[a-zA-Z0-9_-]+',runtime_tag)
variant_path=project/('wsa_test/PvZ2-reconstruction-'+runtime_tag+'.apk')
if runtime and variant_path.exists():
    assert hashlib.file_digest(variant_path.open('rb'),'sha256').hexdigest()==runtime['installed_apk_sha256']
    with zipfile.ZipFile(built) as current,zipfile.ZipFile(variant_path) as tested:
        entries_match=True
        for name in current.namelist():
            if name.endswith('/') or name in ('AndroidManifest.xml','resources.arsc'):continue
            if re.fullmatch(r'META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))',name,re.I):continue
            if stream_hash(current,name)!=stream_hash(tested,name):entries_match=False;break
        original_table=current.read('resources.arsc');test_table=bytearray(tested.read('resources.arsc'))
        offset=struct.unpack_from('<H',test_table,2)[0];patches=0
        while offset<len(test_table):
            kind,header,size=struct.unpack_from('<HHI',test_table,offset)
            if kind==0x200 and u32(test_table,offset+8)==0x7f:
                test_table[offset+12:offset+268]=original_table[offset+12:offset+268];patches+=1
            offset+=size
        runtime_payload_matches=entries_match and patches==1 and test_table==original_table
behavior_path=project/'framework-behavior-validation.json';behavior_wsa_path=project/'framework-wsa-differential-validation.json'
desktop_behavior=False;wsa_behavior=False;probe_checks=None
if behavior_path.exists():
    behavior=json.loads(behavior_path.read_text(encoding='utf-8'))
    desktop_behavior=behavior['passed'] and all(hashlib.file_digest((project/name).open('rb'),'sha256').hexdigest()==sha for name,sha in behavior['source_sha256'].items())
if behavior_wsa_path.exists() and (runtime_matches or runtime_payload_matches):
    behavior=json.loads(behavior_wsa_path.read_text(encoding='utf-8'))
    wsa_behavior=behavior['passed'] and behavior['reconstructed_installed_apk_sha256']==runtime['installed_apk_sha256']
    if wsa_behavior:probe_checks=behavior.get('total_checks_per_target',behavior['runs']['reconstructed'][0]['checks'])
compiled_popcap={'L'+c['class'].removesuffix('.smali')+';' for c in bridge['classes']}|bootstrap_classes
legacy_switch='Lcom/popcap/SexyAppFramework/GooglePlayPurchaseDriver$11;'
assert popcap_classes==compiled_popcap|{legacy_switch}
result={'build_completed':True,'windows_powershell_entrypoint_build_completed':True,'signed_apk':str(built.relative_to(base)),
        'signed_apk_size':built.stat().st_size,'signed_apk_sha256':built_sha,
        'signature_schemes_verified':['v1','v2','v3'],'dex_files':dex_records,'total_classes':sum(d['class_count'] for d in dex_records),
        'java_bootstrap_compiled_classes':next(d['class_count'] for d in dex_records if d['name']=='classes8.dex'),
        'java_game_bridge_compiled_classes':bridge['reconstructed_classes'],'compile_only_stubs_packaged':False,
        'java_source_files':len(list((project/'src/bootstrap').rglob('*.java')))+len(list((project/'src/game_bridge').rglob('*.java'))),
        'main_dex_popcap_source_files':bridge['main_dex_popcap_source_files'],
        'all_main_dex_popcap_exported_java_files_in_build':bridge['all_main_dex_popcap_exported_java_files_in_build'],
        'popcap_namespace_total_classes':len(popcap_classes),'popcap_namespace_source_compiled_classes':len(compiled_popcap),
        'popcap_namespace_remaining_smali_classes':[legacy_switch],
        'compiler_added_private_enum_methods':bridge['compiler_added_private_enum_methods'],'native_method_declarations_preserved':bridge['native_methods_preserved'],
        'resource_and_build_constant_values_preserved':generated_resource_constants_checked,
        'framework_behavior_desktop_passed':desktop_behavior,'framework_behavior_wsa_differential_passed':wsa_behavior,'framework_probe_checks_per_run':probe_checks,
        'unchanged_non_dex_entries_verified':len(unchanged),'resource_packages':packages,'native_libraries':libraries,
        'original_manifest_preserved':True,'original_apk_sha256_unchanged':apk_sha,'complete_high_level_source':False,
        'native_game_engine_compiled_from_source':False,'resource_table_compiled_from_xml':False,
        'device_runtime_tested':runtime_matches or runtime_payload_matches,
        'runtime_source_archive_hash_matches':runtime_matches,'runtime_test_variant_payload_matches_current_build':runtime_payload_matches,
        'device_runtime_test_scope':runtime.get('test_scope','Isolated WSA variant; loading and welcome screen only') if runtime_matches or runtime_payload_matches else None,
        'offline_overlay_fix_verified':runtime.get('communication_overlay_removed',False) if runtime_matches or runtime_payload_matches else False,
        'local_profile_survived_cold_restart':runtime.get('local_profile_survived_cold_restart',False) if runtime_matches or runtime_payload_matches else False,
        'complete_gameplay_validated':False,
        'seconds':round(time.time()-started,1)}
(project/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['native_libraries','dex_files']},ensure_ascii=False,indent=2))
