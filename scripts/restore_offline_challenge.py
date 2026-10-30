"""Restore retained challenge flow with a device-clock fallback on failed time requests.
Only this task's error-dialog body is reused. Online callbacks, attempt deduction,
level selection and rewards retain their original logic.
"""
import hashlib,json,struct
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
source=base/'native_analysis/original_speed_button/libSrc-original-speed-unlocked.so'
original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='fd7b6a33423cb4c18c117a2dab103f6ae56b92be711a144a6110533b92076928'
out=base/'native_analysis/offline_challenge';out.mkdir(exist_ok=True)
start=0xf864a8
asm='''
push {r0,r3,r4,r5,r6,lr}
sub sp,sp,#8
mov r0,sp
mov r1,#0
bl 0x157974
cmp r0,#0
bne finish
ldr r5,[sp]
cmp r5,#0
ble finish
bl 0xf854ac
str r5,[r0,#12]
adr r0,manager_delta
ldr r1,[r0]
add r0,r0,r1
ldr r0,[r0]
cmp r0,#0
beq finish
bl 0x7b98dc
cmp r0,#0
beq finish
mov r5,r0
add r0,r5,#0x320
bl 0x758d3c
cmp r0,#0
bne generate
ldr r0,[r5,#0x48]
ldr r1,[r5,#0x4c]
cmp r0,r1
bne finish
generate:
mov r0,r5
bl 0x737ed8
mov r0,r5
bl 0x7210c4
finish:
add sp,sp,#8
pop {r0,r3,r4,r5,r6,lr}
b 0xf865ac
manager_delta:
.word 0
'''
encoding,_=Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(asm,start)
code=bytearray(encoding)
struct.pack_into('<I',code,len(code)-4,0x18400a4-(start+len(code)-4))
assert len(code)<=0xf86594-start
blob=bytearray(original);blob[start-0x10000:start-0x10000+len(code)]=code
assert blob[0xf864a4-0x10000:0xf864a8-0x10000]==bytes.fromhex('4000001a')
# Challenge submenu only: legacy introduction highlighting otherwise disables
# the other two modes even after an offline attempt returns. Do not change the
# profile tutorial state, difficulty unlocks, or introductions in other menus.
intro_site=0xa4880c
intro_stub=start+len(code)
intro_asm='cmp r7,#0; moveq r3,#0; ldrne r3,[r0,#0x1c]; b 0xa48810'
intro_code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(intro_asm,intro_stub)[0])
assert intro_stub+len(intro_code)<=0xf86594
assert original[intro_site-0x10000:intro_site-0x10000+4]==bytes.fromhex('1c3090e5')
intro_branch=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(f'b {intro_stub}',intro_site)[0])
blob[intro_site-0x10000:intro_site-0x10000+4]=intro_branch
blob[intro_stub-0x10000:intro_stub-0x10000+len(intro_code)]=intro_code

