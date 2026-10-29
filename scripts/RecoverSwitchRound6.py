#@category APKAnalysis
import json,os,codecs,time
from java.math import BigInteger
from ghidra.program.database import SpecExtension
from ghidra.program.model.address import AddressSet
from ghidra.program.model.symbol import SourceType
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];switch=json.load(open(args[1]));xml=open(args[2]).read()
if not os.path.isdir(out):os.makedirs(out)
fm=currentProgram.getFunctionManager();context=currentProgram.getProgramContext();mode=currentProgram.getRegister('TMode')
extensions=SpecExtension(currentProgram);extensions.addReplaceCompilerSpecExtension(xml,monitor)
print('ROUND6_EXTENSION_INSTALLED')
def ensure(address,thumb,name):
    addr=toAddr(address);ins=currentProgram.getListing().getInstructionAt(addr)
    if ins is None:context.setValue(mode,addr,addr,BigInteger.valueOf(thumb));disassemble(addr)
    f=fm.getFunctionAt(addr)
    if f is None:f=createFunction(addr,name)
    return f
helper=ensure('015eddfc',1,'__gnu_thumb1_case_si')
helper.setInline(False);helper.setCallFixup('pvz2_thumb_case_si')
for addr,thumb in [('00157794',0),('0015867c',0),('01501ca4',1)]:
    f=ensure(addr,thumb,None)
    if f:f.setNoReturn(True)
entry=toAddr(switch['function']);f=fm.getFunctionAt(entry)
if f:fm.removeFunction(entry)
# Decode every independently recovered destination. Avoid decoding the table as code.
for address in sorted(set(e['target'] for e in switch['entries'])):
    addr=toAddr(address);ins=currentProgram.getListing().getInstructionAt(addr)
    if ins is None:context.setValue(mode,addr,addr,BigInteger.ONE);disassemble(addr)
context.setValue(mode,entry,entry,BigInteger.ONE) if currentProgram.getListing().getInstructionAt(entry) is None else None
disassemble(entry)
body=AddressSet(CreateFunctionCmd.getFunctionBody(currentProgram,entry,monitor))
for address in sorted(set(e['target'] for e in switch['entries'])):
    body.add(CreateFunctionCmd.getFunctionBody(currentProgram,toAddr(address),monitor))
body.delete(toAddr('01505580'),toAddr('015056af'))
owners=[]
for owner in fm.getFunctionsOverlapping(body):
    owners.append({'address':str(owner.getEntryPoint()),'name':owner.getName()})
for owner in owners:fm.removeFunction(toAddr(owner['address']))
f=fm.createFunction('Candidate_Switch_01505544',entry,body,SourceType.ANALYSIS)
print('ROUND6_SWITCH_BODY '+str(body.getNumAddresses()))
decomp=DecompInterface();opts=DecompileOptions();opts.setMaxPayloadMBytes(96);opts.setMaxInstructions(150000)
decomp.setOptions(opts);decomp.openProgram(currentProgram);started=time.time()
result=decomp.decompileFunction(f,120,monitor);c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
record={'address':str(entry),'size':body.getNumAddresses(),'body_ranges':[{'start':str(r.getMinAddress()),'end':str(r.getMaxAddress())} for r in body.getAddressRanges()],
        'removed_owners_in_experimental_project':owners,'helper_callfixup':helper.getCallFixup(),'helper_model_xml':xml,'seconds':round(time.time()-started,2)}
if c:
    text=unicode(c.getC())
    with codecs.open(os.path.join(out,'01505544.c'),'w','utf-8') as fp:fp.write(u'/* Experimental switch recovery using a sample-specific, machine-checked helper model. */\n'+text)
    record.update(status='ok',file='01505544.c',halt_baddata='halt_baddata' in text,warnings=text.count('/* WARNING:'))
    high=result.getHighFunction();tables=[]
    if high:
        for table in high.getJumpTables():
            tables.append({'switch_address':str(table.getSwitchAddress()),'cases':[str(a) for a in table.getCases()],'labels':[int(v) for v in table.getLabelValues()]})
    record['jump_tables']=tables
else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(record,fp,indent=2)
decomp.dispose();print('ROUND6_SWITCH_DONE '+record['status'])
