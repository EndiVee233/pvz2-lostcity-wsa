"""Copy an explicit source-only snapshot to the existing publication checkout.

No Git/network mutation; original resources, binaries, keys and private runtime
evidence are excluded. Diagnostic fixture arrays can embed game resources and
are deliberately not published; LibraryOnly remains independently buildable.
"""
from pathlib import Path
import shutil,json,re,os
base=Path(__file__).resolve().parents[1];repo=base/'publish_repo'
assert (repo/'.git').exists()
copied=[]
def copy(source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);copied.append(str(dest.relative_to(repo)).replace('\\','/'))
for p in (base/'native_recovered').rglob('*'):
 if not p.is_file() or 'build' in p.relative_to(base/'native_recovered').parts:continue
 if p.suffix in ('.cpp','.hpp','.ps1','.md') or p.name in ('CMakeLists.txt','build-validation.json'):
  copy(p,repo/'native_recovered'/p.relative_to(base/'native_recovered'))
for p in (base/'scripts').iterdir():
 if p.is_file() and p.suffix in ('.py','.java'):copy(p,repo/'scripts'/p.name)
for p in base.glob('*.md'):copy(p,repo/'docs/recovery'/p.name)
copy(base/'native_analysis/source_build_audit/progress.json',repo/'docs/recovery/source-build-audit.json')
# Convert local workspace Markdown links only when the published target exists.
# Evidence not copied remains identified as local material, without broken links.
for p in [repo/c for c in copied if c.endswith('.md')]:
 text=p.read_text(encoding='utf-8')
 def link(m):
  label,target=m.groups();target=target.strip('<>');prefix='K:/反编译PvZ2/'
  if not target.startswith(prefix):return m[0]
  rel=target[len(prefix):];mapped=repo/rel
  if rel.endswith('.md') and '/' not in rel:mapped=repo/'docs/recovery'/rel
  if not mapped.exists():return label+'（本地材料）'
  return '['+label+']('+os.path.relpath(mapped,p.parent).replace('\\','/')+')'
 p.write_text(re.sub(r'\[([^\]]+)\]\((<?K:/[^\n)]+>?)\)',link,text),encoding='utf-8')
summary=dict(round=33,source_only=True,copied_files=len(copied),files=copied,excluded=['original APK and libraries','game assets and raw RTON','generated *_fixtures.inc arrays','compiled outputs','signing keys','private player saves and runtime evidence'],public_build='native_recovered/build.ps1 -LibraryOnly -Zig <zig.exe>',full_game_source_build=False,default_local_cpp_checkpoints=45591,local_real_package_links=8,local_external_factories='6/66')
(repo/'docs/recovery/source-snapshot.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Copied',len(copied),'source/report files; no binaries, assets or generated fixture arrays')
