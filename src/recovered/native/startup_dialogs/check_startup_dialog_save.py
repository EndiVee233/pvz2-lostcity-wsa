"""Compare private PlayerInfo identities before/after WSA verification.

Only counts/booleans are written to the public analysis folder.
"""
from pathlib import Path
import sys,hashlib,json,tarfile,subprocess
from io import BytesIO
base=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(base/'tools/python_libs'),str(base/'tools/python_helpers')]
from py3rijndael import RijndaelCbc,ZeroPadding
from pyvz2rton import RTONDecoder
folder=base/'rebuild_project/logs/wsa/startup-dialogs'
key=hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
def profiles(blob):
 if blob[:2]==b'\x10\x00':blob=RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24).decrypt(blob[2:])
 assert blob[:4]==b'RTON'
 f=BytesIO(blob[4:]);f.name='private-save'
 data=json.loads(RTONDecoder(repairFiles=False).parse_root_object(f))
 return {str(o['uid']):o['objdata']['n'] for o in data['objects'] if o['objclass']=='PlayerInfo'}
with tarfile.open(folder/'before-v5-private-files.tar') as t:before=profiles(t.extractfile('files/userdataNo_Backup/pp.dat').read())
r=subprocess.run(['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526','exec-out','run-as','com.popcap.pvz2cthd.reconstruction','cat','files/userdataNo_Backup/pp.dat'],capture_output=True,check=True)
(folder/'after-v5-private.dat').write_bytes(r.stdout)
after=profiles(r.stdout)
assert before==after
record={'before_profile_count':len(before),'after_profile_count':len(after),'profile_uid_and_name_map_preserved':before==after}
(base/'native_analysis/startup_dialogs/save-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
