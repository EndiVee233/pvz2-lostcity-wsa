from pathlib import Path
import sys, json, csv, re

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools/python_libs'))
from elftools.elf.elffile import ELFFile

out = BASE / 'native_analysis'
out.mkdir(exist_ok=True)
summaries = []
for path in sorted((BASE / 'raw/lib').rglob('*.so')):
    dest = out / path.stem
    dest.mkdir(exist_ok=True)
    with path.open('rb') as f:
        elf = ELFFile(f)
        symbols = []
        for section in elf.iter_sections():
            if section['sh_type'] not in ('SHT_SYMTAB', 'SHT_DYNSYM'):
                continue
            for sym in section.iter_symbols():
                if sym.name:
                    symbols.append({'name': sym.name, 'address': hex(sym['st_value']),
                                    'size': sym['st_size'], 'type': sym['st_info']['type'],
                                    'binding': sym['st_info']['bind'],
                                    'defined': sym['st_shndx'] != 'SHN_UNDEF', 'table': section.name})
        with (dest / 'symbols.csv').open('w', encoding='utf-8-sig', newline='') as dst:
            writer = csv.DictWriter(dst, fieldnames=['name','address','size','type','binding','defined','table'])
            writer.writeheader(); writer.writerows(symbols)
        functions = [s for s in symbols if s['defined'] and s['type'] == 'STT_FUNC']
        key = [s for s in functions if re.search(r'Java_|JNI_OnLoad|Plant|Zombie|Board|Lawn|Sun|Seed|Coin|Hook|hook', s['name'])]
        (dest / 'key_functions.json').write_text(json.dumps(key, indent=2, ensure_ascii=False), encoding='utf-8')
        summary = {'file':str(path.relative_to(BASE)), 'machine':elf['e_machine'],
                   'bits':elf.elfclass, 'entry':hex(elf['e_entry']),
                   'has_symtab':elf.get_section_by_name('.symtab') is not None,
                   'defined_function_symbols':len(functions), 'key_functions':len(key),
                   'needed':[t.needed for sec in elf.iter_sections() if sec['sh_type']=='SHT_DYNAMIC'
                             for t in sec.iter_tags() if t.entry.d_tag=='DT_NEEDED']}
        summaries.append(summary)
    raw = path.read_bytes()
    with (dest / 'strings.txt').open('w', encoding='utf-8') as dst:
        for m in re.finditer(rb'[\x20-\x7e]{6,}', raw):
            dst.write(f'0x{m.start():08x}\t{m.group().decode("ascii")}\n')
    print(path.name, len(functions), 'functions', len(key), 'key functions', flush=True)
(out / 'summary.json').write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding='utf-8')
