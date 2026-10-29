"""Single-thread primitives around the real ARM reflection/registry runtime.

Process atexit registration is excluded from this explicit test owner. Decimal
strtod uses the host C runtime only in the common decimal domain; its double
result is passed through the ARM soft-float ABI, not converted to float here.
"""
import ctypes,struct
import recover_owned_stores as h
from unicorn import UC_HOOK_CODE

special={a:n for a,n in h.imports.items() if n in ['__cxa_atexit','atoi','strtod','pthread_once','pthread_mutex_init','pthread_mutex_lock','pthread_mutex_unlock','pthread_mutex_destroy','pthread_cond_broadcast','pthread_key_create','pthread_getspecific','pthread_setspecific']}
for a in special:del h.imports[a]
once_returns=[];tls={};next_key=1
crt=ctypes.CDLL('msvcrt');crt.atoi.argtypes=[ctypes.c_char_p];crt.atoi.restype=ctypes.c_int
crt.strtod.argtypes=[ctypes.c_char_p,ctypes.c_void_p];crt.strtod.restype=ctypes.c_double
def primitives(uc,address,size,unused):
 global next_key
 if address==0x5000600:
  uc.reg_write(h.UC_ARM_REG_R0,0);uc.reg_write(h.UC_ARM_REG_PC,once_returns.pop());return
 name=special.get(address)
 if not name:return
 r0,r1=[uc.reg_read(r) for r in [h.UC_ARM_REG_R0,h.UC_ARM_REG_R1]];lr=uc.reg_read(h.UC_ARM_REG_LR)
 if name=='pthread_once' and not h.words(r0)[0]:
  h.put(r0,1);once_returns.append(lr);uc.reg_write(h.UC_ARM_REG_LR,0x5000600);uc.reg_write(h.UC_ARM_REG_PC,r1);return
 if name=='strtod':
  assert r1==0,'only no-end-pointer decimal reads covered'
  lo,hi=struct.unpack('<II',struct.pack('<d',crt.strtod(h.narrow(r0),None)))
  uc.reg_write(h.UC_ARM_REG_R0,lo);uc.reg_write(h.UC_ARM_REG_R1,hi);uc.reg_write(h.UC_ARM_REG_PC,lr);return
 if name=='atoi':value=crt.atoi(h.narrow(r0))&0xffffffff
 elif name=='pthread_key_create':h.put(r0,next_key);next_key+=1;value=0
 elif name=='pthread_getspecific':value=tls.get(r0,0)
 elif name=='pthread_setspecific':tls[r0]=r1;value=0
 else:value=0
 uc.reg_write(h.UC_ARM_REG_R0,value);uc.reg_write(h.UC_ARM_REG_PC,lr)
h.u.hook_add(UC_HOOK_CODE,primitives)

def seed_ctype():
 table=bytearray(257)
 for c in range(128):
  flags=0
  if c<32 or c==127:flags|=32
  if 65<=c<=90:flags|=1
  if 97<=c<=122:flags|=2
  if 48<=c<=57:flags|=4
  if c in [9,10,11,12,13,32]:flags|=8
  if 32<c<127 and not chr(c).isalnum():flags|=16
  if chr(c) in '0123456789abcdefABCDEF':flags|=64
  if c==32:flags|=128
  table[c+1]=flags
 h.u.mem_write(0x600f000,bytes(table))
 for a,name in h.imports.items():
  if name=='_ctype_':h.put(a,0x600f000)

def seed():
 h.cursor=0x8000000;h.records=[];h.events=[];h.alias_ids=[]
 h.u.mem_write(0x6000000,bytes(0x20000));h.put(0x18cbf70,h.REG);h.put(0x18cbf74,h.REG)
 # _INIT_1265 assigns the evidenced packages/ prefix length (round 18).
 h.put(0x18cbf6c,9)
 h.put(h.REG+0x18,0x87654321);h.put(h.REG+0x20,0,0,h.REG+0x20,h.REG+0x20)
 # Result of the original singleton guards for empty class list/name map.
 # Destructor scheduling is outside the explicit single-thread owner scope.
 h.put(0x18cbfa0,1,0,0,0);h.put(0x18cbfb0,1,0,0,0,0x18cbfb8,0x18cbfb8,0)
 h.pool=h.call(0x11f13a8,[])
 seed_ctype()
