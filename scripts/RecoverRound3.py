#@category APKAnalysis
import json,csv,os,re,time
from ghidra.app.decompiler import DecompInterface,DecompileOptions
from ghidra.program.model.symbol import SourceType

args=getScriptArgs();out=args[0];config=json.load(open(args[1]))
folder=os.path.join(out,'functions');assembly=os.path.join(out,'large_function_assembly')
for path in [folder,assembly]:
    if not os.path.isdir(path):os.makedirs(path)
manager=currentProgram.getFunctionManager();imagebase=currentProgram.getImageBase().getOffset()
renames=[]
for row in config['labels']:
    f=getFunctionAt(toAddr(int(row['address'],16)))
    if f is None:continue
    old=f.getName()
    if old.startswith('FUN_'):
        try:f.setName(row['recovered_name'],SourceType.ANALYSIS)
        except Exception as error:print('RENAME_WARNING '+str(error))
    renames.append(dict(row,original_name=old,applied_name=f.getName()))
with open(os.path.join(out,'applied_names.json'),'w') as fp:json.dump(renames,fp,indent=2)

decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(64)
options.setMaxInstructions(100000);decomp.setOptions(options);decomp.openProgram(currentProgram)
records=[];started=time.time();attempted=set()
previous=set(config['previous_successful_addresses'])
def checkpoint():
    successes=[r for r in records if r['status']=='ok']
    result={'function_records':len(records),'exported_functions':len(successes),
            'new_unique_functions':sum(r['address'] not in previous for r in successes),
            'errors':sum(r['status']!='ok' for r in records),'seconds':round(time.time()-started,1),
            'applied_role_labels':len(renames),'exports':records}
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(result,fp,indent=2)
def export(function,row,styles):
    addr=str(function.getEntryPoint());t=time.time();attempts=[]
    record={'address':addr,'elf_address':hex(function.getEntryPoint().getOffset()-imagebase).rstrip('L'),
            'name':function.getName(),'size':function.getBody().getNumAddresses(),
            'strings':row.get('strings',[]),'reasons':row.get('reasons',[]),'previously_exported':addr in previous}
    for style,timeout in styles:
        decomp.setSimplificationStyle(style)
        try:
            result=decomp.decompileFunction(function,timeout,monitor)
            if result and result.decompileCompleted() and result.getDecompiledFunction() is not None:
                filename=addr+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',function.getName())[:120]+'.c'
                with open(os.path.join(folder,filename),'w') as fp:
                    fp.write('/* Recovered pseudocode; Ghidra address '+addr+'; ELF '+record['elf_address']+'; mode '+style+'. */\n')
                    fp.write(result.getDecompiledFunction().getC())
                record.update(status='ok',file='functions/'+filename,mode=style)
                break
            if result and result.decompileCompleted() and result.getHighFunction() is not None:
                irfile=addr+'_'+style+'.pcode'
                with open(os.path.join(assembly,irfile),'w') as fp:
                    fp.write('; Ghidra high p-code; mode '+style+'; not reconstructed C source.\n')
                    for op in result.getHighFunction().getPcodeOps():fp.write(str(op)+'\n')
                attempts.append({'mode':style,'error':'C output unavailable in this mode; high p-code saved','ir_file':'large_function_assembly/'+irfile})
            else:attempts.append({'mode':style,'error':result.getErrorMessage() if result else 'No result'})
        except Exception as error:attempts.append({'mode':style,'error':str(error)})
    if 'status' not in record:record.update(status='error',error=attempts[-1]['error'] if attempts else 'Not attempted')
    record['attempts']=attempts;record['seconds']=round(time.time()-t,2)
    try:
        record['direct_callees']=[{'address':str(c.getEntryPoint()),'name':c.getName()} for c in function.getCalledFunctions(monitor)][:100]
    except Exception as error:record['call_graph_error']=str(error)
    records.append(record);attempted.add(addr)

for row in config['failed']:
    f=getFunctionAt(toAddr(int(row['address'],16)))
    if f is None:continue
    with open(os.path.join(assembly,row['address']+'.asm'),'w') as fp:
        fp.write('; Ghidra-defined function body; boundaries may be imperfect.\n')
        for ins in currentProgram.getListing().getInstructions(f.getBody(),True):fp.write(str(ins.getAddress())+'  '+str(ins)+'\n')
    export(f,row,[('normalize',25),('firstpass',12)])
    checkpoint();print('ROUND3_LARGE '+row['address']+' '+records[-1]['status']+' '+records[-1].get('mode','none'))

bulk_started=time.time()
for row in config['requests']:
    if time.time()-bulk_started>480:break
    if row['address'] in attempted:continue
    f=getFunctionAt(toAddr(int(row['address'],16)))
    if f is None:continue
    timeout=6 if row['size']>5000 else 3
    export(f,row,[('decompile',timeout)])
    if len(records)%25==0:checkpoint()
    if len(records)%100==0:print('ROUND3_EXPORT_PROGRESS '+str(len(records)))

decomp.dispose();checkpoint()
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    writer=csv.writer(fp);writer.writerow(['address','elf_address','name','size','external','thunk'])
    for f in manager.getFunctions(True):writer.writerow([str(f.getEntryPoint()),hex(f.getEntryPoint().getOffset()-imagebase).rstrip('L'),f.getName(),f.getBody().getNumAddresses(),f.isExternal(),f.isThunk()])
print('ROUND3_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
