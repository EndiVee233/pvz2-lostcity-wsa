#@category APKAnalysis
import json,os,re,time,csv
from ghidra.app.decompiler import DecompInterface,DecompileOptions
out=os.path.join(getScriptArgs()[0],currentProgram.getName());folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(64);decomp.setOptions(options);decomp.openProgram(currentProgram)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
functions=[f for f in manager.getFunctions(True) if not f.isExternal() and not f.isThunk()]
records=[];started=time.time()
print('AUX_EXPORT_START '+currentProgram.getName()+' '+str(len(functions)))
for f in functions:
    address=str(f.getEntryPoint())
    record={'address':address,'elf_address':hex(f.getEntryPoint().getOffset()-base).rstrip('L'),'name':f.getName(),'size':f.getBody().getNumAddresses()}
    try:
        result=decomp.decompileFunction(f,6 if record['size']>12000 else 3,monitor)
        c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        if c is not None:
            filename=address+'.c'
            with open(os.path.join(folder,filename),'w') as fp:fp.write('/* Recovered '+currentProgram.getName()+' pseudocode; original types may be incomplete. */\n'+c.getC())
            record.update(status='ok',file='functions/'+filename)
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:record.update(status='error',error=str(error))
    records.append(record)
    if len(records)%1000==0:print('AUX_EXPORT_PROGRESS '+currentProgram.getName()+' '+str(len(records)))
decomp.dispose()
summary={'library':currentProgram.getName(),'recognized_non_thunk_functions':len(functions),
         'exported_functions':sum(r['status']=='ok' for r in records),'errors':sum(r['status']!='ok' for r in records),
         'seconds':round(time.time()-started,1),'exports':records}
with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    w=csv.writer(fp);w.writerow(['address','elf_address','name','size'])
    for r in records:w.writerow([r['address'],r['elf_address'],r['name'],r['size']])
print('AUX_EXPORT_DONE '+currentProgram.getName()+' '+str(summary['exported_functions'])+' / '+str(len(functions)))
