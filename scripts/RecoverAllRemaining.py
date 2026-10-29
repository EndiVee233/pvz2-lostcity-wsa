#@category APKAnalysis
import json,os,re,time,csv
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];config=json.load(open(args[1]))
folder=os.path.join(out,'functions');irfolder=os.path.join(out,'fallback_ir')
for p in [folder,irfolder]:
    if not os.path.isdir(p):os.makedirs(p)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
known=set(config['known']);existing_ir=set(config['existing_ir'])
targets=[f for f in manager.getFunctions(True) if not f.isExternal() and not f.isThunk() and str(f.getEntryPoint()) not in known and str(f.getEntryPoint()) not in existing_ir]
targets.sort(key=lambda f:(f.getBody().getNumAddresses(),f.getEntryPoint().getOffset()))
decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(64);options.setMaxInstructions(150000)
decomp.setOptions(options);decomp.openProgram(currentProgram)
started=time.time();records=[];ok=0;failed=[]
journal=open(os.path.join(out,'exports.jsonl'),'w')
def progress():
    summary={'targets':len(targets),'processed':len(records),'exported_functions':ok,'errors':len(failed),
             'seconds':round(time.time()-started,1),'existing_ir_only_addresses':list(existing_ir)}
    with open(os.path.join(out,'progress.json'),'w') as fp:json.dump(summary,fp,indent=2)
for function in targets:
    address=str(function.getEntryPoint());t=time.time()
    row={'address':address,'elf_address':hex(function.getEntryPoint().getOffset()-base).rstrip('L'),
         'name':function.getName(),'size':function.getBody().getNumAddresses()}
    try:
        result=decomp.decompileFunction(function,6 if row['size']>12000 else 3,monitor)
        recovered=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        if recovered is not None:
            filename=address+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',function.getName())[:120]+'.c'
            with open(os.path.join(folder,filename),'w') as fp:
                fp.write('/* Full recognized-function pass; recovered pseudocode; ELF '+row['elf_address']+'. */\n')
                fp.write(recovered.getC())
            row.update(status='ok',file='functions/'+filename);ok+=1
        else:row.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:row.update(status='error',error=str(error))
    row['seconds']=round(time.time()-t,3)
    records.append(row);journal.write(json.dumps(row)+'\n')
    if row['status']=='error':failed.append(row)
    if len(records)%250==0:journal.flush();progress()
    if len(records)%1000==0:print('FULL_EXPORT_PROGRESS '+str(len(records))+' / '+str(len(targets))+' C='+str(ok)+' errors='+str(len(failed)))
journal.close();progress()

decomp.setSimplificationStyle('normalize');irresults=[]
for row in failed:
    function=getFunctionAt(toAddr(int(row['address'],16)))
    result=decomp.decompileFunction(function,5,monitor)
    high=result.getHighFunction() if result else None
    record={'address':row['address'],'name':row['name']}
    if high is not None:
        filename=row['address']+'.pcode';count=0
        with open(os.path.join(irfolder,filename),'w') as fp:
            fp.write('; Fallback normalized high p-code; not reconstructed C.\n')
            for op in high.getPcodeOps():
                fp.write(str(op.getSeqnum().getTarget())+'  '+str(op)+'\n');count+=1
                if count>=100000:break
        record.update(status='ok',file='fallback_ir/'+filename,operations=count,truncated=count>=100000)
    else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    irresults.append(record)
    if len(irresults)%25==0:print('FULL_FALLBACK_PROGRESS '+str(len(irresults))+' / '+str(len(failed)))
decomp.dispose()
with open(os.path.join(out,'ir_results.json'),'w') as fp:json.dump(irresults,fp,indent=2)
summary={'targets':len(targets),'processed':len(records),'exported_functions':ok,'errors':len(failed),
         'seconds':round(time.time()-started,1),'existing_ir_only_addresses':list(existing_ir),'exports':records,
         'fallback_ir_successes':sum(r['status']=='ok' for r in irresults)}
with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    w=csv.writer(fp);w.writerow(['address','elf_address','name','size','external','thunk'])
    for f in manager.getFunctions(True):w.writerow([str(f.getEntryPoint()),hex(f.getEntryPoint().getOffset()-base).rstrip('L'),f.getName(),f.getBody().getNumAddresses(),f.isExternal(),f.isThunk()])
print('FULL_EXPORT_DONE '+str(ok)+' / '+str(len(targets))+' IR='+str(summary['fallback_ir_successes']))
