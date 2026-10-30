"""Read-only WSA installed-code, save-identity and complete APK parity checks."""
import hashlib,json,struct,tarfile,zipfile
from observe_offline_challenge import base,call,app,decode,number
out=base/'native_analysis/no_recharge_gift'
private=base/'rebuild_project/logs/wsa/no-recharge-gift'
pid=call('shell','pidof',app).decode().strip();assert pid.isdecimal()
maps=call('shell','run-as',app,'cat',f'/proc/{pid}/maps').decode()
row=next(l.split() for l in maps.splitlines() if l.endswith('/libSrc.so') and int(l.split()[2],16)==0)
load=int(row[0].split('-')[0],16)
code=call('exec-out','run-as',app,'dd',f'if=/proc/{pid}/mem','bs=1',f'skip={load+0x2204b0}','count=4','status=none')
assert code==bytes.fromhex('1eff2fe1'),code.hex()
installed=call('shell','pm','path',app).decode().strip().removeprefix('package:')
native=call('shell','sha256sum',installed.removesuffix('/base.apk')+'/lib/arm/libSrc.so').decode().split()[0]
assert native==hashlib.sha256((out/'libSrc-no-recharge-gift.so').read_bytes()).hexdigest()
with tarfile.open(private/'profiles-before.tar') as t:before=decode(t.extractfile('files/userdataNo_Backup/pp.dat').read())
afterraw=call('exec-out','run-as',app,'cat','files/userdataNo_Backup/pp.dat');(private/'profiles-after.dat').write_bytes(afterraw)
after=decode(afterraw)
def profiles(d):return {str(o['uid']):(o['objdata']['n'],o['objdata']['c'],o['objdata']['gg']) for o in d['objects'] if o['objclass']=='PlayerInfo'}
bp,ap=profiles(before),profiles(after)
assert bp.keys()==ap.keys() and all(bp[k][0]==ap[k][0] and bp[k][2]==ap[k][2] for k in bp)
currency=[dict(coins_before=number(bp[k][1]),coins_after=number(ap[k][1]),gems_before=bp[k][2],gems_after=ap[k][2]) for k in bp]
full=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v11.apk'
runtime=base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v11-runtime-only.apk'
with zipfile.ZipFile(full) as a,zipfile.ZipFile(runtime) as b:
 an={n for n in a.namelist() if not n.startswith('META-INF/')};bn={n for n in b.namelist() if not n.startswith('META-INF/')}
 assert an-bn=={f'assets/pvz2data.zip.{i:03d}' for i in range(1,4)} and not bn-an
 for name in bn:
  with a.open(name) as x,b.open(name) as y:assert hashlib.file_digest(x,'sha256').digest()==hashlib.file_digest(y,'sha256').digest(),name
log=call('logcat','-d','-v','threadtime','--pid='+pid).decode(errors='replace');(private/'logcat.txt').write_text(log,encoding='utf-8')
fatal=[l for l in log.splitlines() if any(k in l for k in ['Fatal signal','FATAL EXCEPTION','UnsatisfiedLinkError'])];assert not fatal
record=dict(date='2026-10-30',installed_variant='v11-runtime-only',startup_verified=True,
            installed_native_sha256=native,live_spawner_entry_bytes=code.hex(),profile_count=len(profiles(after)),
            profile_names_uids_preserved=True,gems_preserved=True,currency_observations=currency,full_runtime_common_payloads_identical=True,
            full_apk_sha256=hashlib.file_digest(full.open('rb'),'sha256').hexdigest(),
            runtime_apk_sha256=hashlib.file_digest(runtime.open('rb'),'sha256').hexdigest(),
            arm_cases_passed=72,random_drop_long_session_verified=False,fatal_log_lines=fatal)
(out/'wsa-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
