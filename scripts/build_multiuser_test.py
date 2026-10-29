"""Build an isolated offline WSA candidate with only the proven menu patch."""
from pathlib import Path
import zipfile,shutil,re,subprocess,json,hashlib,sys
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project';out=p/'wsa_test'
source=out/'PvZ2-reconstruction-offline-v2.apk'
tag=sys.argv[1] if len(sys.argv)>1 else 'v1'
assert re.fullmatch(r'v[12345]',tag)
native=base/('native_analysis/startup_dialogs/libSrc-no-startup-dialogs.so' if tag=='v5' else 'native_analysis/multiuser/fixes/libSrc-multiuser-fixed.so' if tag!='v1' else 'native_analysis/multiuser/libSrc-multiuser.so')
assert native.exists(),'Run restore_multiuser_entry.py first'
unsigned=out/('PvZ2-reconstruction-multiuser-'+tag+'-unsigned.apk')
aligned=out/('PvZ2-reconstruction-multiuser-'+tag+'-aligned.apk')
signed=out/('PvZ2-reconstruction-multiuser-'+tag+'.apk')
with zipfile.ZipFile(source) as src,zipfile.ZipFile(unsigned,'w',allowZip64=True) as dst:
 for info in src.infolist():
  if re.fullmatch(r'META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))',info.filename,re.I):continue
  if info.filename=='lib/armeabi/libSrc.so':dst.writestr(info,native.read_bytes());continue
  if tag in ('v3','v4','v5') and info.filename=='lib/armeabi/libRestart.so':dst.writestr(info,(base/'native_analysis/multiuser/fixes/libRestart-cache-fixed.so').read_bytes());continue
  with src.open(info) as a,dst.open(info,'w') as b:shutil.copyfileobj(a,b,1024*1024)
java='K:/pvz2-tools/jdk21/bin/java.exe';vm=['-Xms32m','-Xmx768m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2']
def run(args,name):
 with (p/'logs/wsa'/name).open('wb') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
run([str(p/'tools/zipalign.exe'),'-f','4',str(unsigned),str(aligned)],'multiuser-align.txt')
run([java,*vm,'-jar',str(p/'tools/apksigner.jar'),'sign','--ks',str(p/'keys/rebuild-debug.jks'),'--ks-key-alias','rebuild-debug','--ks-pass','pass:android','--key-pass','pass:android','--min-sdk-version','9','--out',str(signed),str(aligned)],'multiuser-sign.txt')
run([java,*vm,'-jar',str(p/'tools/apksigner.jar'),'verify','--verbose',str(signed)],'multiuser-sign-verify.txt')
run([str(p/'tools/zipalign.exe'),'-c','4',str(signed)],'multiuser-align-verify.txt')
with zipfile.ZipFile(source) as a,zipfile.ZipFile(signed) as b:
 changed=[]
 for name in a.namelist():
  if name.startswith('META-INF/'):continue
  if hashlib.sha256(a.read(name)).digest()!=hashlib.sha256(b.read(name)).digest():changed.append(name)
 assert set(changed)==({'lib/armeabi/libSrc.so','lib/armeabi/libRestart.so'} if tag in ('v3','v4','v5') else {'lib/armeabi/libSrc.so'}),changed
record={'source_offline_apk_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),
 'test_apk_sha256':hashlib.file_digest(signed.open('rb'),'sha256').hexdigest(),
 'changed_payload_entries':changed,'offline_manifest_preserved':True,'isolated_application_id_preserved':True,
 'runtime_verified':False}
(out/('multiuser-'+tag+'-build-validation.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
