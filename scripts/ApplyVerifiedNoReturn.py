#@category APKAnalysis
import json,os
from java.math import BigInteger
args=getScriptArgs();proof=json.load(open(args[0]));rows=[]
known={r['address']:r for r in proof['seeds']+proof['proven_wrappers']}
fm=currentProgram.getFunctionManager();context=currentProgram.getProgramContext();mode=currentProgram.getRegister('TMode')
for address in ['00157794','01501ca4']:
    row=known[address];addr=toAddr(address);f=fm.getFunctionAt(addr);record={'address':address}
    thumb=int(row.get('instructions',[{'thumb':0}])[0]['thumb'])
    if f is None:
        owner=fm.getFunctionContaining(addr)
        if owner:record.update(status='skipped',reason='Already contained by '+str(owner.getEntryPoint()))
        else:
            ins=currentProgram.getListing().getInstructionAt(addr)
            if ins is None:context.setValue(mode,addr,addr,BigInteger.valueOf(thumb));disassemble(addr)
            value=context.getValue(mode,addr,False)
            if int(value or 0)!=thumb:record.update(status='skipped',reason='Existing decode mode differs')
            else:f=createFunction(addr,None)
    if f:f.setNoReturn(True);record.update(status='applied',size=f.getBody().getNumAddresses())
    rows.append(record)
with open(args[1],'w') as fp:json.dump(rows,fp,indent=2)
print('VERIFIED_NORETURN_APPLIED '+str(rows))
