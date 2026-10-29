#@category APKAnalysis
import json,os,re,time
from ghidra.app.decompiler import DecompInterface
args=getScriptArgs();out=args[0]
requests=json.load(open(args[1]))
folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
decomp=DecompInterface();decomp.openProgram(currentProgram)
started=time.time();records=[]
for request in requests:
    if time.time()-started>180:break
    address=request['address'];function=getFunctionAt(toAddr(int(address,16)))
    if function is None:continue
    row={'address':address,'elf_address':hex(function.getEntryPoint().getOffset()-currentProgram.getImageBase().getOffset()).rstrip('L'),
         'name':function.getName(),'strings':request.get('strings',[]),'score':0,'call_paths':[],
         'targeted_reason':request['reason']}
    result=decomp.decompileFunction(function,30,monitor)
    if result and result.decompileCompleted():
        filename=address+'_'+re.sub(r'[^a-zA-Z0-9_.-]','_',function.getName())[:100]+'.c'
        with open(os.path.join(folder,filename),'w') as fp:
            fp.write('/* Ghidra pseudocode; ELF address '+row['elf_address']+'; targeted follow-up export. */\n')
            fp.write(result.getDecompiledFunction().getC())
        row.update(status='ok',file='functions/'+filename)
    else:row.update(status='error',error=result.getErrorMessage() if result else 'No result')
    records.append(row)
    print('TARGET_EXPORT '+address+' '+row['status'])
decomp.dispose()
with open(os.path.join(out,'targeted_results.json'),'w') as fp:json.dump(records,fp,indent=2)
print('TARGET_EXPORT_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
