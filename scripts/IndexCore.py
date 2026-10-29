#@category APKAnalysis
import json, csv, os, time, re
from ghidra.app.decompiler import DecompInterface

args=getScriptArgs()
out=args[0]
strings=json.load(open(args[1]))
if not os.path.isdir(out):os.makedirs(out)
base=currentProgram.getImageBase().getOffset()
manager=currentProgram.getFunctionManager()
refs=currentProgram.getReferenceManager()
functions=list(manager.getFunctions(True))
rows=[]
for f in functions:
    rows.append({'address':str(f.getEntryPoint()),'elf_address':hex(f.getEntryPoint().getOffset()-base).rstrip('L'),
                 'name':f.getName(),'size':f.getBody().getNumAddresses(),'external':f.isExternal(),'thunk':f.isThunk()})
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    writer=csv.DictWriter(fp,fieldnames=['address','elf_address','name','size','external','thunk'])
    writer.writeheader();writer.writerows(rows)
interesting={}
evidence=[]
for item in strings:
    addr=toAddr(base+int(item['elf_address'],16))
    found=[]
    for ref in refs.getReferencesTo(addr):
        caller=manager.getFunctionContaining(ref.getFromAddress())
        if caller is not None:
            key=str(caller.getEntryPoint())
            found.append({'function':key,'from':str(ref.getFromAddress()),'name':caller.getName()})
            interesting.setdefault(key,{'function':caller,'strings':[],'score':0})
            if item['text'] not in interesting[key]['strings']:interesting[key]['strings'].append(item['text'])
            interesting[key]['score']+=item['score']
    if found:evidence.append({'text':item['text'],'elf_address':item['elf_address'],'references':found})
for f in functions:
    if f.isExternal() or f.isThunk():continue
    if f.getName().startswith(('JNI_dyn_','Java_')) or f.getName()=='JNI_OnLoad':
        key=str(f.getEntryPoint());interesting.setdefault(key,{'function':f,'strings':[],'score':0});interesting[key]['score']+=10000
        frontier=[f]
        visited=set([key])
        for depth in range(2):
            following=[]
            for parent in frontier:
                for child in parent.getCalledFunctions(monitor):
                    childkey=str(child.getEntryPoint())
                    if child.isExternal() or child.isThunk() or childkey in visited:continue
                    visited.add(childkey)
                    interesting.setdefault(childkey,{'function':child,'strings':[],'score':0})
                    interesting[childkey]['score']+=1000//(depth+1)
                    interesting[childkey].setdefault('call_paths',[]).append(f.getName()+' depth '+str(depth+1))
                    following.append(child)
            frontier=following[:100]
with open(os.path.join(out,'string_references.json'),'w') as fp:json.dump(evidence,fp,indent=2)
decomp=DecompInterface();decomp.openProgram(currentProgram)
selected=sorted(interesting.values(),key=lambda item:(-item['score'],str(item['function'].getEntryPoint())))[:1000]
folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
exports=[];started=time.time()
for item in selected:
    f=item['function'];addr=str(f.getEntryPoint())
    if time.time()-started>600:break
    record={'address':addr,'elf_address':hex(f.getEntryPoint().getOffset()-base).rstrip('L'),'name':f.getName(),
            'strings':item['strings'],'score':item['score'],'call_paths':item.get('call_paths',[])}
    try:
        result=decomp.decompileFunction(f,12,monitor)
        if result and result.decompileCompleted():
            filename=addr+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',f.getName())[:100]+'.c'
            with open(os.path.join(folder,filename),'w') as fp:
                fp.write('/* Ghidra pseudocode; ELF address '+record['elf_address']+'; string references are navigation hints. */\n')
                fp.write(result.getDecompiledFunction().getC())
            record.update(status='ok',file='functions/'+filename)
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:record.update(status='error',error=str(error))
    exports.append(record)
    if len(exports)%100==0:print('CORE_EXPORT_PROGRESS '+str(len(exports)))
decomp.dispose()
summary={'recognized_functions':len(functions),'non_thunk_internal_functions':sum(not f.isExternal() and not f.isThunk() for f in functions),
         'strings_with_function_references':len(evidence),'candidate_functions':len(interesting),
         'exported_functions':sum(x['status']=='ok' for x in exports),'export_errors':sum(x['status']=='error' for x in exports),
         'export_seconds':round(time.time()-started,1),'exports':exports}
with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(summary,fp,indent=2)
print('CORE_INDEX '+str(summary['recognized_functions'])+' functions; exported '+str(summary['exported_functions']))
