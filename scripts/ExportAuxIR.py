#@category APKAnalysis
import json,os
from ghidra.app.decompiler import DecompInterface
out=getScriptArgs()[0];config=json.load(open(getScriptArgs()[1]));name=currentProgram.getName()
folder=os.path.join(out,name,'fallback_ir')
if not os.path.isdir(folder):os.makedirs(folder)
decomp=DecompInterface();decomp.openProgram(currentProgram);decomp.setSimplificationStyle('normalize')
records=[]
for row in config.get(name,[]):
    f=getFunctionAt(toAddr(int(row['address'],16)))
    record={'address':row['address'],'name':row['name']}
    try:
        result=decomp.decompileFunction(f,5,monitor);high=result.getHighFunction() if result else None
        if high is not None:
            count=0;filename=row['address']+'.pcode'
            with open(os.path.join(folder,filename),'w') as fp:
                fp.write('; Auxiliary-library normalized high p-code; not C source.\n')
                for op in high.getPcodeOps():
                    fp.write(str(op.getSeqnum().getTarget())+'  '+str(op)+'\n');count+=1
                    if count>=100000:break
            record.update(status='ok',file='fallback_ir/'+filename,operations=count,truncated=count>=100000)
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as error:record.update(status='error',error=str(error))
    records.append(record)
decomp.dispose()
with open(os.path.join(out,name,'ir_results.json'),'w') as fp:json.dump(records,fp,indent=2)
print('AUX_IR_DONE '+name+' '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
