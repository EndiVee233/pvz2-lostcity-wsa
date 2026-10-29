"""Run the exact same behavior probe on original and reconstructed DEX in WSA."""
from pathlib import Path
import subprocess,zipfile,json,hashlib,os,sys
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project';logs=p/'logs/wsa'
adb='K:/pvz2-tools/platform-tools/adb.exe';java='K:/pvz2-tools/jdk21/bin/java.exe'
prefix=[adb,'-s','127.0.0.1:58526'];vm=['-Xms16m','-Xmx256m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2']
tag=sys.argv[1] if len(sys.argv)>1 else 'v5'
assert tag.replace('-','').replace('_','').isalnum()
jar=p/'build/framework-probe.jar';dex=p/'build/framework-probe-dex';dex.mkdir(exist_ok=True)
classes=p/'build/framework-probe-classes'
with zipfile.ZipFile(jar,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for f in (classes/'com').rglob('*.class'):z.write(f,f.relative_to(classes).as_posix())
compile=subprocess.run([java,*vm,'-cp',str(p/'tools/d8-stable.jar'),'com.android.tools.r8.D8','--force-passthrough-assertions',
    '--min-api','9','--lib',str(p/'tools/android-30.jar'),'--classpath',str(p/'tools/original-dex-api.jar'),'--output',str(dex),str(jar)],
    stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(logs/'framework-probe-d8.log').write_bytes(compile.stdout);compile.check_returncode()
subprocess.run([*prefix,'push',str(dex/'classes.dex'),'/data/local/tmp/pvz2-framework-probe.dex'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
original_dex=base/'raw/classes.dex'
with zipfile.ZipFile(base/'PvZ2-LostCity-1.7.5.apk') as source:
    baseline_hash=hashlib.sha256(source.read('classes.dex')).hexdigest()
assert hashlib.file_digest(original_dex.open('rb'),'sha256').hexdigest()==baseline_hash
subprocess.run([*prefix,'push',str(original_dex),'/data/local/tmp/pvz2-original-classes.dex'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
assert subprocess.check_output([*prefix,'shell','sha256sum','/data/local/tmp/pvz2-original-classes.dex']).decode().split()[0]==baseline_hash
results={}
for label,app in [('original','com.popcap.pvz2cthd'),('reconstructed','com.popcap.pvz2cthd.reconstruction')]:
    if label=='original':path='/data/local/tmp/pvz2-original-classes.dex'
    else:
        path=subprocess.check_output([*prefix,'shell','pm','path',app],timeout=30).decode().strip().removeprefix('package:')
        assert path.startswith('/data/app/') and path.endswith('/base.apk')
        installed_sha=subprocess.check_output([*prefix,'shell','sha256sum',path]).decode().split()[0]
        assert installed_sha==json.loads((p/('wsa_test/variant-validation-'+tag+'.json')).read_text(encoding='utf-8'))['test_apk_sha256']
    rows=[]
    for probe_class in ['com.popcap.SexyAppFramework.FrameworkProbe','com.popcap.util.ServicesProbe']:
        mode='-da'
        run=subprocess.run([*prefix,'shell','env','CLASSPATH=/data/local/tmp/pvz2-framework-probe.dex:'+path,
            'app_process',mode,'/system/bin',probe_class],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=40)
        (logs/('probe-'+tag+'-'+label+'-'+probe_class.rsplit('.',1)[-1]+'.log')).write_bytes(run.stdout)
        if run.returncode:print(run.stdout.decode('utf-8',errors='replace'))
        run.check_returncode();lines=run.stdout.decode('utf-8',errors='replace').splitlines();row=json.loads(next(s for s in reversed(lines) if s.startswith('{"passed":')))
        assert row['passed'];row['probe_class']=probe_class;rows.append(row)
    results[label]=rows
assert results['original']==results['reconstructed'],results
record={'passed':True,'same_probe_results_on_original_and_reconstructed_dex':True,'runs':results,
        'test_variant_tag':tag,'total_checks_per_target':sum(row['checks'] for row in results['reconstructed']),
        'baseline':'classes.dex extracted from input APK, not the independently installed original app',
        'original_main_dex_sha256':baseline_hash,'reconstructed_installed_apk_sha256':installed_sha,
        'android_assertion_note':'Android probes use default disabled assertions; enabled/disabled framework behavior is separately checked on desktop JVM',
        'probe_dex_sha256':hashlib.file_digest((dex/'classes.dex').open('rb'),'sha256').hexdigest(),
        'test_only_native_callback_overrides':True,'test_log_adapter_packaged_in_probe':False,
        'test_harness_or_compile_only_api_packaged_in_app':False,'full_gameplay_validated':False}
latest=p/'framework-wsa-differential-validation.json'
if latest.exists():
    previous=json.loads(latest.read_text(encoding='utf-8'));oldtag=previous.get('test_variant_tag','v4')
    (p/('framework-wsa-differential-validation-'+oldtag+'.json')).write_text(json.dumps(previous,indent=2),encoding='utf-8')
latest.write_text(json.dumps(record,indent=2),encoding='utf-8')
(p/('framework-wsa-differential-validation-'+tag+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
