"""Build an isolated offline WSA candidate with only the proven menu patch."""
from pathlib import Path
import zipfile,shutil,re,subprocess,json,hashlib,sys,copy
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project';out=p/'wsa_test'
source=out/'PvZ2-reconstruction-offline-v2.apk'
tag=sys.argv[1] if len(sys.argv)>1 else 'v1'
assert re.fullmatch(r'v(?:[1-9]|10|11)',tag)
runtime_only='--runtime-only' in sys.argv
assert not runtime_only or tag in ('v7','v8','v9','v10','v11')
if tag in ('v6','v7','v8','v9','v10','v11'):source=out/('PvZ2-reconstruction-multiuser-v'+str(int(tag[1:])-1)+'.apk')
native=base/('native_analysis/startup_dialogs/libSrc-no-startup-dialogs.so' if tag in ('v5','v6') else 'native_analysis/multiuser/fixes/libSrc-multiuser-fixed.so' if tag!='v1' else 'native_analysis/multiuser/libSrc-multiuser.so')
if tag in ('v7','v8'):native=base/'native_analysis/worldmap_entries/libSrc-no-worldmap-entries.so'
if tag=='v9':native=base/'native_analysis/original_speed_button/libSrc-original-speed-unlocked.so'
if tag=='v10':native=base/'native_analysis/offline_challenge/libSrc-offline-challenge.so'
if tag=='v11':native=base/'native_analysis/no_recharge_gift/libSrc-no-recharge-gift.so'
glshim=base/('native_analysis/glshim_threads16/build/libRestart.so' if tag in ('v6','v7','v8','v9','v10','v11') else 'native_analysis/multiuser/fixes/libRestart-cache-fixed.so')
speed=base/'native_analysis/original_speed_button'
assert native.exists(),'Run restore_multiuser_entry.py first'
variant=tag+('-runtime-only' if runtime_only else '')
unsigned=out/('PvZ2-reconstruction-multiuser-'+variant+'-unsigned.apk')
aligned=out/('PvZ2-reconstruction-multiuser-'+variant+'-aligned.apk')
signed=out/('PvZ2-reconstruction-multiuser-'+variant+'.apk')
omitted=[]
with zipfile.ZipFile(source) as src,zipfile.ZipFile(unsigned,'w',allowZip64=True) as dst:
 for info in src.infolist():
  info=copy.copy(info)
  if runtime_only and re.fullmatch(r'assets/pvz2data\.zip\.\d{3}',info.filename):omitted.append(info.filename);continue
  if re.fullmatch(r'META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))',info.filename,re.I):continue
  if info.filename=='lib/armeabi/libSrc.so':dst.writestr(info,native.read_bytes());continue
  if tag=='v8' and info.filename=='classes8.dex':dst.writestr(info,(speed/'bootstrap/dex/classes.dex').read_bytes());continue
  if tag=='v8' and re.fullmatch(r'assets/pvz2data\.zip\.\d{3}',info.filename):
   with (speed/Path(info.filename).name).open('rb') as a,dst.open(info,'w') as b:shutil.copyfileobj(a,b,1024*1024)
   continue
  if tag in ('v3','v4','v5','v6','v7','v8','v9','v10','v11') and info.filename=='lib/armeabi/libRestart.so':dst.writestr(info,glshim.read_bytes());continue
  with src.open(info) as a,dst.open(info,'w') as b:shutil.copyfileobj(a,b,1024*1024)
 if tag=='v8':dst.write(speed/'dynamic-original-speed.rsb.smf','assets/reconstruction/dynamic-original-speed.rsb.smf',compress_type=zipfile.ZIP_DEFLATED)
java='K:/pvz2-tools/jdk21/bin/java.exe';vm=['-Xms32m','-Xmx768m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2']
if tag in ('v6','v7','v8','v9','v10','v11'):vm[1]='-Xmx256m'
def run(args,name):
 with (p/'logs/wsa'/name).open('wb') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
