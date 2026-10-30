from pathlib import Path
import sys
base=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(base/'tools/python_libs'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
blob=(base/'raw/lib/armeabi/libSrc.so').read_bytes()
md=Cs(CS_ARCH_ARM,CS_MODE_ARM)
instructions=list(md.disasm(blob[0x8f3588:0x8f3588+0x800],0x903588))
for i,ins in enumerate(instructions):
    if ins.mnemonic=='bl' and ins.op_str=='#0x71688c':
        for row in instructions[max(0,i-14):i+16]:print(hex(row.address),row.bytes.hex(),row.mnemonic,row.op_str)
print('tail')
for row in instructions[-35:]:print(hex(row.address),row.mnemonic,row.op_str)
