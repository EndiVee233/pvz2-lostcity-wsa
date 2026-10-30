"""Validate installed v7 runtime payloads and preserve private profile evidence locally."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import zipfile

base = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(base/'tools/python_libs'),str(base/'tools/python_helpers')]
from py3rijndael import RijndaelCbc, ZeroPadding
from pyvz2rton import RTONDecoder
folder = base/'rebuild_project/logs/wsa/worldmap-entries'
adb = ['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526']
app = 'com.popcap.pvz2cthd.reconstruction'
def call(*args):return subprocess.check_output([*adb,*args],timeout=60)
def shell(*args):return call('shell',*args).decode('utf-8',errors='replace').strip()

pid = shell('pidof',app)
assert re.fullmatch(r'\d+',pid)
apk_path = shell('pm','path',app).removeprefix('package:')
native_root = apk_path.removesuffix('/base.apk')+'/lib/arm/'
expected = {'libSrc.so':base/'native_analysis/worldmap_entries/libSrc-no-worldmap-entries.so',
            'libRestart.so':base/'native_analysis/glshim_threads16/build/libRestart.so'}
native_hashes = {}
for name,path in expected.items():
    value = shell('sha256sum',native_root+name).split()[0]
    assert value == hashlib.sha256(path.read_bytes()).hexdigest()
    native_hashes[name] = value
private = call('exec-out','run-as',app,'cat','files/userdataNo_Backup/pp.dat')
(folder/'profiles-after.dat').write_bytes(private)
key = hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
def identities(blob):
    if blob[:2] == b'\x10\x00':blob = RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24).decrypt(blob[2:])
    assert blob[:4] == b'RTON'
    fp = BytesIO(blob[4:]); fp.name = 'private-save'
    data = json.loads(RTONDecoder(repairFiles=False).parse_root_object(fp))
    return {str(o['uid']):o['objdata']['n'] for o in data['objects'] if o['objclass']=='PlayerInfo'}
with tarfile.open(folder/'profiles-before.tar') as archive:
    before = identities(archive.extractfile('files/userdataNo_Backup/pp.dat').read())
after = identities(private)
assert before == after
log = call('logcat','-d','-v','threadtime','--pid='+pid).decode('utf-8',errors='replace')
(folder/'v7-logcat.txt').write_text(log,encoding='utf-8')
fatals = [line for line in log.splitlines() if any(marker in line for marker in
          ['FATAL EXCEPTION','Fatal signal','UnsatisfiedLinkError','VerifyError'])]
assert not fatals
workers = [tuple(map(int,row)) for row in re.findall(r'ASTC workers limit=(\d+) selected=(\d+) started=(\d+)',log)]
assert workers and all(row[0] == 16 for row in workers)
full = base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v7.apk'
runtime = base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v7-runtime-only.apk'
with zipfile.ZipFile(full) as a,zipfile.ZipFile(runtime) as b:
    full_names = {name for name in a.namelist() if not name.startswith('META-INF/')}
    small_names = {name for name in b.namelist() if not name.startswith('META-INF/')}
    assert full_names-small_names == {f'assets/pvz2data.zip.{i:03d}' for i in range(1,4)}
    assert not small_names-full_names
    for name in sorted(small_names):
        with a.open(name) as fp,b.open(name) as gp:
            assert hashlib.file_digest(fp,'sha256').digest() == hashlib.file_digest(gp,'sha256').digest(),name
record = dict(date='2026-10-30',application_id=app,installed_variant='v7-runtime-only',
              runtime_verified=True,full_apk_runtime_payload_matches_installed_test_variant=True,
              full_apk_assets_complete=True,installed_test_reuses_existing_extracted_resources=True,
              full_apk_sha256=hashlib.file_digest(full.open('rb'),'sha256').hexdigest(),
              runtime_test_apk_sha256=hashlib.file_digest(runtime.open('rb'),'sha256').hexdigest(),
              native_sha256=native_hashes,profile_count=len(after),profile_uids_and_names_preserved=True,
              visual_checks={'lottery_removed':True,'recharge_removed':True,'gemreturn_removed':True,
                             'plant_trial_removed':True,'gems_display':18,'coins_display':5880,
                             'after_four_old_position_taps_no_dialog':True},
              glshim_thread_limit_observed=16,glshim_worker_log_count=len(workers),fatal_log_lines=fatals,
              scope='Menu/world-map rendering and old-entry-position taps only; no purchase or full campaign tests.')
(base/'native_analysis/worldmap_entries/wsa-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for variant in ('v7','v7-runtime-only'):
    path = base/f'rebuild_project/wsa_test/multiuser-{variant}-build-validation.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(runtime_payload_verified_in_wsa=True,installed_apk_variant='v7-runtime-only',
                full_apk_installed=False,removed_worldmap_entries=['lottery','recharge','60x gem return','plant trial (植物奇遇)'])
    data['runtime_verified'] = variant == 'v7-runtime-only'
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
