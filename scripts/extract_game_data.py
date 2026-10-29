from pathlib import Path, PurePosixPath
import shutil, zipfile, json, sys

base = Path(__file__).resolve().parents[1]
data = base/'game_data'
data.mkdir(exist_ok=True)
joined = data/'pvz2data.zip'
parts = sorted((base/'apktool_out/assets').glob('pvz2data.zip.???'))
with joined.open('wb') as dst:
    for part in parts:
        with part.open('rb') as src:
            shutil.copyfileobj(src, dst, 8*1024*1024)
        print('Joined', part.name, flush=True)
with zipfile.ZipFile(joined) as z:
    listing = [{'path':i.filename,'size':i.file_size,'compressed_size':i.compress_size} for i in z.infolist()]
    (data/'archive_inventory.json').write_text(json.dumps(listing,indent=2,ensure_ascii=False),encoding='utf-8')
    root = (data/'extracted').resolve()
    for i in z.infolist():
        relative = PurePosixPath(i.filename.replace('\\','/'))
        target = root.joinpath(*relative.parts).resolve()
        if relative.is_absolute() or not target.is_relative_to(root):
            raise ValueError('Unsafe archive path: '+i.filename)
        if i.is_dir():
            target.mkdir(parents=True,exist_ok=True)
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(i) as src,target.open('wb') as dst:
                shutil.copyfileobj(src,dst,1024*1024)
        if i.file_size>50*1024*1024:print('Extracted',i.filename,i.file_size,flush=True)
    print('Extracted',len(listing),'entries; ZIP CRC validated during reads',flush=True)

sys.path.insert(0,str(base/'tools/python_helpers'))
from pyvz2rton import RTONDecoder
decoder = RTONDecoder(repairFiles=False)
results=[]
roots=[base/'apktool_out/assets',data/'extracted']
for root in roots:
    for src in root.rglob('*'):
        if not src.is_file() or src.suffix.lower()!='.rton':continue
        row={'source':str(src.relative_to(base))}
        try:
            with src.open('rb') as fp:
                magic=fp.read(4)
                if magic!=b'RTON':raise ValueError('Not plaintext RTON; header='+magic.hex())
                decoded=decoder.parse_root_object(fp)
            parsed=json.loads(decoded)
            dest=base/'rton_json'/root.relative_to(base)/src.relative_to(root)
            dest=dest.with_suffix('.json');dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(parsed,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            row.update(status='ok',output=str(dest.relative_to(base)))
        except Exception as exc:row.update(status='error',error=str(exc))
        results.append(row)
(data/'rton_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('RTON decoded:',sum(x['status']=='ok' for x in results),'of',len(results),flush=True)
