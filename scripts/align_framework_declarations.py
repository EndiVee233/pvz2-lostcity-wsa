"""Align anonymous numbering with the original without changing initializer order."""
from pathlib import Path
import re
path=Path(__file__).resolve().parents[1]/'rebuild_project/src/game_bridge/com/popcap/SexyAppFramework/GooglePlayPurchaseDriver.java'
text=path.read_text(encoding='utf-8')
for name,anchor in [('startOperation','private IabHelper.OnIabSetupFinishedListener mOnIabSetupFinishedListener'),
                    ('Refresh','private IabHelper.QueryInventoryFinishedListener mQueryInventoryFinishedListener'),
                    ('RequestPayment','private IabHelper.OnIabPurchaseFinishedListener mOnIabPurchaseFinishedListener'),
                    ('ConfirmDelivery',None)]:
    match=re.search(r'^    (?:public|private) (?:void )?'+name+r'\(',text,re.M);assert match,name
    begin=match.start();body=text.index('{',match.end())
    masked=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/',lambda m:' '*len(m[0]),text)
    depth=1;end=body+1
    while depth:
        depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
    block=text[begin:end]+'\n\n'
    text=text[:begin]+text[end:];pos=text.index('    '+anchor) if anchor else text.rfind('}')
    text=text[:pos]+block+text[pos:]
path.write_text(text,encoding='utf-8')
print('Aligned original anonymous class order; field initializer order preserved.')
