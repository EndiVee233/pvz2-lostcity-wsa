"""Continue native recovery after the offline UI fix; verify original bridge instructions."""
from pathlib import Path
import struct,json,sys
from native_emulation_support import machine,base
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
out=base/'native_analysis/core_round7/network_bridge';out.mkdir(parents=True,exist_ok=True)
rows=[]
for status in [0,1,2,3,0xffffffff]:
    uc,_=machine();obj=0x6000000;env=0x6001000;jobject=0x12345678;events=[];initial=bytearray(b'\xa5'*0x34)
    struct.pack_into('<I',initial,8,jobject);uc.mem_write(obj,bytes(initial))
    uc.reg_write(UC_ARM_REG_SP,0x4080000);uc.reg_write(UC_ARM_REG_LR,0x5000100);uc.reg_write(UC_ARM_REG_R0,obj)
    def hook(uc,address,size,user):
        if address==0x5000100:uc.emu_stop();return
        if address==0x133ac10:
            uc.reg_write(UC_ARM_REG_R0,env);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
        if address==0x137a1fc:
            args=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            assert args==[0x18d5264,env,jobject],args;events.append(args)
            uc.reg_write(UC_ARM_REG_R0,status);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    uc.hook_add(UC_HOOK_CODE,hook);uc.emu_start(0x137a2b0,0,count=100)
    expected=bytearray(initial);struct.pack_into('<I',expected,0x24,status)
    assert bytes(uc.mem_read(obj,0x34))==expected and len(events)==1
    assert uc.reg_read(UC_ARM_REG_SP)==0x4080000 and uc.reg_read(UC_ARM_REG_PC)==0x5000100
    rows.append({'function':'0x0137a2b0','input_java_status':status,'cached_status_offset':'0x24','jobject_offset':'0x08','other_object_bytes_preserved':True,'stack_preserved':True})
thunks=[]
for entry,target in [(0x137a488,0x137a40c),(0x137a4b0,0x137a490)]:
    for this in [0x6000004,0x6000044,0x6001004]:
        uc,_=machine();uc.reg_write(UC_ARM_REG_R0,this);uc.reg_write(UC_ARM_REG_LR,0x5000100);uc.reg_write(UC_ARM_REG_SP,0x4080000)
        def stop(uc,address,size,user):
            if address==target:uc.emu_stop()
        uc.hook_add(UC_HOOK_CODE,stop);uc.emu_start(entry,0,count=10)
        assert uc.reg_read(UC_ARM_REG_PC)==target and uc.reg_read(UC_ARM_REG_R0)==this-4
        assert uc.reg_read(UC_ARM_REG_SP)==0x4080000 and uc.reg_read(UC_ARM_REG_LR)==0x5000100
        thunks.append({'entry':hex(entry),'target':hex(target),'secondary_this':hex(this),'primary_this':hex(this-4),'stack_and_return_address_preserved':True})
record={'scope':'Original ARM instructions; JNI helper results are supplied by bounded hooks, not a full native-engine test',
        'status_refresh_cases':rows,'secondary_base_thunk_cases':thunks,'cases_passed':len(rows)+len(thunks),
        'newly_decoded_small_entrypoints':['0x0137a488','0x0137a4b0'],
        'layout_evidence':{'object_allocation_bytes':'0x34','primary_vptr_offset':'0x00','secondary_vptr_offset':'0x04','java_object_offset':'0x08','status_offset':'0x24'},
        'source_fragment_compiled':False,'source_fragment_linked_into_apk':False}
(out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2))
