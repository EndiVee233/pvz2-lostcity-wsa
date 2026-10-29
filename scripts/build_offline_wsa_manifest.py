from pathlib import Path
import xml.etree.ElementTree as ET,subprocess
base=Path(__file__).resolve().parents[1];p=base/'rebuild_project';out=p/'wsa_test';ns='http://schemas.android.com/apk/res/android'
ET.register_namespace('android',ns);tree=ET.parse(out/'AndroidManifest.xml');app=tree.getroot().find('application');assert app is not None
for item in list(app):
    if item.tag=='meta-data' and item.get('{'+ns+'}name')=='pvz2.reconstruction.offline':app.remove(item)
ET.SubElement(app,'meta-data',{'{'+ns+'}name':'pvz2.reconstruction.offline','{'+ns+'}value':'true'})
manifest=out/'offline-AndroidManifest.xml';tree.write(manifest,encoding='utf-8',xml_declaration=True)
run=subprocess.run(['K:/pvz2-tools/build-tools-r34/android-14/aapt2.exe','link','-o',str(out/'offline-manifest-linked.apk'),'--manifest',str(manifest),
    '-I',str(base/'tools/apktool-framework/1.apk'),'-I',str(base/'PvZ2-LostCity-1.7.5.apk'),'--min-sdk-version','9','--target-sdk-version','30',
    '--version-code','747','--version-name','1.7.5-offline-reconstruction'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(p/'logs/wsa/offline-manifest-link.txt').write_bytes(run.stdout);run.check_returncode();print('Offline test manifest linked.')
