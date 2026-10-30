"""Record the bounded ARM decoder tests separately from APK installation status."""
from pathlib import Path
import hashlib
import json
import re
import sys

base = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base / 'tools/python_libs'))
from elftools.elf.elffile import ELFFile

folder = base / 'native_analysis/glshim_threads16'
library = folder / 'build/libRestart.so'
with library.open('rb') as fp:
    elf = ELFFile(fp)
    assert elf.elfclass == 32 and elf['e_machine'] == 'EM_ARM'
    names = {symbol.name for symbol in elf.get_section_by_name('.dynsym').iter_symbols()
             if symbol['st_shndx'] != 'SHN_UNDEF'}
    required = ['glTexImage2D', 'glTexSubImage2D', 'glCompressedTexImage2D']
    assert all(name in names for name in required)
    needed = [tag.needed for tag in elf.get_section_by_name('.dynamic').iter_tags()
              if tag.entry.d_tag == 'DT_NEEDED']
    assert 'libc++_shared.so' not in needed
    assert elf.get_section_by_name('.init_array')['sh_size'] > 0

log = (base / 'native_analysis/glshim-threads16-device-tests.log').read_text(encoding='utf-8-sig')
assert 'PASS all pixel comparisons, capped workers and failed-thread joins' in log
rows = [dict(zip(['block', 'width', 'height', 'cpus', 'strips', 'created', 'failure', 'ms'],
                 map(int, match)))
        for match in re.findall(r'PASS block=(\d+) size=(\d+)x(\d+) cpus=(\d+) strips=(\d+) created=(\d+) failure=(\d+) ms=(\d+)', log)]
assert len(rows) == 14
assert all(row['created'] == 16 for row in rows
           if row['cpus'] == 20 and row['failure'] == 0)
record = {
    'date': '2026-10-30', 'abi': 'armeabi-v7a', 'wsa_online_cpus': 20,
    'max_astc_threads': 16, 'decoder_runtime_verified': True,
    'apk_installation_verified': False, 'game_runtime_verified': False,
    'installation_limit': 'Both non-streaming and streaming install attempts lost the WSA debugging connection before success.',
    'pixel_comparison_scenarios': rows, 'worker_selection_checks': 6,
    'required_exports': required, 'dt_needed': needed,
    'library_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
    'scope': 'Production ASTC strip decode against serial codec on generated test images; excludes full-game loading and GPU upload benchmarks.',
}
(folder / 'validation.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
build_file = folder / 'build/build-validation.json'
build = json.loads(build_file.read_text(encoding='utf-8'))
build.update(decoder_runtime_verified=True, game_runtime_verified=False)
assert build['source_sha256'] == hashlib.sha256((base / 'publish_repo/src/glshim/glshim.cpp').read_bytes()).hexdigest()
build_file.write_text(json.dumps(build, indent=2), encoding='utf-8')
apk_file = base / 'rebuild_project/wsa_test/multiuser-v6-build-validation.json'
apk = json.loads(apk_file.read_text(encoding='utf-8'))
apk.update(source_variant_tag='v5', source_apk_sha256=apk['source_offline_apk_sha256'],
           decoder_runtime_verified=True, apk_installation_verified=False, max_astc_threads=16)
apk_file.write_text(json.dumps(apk, indent=2), encoding='utf-8')
public = base / 'publish_repo/docs/recovery/glshim-threads16-validation.json'
public.write_text(json.dumps(record, indent=2), encoding='utf-8')
print('ARM32 exports verified; 14 pixel scenarios and 6 worker-selection checks passed; APK install remains unverified.')
