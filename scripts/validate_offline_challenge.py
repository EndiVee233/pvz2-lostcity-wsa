"""Check installed payload, complete APK parity and private save observations."""
from pathlib import Path
import hashlib,json,tarfile,zipfile
from observe_offline_challenge import base,folder,call,decode,snapshot,challenge_state,app
out=base/'native_analysis/offline_challenge'
def shell(*args):return call('shell',*args).decode('utf-8',errors='replace').strip()
pid=shell('pidof',app);assert pid.isdecimal()
apk=shell('pm','path',app).removeprefix('package:')
native={}
for name,path in [('libSrc.so',out/'libSrc-offline-challenge.so'),
 ('libRestart.so',base/'native_analysis/glshim_threads16/build/libRestart.so')]:
 value=shell('sha256sum',apk.removesuffix('/base.apk')+'/lib/arm/'+name).split()[0]
 assert value==hashlib.sha256(path.read_bytes()).hexdigest()
 native[name]=value
resource=shell('sha256sum','/sdcard/Android/data/'+app+'/files/dynamic.rsb.smf').split()[0]
assert resource=='0aae11cf23e05377026323816f6e458264bdc193b312177bca6824589fa1d29f'
with tarfile.open(folder/'profiles-before.tar') as archive:
 before=decode(archive.extractfile('files/userdataNo_Backup/pp.dat').read())
after=snapshot('verified-final')
def identities(parsed):return {str(o['uid']):o['objdata']['n'] for o in parsed['objects'] if o['objclass']=='PlayerInfo'}
assert identities(before)==identities(after)
states=[]
for name in ('devil-paused','after-garg','after-yeti-start'):
 parsed=json.loads((folder/(name+'.json')).read_text(encoding='utf-8'))
 states.append(challenge_state(parsed)[1])
assert [state['level'] for state in states]==['festival_lv3_easy','festival_lv1_easy','festival_lv2_easy']
assert all(s['counts']==dict(yeti=1,gargantuar=1,devil=1) and s['reward_seed_count']==15 for s in states)
start=json.loads((folder/'devil-paused.json').read_text(encoding='utf-8'))
assert start['objects'][1]['objdata']['lfprii']==after['objects'][1]['objdata']['lfprii']
assert all(s['coins']==5880 and s['gems']==18 for s in states)
log=call('logcat','-d','-v','threadtime','--pid='+pid).decode('utf-8',errors='replace')
(folder/'final-logcat.txt').write_text(log,encoding='utf-8')
fatals=[line for line in log.splitlines() if any(m in line for m in ('FATAL EXCEPTION','Fatal signal','UnsatisfiedLinkError','VerifyError'))]
assert not fatals
full=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v10.apk'
runtime=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v10-runtime-only.apk'
with zipfile.ZipFile(full) as a,zipfile.ZipFile(runtime) as b:
 an={n for n in a.namelist() if not n.startswith('META-INF/')};bn={n for n in b.namelist() if not n.startswith('META-INF/')}
 assert an-bn=={f'assets/pvz2data.zip.{i:03d}' for i in range(1,4)} and not bn-an
 for name in bn:
  with a.open(name) as fp,b.open(name) as gp:assert hashlib.file_digest(fp,'sha256').digest()==hashlib.file_digest(gp,'sha256').digest(),name
patch=json.loads((out/'patch-validation.json').read_text(encoding='utf-8'))
attempts=json.loads((out/'attempt-validation.json').read_text(encoding='utf-8'))
record=dict(date='2026-10-30',application_id=app,installed_variant='v10-runtime-only',
 runtime_verified=True,full_apk_installed=False,full_apk_runtime_payload_matches_installed_variant=True,
 full_apk_assets_complete=True,full_apk_sha256=hashlib.file_digest(full.open('rb'),'sha256').hexdigest(),
 test_apk_sha256=hashlib.file_digest(runtime.open('rb'),'sha256').hexdigest(),native_sha256=native,
 resource_sha256=resource,profile_count=len(identities(after)),profile_uids_and_names_preserved=True,
 challenge_modes_loaded=['devil','gargantuar','yeti'],normal_difficulty_levels=[s['level'] for s in states],
 daily_counts_each_mode=1,same_day_reentry_does_not_refill=True,challenge_seed_records_preserved_across_restart=True,
 no_test_currency_spent=True,profile_tutorial_state_unchanged_by_submenu_patch=True,
 arm_cases_passed=patch['arm_cases_passed']+attempts['arm_cases_passed'],
 complete_victory_and_reward_collection_verified=False,hard_and_legend_difficulties_runtime_verified=False,
 fatal_log_lines=fatals,scope='Normal challenge levels loaded offline; original victory/reward paths retained, but a full victory/reward collection was not completed.')
(out/'wsa-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
for variant in ('v10','v10-runtime-only'):
 path=base/f'rebuild_project/wsa_test/multiuser-{variant}-build-validation.json'
 item=json.loads(path.read_text(encoding='utf-8'));item.update(runtime_verified=variant.endswith('runtime-only'),
 runtime_payload_verified_in_wsa=True,installed_apk_variant='v10-runtime-only',full_apk_installed=False,
 offline_challenge_modes_loaded=record['challenge_modes_loaded'],full_victory_reward_verified=False)
 path.write_text(json.dumps(item,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
