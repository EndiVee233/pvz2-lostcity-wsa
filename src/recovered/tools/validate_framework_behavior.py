"""Desktop behavioral tests of compiled Java. Android Log is a test-only no-op adapter."""
from pathlib import Path
import subprocess,json,hashlib,os
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project'
java_home=Path('K:/pvz2-tools/jdk21/bin');classes=p/'build/framework-probe-classes';classes.mkdir(exist_ok=True)
sources=list((p/'tests/java').rglob('*.java'))
cmd=[str(java_home/'javac.exe'),'-J-Xmx256m','-J-XX:+UseSerialGC','-J-XX:ActiveProcessorCount=2','-encoding','UTF-8','-source','8','-target','8','-Xlint:-options',
     '-bootclasspath',str(p/'tools/android-30.jar'),'-classpath',str(p/'build/bridge-classes'),'-d',str(classes),*[str(s) for s in sources]]
compiled=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(p/'logs/framework-probe-javac.log').write_bytes(compiled.stdout);compiled.check_returncode()
records=[]
for mode in ['-da','-ea']:
    run=subprocess.run([str(java_home/'java.exe'),'-Xms16m','-Xmx256m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2',mode,'-cp',
        os.pathsep.join(map(str,[classes,p/'build/bridge-classes',p/'tools/android-30.jar'])),'com.popcap.SexyAppFramework.FrameworkProbe'],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
    (p/('logs/framework-probe-'+mode[1:]+'.log')).write_bytes(run.stdout)
    if run.returncode:print(run.stdout.decode('utf-8',errors='replace'))
    run.check_returncode();record=json.loads(run.stdout.decode().splitlines()[-1]);assert record['passed'];records.append(record)
source_hashes={f.relative_to(p).as_posix():hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
               for f in [p/'src/game_bridge/com/popcap/SexyAppFramework/AndroidHttpTransaction.java',p/'src/game_bridge/com/popcap/SexyAppFramework/AndroidUIEventManager.java',p/'src/game_bridge/com/popcap/SexyAppFramework/utils/Base64.java']}
result={'passed':True,'environment':'Desktop JVM with Android Log test adapter; not Android runtime equivalence',
        'test_classes_packaged_in_apk':False,'runs':records,'source_sha256':source_hashes,
        'covered':['RFC 4648 Base64 vectors, binary roundtrips, malformed padding and URL alphabet','Fixed little-endian native input-event wire vectors and overflow','HTTP GET, POST, error, cancellation during callback, read timeout and native pointer forwarding']}
(p/'framework-behavior-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
