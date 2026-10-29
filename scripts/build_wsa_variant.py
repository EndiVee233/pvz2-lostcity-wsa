from pathlib import Path
import zipfile,shutil,re,subprocess,json,hashlib,struct,sys
base=Path(__file__).resolve().parents[1];project=base/'rebuild_project';out=project/'wsa_test';logs=project/'logs/wsa'
source=project/'output/PvZ2-LostCity-1.7.5-rebuilt.apk'
offline='--offline' in sys.argv[2:]
with zipfile.ZipFile(out/('offline-manifest-linked.apk' if offline else 'manifest-linked.apk')) as z:manifest=z.read('AndroidManifest.xml')
tag=sys.argv[1] if len(sys.argv)>1 else 'v2'
assert re.fullmatch(r'[a-zA-Z0-9_-]+',tag)
unsigned=out/('PvZ2-reconstruction-'+tag+'-unsigned.apk');aligned=out/('PvZ2-reconstruction-'+tag+'-aligned.apk');signed=out/('PvZ2-reconstruction-'+tag+'.apk')
with zipfile.ZipFile(source) as src:original_resources=src.read('resources.arsc')
resources=bytearray(original_resources);offset=struct.unpack_from('<H',resources,2)[0];patched_packages=[]
while offset<len(resources):
    kind,header,size=struct.unpack_from('<HHI',resources,offset)
    if kind==0x200 and struct.unpack_from('<I',resources,offset+8)[0]==0x7f:
        old=bytes(resources[offset+12:offset+268]);new='com.popcap.pvz2cthd.reconstruction'.encode('utf-16le')
        resources[offset+12:offset+268]=new+b'\0'*(256-len(new));patched_packages.append({'offset':offset+12,'original':old.hex()})
    offset+=size
assert len(patched_packages)==1
with zipfile.ZipFile(source) as src,zipfile.ZipFile(unsigned,'w',allowZip64=True) as dst:
    for info in src.infolist():
        if re.fullmatch(r'META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))',info.filename,re.I):continue
        if info.filename=='AndroidManifest.xml':dst.writestr(info,manifest);continue
        if info.filename=='resources.arsc':dst.writestr(info,resources);continue
        with src.open(info) as a,dst.open(info,'w') as b:shutil.copyfileobj(a,b,1024*1024)
java='K:/pvz2-tools/jdk21/bin/java.exe';vm=['-Xms32m','-Xmx768m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2']
def run(args,log):
    with (logs/log).open('wb') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
run([str(project/'tools/zipalign.exe'),'-f','4',str(unsigned),str(aligned)],'variant-align.txt')
run([java,*vm,'-jar',str(project/'tools/apksigner.jar'),'sign','--ks',str(project/'keys/rebuild-debug.jks'),'--ks-key-alias','rebuild-debug','--ks-pass','pass:android','--key-pass','pass:android','--min-sdk-version','9','--out',str(signed),str(aligned)],'variant-sign.txt')
run([java,*vm,'-jar',str(project/'tools/apksigner.jar'),'verify','--verbose',str(signed)],'variant-verify.txt')
with zipfile.ZipFile(source) as src,zipfile.ZipFile(signed) as dst:
    names=[n for n in src.namelist() if n.endswith('.dex') or n.startswith('lib/')]
    for name in names:assert hashlib.sha256(src.read(name)).digest()==hashlib.sha256(dst.read(name)).digest(),name
    check=bytearray(dst.read('resources.arsc'))
    for patch in patched_packages:check[patch['offset']:patch['offset']+256]=bytes.fromhex(patch['original'])
    assert check==original_resources
record={'test_application_id':'com.popcap.pvz2cthd.reconstruction','source_apk_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),
        'offline_manifest_flag':offline,
        'test_apk_sha256':hashlib.file_digest(signed.open('rb'),'sha256').hexdigest(),'test_apk_size':signed.stat().st_size,
        'dex_and_native_libraries_match_source':True,'resource_table_only_7f_package_name_changed':True,'manifest_isolated_package_and_provider_authorities':True,
        'original_installed_package_uninstalled':False,'original_app_data_cleared':False}
(out/('variant-validation-'+tag+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
