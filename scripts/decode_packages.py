from pathlib import Path
import mmap, sys, json, hashlib, struct, zlib

base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
sys.path.insert(0,str(base/'tools/python_helpers'))
import rsbtool
from pyvz2rton import RTONDecoder
from py3rijndael import RijndaelCbc, ZeroPadding
from io import BytesIO

key=hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
cipher=RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24)
decoder=RTONDecoder(repairFiles=False)
results=[]

def decode(blob, relative):
    row={'source':str(relative)}
    try:
        if blob[:2]==b'\x10\x00':blob=cipher.decrypt(blob[2:])
        if blob[:4]!=b'RTON':raise ValueError('Unexpected magic '+blob[:4].hex())
        fp=BytesIO(blob[4:]);fp.name=str(relative)
        parsed=json.loads(decoder.parse_root_object(fp))
        dest=(base/'rton_json'/relative).with_suffix('.json')
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(parsed,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        row.update(status='ok',output=str(dest.relative_to(base)))
    except Exception as exc:row.update(status='error',error=str(exc))
    results.append(row)

for src in (base/'apktool_out/assets').rglob('*'):
    if src.is_file() and src.suffix.lower()=='.rton':decode(src.read_bytes(),src.relative_to(base))
print('Asset RTON:',sum(r['status']=='ok' for r in results),'/',len(results),flush=True)

indexes=[]
for src in sorted((base/'game_data/extracted').rglob('*.rsb.smf')):
    with src.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        head=rsbtool.parse_head(data)
        files=rsbtool.read_string_list(data,head['fileList_BeginOffset'],head['fileList_Length'],0)
        packs=rsbtool.read_rsgp_info(data,head['rsgpInfo_BeginOffset'],head['rsgp_Number'],head['rsgpInfo_EachLength'])
        index={'source':str(src.relative_to(base)),'header':head,'files':files,'packages':packs}
        dest=base/'game_data/rsb_indexes'/(src.name+'.json');dest.parent.mkdir(exist_ok=True)
        dest.write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
        indexes.append({'file':src.name,'resources':len(files),'groups':len(packs)})
        # Export configuration groups; large texture/sound groups remain in the original RSB.
        for pack in packs:
            if pack['ID'].lower()!='packages':continue
            offset=pack['fields'][0]
            flags=struct.unpack_from('<I',data,offset+0x10)[0]
            p0_offset,p0_size,p0_rawsize=struct.unpack_from('<III',data,offset+0x18)
            fl_len,fl_off=struct.unpack_from('<II',data,offset+0x48)
            entries=rsbtool.read_string_list(data,offset+fl_off,fl_len,1)
            section=data[offset+p0_offset:offset+p0_offset+p0_size]
            if flags & 2:section=zlib.decompress(section)
            for name,info in entries:
                if not info or info[0]!=0:continue
                _,pos,size=info
                relative=Path('packages')/src.name/Path(name.replace('\\','/'))
                if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe resource path')
                blob=section[pos:pos+size]
                raw=base/'game_data'/relative;raw.parent.mkdir(parents=True,exist_ok=True);raw.write_bytes(blob)
                if name.lower().endswith('.rton'):decode(blob,relative)
        print(src.name,'indexed',len(files),'resources',flush=True)
(base/'game_data/rsb_summary.json').write_text(json.dumps(indexes,indent=2,ensure_ascii=False),encoding='utf-8')
(base/'game_data/rton_decoded_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print('Total decoded',sum(r['status']=='ok' for r in results),'of',len(results),flush=True)
