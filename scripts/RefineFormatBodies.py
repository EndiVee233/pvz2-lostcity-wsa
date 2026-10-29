#@category APKAnalysis
import json,os,codecs,time
from ghidra.program.model.symbol import SourceType,RefType
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];before=json.load(open(args[1]));records=[]
for row in before['exports']:
    if row['status']!='ok':continue
    f=getFunctionAt(toAddr(row['address']));old_size=f.getBody().getNumAddresses()
    for table in row['jump_tables']:
        ins=currentProgram.getListing().getInstructionAt(toAddr(table['switch_address']))
        for target in table['cases']:
            addr=toAddr(target);disassemble(addr)
            ins.addOperandReference(0,addr,RefType.COMPUTED_JUMP,SourceType.ANALYSIS)
    CreateFunctionCmd.fixupFunctionBody(currentProgram,f,monitor)
    body=f.getBody();decomp=DecompInterface();opts=DecompileOptions();opts.setMaxPayloadMBytes(96);opts.setMaxInstructions(150000)
    decomp.setOptions(opts);decomp.openProgram(currentProgram);t=time.time()
    result=decomp.decompileFunction(f,60,monitor);c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
    rec={'address':row['address'],'style':'decompile','size':body.getNumAddresses(),'previous_experimental_size':old_size,
         'body_ranges':[{'start':str(r.getMinAddress()),'end':str(r.getMaxAddress())} for r in body.getAddressRanges()],
         'seconds':round(time.time()-t,2)}
    if c:
        text=unicode(c.getC());filename=row['address']+'_decompile.c'
        with codecs.open(os.path.join(out,filename),'w','utf-8') as fp:fp.write(u'/* Experimental format-function recovery; entry and nested switch bodies are included. */\n'+text)
        rec.update(status='ok',file=filename,halt_baddata='halt_baddata' in text,warnings=text.count('/* WARNING:'))
        rec['jump_tables']=[{'switch_address':str(table.getSwitchAddress()),'cases':[str(a) for a in table.getCases()],'labels':[int(v) for v in table.getLabelValues()]} for table in result.getHighFunction().getJumpTables()]
    else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
    decomp.dispose();records.append(rec);print('FORMAT_REFINED '+row['address']+' '+str(old_size)+' -> '+str(rec['size'])+' '+rec['status'])
with open(os.path.join(out,'summary.json'),'w') as fp:json.dump({'exports':records},fp,indent=2)
