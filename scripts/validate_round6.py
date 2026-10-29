from pathlib import Path
import json,sys,struct,hashlib,re,zipfile,xml.etree.ElementTree as ET
base=Path(__file__).resolve().parents[1];root=base/'native_analysis/core_round6';model=root/'model'
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
so=base/'raw/lib/armeabi/libSrc.so';blob=so.read_bytes()
with so.open('rb') as f:
    elf=ELFFile(f);segments=[dict(s.header) for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    executable=[(s['sh_addr']+0x10000,s['sh_addr']+0x10000+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read(address,size):
    va=address-0x10000
    for s in segments:
        if s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
            off=s['p_offset']+va-s['p_vaddr'];return blob[off:off+size]
    raise AssertionError(('outside file',hex(address)))
catalog=json.loads((model/'function_catalog.json').read_text(encoding='utf-8'));addresses={r['address'] for r in catalog};assert len(addresses)==len(catalog)
old=json.loads((base/'native_analysis/core_round5/model/function_catalog.json').read_text(encoding='utf-8'));assert {r['address'] for r in old}<=addresses
for row in catalog:
    assert (base/row['source']).is_file() and (base/row['readable_file']).is_file(),row['address']
    assert 'halt_baddata' not in (base/row['source']).read_text('utf-8'),row['address']
switch=json.loads((root/'switch/summary.json').read_text(encoding='utf-8'));original=json.loads((base/'native_analysis/core_round5/model/gnu_thumb_case_si_switch.json').read_text(encoding='utf-8'))
table=next(t for t in switch['jump_tables'] if t['switch_address']=='0150557c')
assert table['labels']==list(range(76))
assert table['cases']==[r['target'] for r in original['entries']]
assert switch['helper_model_xml']==(root/'pvz2_thumb_case_si.xml').read_text('utf-8')
model_body=ET.fromstring(switch['helper_model_xml']).find('./pcode/body').text
assert 'lr = tmpptr + offset;' in model_body and 'ISAModeSwitch = 1;' in model_body and 'TB = 1;' in model_body
assert 'offset = offset * 4' not in model_body
assert all(text in model_body for text in ['CY = carry(tmpptr, offset);','OV = scarry(tmpptr, offset);','NG = lr s< 0;','ZR = lr == 0;'])
formats=json.loads((root/'formats/summary.json').read_text(encoding='utf-8'))['exports'];configs=json.loads((root/'format_switches.json').read_text(encoding='utf-8'))['functions']
arm=Cs(CS_ARCH_ARM,CS_MODE_ARM);thumb=Cs(CS_ARCH_ARM,CS_MODE_THUMB);instructions=0;branch_entries=0
new_records=[switch]+formats
for row in new_records:
    assert row['status']=='ok' and not row['halt_baddata']
    total=0;ranges=[]
    for block in row['body_ranges']:
        lo=int(block['start'],16);hi=int(block['end'],16)+1;size=hi-lo;total+=size;ranges.append((lo,hi))
        assert any(start<=lo<hi<=end for start,end in executable)
        data=read(lo,size);decoded=list((thumb if row['address']=='01505544' else arm).disasm(data,lo))
        assert sum(i.size for i in decoded)==size,(row['address'],block)
        instructions+=len(decoded)
    assert total==row['size']
    def contains(address):return any(lo<=address<hi for lo,hi in ranges)
    for table in row['jump_tables']:
        assert contains(int(table['switch_address'],16))
        assert all(contains(int(c,16)) for c in table['cases'])
    if row['address']=='01505544':continue
    request=next(r for r in configs if r['address']==row['address'])
    assert max(hi for lo,hi in ranges)<=int(request['next_known_function'],16)
    dispatch=next(t for t in row['jump_tables'] if t['switch_address']==request['switch_address'])
    assert dispatch['cases']==[r['instruction_address'] for r in request['entries']]
    assert dispatch['labels']==[n*4 for n in range(84)]
    for entry in request['entries']:
        address=int(entry['instruction_address'],16);assert read(address,4).hex()==entry['instruction_bytes']
        ins=list(arm.disasm(read(address,4),address))[0]
        assert ins.mnemonic=='b' and int(ins.op_str[1:],16)==int(entry['target'],16)
        assert contains(address) and contains(int(entry['target'],16));branch_entries+=1
emulation=json.loads((base/'logs/round6_emulation.json').read_text(encoding='utf-8'))
assert emulation['helper_cases_verified']==76 and len(emulation['helper_cases'])==76
assert len(emulation['format_cases'])==14 and all(r['passed'] for r in emulation['format_cases'])
for r in emulation['helper_cases']:assert r['thumb_preserved'] and r['r0_r1_sp_preserved'] and r['nzcv_matches_model']
links=0
for path in [base/'第六轮恢复结果.md',*model.glob('*.md')]:
    for target in re.findall(r'\]\((K:/[^)]+)\)',path.read_text('utf-8')):
        if Path(target)==base/'logs/round6_validation.json':links+=1;continue
        assert Path(target).is_file(),(path,target);links+=1
apk=base/'PvZ2-LostCity-1.7.5.apk'
apk_sha=hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()
assert apk_sha=='1655512770c6968bd4216f0d66b8be955ce464c6e6881b5de6cbf776f245e1a4'
with zipfile.ZipFile(apk) as z:assert hashlib.sha256(z.read('lib/armeabi/libSrc.so')).digest()==hashlib.sha256(blob).digest()
summary=json.loads((model/'round6_summary.json').read_text(encoding='utf-8'))
summary.update(new_instruction_bytes_decodable=instructions,arm_main_branch_entries_verified=branch_entries,
               helper_table_entries_match_ELF=76,links_verified=links,apk_sha256_unchanged=apk_sha,
               raw_library_matches_original_APK=True,pseudocode_equivalence_proven=False,game_runtime_tested=False)
(base/'logs/round6_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='remaining_jumptable_warning_addresses'},ensure_ascii=False,indent=2))
