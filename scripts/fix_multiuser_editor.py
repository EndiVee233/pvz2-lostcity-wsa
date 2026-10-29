"""Restore transactional profile editing using small position-independent ARM shims."""
from pathlib import Path
import sys,struct,hashlib,json
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'tools/python_libs'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from elftools.elf.elffile import ELFFile
source=base/'native_analysis/multiuser/libSrc-multiuser.so';blob=bytearray(source.read_bytes())
assert hashlib.sha256(blob).hexdigest()=='8cf911dc04ceace93dbd3569d53b605fde87f32793a98728587ca6264983b3b6'
out=base/'native_analysis/multiuser/fixes';out.mkdir(exist_ok=True)
ks=Ks(KS_ARCH_ARM,KS_MODE_ARM);records=[]
def asm(s,a):return bytes(ks.asm(s,a)[0])
def patch(a,s,expected):
 expected=bytes.fromhex(expected);off=a-0x10000;old=bytes(blob[off:off+len(expected)])
 assert old==expected, (hex(a),old.hex())
 new=asm(s,a);assert len(new)==len(old)
 blob[off:off+len(new)]=new;records.append({'address':hex(a),'original':old.hex(),'patched':new.hex(),'asm':s})
# The added RX mapping occupies the old GNU_STACK program-header slot. Shared
# libraries use the process's existing non-executable stack; no RWX mapping.
va=0x1a00000;address=va+0x10000;offset=(len(blob)+4095)&~4095
code=asm('''
cmp r1, #6
beq cancel
push {r4-r10,fp,lr}
b 0x46f91c
cancel:
push {r4,lr}
ldr r0, app_delta
app_add: add r0, pc, r0
ldr r0, [r0]
add r0, r0, #0x1300
ldr r0, [r0, #0x6c]
ldr r0, [r0, #0xa8]
bl 0x7fc270
pop {r4,pc}
app_delta: .word 0
''',address)
# app_add is the 7th instruction, PC observes its address + 8.
code=bytearray(code);struct.pack_into('<I',code,len(code)-4,(0x1846b60-(address+24+8))&0xffffffff)
prefill_address=address+len(code)
prefill=asm('''
push {r4,r5,r6,lr}
mov r4,r0
mov r5,r1
ldr r2,[r6,#0xe0]
cmp r2,#1
bne random_copy
bl 0x11e74b4
add r1,r6,#0xd8
bl 0x1ea034
mov r1,r0
mov r0,r4
bl 0x71669c
pop {r4,r5,r6,pc}
random_copy:
mov r0,r4
mov r1,r5
blx 0x14fae38
pop {r4,r5,r6,pc}
''',prefill_address)
code+=prefill
delete_address=address+len(code)
code+=asm('''
push {r4,r5,r6,lr}
mov r4,r0
bl 0x7bdeac
mov r5,r0
cmp r0,#0
beq delete_done
ldr r0,[r4,#4]
add r0,r0,#4
bl 0x4b10a0
delete_done:
mov r0,r5
pop {r4,r5,r6,pc}
''',delete_address)
patch(0x46f918,'b '+hex(address),'f04f2de9')
patch(0x4755cc,'mov r1,#6','0410a0e3')
patch(0x474df4,'bl '+hex(prefill_address),'0f1842fa')
patch(0x474f20,'sub r1,fp,#0xb4','0a10a0e1')
patch(0x474f34,'mov r3,#1','0030a0e3')
patch(0x46e864,'bl '+hex(delete_address),'903d0deb')
phoff=struct.unpack_from('<I',blob,28)[0];entsize,count=struct.unpack_from('<HH',blob,42)
for i in range(count):
 pos=phoff+i*entsize
 if struct.unpack_from('<I',blob,pos)[0]==0x6474e551:
  original_header=bytes(blob[pos:pos+32]).hex()
  struct.pack_into('<8I',blob,pos,1,offset,va,va,len(code),len(code),5,4096)
  break
else:raise AssertionError('Missing GNU_STACK header')
blob+=b'\0'*(offset-len(blob));blob+=code
target=out/'libSrc-multiuser-fixed.so';target.write_bytes(blob)
record={'patches':records,'code_address':hex(address),'code_file_offset':hex(offset),'prefill_address':hex(prefill_address),'delete_address':hex(delete_address),'code_bytes':len(code),'replaced_program_header':original_header,'original_baseline_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(blob).hexdigest(),'runtime_verified':False}
(out/'patch-manifest.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
(out/'shims.asm.txt').write_text('\n'.join(hex(i.address)+' '+i.mnemonic+' '+i.op_str for i in __import__('capstone').Cs(__import__('capstone').CS_ARCH_ARM,__import__('capstone').CS_MODE_ARM).disasm(bytes(code),address)),encoding='utf-8')
print(json.dumps(record,indent=2))
