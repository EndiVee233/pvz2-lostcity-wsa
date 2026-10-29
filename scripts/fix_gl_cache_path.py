"""Retarget the existing ASTC cache to the isolated application's private cache."""
from pathlib import Path
import struct,json,hashlib
base=Path(__file__).resolve().parents[1];p=base/'native_analysis/multiuser/fixes'
src=base/'raw/lib/armeabi/libRestart.so';b=bytearray(src.read_bytes())
va=0xc0000;off=(len(b)+4095)&~4095;extra=bytearray();rows=[]
root='/data/data/com.popcap.pvz2cthd.reconstruction/cache'
for literal,pc,old,new in [(0x468cc,0x465c4,'/data/data/com.popcap.pvz2cthd/cache',root),
 (0x468d0,0x465d0,'/data/data/com.popcap.pvz2cthd/cache/glcache',root+'/glcache'),
 (0x46e90,0x46e5e,'/data/data/com.popcap.pvz2cthd/cache/glcache/%016llx.rgba',root+'/glcache/%016llx.rgba')]:
 original=struct.unpack_from('<I',b,literal)[0];target=(pc+original)&0xffffffff
 assert b[target:target+len(old)+1]==old.encode()+b'\0'
 address=va+len(extra);extra+=new.encode()+b'\0';struct.pack_into('<I',b,literal,(address-pc)&0xffffffff)
 rows.append({'literal_file_offset':hex(literal),'old_target':hex(target),'new_target':hex(address),'new_path':new})
ph=struct.unpack_from('<I',b,28)[0];size,count=struct.unpack_from('<HH',b,42)
for i in range(count):
 pos=ph+i*size
 if struct.unpack_from('<I',b,pos)[0]==0x6474e551:
  struct.pack_into('<8I',b,pos,1,off,va,va,len(extra),len(extra),4,4096);break
else:raise AssertionError('GNU_STACK slot missing')
b+=b'\0'*(off-len(b));b+=extra
(p/'libRestart-cache-fixed.so').write_bytes(b)
(p/'gl-cache-patch.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(b).hexdigest(),'paths':rows,'scope':'Only existing cache path literals; original full-resolution ASTC decoder retained'},indent=2),encoding='utf-8')
print('Private ASTC cache path references updated:',len(rows))
