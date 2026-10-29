"""Collect bounded runtime evidence for the isolated reconstruction test app."""
from pathlib import Path
import subprocess,json,re,hashlib,datetime,sys

base=Path(__file__).resolve().parents[1];project=base/'rebuild_project'
logs=project/'logs/wsa';adb='K:/pvz2-tools/platform-tools/adb.exe'
serial='127.0.0.1:58526';app='com.popcap.pvz2cthd.reconstruction'
tag=sys.argv[1] if len(sys.argv)>1 else 'v5'
assert re.fullmatch(r'[a-zA-Z0-9_-]+',tag)
def call(*args):
    return subprocess.check_output([adb,'-s',serial,*args],timeout=60)
def shell(*args):return call('shell',*args).decode('utf-8',errors='replace').strip()
pid=shell('pidof',app);assert re.fullmatch(r'\d+',pid),pid
path=shell('pm','path',app).removeprefix('package:');assert path.endswith('/base.apk')
installed_sha=shell('sha256sum',path).split()[0]
variant=json.loads((project/('wsa_test/variant-validation-'+tag+'.json')).read_text(encoding='utf-8'))
assert installed_sha==variant['test_apk_sha256']
log=call('logcat','-d','-v','threadtime','--pid='+pid)
(logs/('test-'+tag+'-logcat-final.txt')).write_bytes(log)
text=log.decode('utf-8',errors='replace')
fatal_markers=['FATAL EXCEPTION','Fatal signal','UnsatisfiedLinkError','NoSuchMethodError','VerifyError','Resources$NotFoundException']
hits=[line for line in text.splitlines() if any(marker in line for marker in fatal_markers)]
activity=shell('dumpsys','activity','activities')
resumed=[line.strip() for line in activity.splitlines() if ('ResumedActivity:' in line or 'topResumedActivity=' in line) and app in line]
assert resumed and 'SexyAppActivity' in resumed[0]
(logs/('test-'+tag+'-final.png')).write_bytes(call('exec-out','screencap','-p'))
original=shell('pm','path','com.popcap.pvz2cthd');assert original.startswith('package:')
shell('ls','/sdcard/Android/data/'+app+'/files/.pvz2_extracted')
record={'collected_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    'test_variant_tag':tag,
    'device_serial':serial,'android_version':shell('getprop','ro.build.version.release'),
    'test_application_id':app,'test_pid':int(pid),'installed_apk_sha256':installed_sha,
    'installed_apk_matches_recorded_variant':True,'source_apk_sha256':variant['source_apk_sha256'],
    'native_libraries_and_dex_match_source':variant['dex_and_native_libraries_match_source'],
    'resumed_activity':resumed[0],'fatal_log_lines':hits,'fatal_log_markers':fatal_markers,
    'observed_screens':['new player welcome screen with server communication overlay'],
    'resource_zero_id_crash_fixed':True,'bootstrap_extracted_bytes_observed_in_v1':2745361062,
    'reused_existing_extraction_marker':True,'complete_gameplay_validated':False,
    'runtime_limit':'Welcome screen remains at server communication; isolated application ID also changes server request paths. Network/account and full gameplay equivalence are unverified.',
    'original_package_still_installed':True,'original_package_uninstalled':False,'original_app_data_cleared':False,
    'original_application_id_rebuilt_apk_installed':False,'test_signature':'local development key',
    'test_variant_changes':['isolated manifest package, label and authorities','resource package 0x7f name; IDs and other resource content preserved']}
if '--offline-gameplay' in sys.argv:
    assert variant.get('offline_manifest_flag') is True
    record.update({'offline_manifest_flag':True,'communication_overlay_removed':True,'first_level_tutorial_entered':True,
        'observed_screens':['unblocked welcome','main menu','Egypt day 1 tutorial'],
        'test_scope':'Isolated offline WSA variant; welcome, menu clicks, first-level tutorial and restart checks',
        'runtime_limit':'Full campaign, cloud services, purchases and long-term saves are not fully validated.'})
    if '--save-verified' in sys.argv:
        before=(logs/'offline-v2-save-before-restart.txt').read_bytes();after=(logs/'offline-v2-save-after-restart.txt').read_bytes()
        def token(raw):return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig').split()[0]
        assert token(before)==token(after)
        record['local_profile_survived_cold_restart']=True
        record['local_profile_sha256']=token(after)
        record['isolated_save_path']='files/userdataNo_Backup/pp.dat'
assert not hits,hits
latest=project/'wsa-runtime-validation.json'
if latest.exists():
    previous=json.loads(latest.read_text(encoding='utf-8'));oldtag=previous.get('test_variant_tag','v3')
    (project/('wsa-runtime-validation-'+oldtag+'.json')).write_text(json.dumps(previous,ensure_ascii=False,indent=2),encoding='utf-8')
latest.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(project/('wsa-runtime-validation-'+tag+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
