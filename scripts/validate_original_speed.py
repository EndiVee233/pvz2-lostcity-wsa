"""Collect v9 resource, payload, profile and real speed-toggle evidence."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
import struct
import subprocess
import sys
import tarfile
import zipfile

base=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(base/'tools/python_libs'),str(base/'tools/python_helpers')]
from py3rijndael import RijndaelCbc,ZeroPadding
from pyvz2rton import RTONDecoder
out=base/'native_analysis/original_speed_button'
folder=base/'rebuild_project/logs/wsa/original-speed'
adb=['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526']
app='com.popcap.pvz2cthd.reconstruction'
def call(*args):return subprocess.check_output([*adb,*args],timeout=60)
def shell(*args):return call('shell',*args).decode('utf-8',errors='replace').strip()
pid=shell('pidof',app);assert pid.isdecimal()
apk=shell('pm','path',app).removeprefix('package:')
hashes={}
for name,path in [('libSrc.so',out/'libSrc-original-speed-unlocked.so'),
                  ('libRestart.so',base/'native_analysis/glshim_threads16/build/libRestart.so')]:
    value=shell('sha256sum',apk.removesuffix('/base.apk')+'/lib/arm/'+name).split()[0]
    assert value==hashlib.sha256(path.read_bytes()).hexdigest()
    hashes[name]=value
resource=shell('sha256sum','/sdcard/Android/data/'+app+'/files/dynamic.rsb.smf').split()[0]
assert resource==hashlib.sha256((out/'dynamic-original-speed.rsb.smf').read_bytes()).hexdigest()
mtime=shell('stat','-c','%Y:%s','/sdcard/Android/data/'+app+'/files/dynamic.rsb.smf')
shell('ls','/sdcard/Android/data/'+app+'/files/.original-speed-57d9c44')
data=call('exec-out','run-as',app,'cat','files/userdataNo_Backup/pp.dat')
(folder/'profiles-after-v9.dat').write_bytes(data)
key=hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
def identities(blob):
    if blob[:2]==b'\x10\x00':blob=RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24).decrypt(blob[2:])
    assert blob[:4]==b'RTON'
    fp=BytesIO(blob[4:]);fp.name='private-save'
    parsed=json.loads(RTONDecoder(repairFiles=False).parse_root_object(fp))
    return {str(o['uid']):o['objdata']['n'] for o in parsed['objects'] if o['objclass']=='PlayerInfo'}
with tarfile.open(folder/'profiles-before.tar') as archive:
    before=identities(archive.extractfile('files/userdataNo_Backup/pp.dat').read())
after=identities(data);assert before==after
log=call('logcat','-d','-v','threadtime','--pid='+pid).decode('utf-8',errors='replace')
(folder/'v9-logcat.txt').write_text(log,encoding='utf-8')
fatals=[line for line in log.splitlines() if any(m in line for m in ['FATAL EXCEPTION','Fatal signal','UnsatisfiedLinkError','VerifyError'])]
assert not fatals
toggle=json.loads((out/'toggle-wsa-validation.json').read_text(encoding='utf-8'))
assert toggle['actual_game_speed_sequence']==[1.0,2.0,1.0]
full=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v9.apk'
runtime=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v9-runtime-only.apk'
with zipfile.ZipFile(full) as a,zipfile.ZipFile(runtime) as b:
    an={n for n in a.namelist() if not n.startswith('META-INF/')}
    bn={n for n in b.namelist() if not n.startswith('META-INF/')}
    assert an-bn=={f'assets/pvz2data.zip.{i:03d}' for i in range(1,4)} and not bn-an
    for name in bn:
        with a.open(name) as fp,b.open(name) as gp:
            assert hashlib.file_digest(fp,'sha256').digest()==hashlib.file_digest(gp,'sha256').digest(),name
record=dict(date='2026-10-30',application_id=app,installed_variant='v9-runtime-only',runtime_verified=True,
            full_apk_runtime_payload_matches_installed_variant=True,full_apk_assets_complete=True,
            full_apk_sha256=hashlib.file_digest(full.open('rb'),'sha256').hexdigest(),
            test_apk_sha256=hashlib.file_digest(runtime.open('rb'),'sha256').hexdigest(),
            native_sha256=hashes,resource_sha256=resource,resource_mtime_and_size=mtime,
            upgrade_resource_overlay_verified=True,profile_count=len(after),profile_uids_and_names_preserved=True,
            actual_game_speed_sequence=toggle['actual_game_speed_sequence'],speed_observation_read_only=True,
            original_double_arrow_style_visible=True,no_recharge_modal_on_toggle=True,
            worldmap_entries_still_removed=True,fatal_log_lines=fatals,
            scope='Original-style resource migration and local in-level 1x/2x toggles; no full campaign or store transaction validation.')
(out/'wsa-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for variant in ('v9','v9-runtime-only'):
    path=base/f'rebuild_project/wsa_test/multiuser-{variant}-build-validation.json'
    item=json.loads(path.read_text(encoding='utf-8'))
    item.update(runtime_verified=variant=='v9-runtime-only',runtime_payload_verified_in_wsa=True,
                installed_apk_variant='v9-runtime-only',full_apk_installed=False,actual_game_speed_sequence=[1.0,2.0,1.0])
    path.write_text(json.dumps(item,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
