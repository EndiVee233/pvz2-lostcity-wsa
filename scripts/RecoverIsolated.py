#@category APKAnalysis
import json,os,codecs,time,re
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];config=json.load(open(args[1]));folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(96);options.setMaxInstructions(150000)
decomp.setOptions(options);decomp.openProgram(currentProgram)
records=[];started=time.time()
def checkpoint():
    summary={'exports':records,'requested':len(config['requests']),'processed':len(records),
             'exported_functions':sum(r['status']=='ok' for r in records),'errors':sum(r['status']=='error' for r in records),
             'seconds':round(time.time()-started,1),'language':str(currentProgram.getLanguageID()),'method':'Isolated fresh ELF import without inherited analysis types; previous owner functions may be removed only in this experimental project'}
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
for request in config['requests']:
    addr=toAddr(int(request['address'],16));record=dict(request);t=time.time()
    try:
        f=getFunctionAt(addr)
        if f is None:
            owner=manager.getFunctionContaining(addr)
            if owner is not None:
                record['experimental_removed_owner']=str(owner.getEntryPoint());manager.removeFunction(owner.getEntryPoint())
            disassemble(addr);f=createFunction(addr,'Candidate_'+request['address'])
        else:disassemble(addr)
        if f is None:raise RuntimeError('Could not create candidate entry')
        record.update(elf_address=hex(addr.getOffset()-base).rstrip('L'),name=f.getName(),body_size=f.getBody().getNumAddresses())
        decomp.resetDecompiler()
        timeout=45 if request['group']=='hard_failure' and request.get('baseline_size',0)>12000 else (18 if request['group']=='hard_failure' else 5)
        result=decomp.decompileFunction(f,timeout,monitor)
        c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        if c is not None:
            text=unicode(c.getC());filename=request['address']+'.c'
            with codecs.open(os.path.join(folder,filename),'w','utf-8') as fp:
                fp.write(u'/* Isolated-import boundary/type recovery candidate. Original primary analysis remains unchanged. */\n'+text)
            record.update(status='ok',file='functions/'+filename,control_flow_truncated=('halt_baddata' in text),warning_comments=text.count('/* WARNING:'),characters=len(text))
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:record.update(status='error',error=str(error))
    record['seconds']=round(time.time()-t,2);records.append(record)
    if len(records)%10==0:checkpoint()
    if len(records)%25==0:print('ROUND4_ISOLATED_PROGRESS '+str(len(records)))
decomp.dispose();checkpoint()
print('ROUND4_ISOLATED_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
