from pathlib import Path
import csv,json,re
base=Path(__file__).resolve().parents[1]
root=base/'native_analysis/core_deep'
p=root/'functions.csv'
with p.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f)
    fields=[name.lstrip('\ufeff') for name in reader.fieldnames]
    rows=[{key.lstrip('\ufeff'):value for key,value in row.items()} for row in reader]
for row in rows:row['elf_address']=row['elf_address'].rstrip('L')
with p.open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
p=root/'summary.json';summary=json.loads(p.read_text(encoding='utf-8'))
for row in summary['exports']:row['elf_address']=row['elf_address'].rstrip('L')
p.write_text(json.dumps(summary,indent=2),encoding='utf-8')
for p in (root/'functions').glob('*.c'):
    raw=p.read_bytes().replace(b'\r\r\n',b'\n').replace(b'\r\n',b'\n')
    raw=re.sub(rb'(ELF address 0x[0-9a-fA-F]+)L',rb'\1',raw)
    p.write_bytes(raw)
print('Normalized addresses and line endings for',len(summary['exports']),'export records')
