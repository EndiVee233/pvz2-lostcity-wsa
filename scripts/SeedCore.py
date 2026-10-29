#@category APKAnalysis
import json
from java.math import BigInteger
from ghidra.program.model.symbol import SourceType

args=getScriptArgs()
entries=json.load(open(args[0]))
base=currentProgram.getImageBase().getOffset()
for item in entries:
    addr=toAddr(base+int(item['elf_address'],16))
    try:
        mode=currentProgram.getRegister('TMode')
        if mode:
            currentProgram.getProgramContext().setValue(mode,addr,addr,BigInteger.ONE if item['thumb'] else BigInteger.ZERO)
        disassemble(addr)
        function=getFunctionAt(addr)
        name='JNI_dyn_'+item['name']+'_'+str(addr)
        if function is None:function=createFunction(addr,name)
        elif function.getName().startswith('FUN_'):function.setName(name,SourceType.USER_DEFINED)
        if function:
            function.setComment('Recovered from ELF JNINativeMethod table '+item['table_address']+'; '+item['name']+item['signature'])
    except Exception as error:print('SEED_WARNING '+str(error))
for option in ['Decompiler Switch Analysis','Call Convention ID','Stack','Non-Returning Functions - Discovered']:
    try:setAnalysisOption(currentProgram,option,'false')
    except Exception as error:print('OPTION_WARNING '+option+': '+str(error))
print('CORE_SEEDED '+str(len(entries)))
