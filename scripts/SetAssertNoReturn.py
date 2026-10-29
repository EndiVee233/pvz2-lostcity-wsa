#@category APKAnalysis
import json
rows=[]
for f in currentProgram.getFunctionManager().getFunctions(True):
    if f.getName()!='__android_log_assert':continue
    rows.append({'address':str(f.getEntryPoint()),'name':f.getName(),'size':f.getBody().getNumAddresses(),
                 'original_noreturn':bool(f.hasNoReturn()),'thunk':bool(f.isThunk()),'kind':'ABI declaration'})
    f.setNoReturn(True)
with open(getScriptArgs()[0],'w') as fp:json.dump(rows,fp,indent=2)
print('ASSERT_NORETURN_SEEDS '+str(len(rows)))
