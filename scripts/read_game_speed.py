"""Read only the known speed scalar from the debuggable isolated game process."""
import json
import struct
import subprocess

adb=['K:/pvz2-tools/platform-tools/adb.exe','-s','127.0.0.1:58526']
app='com.popcap.pvz2cthd.reconstruction'
def call(*args):return subprocess.check_output([*adb,*args],stderr=subprocess.PIPE,timeout=30)
def read_speed():
    pid=call('shell','pidof',app).decode().strip()
    assert pid.isdecimal()
    maps=call('shell','run-as',app,'cat',f'/proc/{pid}/maps').decode()
    candidates=[line.split() for line in maps.splitlines() if line.endswith('/libSrc.so')]
    first=next(row for row in candidates if int(row[2],16)==0)
    load_base=int(first[0].split('-')[0],16)
    def mem(address,size):
        raw=call('exec-out','run-as',app,'dd',f'if=/proc/{pid}/mem',
                 'bs=1',f'skip={address}',f'count={size}','status=none')
        assert len(raw)==size
        return raw
    controller=struct.unpack('<I',mem(load_base+0x1830528,4))[0]
    value=struct.unpack('<f',mem(controller+0x30,4))[0]
    assert value in (1.0,2.0),value
    return value

if __name__=='__main__':
    print(json.dumps({'speed_multiplier':read_speed()}))
