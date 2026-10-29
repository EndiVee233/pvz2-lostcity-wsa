#@category APKAnalysis
import json,os,time,codecs
from ghidra.app.decompiler import DecompInterface,DecompileOptions

args=getScriptArgs();out=args[0];config=json.load(open(args[1]))
if not os.path.isdir(os.path.join(out,'functions')):os.makedirs(os.path.join(out,'functions'))
fm=currentProgram.getFunctionManager();listing=currentProgram.getListing()
trusted_names=set(['__cxa_throw','__cxa_rethrow','__cxa_pure_virtual','abort','exit','_exit','__stack_chk_fail','__android_log_assert'])
known={};proofs=[];rejected={};changed=[];started=time.time()

def function_record(f):
    return {'address':str(f.getEntryPoint()),'name':f.getName(),'size':f.getBody().getNumAddresses(),
            'original_noreturn':bool(f.hasNoReturn()),'thunk':bool(f.isThunk())}

for f in fm.getFunctions(True):
    if f.getName() in trusted_names:
        row=function_record(f);row['kind']='ABI declaration';known[row['address']]=row

def prove(f):
    trace={};active=set();done=set();ends=[]
    def walk(addr):
        key=str(addr)
        if key in done:return True
        if key in active:raise ValueError('cycle')
        if len(trace)>256:raise ValueError('short-wrapper instruction limit')
        if not f.getBody().contains(addr):raise ValueError('outside function '+key)
        ins=listing.getInstructionAt(addr)
        if ins is None:raise ValueError('no instruction '+key)
        flow=ins.getFlowType();targets=list(ins.getFlows());fall=ins.getFallThrough()
        row={'address':key,'text':str(ins),'bytes':''.join('%02x'%(int(b)&255) for b in ins.getBytes()),
             'flow':str(flow),'targets':[str(x) for x in targets],'fallthrough':str(fall) if fall else None,
             'conditional':bool(flow.isConditional())}
        trace[key]=row;active.add(key)
        if flow.isCall():
            terminal=len(targets)==1 and str(targets[0]) in known
            if terminal:
                ends.append({'instruction':key,'callee':str(targets[0]),'kind':'call'})
                if flow.isConditional():
                    if fall is None:raise ValueError('conditional call missing fallthrough')
                    walk(fall)
            else:
                if fall is None:raise ValueError('unknown call without fallthrough')
                walk(fall)
        elif flow.isJump():
            if not targets:raise ValueError('computed jump')
            for target in targets:
                if str(target) in known:ends.append({'instruction':key,'callee':str(target),'kind':'tail jump'})
                else:walk(target)
            if flow.isConditional():
                if fall is None:raise ValueError('conditional jump missing fallthrough')
                walk(fall)
        elif flow.isTerminal():raise ValueError('return or unproven terminal')
        else:
            if fall is None:raise ValueError('missing fallthrough')
            walk(fall)
        active.remove(key);done.add(key);return True
    try:
        walk(f.getEntryPoint())
        if not ends:return None,'no trusted terminal'
        row=function_record(f);row.update(kind='machine CFG proof',instructions=sorted(trace.values(),key=lambda x:x['address']),terminals=ends)
        return row,None
    except (ValueError,RuntimeError) as e:return None,str(e)

# Only inspect direct callers of already proven non-returning functions. No loop,
# unknown branch, return, or escape from the existing body is accepted as proof.
frontier=list(known)
while frontier:
    pending=set()
    for address in frontier:
        for ref in currentProgram.getReferenceManager().getReferencesTo(toAddr(address)):
            if ref.getReferenceType().isCall() or ref.getReferenceType().isJump():
                caller=fm.getFunctionContaining(ref.getFromAddress())
                if caller and not caller.isExternal() and caller.getBody().getNumAddresses()<=4096:
                    pending.add(str(caller.getEntryPoint()))
    frontier=[]
    for address in sorted(pending):
        if address in known:continue
        f=fm.getFunctionAt(toAddr(address));row,error=prove(f)
        if row:
            known[address]=row;proofs.append(row);frontier.append(address);rejected.pop(address,None)
        else:rejected[address]=error

for address,row in sorted(known.items()):
    f=fm.getFunctionAt(toAddr(address))
    if f and not f.hasNoReturn():f.setNoReturn(True);changed.append(address)

with open(os.path.join(out,'noreturn_proofs.json'),'w') as fp:
    json.dump({'seeds':[x for x in known.values() if x['kind']=='ABI declaration'],'proven_wrappers':proofs,
               'changed_noreturn_addresses':changed,'rejected_candidates':rejected},fp,indent=2)
print('NORETURN_PROVEN '+str(len(proofs))+' CHANGED '+str(len(changed)))

decomp=DecompInterface();opts=DecompileOptions();opts.setMaxPayloadMBytes(96);opts.setMaxInstructions(150000)
decomp.setOptions(opts);decomp.openProgram(currentProgram);records=[]
def checkpoint():
    with open(os.path.join(out,'summary.json'),'w') as fp:
        json.dump({'exports':records,'processed':len(records),'requested':len(config['requests']),
                   'proven_wrappers':len(proofs),'changed_noreturn':len(changed),'seconds':round(time.time()-started,1)},fp,indent=2)
for row in config['requests']:
    address=row['address'];f=fm.getFunctionAt(toAddr(address));rec={'address':address}
    try:
        if f is None:rec.update(status='missing')
        else:
            rec.update(name=f.getName(),size=f.getBody().getNumAddresses())
            result=decomp.decompileFunction(f,int(row.get('timeout',20)),monitor)
            c=result.getDecompiledFunction() if result and result.decompileCompleted() else None
            if c:
                text=unicode(c.getC());filename='functions/'+address+'.c'
                with codecs.open(os.path.join(out,filename),'w','utf-8') as fp:
                    fp.write(u'/* Fifth-round pseudocode after machine-proven no-return metadata correction. */\n'+text)
                rec.update(status='ok',file=filename,halt_baddata=('halt_baddata' in text),warnings=text.count('/* WARNING:'),
                           jumptable_warning=('Could not recover jumptable' in text))
            else:rec.update(status='error',error=result.getErrorMessage() if result else 'No result')
    except Exception as e:rec.update(status='error',error=str(e))
    records.append(rec)
    if len(records)%20==0:checkpoint();print('NORETURN_EXPORT_PROGRESS '+str(len(records)))
decomp.dispose();checkpoint();print('NORETURN_DONE '+str(len(records)))
