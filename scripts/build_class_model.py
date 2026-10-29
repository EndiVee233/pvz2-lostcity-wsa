from pathlib import Path
import sys,json,re,struct,collections
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from elftools.elf.elffile import ELFFile
source=base/'raw/lib/armeabi/libSrc.so';blob=source.read_bytes()
with source.open('rb') as fp:
    elf=ELFFile(fp)
    segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    code_regions=[(s['sh_addr'],s['sh_addr']+s['sh_size']) for s in elf.iter_sections() if s['sh_flags']&4]
def read_elf(address,size):
    for seg in segments:
        if seg['p_vaddr']<=address and address+size<=seg['p_vaddr']+seg['p_filesz']:
            off=seg['p_offset']+address-seg['p_vaddr'];return blob[off:off+size]
    return None
def resolve(expr):
    expr=expr.strip()
    m=re.fullmatch(r'DAT_([0-9a-f]{8})\s*\+\s*(0x[0-9a-f]+)',expr)
    if m:
        raw=read_elf(int(m[1],16)-0x10000,4)
        return (struct.unpack('<I',raw)[0]+int(m[2],16))&0xffffffff if raw else None
    m=re.fullmatch(r'&?(?:DAT_|UNK_|LAB_|FUN_|func_0x|PTR_\w*|Recovered_\w+_)([0-9a-f]{8})',expr)
    return int(m[1],16) if m else None
def text_value(expr):
    expr=expr.strip()
    if expr.startswith('"'):
        try:return json.loads(expr)
        except ValueError:return None
    address=resolve(expr)
    raw=read_elf(address-0x10000,256) if address else None
    if not raw or b'\0' not in raw:return None
    raw=raw.split(b'\0',1)[0]
    if not raw or any(c<32 or c>126 for c in raw):return None
    return raw.decode('ascii')

is_round4='--round4' in sys.argv or '--round5' in sys.argv
root=base/('native_analysis/core_round5' if '--round5' in sys.argv else ('native_analysis/core_round4' if is_round4 else 'native_analysis/core_round3'))
baseline_root=base/'native_analysis/core_round3'
catalog={}
for folder in ([] if is_round4 else [base/'native_analysis/core_deep',root,root/'expand',root/'virtual_methods',root/'virtual_methods_extra',root/'constructors',root/'virtual_methods_final',root/'full_library']):
    if not (folder/'summary.json').exists():continue
    data=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    for row in data['exports']:
        if row['status']!='ok':continue
        src=folder/row['file']
        if src.exists():catalog[row['address']]=dict(row,source=str(src.relative_to(base)))
if is_round4:
    for row in json.loads((root/'model/function_catalog.json').read_text()):catalog[row['address']]=row
getters=json.loads(((baseline_root if is_round4 else root)/'type_metadata_getters.json').read_text())
registrations=json.loads(((baseline_root if is_round4 else root)/'class_registrations.json').read_text())
getternames={r['address']:r['class_name'] for r in getters}
classes={}
ctorpath=(baseline_root if is_round4 else root)/'constructor_candidates.json'
ctorcandidates={r['class_name']:r for r in json.loads(ctorpath.read_text())} if ctorpath.exists() else {}
for row in registrations:
    item=classes.setdefault(row['class_name'],{'name':row['class_name'],'registrations':[],'fields':[],'vtable':[]})
    item['registrations'].append(row)
for row in getters:
    item=classes.setdefault(row['class_name'],{'name':row['class_name'],'registrations':[],'fields':[],'vtable':[]})
    item.update(metadata_getter=row['address'],parent_getter=row['parent_metadata_getter'],
                parent=getternames.get(row['parent_metadata_getter']),type_callback=row['type_callback'])