run([str(p/'tools/zipalign.exe'),'-f','4',str(unsigned),str(aligned)],'multiuser-align.txt')
run([java,*vm,'-jar',str(p/'tools/apksigner.jar'),'sign','--ks',str(p/'keys/rebuild-debug.jks'),'--ks-key-alias','rebuild-debug','--ks-pass','pass:android','--key-pass','pass:android','--min-sdk-version','9','--out',str(signed),str(aligned)],'multiuser-sign.txt')
run([java,*vm,'-jar',str(p/'tools/apksigner.jar'),'verify','--verbose',str(signed)],'multiuser-sign-verify.txt')
run([str(p/'tools/zipalign.exe'),'-c','4',str(signed)],'multiuser-align-verify.txt')
with zipfile.ZipFile(source) as a,zipfile.ZipFile(signed) as b:
 changed=[]
 for name in a.namelist():
  if name.startswith('META-INF/') or name in omitted:continue
  with a.open(name) as before,b.open(name) as after:
   if hashlib.file_digest(before,'sha256').digest()!=hashlib.file_digest(after,'sha256').digest():changed.append(name)
 if tag=='v8':
  assert 'classes8.dex' in changed and set(changed)<={'classes8.dex',*[f'assets/pvz2data.zip.{i:03d}' for i in range(1,4)]},changed
  assert set(b.namelist())-set(a.namelist())=={'assets/reconstruction/dynamic-original-speed.rsb.smf'}
 else:assert set(changed)==({'lib/armeabi/libRestart.so'} if tag=='v6' else {'lib/armeabi/libSrc.so','lib/armeabi/libRestart.so'} if tag in ('v3','v4','v5') else {'lib/armeabi/libSrc.so'}),changed
 assert not runtime_only or len(omitted)==3
record={'source_offline_apk_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),
 'test_apk_sha256':hashlib.file_digest(signed.open('rb'),'sha256').hexdigest(),
 'changed_payload_entries':changed,'offline_manifest_preserved':True,'isolated_application_id_preserved':True,
 'runtime_verified':False}
if tag=='v7':record.update(source_variant='v6',source_apk_sha256=record['source_offline_apk_sha256'],max_astc_threads=16,removed_worldmap_entries=['lottery','recharge','60x gem return','plant trial (植物奇遇)'],requires_existing_extracted_resources=runtime_only,omitted_resource_parts=omitted)
if tag=='v8':record.update(source_variant='v7',source_apk_sha256=record['source_offline_apk_sha256'],max_astc_threads=16,worldmap_entry_patch_preserved=True,original_speed_patch_commit='57d9c4490c83d8c6911fafbedc6d42d9accff805',existing_resource_update_packaged=True,added_payload_entries=['assets/reconstruction/dynamic-original-speed.rsb.smf'],requires_existing_extracted_resources=runtime_only,omitted_resource_parts=omitted)
if tag=='v9':record.update(source_variant='v8',source_apk_sha256=record['source_offline_apk_sha256'],max_astc_threads=16,worldmap_entry_patch_preserved=True,original_speed_style_preserved=True,local_speed_recharge_gate_removed=True,existing_resource_update_packaged=True,requires_existing_extracted_resources=runtime_only,omitted_resource_parts=omitted)
if tag=='v10':record.update(source_variant='v9',source_apk_sha256=record['source_offline_apk_sha256'],max_astc_threads=16,worldmap_entry_patch_preserved=True,original_speed_style_preserved=True,local_speed_recharge_gate_removed=True,offline_challenge_candidate=True,requires_existing_extracted_resources=runtime_only,omitted_resource_parts=omitted)
if tag=='v11':record.update(source_variant='v10',zombie_recharge_gift_drop_disabled=True,requires_existing_extracted_resources=runtime_only,omitted_resource_parts=omitted)
(out/('multiuser-'+variant+'-build-validation.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
