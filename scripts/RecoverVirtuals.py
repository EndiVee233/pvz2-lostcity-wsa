#@category APKAnalysis
import json,os,re,time,csv
from ghidra.app.decompiler import DecompInterface,DecompileOptions
from ghidra.program.model.symbol import SourceType
args=getScriptArgs();out=args[0];config=json.load(open(args[1]))
folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(64);options.setMaxInstructions(100000)
decomp.setOptions(options);decomp.openProgram(currentProgram)
started=time.time();records=[];created=[];names=[]
def checkpoint():
    summary={'exports':records,'exported_functions':sum(r['status']=='ok' for r in records),
             'errors':sum(r['status']=='error' for r in records),'skipped':sum(r['status']=='skipped' for r in records),
             'created_functions':created,'requested':len(config['requests']),'processed':len(records),'seconds':round(time.time()-started,1)}
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
for row in config['requests']:
    if time.time()-started>360:break
    addr=toAddr(int(row['address'],16));f=getFunctionAt(addr)
    rec={'address':row['address'],'elf_address':hex(addr.getOffset()-base).rstrip('L'),'class_slots':row['class_slots'],'reasons':['Vtable slot function pointer from a class-associated allocation callback']}
    try:
        if f is None:
            containing=manager.getFunctionContaining(addr)
            if containing is not None:
                rec.update(status='skipped',error='Entry is inside existing function '+str(containing.getEntryPoint()))
            else:
                disassemble(addr);f=createFunction(addr,row['suggested_name'])
                if f:created.append(row['address'])
        if f:
            old=f.getName()
            if old.startswith('FUN_') and row['unique_class']:
                f.setName(row['suggested_name'],SourceType.ANALYSIS);names.append({'address':row['address'],'original_name':old,'applied_name':f.getName()})
            rec.update(name=f.getName(),size=f.getBody().getNumAddresses())
            result=decomp.decompileFunction(f,5 if f.getBody().getNumAddresses()>5000 else 2,monitor)
            recovered=result.getDecompiledFunction() if result and result.decompileCompleted() else None
            if recovered is not None:
                filename=row['address']+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',f.getName())[:120]+'.c'
                with open(os.path.join(folder,filename),'w') as fp:
                    fp.write('/* Vtable-associated recovered pseudocode; ELF '+rec['elf_address']+'; slot labels are inferred, original method names unknown. */\n')
                    fp.write(recovered.getC())
                rec.update(status='ok',file='functions/'+filename)
                rec['direct_callees']=[{'address':str(c.getEntryPoint()),'name':c.getName()} for c in f.getCalledFunctions(monitor)][:100]
            else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
        elif 'status' not in rec:rec.update(status='error',error='Could not create function at verified executable pointer')
    except Exception as error:rec.update(status='error',error=str(error))
    records.append(rec)
    if len(records)%50==0:checkpoint()
    if len(records)%250==0:print('ROUND3_VIRTUAL_PROGRESS '+str(len(records)))
decomp.dispose();checkpoint()
with open(os.path.join(out,'applied_names.json'),'w') as fp:json.dump(names,fp,indent=2)
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    w=csv.writer(fp);w.writerow(['address','elf_address','name','size','external','thunk'])
    for f in manager.getFunctions(True):w.writerow([str(f.getEntryPoint()),hex(f.getEntryPoint().getOffset()-base).rstrip('L'),f.getName(),f.getBody().getNumAddresses(),f.isExternal(),f.isThunk()])
print('ROUND3_VIRTUAL_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