# Execute actual callback and original daily reset; stub OS/config/event/UI boundaries.
cases=[]
for success in (False,True):
 for mode in range(3):
  for old_day in (1260929,1260930,1260931):
   uc,imports=machine();uc.mem_write(start,bytes(code))
   task,app,manager,player,clock,config,tm,event,node=(0x6000000+i*0x1000 for i in range(9))
   def put(a,v):uc.mem_write(a,struct.pack('<I',v&0xffffffff))
   def get(a):return struct.unpack('<I',uc.mem_read(a,4))[0]
   put(task+4,mode);put(0x1846b60,app);put(0x18400a4,manager);put(0x1833050,event)
   put(player+0x320,old_day)
   for offset in (0x338,0x340,0x348):
    key=0x12345678+offset;shift=key&31
    put(player+offset,key);put(player+offset-4,((key<<shift)|(key>>(32-shift)))&0xffffffff)
   put(player+0x48,player+0x800);put(player+0x4c,player+0x814)
   put(tm+12,30);put(tm+16,9);put(tm+20,126);put(tm+24,5)
   calls=[];seeds=[];saves=[]
   def ret(cpu,value=0):cpu.reg_write(UC_ARM_REG_R0,value);cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
   def hook(cpu,pc,size,user):
    r0=cpu.reg_read(UC_ARM_REG_R0);r1=cpu.reg_read(UC_ARM_REG_R1)
    if pc==0x157974:put(r0,1793318400);put(r0+4,0);ret(cpu)
    elif pc==0xf854ac:ret(cpu,clock)
    elif pc==0x7b98dc:assert r0==manager;ret(cpu,player)
    elif pc==0x157854:ret(cpu,tm)
    elif pc==0x41a4e8:ret(cpu)
    elif pc==0x4161fc:ret(cpu,config)
    elif pc in (0x8d4190,0x8d4380):ret(cpu)
    elif pc==0x8d5a68:ret(cpu,1)
    elif pc==0x8d60d4:ret(cpu,1)
    elif pc==0x1f1314:ret(cpu,node)
    elif pc==0x34f688:ret(cpu)
    elif pc==0x737ed8:assert r0==player;seeds.append(True);ret(cpu)
    elif pc==0x7210c4:assert r0==player;saves.append(True);ret(cpu)
    elif pc==0x420c24:assert r0==app;calls.append(r1);ret(cpu)
    elif pc in imports:raise AssertionError(('unexpected import',imports[pc]))
   uc.hook_add(UC_HOOK_CODE,hook)
   stack,end=0x4080000,0x5000100
   for register,value in ((UC_ARM_REG_R0,task),(UC_ARM_REG_R1,int(success)),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,end),(UC_ARM_REG_R4,0x12345678)):
    uc.reg_write(register,value)
   uc.emu_start(0xf86478,end,count=3000)
   assert uc.reg_read(UC_ARM_REG_PC)==end and uc.reg_read(UC_ARM_REG_SP)==stack
   assert uc.reg_read(UC_ARM_REG_R4)==0x12345678 and calls==[mode]
   refreshed=not success and old_day<1260930
   assert len(seeds)==len(saves)==int(refreshed)
   for offset in (0x334,0x33c,0x344):
    raw,key=get(player+offset),get(player+offset+4);shift=key&31
    assert (((raw>>shift)|(raw<<(32-shift)))&0xffffffff)^key==int(refreshed)
   assert get(player+0x320)==(1260930 if refreshed else old_day)
   cases.append(dict(server_success=success,mode=mode,stored_day=old_day,refreshed=refreshed))
intro_cases=[]
uc,_=machine();uc.mem_write(intro_site,intro_branch);uc.mem_write(intro_stub,intro_code)
for menu in range(13):
 for state in (0,9,12,15,16,19,21,23,32):
  uc.mem_write(0x600001c,struct.pack('<I',state))
  uc.reg_write(UC_ARM_REG_R0,0x6000000);uc.reg_write(UC_ARM_REG_R7,menu)
  uc.emu_start(intro_site,0xa48810,count=10)
  assert uc.reg_read(UC_ARM_REG_PC)==0xa48810
  assert uc.reg_read(UC_ARM_REG_R3)==(0 if menu==0 else state)
  assert struct.unpack('<I',uc.mem_read(0x600001c,4))[0]==state
  intro_cases.append(dict(menu=menu,profile_state=state))
target=out/'libSrc-offline-challenge.so';target.write_bytes(blob)
record=dict(source_sha256=hashlib.sha256(original).hexdigest(),patched_sha256=hashlib.sha256(blob).hexdigest(),
 patches=[dict(ghidra_address=hex(start),file_offset=hex(start-0x10000),length=len(code),
 before_sha256=hashlib.sha256(original[start-0x10000:start-0x10000+len(code)]).hexdigest(),after_hex=code.hex(),
 scope='Challenge time-task failure body only; PIC device clock and original daily reset'),
 dict(ghidra_address=hex(intro_site),before='1c3090e5',after=intro_branch.hex(),
 stub_address=hex(intro_stub),stub_hex=intro_code.hex(),scope='Challenge submenu introduction lock only')],
 arm_cases_passed=len(cases)+len(intro_cases),cases=cases,intro_cases=intro_cases,runtime_verified=False,
 scope='Original daily limits, same-day persistence and backward-clock protection retained; WSA gameplay/rewards need separate verification.')
(out/'patch-validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in record.items() if k not in ('cases','intro_cases','patches')},indent=2))
