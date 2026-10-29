#@category APKAnalysis
import json,os
args=getScriptArgs();proofs=json.load(open(args[0]));out=args[1]
if len(args)>2:proofs['seeds'].extend(json.load(open(args[2])))
context=currentProgram.getProgramContext();mode=currentProgram.getRegister('TMode')
listing=currentProgram.getListing();fm=currentProgram.getFunctionManager()
for row in proofs['proven_wrappers']:
    f=fm.getFunctionAt(toAddr(row['address']))
    row['body_ranges']=[{'start':str(r.getMinAddress()),'end':str(r.getMaxAddress())} for r in f.getBody().getAddressRanges()]
    for ins in row['instructions']:
        value=context.getValue(mode,toAddr(ins['address']),False)
        ins['thumb']=int(value) if value else 0
for row in proofs['seeds']:
    f=fm.getFunctionAt(toAddr(row['address']));row['symbol_source']=str(f.getSymbol().getSource())
    if f.isThunk():
        target=f.getThunkedFunction(True)
        row['resolved_thunk']={'address':str(target.getEntryPoint()),'name':target.getName(),'external':bool(target.isExternal())}
with open(out,'w') as fp:json.dump(proofs,fp,indent=2)
print('NORETURN_AUDITED '+str(len(proofs['proven_wrappers'])))
