from pathlib import Path
import re,json
base=Path(__file__).resolve().parents[1];project=base/'rebuild_project'
original=base/'java_by_dex/classes8/sources/com/popcap/pvz2cthd/BootActivity.java'
source=original.read_text(encoding='utf-8')
source=re.sub(r'/\* JADX[^*]*\*/\s*','',source)
source=re.sub(r'new Runnable\(this\) \{[^@]*@Override', 'new Runnable() {\n                @Override',source)
source=source.replace('this.this$0.','BootActivity.this.')
def replace_method(text,signature,replacement):
    start=text.index(signature);opening=text.index('{',start);depth=1;i=opening+1
    while depth:
        if text[i]=='{':depth+=1
        elif text[i]=='}':depth-=1
        i+=1
    return text[:start]+replacement+text[i:]
extract='''public void extract(File file) {
        ZipInputStream input = null;
        try {
            file.mkdirs();
            input = new ZipInputStream(new BufferedInputStream(
                    new ConcatAssetInputStream(getAssets(), PARTS), 1048576));
            byte[] buffer = new byte[1048576];
            ZipEntry entry;
            while ((entry = input.getNextEntry()) != null) {
                String name = entry.getName();
                if (name == null || !name.startsWith(PREFIX)) continue;
                String relative = name.substring(PREFIX.length());
                if (relative.length() == 0) continue;
                File target = new File(file, relative);
                if (entry.isDirectory()) {
                    target.mkdirs();
                } else {
                    File parent = target.getParentFile();
                    if (parent != null) parent.mkdirs();
                    FileOutputStream output = new FileOutputStream(target);
                    try {
                        int count;
                        while ((count = input.read(buffer)) > 0) {
                            output.write(buffer, 0, count);
                            written += count;
                        }
                    } finally {
                        output.close();
                    }
                }
            }
            new File(file, ".pvz2_extracted").createNewFile();
            done = true;
            Log.i(TAG, "extract done: " + written + " bytes");
        } catch (Throwable failure) {
            error = failure.toString();
            Log.e(TAG, "extract failed", failure);
        } finally {
            if (input != null) {
                try { input.close(); } catch (Throwable ignored) { }
            }
        }
    }'''
cache='''public void importCache(File file, File directory) {
        directory.mkdirs();
        ZipInputStream input = null;
        try {
            input = new ZipInputStream(new BufferedInputStream(new FileInputStream(file), 1048576));
            byte[] buffer = new byte[1048576];
            ZipEntry entry;
            while ((entry = input.getNextEntry()) != null) {
                if (entry.isDirectory()) continue;
                String name = entry.getName();
                if (name.startsWith("glcache/")) name = name.substring(8);
                if (name.length() == 0 || name.contains("/") || name.contains("..")) continue;
                FileOutputStream output = new FileOutputStream(new File(directory, name));
                try {
                    int count;
                    while ((count = input.read(buffer)) > 0) {
                        output.write(buffer, 0, count);
                        cacheWritten += count;
                    }
                } finally {
                    output.close();
                }
            }
            cacheDone = true;
        } catch (Throwable failure) {
            cacheFailed = true;
            Log.e(TAG, "cache import failed", failure);
        } finally {
            if (input != null) {
                try { input.close(); } catch (Throwable ignored) { }
            }
        }
    }'''
source=replace_method(source,'public void extract(File file)',extract)
source=replace_method(source,'public void importCache(File file, File file2)',cache)
smali=(base/'apktool_out/smali_classes8/com/popcap/pvz2cthd/BootActivity.smali').read_text(encoding='utf-8')
for name in re.findall(r'^\.method private (\w+)\(',smali,re.M):
    source=re.sub(r'\bpublic (void|File|boolean|int) '+re.escape(name)+r'\(',r'private \1 '+name+'(',source)
source=source.replace('public class BootActivity extends Activity {','''/**
 * Source reconstruction from this APK's classes8.dex.
 * Anonymous-class syntax and two exception/cleanup blocks were repaired for javac.
 * This is a maintained reconstruction, not the original developer source.
 * Build validation does not establish device/runtime equivalence.
 */
public class BootActivity extends Activity {''')
dest=project/'src/bootstrap/com/popcap/pvz2cthd/BootActivity.java';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(source,encoding='utf-8')
(project/'source-reconstruction.json').write_text(json.dumps({'source_origin':str(original.relative_to(base)),
    'reconstructed_java':['src/bootstrap/com/popcap/pvz2cthd/BootActivity.java'] +
        [p.relative_to(project).as_posix() for p in sorted((project/'src/game_bridge').rglob('*.java'))],
    'game_bridge_repairs':['SexyAppActivity: replace PurchaseCode.BILL_XML_PARSE_ERR with its original constant value 1200'],
    'compile_only_api_stubs':'tools/original-dex-api.jar; original DEX declarations, compile aliases and two unresolved original references; excluded from APK',
    'inactive_historical_stubs':'src/compile_only; no longer used by the current build',
    'repairs':['Anonymous outer-instance constructors expressed using Java lexical capture','Structured extraction and cache-import cleanup from decompiled catch control flow'],
    'native_libraries_rebuilt_from_source':False,'other_managed_classes_built_from':'Smali assembly',
    'resources_built_from':'Original binary resource table and resource files; both package IDs 0x66 and 0x7f retained'},indent=2),encoding='utf-8')
print('Reconstructed Java source:',dest)
