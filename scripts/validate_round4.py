from pathlib import Path
import sys,json,re,hashlib,struct
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round4';model=root/'model'
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
p=base/'raw/lib/armeabi/libSrc.so';blob=p.read_bytes()
with p.open('rb') as f:
    elf=ELFFile(f);segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    code_regions=[(s['sh_addr'],s['sh_addr']+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read(gh,size):
    va=gh-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    return None
catalog=json.loads((model/'function_catalog.json').read_text());addresses={r['address'] for r in catalog}
assert len(addresses)==len(catalog)
baseline={r['address'] for r in json.loads((base/'native_analysis/core_round3/model/function_catalog.json').read_text())}
assert baseline<=addresses
for row in catalog:
    assert (base/row['source']).stat().st_size>100,row['address']
    assert (base/row['readable_file']).is_file(),row['address']
    if row.get('experimental_boundary'):assert row['body_size']>=4
classes=json.loads((model/'classes.json').read_text());field_count=0;slot_count=0
for item in classes:
    if item['registrations']:
        bound=max(int(r['registered_size'],16) for r in item['registrations'])
        for field in item['fields']:assert 0<=int(field['offset'],16)<bound
    field_count+=len(item['fields'])
    if not item['vtable']:continue
    addr=int(item['vtable_address'],16)
    assert struct.unpack('<II',read(addr-8,8))==(0,0)
    for row in item['vtable']:
        ptr=struct.unpack('<I',read(addr+row['slot']*4,4))[0]
        assert ptr and any(lo<=ptr&~1<hi for lo,hi in code_regions)
        assert (ptr&~1)+0x10000==int(row['address'],16)
        slot_count+=1
methods=json.loads((model/'reflected_methods.json').read_text())
for row in methods:
    assert not row['member_flags']&1
    va=int(row['address'],16)-0x10000
    assert any(lo<=va<hi for lo,hi in code_regions)
hp=next(r for r in methods if r['class_name']=='Zombie' and r['method_name']=='GetHitpoints')
zombie=next(r for r in classes if r['name']=='Zombie')
assert hp['simple_getter_offset']=='0x138' and hp['member_flags']==0
assert 'float' in hp['nearby_type_strings']
field=next(r for r in zombie['fields'] if r['name']=='m_hitpoints')
assert field['offset']=='0x138' and field['type_size']==4 and field['candidate_type_name']=='float'
assert hp['address'] in addresses
paths=[base/'第四轮恢复结果.md',model/'类型目录.md',model/'反射方法目录.md',model/'Zombie_GetHitpoints_证据.md',*list((model/'classes').glob('*.md'))]
links=0
for path in paths:
    for target in re.findall(r'\]\((K:/[^)]+)\)',path.read_text(encoding='utf-8')):
        assert Path(target).is_file(),(path,target)
        links+=1
sha=hashlib.file_digest((base/'PvZ2-LostCity-1.7.5.apk').open('rb'),'sha256').hexdigest()
assert sha=='1655512770c6968bd4216f0d66b8be955ce464c6e6881b5de6cbf776f245e1a4'
summary=json.loads((model/'round4_summary.json').read_text())
summary.update(class_field_records_verified=field_count,vtable_slots_verified=slot_count,reflected_method_records_verified=len(methods),
               getter_registration_field_and_machine_code_agree=True,links_verified=links,apk_sha256_unchanged=sha)
(base/'logs/round4_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
