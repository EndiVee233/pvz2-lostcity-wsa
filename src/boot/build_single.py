import zipfile, os, sys, time

SRC = r'Y:\PvZ_work\pvz2-1.7.5-launcherless.apk'
DST = r'Y:\PvZ_work\pvz2-1.7.5-single-unsigned.apk'
MANIFEST = r'work\bootstrap\AndroidManifest_boot.xml'
ARSC = r'work\bootstrap\resources_patched.arsc'
DEX8 = r'work\bootstrap\classes8.dex'
LOGO = r'work\bootstrap\ea_logo.png'
FONT = r'work\bootstrap\pvz2font.ttf'
DATA = r'C:\Users\SpokeIsThere\Desktop\com.popcap.pvz2cthd.zip'

skip_prefixes = ('assets/pvz2tool/version/', 'META-INF/')
skip_names = {'AndroidManifest.xml', 'resources.arsc', 'classes8.dex',
              'assets/pvz2data.zip', 'assets/ea_logo.png', 'assets/pvz2font.ttf'}

def add_file(zout, name, path, compress=zipfile.ZIP_DEFLATED):
    with open(path, 'rb') as f:
        data = f.read()
    zi = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
    zi.compress_type = compress
    zi.external_attr = 0o644 << 16
    zout.writestr(zi, data, compress_type=compress)

def add_big(zout, name, path):
    size = os.path.getsize(path)
    zi = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_STORED
    zi.file_size = size
    zi.external_attr = 0o644 << 16
    with zout.open(zi, 'w') as out, open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            out.write(b)

def main():
    t0 = time.time()
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(DST, 'w', allowZip64=True) as zout:
        # required first entries
        add_file(zout, 'AndroidManifest.xml', MANIFEST)
        add_file(zout, 'resources.arsc', ARSC, zipfile.ZIP_STORED)
        add_file(zout, 'classes8.dex', DEX8)
        add_file(zout, 'assets/ea_logo.png', LOGO)
        add_file(zout, 'assets/pvz2font.ttf', FONT)
        for info in zin.infolist():
            n = info.filename
            if n in skip_names or any(n.startswith(p) for p in skip_prefixes):
                continue
            if n.endswith('/'):
                continue
            zi = zipfile.ZipInfo(n, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zi.internal_attr = info.internal_attr
            zi.create_system = info.create_system
            with zin.open(info) as src, zout.open(zi, 'w', force_zip64=True) as dst:
                while True:
                    b = src.read(1 << 20)
                    if not b:
                        break
                    dst.write(b)
            if int(time.time() - t0) % 30 == 0:
                pass
        for i in range(1, 4):
            add_big(zout, 'assets/pvz2data.zip.%03d' % i, r'work\bootstrap\data_parts\%03d' % i)
    print('done', DST, os.path.getsize(DST), 'in', round(time.time() - t0, 1), 's')

if __name__ == '__main__':
    main()
