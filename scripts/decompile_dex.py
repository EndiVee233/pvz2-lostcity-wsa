from pathlib import Path
import subprocess, json, time

base = Path(__file__).resolve().parents[1]
java = r'K:\pvz2-tools\jdk21\bin\java.exe'
jar = base / 'tools/jadx/lib/jadx-1.5.6-all.jar'
results = []
for dex in sorted((base / 'raw').glob('*.dex')):
    started = time.time()
    log = base / 'logs' / (dex.stem + '_jadx.log')
    cmd = [java, '-Xms64m', '-Xmx900m', '-XX:+UseSerialGC',
           '-XX:ReservedCodeCacheSize=64m', '-XX:MaxMetaspaceSize=192m',
           '-XX:ActiveProcessorCount=2', '-Xss512k', '-cp', str(jar),
           'jadx.cli.JadxCLI', '-r', '-j', '1', '--show-bad-code',
           '--log-level', 'warn', '-d', str(base/'java_by_dex'/dex.stem), str(dex)]
    print('START', dex.name, flush=True)
    with log.open('w', encoding='utf-8') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=base)
    count = len(list((base/'java_by_dex'/dex.stem).rglob('*.java')))
    row = {'dex':dex.name, 'exit_code':result.returncode,
           'seconds':round(time.time()-started, 1), 'java_files':count, 'log':str(log.relative_to(base))}
    results.append(row)
    (base/'logs/dex_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('DONE', json.dumps(row), flush=True)
