#@category APKAnalysis
import json,os,codecs,time
from java.math import BigInteger
from java.util import ArrayList
from ghidra.program.model.symbol import SourceType,RefType
from ghidra.program.model.address import AddressSet
from ghidra.program.model.pcode import JumpTable
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];config=json.load(open(args[1]));records=[]
if not os.path.isdir(out):os.makedirs(out)
fm=currentProgram.getFunctionManager();context=currentProgram.getProgramContext();mode=currentProgram.getRegister('TMode')
for request in config['functions']:
    entry=toAddr(request['address']);branch=toAddr(request['switch_address']);destinations=ArrayList()
    context.setValue(mode,entry,entry,BigInteger.ZERO) if currentProgram.getListing().getInstructionAt(entry) is None else None
    disassemble(entry)
    for row in request['entries']:
        address=toAddr(row['instruction_address']);disassemble(address)
        destinations.add(address)
    f=fm.getFunctionAt(entry)
    if f:fm.removeFunction(entry)
    ins=currentProgram.getListing().getInstructionAt(branch)
    for target in destinations:ins.addOperandReference(0,target,RefType.COMPUTED_JUMP,SourceType.USER_DEFINED)
    body=AddressSet(CreateFunctionCmd.getFunctionBody(currentProgram,entry,monitor))
    for target in destinations:body.add(CreateFunctionCmd.getFunctionBody(currentProgram,target,monitor))
    owners=[f for f in fm.getFunctionsOverlapping(body)]
    for owner in owners:fm.removeFunction(owner.getEntryPoint())
    f=fm.createFunction('Candidate_Format_'+request['address'],entry,body,SourceType.ANALYSIS)
    JumpTable(branch,destinations,True).writeOverride(f)
    print('FORMAT_BODY '+request['address']+' '+str(body.getNumAddresses()))
    for style,timeout in [('decompile',90),('normalize',30)]:
        decomp=DecompInterface();opts=DecompileOptions();opts.setMaxPayloadMBytes(96);opts.setMaxInstructions(150000)
        decomp.setOptions(opts);decomp.setSimplificationStyle(style);decomp.openProgram(currentProgram);t=time.time()
        result=decomp.decompileFunction(f,timeout,monitor);c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        rec={'address':request['address'],'style':style,'size':body.getNumAddresses(),'seconds':round(time.time()-t,2),
             'body_ranges':[{'start':str(r.getMinAddress()),'end':str(r.getMaxAddress())} for r in body.getAddressRanges()]}
        if c:
            text=unicode(c.getC());filename=request['address']+'_'+style+'.c'
            with codecs.open(os.path.join(out,filename),'w','utf-8') as fp:fp.write(u'/* Experimental format-function recovery with ELF-verified ARM switch destinations. */\n'+text)
            rec.update(status='ok',file=filename,halt_baddata='halt_baddata' in text,warnings=text.count('/* WARNING:'))
            high=result.getHighFunction();tables=[]
            if high:
                for table in high.getJumpTables():tables.append({'switch_address':str(table.getSwitchAddress()),'cases':[str(a) for a in table.getCases()],'labels':[int(v) for v in table.getLabelValues()]})
            rec['jump_tables']=tables
        else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
        decomp.dispose();records.append(rec)
        with open(os.path.join(out,'summary.json'),'w') as fp:json.dump({'exports':records},fp,indent=2)
        print('FORMAT_PROGRESS '+request['address']+' '+style+' '+rec['status'])
        if c and not rec['halt_baddata']:break
print('FORMAT_DONE')
