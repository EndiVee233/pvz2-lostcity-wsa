"""Verify reconstructed classes keep their original Smali API, excluding compile-only stubs."""
from pathlib import Path
import re,json

base=Path(__file__).resolve().parents[1]
project=base/'rebuild_project'

def validate():
    reference=project/'reference/game-bridge-smali-original'
    generated=project/'build/bridge-decoded/smali'
    expected={p.relative_to(reference) for p in reference.rglob('*.smali')}
    actual={p.relative_to(generated) for p in generated.rglob('*.smali')}
    legacy=Path('com/popcap/SexyAppFramework/GooglePlayPurchaseDriver$11.smali')
    assert actual==expected-{legacy}, (expected-actual,actual-expected)
    assert len(actual)==len(expected)-1
    records=[]
    for name in sorted(actual):
        old=(reference/name).read_text(encoding='utf-8')
        new=(generated/name).read_text(encoding='utf-8')
        record={'class':name.as_posix()}
        for kind in ('method','field'):
            before=set(re.findall(r'^\.'+kind+r' (.+)$',old,re.M))
            after=set(re.findall(r'^\.'+kind+r' (.+)$',new,re.M))
            # Ignore field initializer formatting; retain names, types and access flags.
            if kind=='field':
                before={v.split(' = ',1)[0] for v in before}
                after={v.split(' = ',1)[0] for v in after}
            extra=after-before
            allowed={v for v in extra if kind=='method' and re.fullmatch(r'private static synthetic \$values\(\)\[L[^;]+;',v)}
            if name.as_posix()=='com/popcap/SexyAppFramework/AndroidHttpProxy.smali' and kind=='method':
                allowed|=extra&{'static IsOffline()Z'}
            assert before<=after and extra==allowed,(str(name),kind,extra,before-after)
            record[kind+'_original_declarations_preserved']=True
            if allowed:
                assert re.search(r'^\.class .*\benum\b',new,re.M) or allowed=={'static IsOffline()Z'}
                record['compiler_added_private_methods']=sorted(v for v in allowed if v.startswith('private static synthetic $values'))
                if 'static IsOffline()Z' in allowed:record['intentional_added_methods']=['static IsOffline()Z']
        for directive in ('super','implements'):
            assert set(re.findall(r'^\.'+directive+r' (.+)$',old,re.M))==set(re.findall(r'^\.'+directive+r' (.+)$',new,re.M)),(name,directive)
        record['native_methods']=re.findall(r'^\.method (.*\bnative\b.*)$',new,re.M)
        assert (project/'apktool/smali'/name).read_bytes()==(generated/name).read_bytes()
        records.append(record)
        assert 'Lcom/popcap/SexyAppFramework/DreamRootPath;' not in new
    assert (project/'apktool/smali'/legacy).read_bytes()==(reference/legacy).read_bytes()
    result={'reconstructed_classes':len(actual),'compile_only_stubs_packaged':False,'classes':records,
            'main_dex_popcap_source_files':len(list((project/'src/game_bridge/com/popcap').rglob('*.java'))),
            'retained_original_unused_enum_switch_map':legacy.as_posix(),
            'compiler_added_private_enum_methods':sum(len(c.get('compiler_added_private_methods',[])) for c in records),
            'native_methods_preserved':sum(len(c['native_methods']) for c in records)}
    exported={f.relative_to(base/'java_by_dex/classes/sources').as_posix() for f in (base/'java_by_dex/classes/sources/com/popcap').rglob('*.java')}
    maintained={f.relative_to(project/'src/game_bridge').as_posix() for f in (project/'src/game_bridge/com/popcap').rglob('*.java')}
    assert exported==maintained,(exported-maintained,maintained-exported)
    result['all_main_dex_popcap_exported_java_files_in_build']=True
    (project/'bridge-api-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':print(json.dumps(validate(),indent=2))
