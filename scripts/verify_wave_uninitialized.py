"""Prove SpawnCount is not initialized by the original factory.

Run two distinct allocator fill patterns and watch the actual registered word
for CPU stores throughout the original constructor. No host expected defaults.
"""
import hashlib,json
from reflection_emulation_support import h,seed
from unicorn import UC_HOOK_MEM_WRITE
seed();manager=h.call(0x11b10ec,[]);h.call(0x9c6944,[]);h.call(0x11b15b4,[manager])
original_allocate=h.alloc;cases=[]
for pattern in [0xa5,0x5a]:
 address=h.cursor;writes=[]
 def allocate(size):
  result=original_allocate(size)
  if result==address:
   assert size==0x60
   h.u.mem_write(result,bytes([pattern])*size)
  return result
 def watch(uc,access,target,size,value,unused):writes.append(dict(address=target-address,size=size,value=value))
 h.alloc=allocate;hook=h.u.hook_add(UC_HOOK_MEM_WRITE,watch,begin=address+88,end=address+91)
 result=h.call(0x9c4c70,[]);h.u.hook_del(hook);h.alloc=original_allocate
 assert result==address and not writes
 word=h.words(address+88)[0];assert word==pattern*0x01010101
 cases.append(dict(allocator_fill_byte=pattern,registered_offset=88,word_after_constructor=word,cpu_writes=writes))
 h.call(0x9c7a18,[result])
folder=h.base/'native_analysis/core_round28/wave_reflection';folder.mkdir(parents=True,exist_ok=True)
record=dict(original_sha256=hashlib.sha256((h.base/'raw/lib/armeabi/libSrc.so').read_bytes()).hexdigest(),cases=cases,spawn_count_initialized_by_factory=False,scope='Actual original 009c4c70 factory and 009c7a18 deletion execute. Two allocator fill patterns survive at registered +0x58 with zero CPU writes; neither pattern is a game default. Host represents this as undefined until a property write. Diagnostic evidence only, not added to C++ assertion count.')
(folder/'uninitialized-field-validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('PASS: original SpawnCount preserves both heap patterns with zero constructor stores')
