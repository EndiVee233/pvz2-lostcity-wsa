"""Promote the PopCap utility, event, network, log and notification packages to Java."""
from pathlib import Path
import json,re,shutil
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project'
origin=base/'java_by_dex/classes/sources';reference=base/'apktool_out/smali'
packages=['com/popcap/util','com/popcap/events','com/popcap/log','com/popcap/network','com/popcap/notifications',
          'com/popcap/pvz2cmhd','com/popcap/purchase/TW']
records=[]
for package in packages:
    for source in sorted((origin/package).rglob('*.java')):
        relative=source.relative_to(origin);dest=p/'src/game_bridge'/relative
        if not dest.exists():
            text=source.read_text(encoding='utf-8')
            text=re.sub(r'(/\* JADX INFO: Access modifiers changed from: (private|protected) \*/\s*(?:@[^\n]*\n\s*)*)public ',
                        lambda m:m[1]+m[2]+' ',text)
            if 'DreamRootPath.' in text:
                text=text.replace('package '+package.replace('/','.')+';',
                                  'package '+package.replace('/','.')+';\n\nimport com.popcap.SexyAppFramework.DreamRootPath;')
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
        records.append(dest.relative_to(p).as_posix())
        folder=reference/relative.parent
        for original in [folder/(source.stem+'.smali'),*folder.glob(source.stem+'$*.smali')]:
            assert original.exists(),original
            backup=p/'reference/game-bridge-smali-original'/original.relative_to(reference)
            backup.parent.mkdir(parents=True,exist_ok=True)
            if not backup.exists():shutil.copyfile(original,backup)
(p/'service-reconstruction.json').write_text(json.dumps({'packages':packages,'source_files':records,
    'manual_repairs_documented_in':'离线修复与源码恢复第三阶段.md','original_implementations_retained_in_reference_smali':True},indent=2),encoding='utf-8')
print('Promoted Java source files:',len(records))