expr=r'(?:"(?:[^"\\]|\\.)*"|DAT_[0-9a-f]{8}\s*\+\s*0x[0-9a-f]+|&?(?:DAT_|UNK_)[0-9a-f]{8})'
write_expr=r'(?:'+expr+r'|[A-Za-z_]\w*(?:\s*\+\s*(?:0x[0-9a-f]+|[A-Za-z_]\w*))?)'
for item in classes.values():
    for reg in item['registrations']:
        record=catalog.get(reg['callback'])
        if not record:continue
        code=(base/record['source']).read_text(encoding='utf-8',errors='replace')
        writes=[]
        for m in re.finditer(r'(?:FUN_|func_0x)014fd0e0\(\s*&?(\w+),\s*('+write_expr+r')\s*(?:,[^;]*)?\);',code):
            # Keep unresolved writes too, so an old field name is never reused.
            writes.append((m.end(),m[1],text_value(m[2])))
        for m in re.finditer(r'\(\*(pcVar\d+)\)\(param_1,param_2,\s*&?(\w+),\s*(0x[0-9a-f]+|[0-9]+),\s*(\w+)\)',code):
            method_slots=list(re.finditer(re.escape(m[1])+r'\s*=\s*([^;]+);',code[:m.start()]))
            if not method_slots or not re.search(r'\*param_1 \+ 0x2c\)',method_slots[-1][1]):continue
            previous=[w for w in writes if w[0]<m.start() and w[1]==m[2]]
            if not previous or previous[-1][2] is None:continue
            name=previous[-1][2]
            if not re.fullmatch(r'[A-Za-z_]\w{0,100}',name):continue
            field={'name':name,'offset':hex(int(m[3],0)),'registration_callback':reg['callback'],
                   'evidence_source':record['source'],'status':'reflection registration offset; runtime layout not verified'}
            # Preserve raw type tags and a nearby explicit type-name string when present.
            assignments=list(re.finditer(re.escape(m[4])+r'\s*=\s*([^;]+);',code[:m.start()]))
            if assignments:
                assign=assignments[-1]
                builtin=re.search(r'\(param_1,([0-9]+),([0-9]+)\)',assign[1])
                if builtin:field.update(type_tag=int(builtin[1]),type_size=int(builtin[2]))
                nearby=[w for w in writes if previous[-1][0]<=w[0]<assign.start() and w[1]!=m[2] and w[2]]
                if nearby:field['candidate_type_name']=nearby[-1][2]
            item['fields'].append(field)
    callback=item.get('type_callback');record=catalog.get(callback)
    if not record:continue
    code=(base/record['source']).read_text(encoding='utf-8',errors='replace')
    allocated=list(re.finditer(r'(\w+)\s*=\s*[^;\n]*operator_new\((0x[0-9a-f]+|[0-9]+)\);',code))
    for allocation in allocated:
        variable=allocation[1]
        if not re.search(r'return '+re.escape(variable)+r';',code):continue
        vptr=list(re.finditer(r'\*'+re.escape(variable)+r'\s*=\s*(&DAT_[0-9a-f]{8}|DAT_[0-9a-f]{8}\s*\+\s*0x[0-9a-f]+);',code[allocation.end():]))
        vtable_source=record['source'];vtable_source_kind='direct allocation callback'
        if vptr:
            gh=resolve(vptr[-1][1])
        else:
            candidate=ctorcandidates.get(item['name']);ctor=catalog.get(candidate['constructor_candidate']) if candidate else None
            if not ctor:continue
            ctorcode=(base/ctor['source']).read_text(encoding='utf-8',errors='replace')
            stores=list(re.finditer(r'(?:\*param_1|\*\(undefined4 \*\)param_1)\s*=\s*(&[A-Za-z_]+[0-9a-f]{8}|DAT_[0-9a-f]{8}\s*\+\s*0x[0-9a-f]+);',ctorcode))
            if not stores:continue
            gh=resolve(stores[-1][1]);item['constructor_candidate']=candidate['constructor_candidate']
            vtable_source=ctor['source'];vtable_source_kind='single helper called after allocation; inferred constructor'
        if gh is None:continue
        header=read_elf(gh-0x10000-8,8)
        if not header or struct.unpack('<II',header)!=(0,0):continue
        slots=[]
        for n in range(1024):
            raw=read_elf(gh-0x10000+n*4,4)
            if not raw:break
            ptr=struct.unpack('<I',raw)[0];va=ptr&~1
            if not ptr or not any(lo<=va<hi for lo,hi in code_regions):break
            slots.append({'slot':n,'vtable_byte_offset':hex(n*4),'address':f'{va+0x10000:08x}','elf_address':hex(va),'thumb':bool(ptr&1)})
        if not slots:continue
        item.update(factory_candidate=callback,factory_source=record['source'],allocation_size=hex(int(allocation[2],0)),
                    vtable_address=f'{gh:08x}',vtable=slots,vtable_walk_capped=len(slots)==1024,
                    vtable_source=vtable_source,vtable_source_kind=vtable_source_kind,vtable_header=[0,0])
        item['size_matches_registration']=any(r['registered_size']==item['allocation_size'] for r in item['registrations']) if item['registrations'] else None
        break

for item in classes.values():
    parent=classes.get(item.get('parent'))
    if not parent or not item['vtable'] or not parent['vtable']:continue
    inherited={slot['slot']:slot['address'] for slot in parent['vtable']}
    for slot in item['vtable']:
        slot['parent_address']=inherited.get(slot['slot'])
        slot['relation_to_parent']='inherited' if slot['address']==slot['parent_address'] else ('overridden' if slot['parent_address'] else 'new_slot')
    item['overridden_slots']=[slot['slot'] for slot in item['vtable'] if slot['relation_to_parent']=='overridden']
    item['inherited_slot_count']=sum(slot['relation_to_parent']=='inherited' for slot in item['vtable'])

out=root/'model';out.mkdir(exist_ok=True)
(out/'classes.json').write_text(json.dumps(list(classes.values()),indent=2),encoding='utf-8')
(out/'function_catalog.json').write_text(json.dumps(list(catalog.values()),indent=2),encoding='utf-8')
virtuals=collections.defaultdict(list)
for item in classes.values():
    for slot in item['vtable']:virtuals[slot['address']].append({'class_name':item['name'],'slot':slot['slot'],'vtable_address':item['vtable_address']})
(out/'virtual_methods.json').write_text(json.dumps(virtuals,indent=2),encoding='utf-8')
summary={'available_unique_pseudocode_functions':len(catalog),'classes':len(classes),'classes_with_registered_fields':sum(bool(x['fields']) for x in classes.values()),
         'field_offset_records':sum(len(x['fields']) for x in classes.values()),'parent_links':sum(bool(x.get('parent')) for x in classes.values()),
         'classes_with_factory_and_vtable':sum(bool(x['vtable']) for x in classes.values()),'virtual_slots':sum(len(x['vtable']) for x in classes.values()),'unique_virtual_method_addresses':len(virtuals)}
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
for key in ['Plant','PlantFramework','PlantPeashooter','PlantSunflower','Zombie','Board']:
    if key in classes:
        item=classes[key];print(key,'parent',item.get('parent'),'fields',len(item['fields']),'slots',len(item['vtable']))
