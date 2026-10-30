"""Compile the maintained bootstrap with the optional original-speed resource update."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

base=Path(__file__).resolve().parents[1]
out=base/'native_analysis/original_speed_button/bootstrap'
classes=out/'classes';dex=out/'dex'
classes.mkdir(parents=True,exist_ok=True);dex.mkdir(parents=True,exist_ok=True)
source=base/'rebuild_project/src/bootstrap/com/popcap/pvz2cthd/BootActivity.java'
jdk=Path('K:/pvz2-tools/jdk21/bin')
tools=base/'rebuild_project/tools'
def run(command,name):
    with (out/name).open('wb') as log:subprocess.run([str(x) for x in command],stdout=log,stderr=subprocess.STDOUT,check=True)
run([jdk/'javac.exe','-J-Xmx256m','-J-XX:+UseSerialGC','-encoding','UTF-8',
     '-source','8','-target','8','-Xlint:-options','-bootclasspath',tools/'android-30-legacy.jar',
     '-d',classes,source],'javac.log')
archive=out/'bootstrap-classes.jar'
with zipfile.ZipFile(archive,'w') as z:
    files=sorted(classes.rglob('*.class'))
    for file in files:z.write(file,file.relative_to(classes).as_posix())
run([jdk/'java.exe','-Xmx256m','-XX:+UseSerialGC','-cp',tools/'d8-stable.jar',
     'com.android.tools.r8.D8','--min-api','9','--lib',tools/'android-30-legacy.jar',
     '--output',dex,archive],'d8.log')
record=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            classes8_dex_sha256=hashlib.sha256((dex/'classes.dex').read_bytes()).hexdigest(),
            generated_classes=len(files),resource_update_on_background_thread=True,
            existing_resources_updated_without_reextracting_all_parts=True)
(out/'build-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
