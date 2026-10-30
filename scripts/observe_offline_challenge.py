"""Read isolated test saves; keep raw data private and print challenge fields only."""
from pathlib import Path
from io import BytesIO
import hashlib,json,subprocess,sys,tarfile
base=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(base/'tools/python_libs'),str(base/'tools/python_helpers')]
from py3rijndael import RijndaelCbc,ZeroPadding
from pyvz2rton import RTONDecoder
adb=['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526']
app='com.popcap.pvz2cthd.reconstruction'
folder=base/'rebuild_project/logs/wsa/offline-challenge'
def call(*args):return subprocess.check_output([*adb,*args],timeout=60)
def decode(blob):
 if blob[:2]==b'\x10\x00':
  key=hashlib.md5(b'com_popcap_pvz2_magento_product_2013_05_05').hexdigest().encode()
  blob=RijndaelCbc(key,key[4:28],ZeroPadding(24),block_size=24).decrypt(blob[2:])
 assert blob[:4]==b'RTON'
 fp=BytesIO(blob[4:]);fp.name='private-save'
 return json.loads(RTONDecoder(repairFiles=False).parse_root_object(fp))
def snapshot(label):
 data=call('exec-out','run-as',app,'cat','files/userdataNo_Backup/pp.dat')
 (folder/(label+'.dat')).write_bytes(data)
 return decode(data)
def number(value):return (((value>>13)|(value<<19))&0xffffffff)^13
def challenge_state(parsed):
 result=[]
 for o in parsed['objects']:
  if o['objclass']!='PlayerInfo':continue
  data=o['objdata'];info=data.get('ainfo',{})
  result.append(dict(level=data.get('l'),tutorial_state=data.get('tp'),
   refresh_day=info.get('rAt'),counts={mode:number(info[key]) for mode,key in
   [('yeti','tcylc'),('gargantuar','tgclc'),('devil','tdilc')] if key in info},
   reward_seed_count=len(data.get('lfprii',[])),coins=number(data['c']),gems=data.get('gg')))
 return result
if __name__=='__main__':
 label=sys.argv[1] if len(sys.argv)>1 else 'observed'
 parsed=snapshot(label)
 (folder/(label+'.json')).write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(challenge_state(parsed),ensure_ascii=False,indent=2))
