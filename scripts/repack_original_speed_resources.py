"""Repack resource parts while copying all other compressed entries unchanged."""
from pathlib import Path
import hashlib
import json
import struct
import zipfile
import zlib

base=Path(__file__).resolve().parents[1]
out=base/'native_analysis/original_speed_button'
original=base/'game_data/pvz2data.zip'
patched=out/'dynamic-original-speed.rsb.smf'
target='com.popcap.pvz2cthd/files/dynamic.rsb.smf'
destination=out/'pvz2data-original-speed.zip'
part_size=419430400
record=[]
# Prove that the source resource archive belongs to the current v7 APK.
digest=hashlib.sha256()
with zipfile.ZipFile(base/'rebuild_project/wsa_test/PvZ2-reconstruction-multiuser-v7.apk') as apk:
    for i in range(1,4):
        with apk.open(f'assets/pvz2data.zip.{i:03d}') as fp:
            while chunk:=fp.read(1048576):digest.update(chunk)
with original.open('rb') as fp:assert hashlib.file_digest(fp,'sha256').digest()==digest.digest()
central=[]
with zipfile.ZipFile(original) as source,destination.open('wb') as dst:
    for info in source.infolist():
        source.fp.seek(info.header_offset)
        header=source.fp.read(30)
        sig,version,flags,method,mtime,mdate,crc,csize,usize,nlen,elen=struct.unpack('<IHHHHHIIIHH',header)
        assert sig==0x04034b50 and info.file_size<0xffffffff and info.compress_size<0xffffffff
        name=source.fp.read(nlen); extra=source.fp.read(elen)
        assert csize!=0xffffffff and usize!=0xffffffff, 'ZIP64 entries require another writer'
        offset=dst.tell()
        flags &= ~8
        payload=None
        if info.filename==target:
            data=patched.read_bytes()
            payload=zlib.compress(data,6,wbits=-15) if method==8 else data
            assert method in (0,8)
            crc=zlib.crc32(data)&0xffffffff; csize=len(payload); usize=len(data)
        else:
            crc=info.CRC; csize=info.compress_size; usize=info.file_size
        dst.write(struct.pack('<IHHHHHIIIHH',0x04034b50,version,flags,method,mtime,mdate,
                              crc,csize,usize,nlen,elen))
        dst.write(name);dst.write(extra)
        copied=hashlib.sha256()
        if payload is not None:
            dst.write(payload);copied.update(payload)
        else:
            left=csize
            while left:
                chunk=source.fp.read(min(left,1048576));assert chunk
                dst.write(chunk);copied.update(chunk);left-=len(chunk)
        record.append(dict(name=info.filename,changed=payload is not None,
                           compressed_sha256=copied.hexdigest(),crc32=crc,size=usize))
        central.append((info,version,flags,method,mtime,mdate,crc,csize,usize,name,extra,offset))
    start=dst.tell()
    for info,version,flags,method,mtime,mdate,crc,csize,usize,name,extra,offset in central:
        dst.write(struct.pack('<IHHHHHHIIIHHHHHII',0x02014b50,
                              (info.create_system<<8)|info.create_version,version,flags,method,mtime,mdate,
                              crc,csize,usize,len(name),len(extra),len(info.comment),0,
                              info.internal_attr,info.external_attr,offset))
        dst.write(name);dst.write(extra);dst.write(info.comment)
    length=dst.tell()-start
    assert dst.tell()<0xffffffff and len(central)<65535
    dst.write(struct.pack('<IHHHHIIH',0x06054b50,0,0,len(central),len(central),length,start,0))
with zipfile.ZipFile(destination) as check:
    assert check.testzip() is None
    assert check.read(target)==patched.read_bytes()
parts=[]
with destination.open('rb') as fp:
    for i in range(1,4):
        path=out/f'pvz2data.zip.{i:03d}';digest=hashlib.sha256();left=part_size
        with path.open('wb') as dst:
            while left and (chunk:=fp.read(min(left,1048576))):
                dst.write(chunk);digest.update(chunk);left-=len(chunk)
        assert path.stat().st_size>0
        parts.append(dict(name=path.name,size=path.stat().st_size,sha256=digest.hexdigest()))
    assert not fp.read(1)
result=dict(source_resource_zip_matches_v7=True,resource_entries=len(record),
            changed_resource_entries=[r['name'] for r in record if r['changed']],
            all_zip_crc_checks_passed=True,unchanged_compressed_streams_copied=True,
            entries=record,parts=parts)
(out/'repack-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
