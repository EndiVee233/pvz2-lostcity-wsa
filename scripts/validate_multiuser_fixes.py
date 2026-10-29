from native_emulation_support import machine,base
import json,struct
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
p=base/'native_analysis/multiuser/fixes';record=json.loads((p/'patch-manifest.json').read_text())
b=(p/'libSrc-multiuser-fixed.so').read_bytes();code_addr=int(record['code_address'],16);off=int(record['code_file_offset'],16)
uc,_=machine();uc.mem_map(code_addr,4096);uc.mem_write(code_addr,b[off:])
for row in record['patches']:uc.mem_write(int(row['address'],16),bytes.fromhex(row['patched']))
events=[];kind='';delete_result=1;obj=0x6000000;dest=0x6005000;source=0x6005100;stop=0x5000100;stack=0x4080000
def word(a,v):uc.mem_write(a,struct.pack('<I',v))
word(0x1846b60,0x6001000);word(0x6001000+0x136c,0x6003000);word(0x6003000+0xa8,0x6004000)
def hook(uc,a,size,user):
 if a in (stop,0x46f91c):uc.emu_stop();return
 if a==0x7fc270:
  assert uc.reg_read(UC_ARM_REG_R0)==0x6004000;events.append('pop_screen')
 elif a==0x11e74b4:uc.reg_write(UC_ARM_REG_R0,0x1234);events.append('registry')
 elif a==0x1ea034:
  assert uc.reg_read(UC_ARM_REG_R1)==obj+0xd8;uc.reg_write(UC_ARM_REG_R0,0x6006000);events.append('resolve')
 elif a==0x71669c:
  assert uc.reg_read(UC_ARM_REG_R0)==dest and uc.reg_read(UC_ARM_REG_R1)==0x6006000;events.append('existing_name')
 elif a==0x14fae38:
  assert uc.reg_read(UC_ARM_REG_R0)==dest and uc.reg_read(UC_ARM_REG_R1)==source;events.append('random_name')
 elif a==0x7bdeac:
  assert uc.reg_read(UC_ARM_REG_R0)==obj;events.append('delete');uc.reg_write(UC_ARM_REG_R0,delete_result)
 elif a==0x4b10a0:
  assert uc.reg_read(UC_ARM_REG_R0)==0x6007004;events.append('save_local');uc.reg_write(UC_ARM_REG_R0,1)
 else:return
 uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
uc.hook_add(UC_HOOK_CODE,hook);rows=[]
for button in (4,5,6,11):
 events.clear();uc.reg_write(UC_ARM_REG_R0,obj);uc.reg_write(UC_ARM_REG_R1,button);uc.reg_write(UC_ARM_REG_SP,stack);uc.reg_write(UC_ARM_REG_LR,stop)
 uc.emu_start(0x46f918,0,count=100)
 assert events==(['pop_screen'] if button==6 else [])
 assert uc.reg_read(UC_ARM_REG_SP)==stack-(0 if button==6 else 36)
 rows.append({'button':button,'events':list(events),'passed':True})
for mode in (0,1,2):
 events.clear();word(obj+0xe0,mode)
 for reg,value in [(UC_ARM_REG_R0,dest),(UC_ARM_REG_R1,source),(UC_ARM_REG_R6,obj),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop)]:uc.reg_write(reg,value)
 uc.emu_start(int(record['prefill_address'],16),0,count=100)
 assert events==(['registry','resolve','existing_name'] if mode==1 else ['random_name'])
 assert uc.reg_read(UC_ARM_REG_SP)==stack and uc.reg_read(UC_ARM_REG_R6)==obj
 rows.append({'editor_mode':mode,'events':list(events),'passed':True})
word(obj+4,0x6007000)
for delete_result in (0,1,2):
 events.clear()
 for reg,value in [(UC_ARM_REG_R0,obj),(UC_ARM_REG_R1,source),(UC_ARM_REG_SP,stack),(UC_ARM_REG_LR,stop)]:uc.reg_write(reg,value)
 uc.emu_start(int(record['delete_address'],16),0,count=100)
 assert events==(['delete','save_local'] if delete_result else ['delete'])
 assert uc.reg_read(UC_ARM_REG_R0)==delete_result and uc.reg_read(UC_ARM_REG_SP)==stack
 rows.append({'delete_result':delete_result,'events':list(events),'passed':True})
(p/'shim-emulation-validation.json').write_text(json.dumps({'passed':True,'cases':rows,'scope':'Injected ARM control flow; engine string/registry/pop callbacks mocked'},indent=2),encoding='utf-8')
print('ARM shim cases passed:',len(rows))
