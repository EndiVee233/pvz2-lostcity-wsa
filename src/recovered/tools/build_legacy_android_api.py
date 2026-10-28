"""Add one removed Notification declaration to the compile-only Android 30 API jar."""
from pathlib import Path
import struct,zipfile,json,hashlib
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project'
source=p/'tools/android-30.jar';out=p/'tools/android-30-legacy.jar'
u2=lambda b,i:struct.unpack_from('>H',b,i)[0]
u4=lambda b,i:struct.unpack_from('>I',b,i)[0]
be2=lambda x:struct.pack('>H',x)
be4=lambda x:struct.pack('>I',x)
with zipfile.ZipFile(source) as z:b=z.read('android/app/Notification.class')
assert b[:4]==b'\xca\xfe\xba\xbe'
count=u2(b,8);i=1;pos=10;strings=[]
while i<count:
    tag=b[pos];pos+=1
    if tag==1:
        size=u2(b,pos);strings.append(b[pos+2:pos+2+size]);pos+=2+size
    elif tag in (3,4):pos+=4
    elif tag in (5,6):pos+=8;i+=1
    elif tag in (7,8,16,19,20):pos+=2
    elif tag in (9,10,11,12,17,18):pos+=4
    elif tag==15:pos+=3
    else:raise ValueError(tag)
    i+=1
cp_end=pos;pos+=6;pos+=2+2*u2(b,pos)
# Member headers follow their table's u2 count, so walk these explicitly.
def member_end(pos,n):
    for _ in range(n):
        attrs=u2(b,pos+6);pos+=8
        for _ in range(attrs):pos+=6+u4(b,pos+2)
    return pos
fields=u2(b,pos);pos=member_end(pos+2,fields)
method_count_pos=pos;methods=u2(b,pos);methods_end=member_end(pos+2,methods)
name='setLatestEventInfo';desc='(Landroid/content/Context;Ljava/lang/CharSequence;Ljava/lang/CharSequence;Landroid/app/PendingIntent;)V'
assert name.encode() not in strings
entries=b''.join(b'\x01'+be2(len(s.encode()))+s.encode() for s in (name,desc,'Code'))
code=be2(1)+be2(5)+be4(2)+b'\x01\xbf'+be2(0)+be2(0)
method=be2(1)+be2(count)+be2(count+1)+be2(1)+be2(count+2)+be4(len(code))+code
patched=b[:8]+be2(count+3)+b[10:cp_end]+entries+b[cp_end:method_count_pos]+be2(methods+1)+b[method_count_pos+2:methods_end]+method+b[methods_end:]
with zipfile.ZipFile(source) as src,zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():dst.writestr(info,patched if info.filename=='android/app/Notification.class' else src.read(info.filename))
record={'compile_only':True,'input_jar_sha256':hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),
        'output_jar_sha256':hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),
        'only_changed_entry':'android/app/Notification.class','added_method':name+desc,
        'method_body':'throw null; compile declaration only, never packaged as Android framework implementation'}
(p/'tools/android-30-legacy.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
