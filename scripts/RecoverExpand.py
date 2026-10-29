#@category APKAnalysis
import json,os,re,time,csv
from ghidra.app.decompiler import DecompInterface,DecompileOptions
from ghidra.program.model.symbol import SourceType
args=getScriptArgs();out=args[0];config=json.load(open(args[1]))
folder=os.path.join(out,'functions');irfolder=os.path.join(out,'large_function_ir')
for p in [folder,irfolder]:
    if not os.path.isdir(p):os.makedirs(p)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
names=[];created=[]
for row in config['labels']:
    addr=toAddr(int(row['address'],16));f=getFunctionAt(addr);old=f.getName() if f else None
    status='existing'
    if f is None:
        containing=manager.getFunctionContaining(addr)
        if containing is None:
            disassemble(addr);f=createFunction(addr,row['recovered_name']);status='created'
            if f:created.append(row['address'])
        else:status='inside_existing_'+str(containing.getEntryPoint())
    if f and f.getName().startswith('FUN_'):
        f.setName(row['recovered_name'],SourceType.ANALYSIS);status='renamed'
    names.append(dict(row,original_name=old,applied_name=f.getName() if f else None,status=status))
with open(os.path.join(out,'applied_names.json'),'w') as fp:json.dump(names,fp,indent=2)

decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(64);options.setMaxInstructions(100000)
decomp.setOptions(options);decomp.openProgram(currentProgram)
irresults=[]
decomp.setSimplificationStyle('normalize')
for row in config.get('failed',[]):
    f=getFunctionAt(toAddr(int(row['address'],16)))
    if f is None:continue
    record={'address':row['address'],'name':f.getName()}
    try:
        result=decomp.decompileFunction(f,30,monitor)
        high=result.getHighFunction() if result else None
        if high is not None:
            filename=row['address']+'.pcode';count=0
            with open(os.path.join(irfolder,filename),'w') as fp:
                fp.write('; Ghidra normalized high p-code; this is an intermediate representation, not recovered C.\n')
                for op in high.getPcodeOps():
                    fp.write(str(op.getSeqnum().getTarget())+'  '+str(op)+'\n');count+=1
                    if count>=200000:break
            record.update(status='ok',file='large_function_ir/'+filename,operations=count,truncated=count>=200000)
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:record.update(status='error',error=str(error))
    irresults.append(record);print('ROUND3_IR '+row['address']+' '+record['status'])
with open(os.path.join(out,'ir_results.json'),'w') as fp:json.dump(irresults,fp,indent=2)

decomp.setSimplificationStyle('decompile');records=[];started=time.time()
def checkpoint():
    summary={'exports':records,'exported_functions':sum(r['status']=='ok' for r in records),
             'errors':sum(r['status']!='ok' for r in records),'seconds':round(time.time()-started,1),
             'labels_with_function':sum(r['applied_name'] is not None for r in names),'created_functions':created}
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
for row in config['requests']:
    if time.time()-started>480:break
    f=getFunctionAt(toAddr(int(row['address'],16)))
    if f is None:continue
    rec={'address':row['address'],'elf_address':hex(f.getEntryPoint().getOffset()-base).rstrip('L'),
         'name':f.getName(),'size':f.getBody().getNumAddresses(),'reasons':row.get('reasons',[]),'strings':row.get('strings',[])}
    try:
        timeout=6 if f.getBody().getNumAddresses()>5000 else 3
        result=decomp.decompileFunction(f,timeout,monitor)
        recovered=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        if recovered is not None:
            filename=row['address']+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',f.getName())[:120]+'.c'
            with open(os.path.join(folder,filename),'w') as fp:
                fp.write('/* Ghidra recovered pseudocode; ELF '+rec['elf_address']+'; recovered role labels are evidence-based aliases. */\n')
                fp.write(recovered.getC())
            rec.update(status='ok',file='functions/'+filename)
        else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:rec.update(status='error',error=str(error))
    try:rec['direct_callees']=[{'address':str(c.getEntryPoint()),'name':c.getName()} for c in f.getCalledFunctions(monitor)][:100]
    except Exception:pass
    records.append(rec)
    if len(records)%25==0:checkpoint()
    if len(records)%200==0:print('ROUND3_EXPAND_PROGRESS '+str(len(records)))
decomp.dispose();checkpoint()
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    w=csv.writer(fp);w.writerow(['address','elf_address','name','size','external','thunk'])
    for f in manager.getFunctions(True):w.writerow([str(f.getEntryPoint()),hex(f.getEntryPoint().getOffset()-base).rstrip('L'),f.getName(),f.getBody().getNumAddresses(),f.isExternal(),f.isThunk()])
print('ROUND3_EXPAND_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
