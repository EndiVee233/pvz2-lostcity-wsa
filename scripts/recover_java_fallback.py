from pathlib import Path
import subprocess,json
base=Path(__file__).resolve().parents[1]
java=Path(r'K:\pvz2-tools\jdk21\bin\java.exe');jar=base/'tools/jadx/lib/jadx-1.5.6-all.jar'
subprocess.run([str(java.with_name('javac.exe')),'-cp',str(jar),'-d',str(base/'tools/java_recovery'),str(base/'scripts/RecoveryBatch.java')],check=True)
results=[]
for dexdir in sorted((base/'java_recovery/simple').iterdir()):
    targets=[]
    for p in dexdir.rglob('*.java'):
        if 'Method not decompiled:' in p.read_text(encoding='utf-8',errors='replace'):
            targets.append('.'.join(p.relative_to(dexdir).with_suffix('').parts))
    if not targets:continue
    targetfile=base/'logs'/(dexdir.name+'_fallback_targets.txt');targetfile.write_text('\n'.join(targets),encoding='utf-8')
    output=base/'java_recovery/fallback'/dexdir.name
    cmd=[str(java),'-Xms64m','-Xmx900m','-Xss2m','-XX:+UseSerialGC','-XX:ReservedCodeCacheSize=48m',
         '-XX:MaxMetaspaceSize=192m','-XX:ActiveProcessorCount=2','-cp',str(jar)+';'+str(base/'tools/java_recovery'),
         'RecoveryBatch',str(base/'raw'/(dexdir.name+'.dex')),str(targetfile),str(output),'FALLBACK']
    with (base/'logs'/(dexdir.name+'_fallback.log')).open('w',encoding='utf-8') as log:proc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=base)
    files=list(output.rglob('*.java'))
    row={'dex':dexdir.name,'target_classes':len(targets),'exported_files':len(files),
         'remaining_method_stubs':sum(p.read_text(encoding='utf-8',errors='replace').count('Method not decompiled:') for p in files),
         'exit_code':proc.returncode};results.append(row)
    (base/'java_recovery/fallback_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('FALLBACK_DONE',json.dumps(row),flush=True)
