"""Apply the repository's original Turbo resource patch, with semantic checks."""
from pathlib import Path
from io import BytesIO
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import zipfile

base = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(base/'tools/python_libs'),str(base/'tools/python_helpers')]
from pyvz2rton import RTONDecoder
import rsbtool  # Workspace reader uses relative offsets in RSGP name lists.
repo = base/'publish_repo'
patch_path = repo/'src/tools/patch_speed.py'
commit = '57d9c4490c83d8c6911fafbedc6d42d9accff805'
committed = subprocess.check_output(['git','-C',str(repo),'show',commit+':src/tools/patch_speed.py'])
assert committed.replace(b'\r\n',b'\n') == patch_path.read_bytes().replace(b'\r\n',b'\n')
subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',commit,'origin/main'],check=True)
sys.path.insert(0,str(patch_path.parent))
spec = importlib.util.spec_from_file_location('github_speed_patch',patch_path)
patch = importlib.util.module_from_spec(spec); spec.loader.exec_module(patch)
assert rsbtool is patch.rsbtool
out = base/'native_analysis/original_speed_button'
out.mkdir(exist_ok=True)
(out/'patch_speed_from_github.py').write_bytes(committed)
source = base/'game_data/extracted/com.popcap.pvz2cthd/files/dynamic.rsb.smf'
original = source.read_bytes()
with zipfile.ZipFile(base/'game_data/pvz2data.zip') as z:
    assert z.read('com.popcap.pvz2cthd/files/dynamic.rsb.smf') == original
data = bytearray(original)
head = rsbtool.parse_head(data)
groups = rsbtool.read_rsgp_info(data,head['rsgpInfo_BeginOffset'],head['rsgp_Number'],head['rsgpInfo_EachLength'])
group = next(g for g in groups if g['ID'].lower()=='packages')
start = group['fields'][0]
assert struct.unpack_from('<I',data,start+0x10)[0] & 2 == 0
data_off = struct.unpack_from('<I',data,start+0x18)[0]
list_len,list_off = struct.unpack_from('<II',data,start+0x48)
files = rsbtool.read_string_list(data,start+list_off,list_len,1)
wanted = {'PACKAGES\\UI_IPAD.RTON','PACKAGES\\UI_IPHONE.RTON',
          'PACKAGES\\UI_IPHONE5.RTON','PACKAGES\\UI_IPHONESTRETCH.RTON'}
def decode(blob):
    fp = BytesIO(blob[4:]);fp.name='speed-layout'
    return json.loads(RTONDecoder(repairFiles=False).parse_root_object(fp))
def diff(a,b,path=()):
    if type(a) is not type(b):return [(path,a,b)]
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        return [row for k in a for row in diff(a[k],b[k],path+(k,))]
    if isinstance(a,list):
        assert len(a)==len(b)
        return [row for i in range(len(a)) for row in diff(a[i],b[i],path+(i,))]
    return [] if a==b else [(path,a,b)]
rows=[];ranges=[]
for name,info in files:
    if name.upper().replace('/','\\') not in wanted:continue
    kind,off,size=info;assert kind==0
    absolute=start+data_off+off
    cipher=bytes(data[absolute:absolute+size])
    plain=patch.decrypt(cipher)
    before=decode(plain)
    modified=plain
    counts=[]
    for old,new in patch.PATCHES:
        count=modified.count(old)
        modified=modified.replace(old,new)
        counts.append(count)
    assert len(modified)<=len(plain)
    modified+=bytes(len(plain)-len(modified))
    encrypted=patch.encrypt(modified)
    assert len(encrypted)==size
    after=decode(patch.decrypt(encrypted))
    changes=diff(before,after)
    for path,old,new in changes:
        assert (path[-1],old,new) in [
            ('Class','ArenaChangeSpeedButton','SpeedChange'),
            ('SizeFromImage','IMAGE_UI_HUD_INGAME_ARENA_CHANGE_SPEED','IMAGE_UI_HUD_INGAME_SPEED')],(name,path,old,new)
    speed=next(o for o in after['objects'] if 'UIChangeSpeedButton' in o.get('aliases',[]))['objdata']
    assert speed['Class']=='SpeedChange' and speed['SizeFromImage']=='IMAGE_UI_HUD_INGAME_SPEED'
    data[absolute:absolute+size]=encrypted
    ranges.append((absolute,absolute+size))
    rows.append(dict(package=name,changes=[dict(path=list(p),before=a,after=b) for p,a,b in changes],
                     token_replacements=counts,normal_speed_widget=speed))
assert len(rows)==4 and any(row['changes'] for row in rows), (len(rows),[name for name,_ in files if 'UI_IP' in name.upper()])
assert len(data)==len(original)
assert all(a==b or any(lo<=i<hi for lo,hi in ranges) for i,(a,b) in enumerate(zip(original,data)))
target=out/'dynamic-original-speed.rsb.smf'
target.write_bytes(data)
record=dict(source_commit=commit,source_commit_url='https://github.com/EndiVee233/pvz2-lostcity-wsa/commit/'+commit,
            source_patch_blob_sha256=hashlib.sha256(committed).hexdigest(),
            source_rsb_sha256=hashlib.sha256(original).hexdigest(),
            patched_rsb_sha256=hashlib.sha256(data).hexdigest(),
            rsb_length_preserved=True,layout_count=4,layouts=rows,
            semantic_changes_limited_to_original_patch_fields=True,runtime_verified=False)
(out/'resource-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k!='layouts'},indent=2),flush=True)
