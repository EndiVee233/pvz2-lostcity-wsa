#@category APKAnalysis
import json,os,re,time,csv,codecs
from java.math import BigInteger
from ghidra.app.decompiler import DecompInterface,DecompileOptions
from ghidra.program.model.symbol import SourceType
args=getScriptArgs();out=args[0];config=json.load(open(args[1]));folder=os.path.join(out,'functions')
if not os.path.isdir(folder):os.makedirs(folder)
manager=currentProgram.getFunctionManager();base=currentProgram.getImageBase().getOffset()
decomp=DecompInterface();options=DecompileOptions();options.setMaxPayloadMBytes(96);options.setMaxInstructions(150000)
decomp.setOptions(options);decomp.openProgram(currentProgram)
started=time.time();records=[];created=[]
def checkpoint():
    data={'exports':records,'requested':len(config['requests']),'processed':len(records),
          'exported_functions':sum(r['status']=='ok' for r in records),'errors':sum(r['status']=='error' for r in records),
          'contained':sum(r['status']=='contained' for r in records),'created_functions':created,'seconds':round(time.time()-started,1)}
    with open(os.path.join(out,'summary.json'),'w') as fp:json.dump(data,fp,indent=2)
for row in config['requests']:
    addr=toAddr(int(row['address'],16));f=getFunctionAt(addr)
    rec={'address':row['address'],'elf_address':hex(addr.getOffset()-base).rstrip('L'),
         'class_slots':row.get('class_slots',[]),'reason':row['reason']}
    try:
        if f is None:
            owner=manager.getFunctionContaining(addr)
            if owner:
                rec.update(status='contained',owner=str(owner.getEntryPoint()),owner_name=owner.getName())
            else:
                disassemble(addr);f=createFunction(addr,row['suggested_name'])
                if f:created.append(row['address'])
        if f:
            old_name=f.getName()
            if (old_name.startswith('FUN_') or (row.get('prefer_reflected_name',False) and old_name.startswith('Recovered_'))) and row.get('unique_class',False):
                f.setName(row['suggested_name'],SourceType.ANALYSIS);rec['replaced_name']=old_name
            rec.update(name=f.getName(),size=f.getBody().getNumAddresses())
            result=decomp.decompileFunction(f,20 if rec['size']>5000 else 6,monitor)
            c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
            if c is not None:
                text=unicode(c.getC());filename=row['address']+'.c'
                with codecs.open(os.path.join(folder,filename),'w','utf-8') as fp:
                    fp.write(u'/* Fourth-round recovered pseudocode; exact original types and names may be unavailable. */\n'+text)
                rec.update(status='ok',file='functions/'+filename,control_flow_truncated=('halt_baddata' in text),warning_comments=text.count('/* WARNING:'))
            else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
        elif 'status' not in rec:rec.update(status='error',error='Function creation failed')
    except Exception as error:rec.update(status='error',error=str(error))
    records.append(rec)
    if len(records)%100==0:checkpoint();print('ROUND4_ENTRIES_PROGRESS '+str(len(records)))
decomp.dispose();checkpoint()
with open(os.path.join(out,'functions.csv'),'wb') as fp:
    w=csv.writer(fp);w.writerow(['address','elf_address','name','size','external','thunk'])
    for f in manager.getFunctions(True):w.writerow([str(f.getEntryPoint()),hex(f.getEntryPoint().getOffset()-base).rstrip('L'),f.getName(),f.getBody().getNumAddresses(),f.isExternal(),f.isThunk()])
print('ROUND4_ENTRIES_DONE '+str(sum(r['status']=='ok' for r in records))+' / '+str(len(records)))
