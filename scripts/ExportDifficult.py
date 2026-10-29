#@category APKAnalysis
import json,os,time,codecs
from ghidra.app.decompiler import DecompInterface,DecompileOptions
args=getScriptArgs();out=args[0];config=json.load(open(args[1]));records=[];started=time.time()
if not os.path.isdir(os.path.join(out,'functions')):os.makedirs(os.path.join(out,'functions'))
decomp=DecompInterface();opts=DecompileOptions();opts.setMaxPayloadMBytes(96);opts.setMaxInstructions(150000)
decomp.setOptions(opts);decomp.openProgram(currentProgram)
for row in config['requests']:
    addr=row['address'];f=getFunctionAt(toAddr(addr));record={'address':addr}
    if not f:record['status']='missing'
    else:
        record.update(name=f.getName(),size=f.getBody().getNumAddresses())
        began=time.time();result=decomp.decompileFunction(f,row.get('timeout',60),monitor)
        c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
        if c:
            text=unicode(c.getC());filename='functions/'+addr+'.c'
            with codecs.open(os.path.join(out,filename),'w','utf-8') as fp:fp.write(u'/* Fifth-round reanalysis; pseudocode, original source types may be unavailable. */\n'+text)
            record.update(status='ok',file=filename,halt_baddata='halt_baddata' in text,warnings=text.count('/* WARNING:'))
        else:record.update(status='error',error=result.getErrorMessage() if result else 'No result')
        record['seconds']=round(time.time()-began,2)
    records.append(record)
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump({'exports':records,'requested':len(config['requests']),'processed':len(records),'seconds':round(time.time()-started,1)},fp,indent=2)
    print('DIFFICULT_PROGRESS '+str(len(records))+' '+addr+' '+record['status'])
decomp.dispose();print('DIFFICULT_DONE')
