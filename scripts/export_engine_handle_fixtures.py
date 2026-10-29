"""Export captured original-ARM outcomes for compiled C++ differential checks."""
import json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
d=json.loads((base/'native_analysis/core_round11/engine_handles/validation.json').read_text())
lines=['// Generated from original ARM outcomes; do not edit expected results.']
slots=[];banks=[];assigns=[];resolves=[]
for r in d['cases']:
 if r['function']=='lookup_slot':
  slots.append('{%dU,%dU,%dU,%dU,%s}'%(r['low'],r['high'],46 if r['state']=='wrong_type' else 45,r['generation']+int(r['state']=='stale'),'true' if r['result_valid'] else 'false'))
 elif r['function']=='registry_store':banks.append('{%dU,%dU}'%(r['encoded'],r['result']))
 elif r['function']=='resolve_object':
  resolves.append('{%s,%s,%s,%dU,%dU,%dU}'%('true' if r['state']=='missing' else 'false','true' if r['state']=='ready' else 'false','true' if r['state']=='lazy' else 'false',r['callback_count'],r['result'],len(r['events'])))
 else:
  events='{'+','.join('{%s,%dU}'%('true' if a=='retain' else 'false',v) for a,v in r['events'])+'}'
  assigns.append('{{%dU,%dU},{%dU,%dU},%s}'%(*r['old'],*r['new'],events))
lines+=['const SlotCase slot_cases[] = {'+','.join(slots)+'};','const BankCase bank_cases[] = {'+','.join(banks)+'};','const AssignCase assign_cases[] = {'+','.join(assigns)+'};']
lines+=['const ResolveCase resolve_cases[] = {'+','.join(resolves)+'};']
(base/'native_recovered/tests/engine_handle_fixtures.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Exported',len(d['cases']),'ARM outcomes')
