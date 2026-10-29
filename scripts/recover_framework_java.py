"""Promote the complete SexyAppFramework Java package into the maintained build."""
from pathlib import Path
import shutil,re,json
base=Path(__file__).resolve().parents[1];project=base/'rebuild_project'
origin=base/'java_by_dex/classes/sources/com/popcap/SexyAppFramework'
repairs=[];sources=[]
for source in sorted(origin.rglob('*.java')):
    relative=Path('com/popcap/SexyAppFramework')/source.relative_to(origin)
    dest=project/'src/game_bridge'/relative
    if not dest.exists():
        text=source.read_text(encoding='utf-8')
        # JADX intentionally widens private members for readability. Restore original visibility.
        text,count=re.subn(r'(/\* JADX INFO: Access modifiers changed from: private \*/\s*)public ',r'\1private ',text)
        if count:repairs.append({'file':relative.as_posix(),'private_visibility_restored':count})
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
    sources.append(dest.relative_to(project).as_posix())
    original_dir=base/'apktool_out/smali'/relative.parent
    candidates=[original_dir/(source.stem+'.smali'),*original_dir.glob(source.stem+'$*.smali')]
    for smali in candidates:
        assert smali.exists(),smali
        backup=project/'reference/game-bridge-smali-original'/smali.relative_to(base/'apktool_out/smali')
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copyfile(smali,backup)
record={'source_files':sources,'initial_repairs':repairs,'manual_repairs_documented_in':'源码恢复第二阶段.md',
        'scope':'Complete com.popcap.SexyAppFramework package including utils; original SDK dependencies compile-only'}
(project/'framework-reconstruction.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('Maintained framework Java files:',len(sources))
