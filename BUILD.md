# BUILD

These notes describe how the released APK was assembled. Paths in
`src/boot/build_single.py` are absolute placeholders from the build machine;
adjust them for your layout.

## Prerequisites

- Android SDK Build-Tools 34.0.0 (`aapt2`, `zipalign`, `apksigner`, `d8`)
- Android NDK 27 (`clang`, CMake 3.22)
- JDK 17+ (the build used Android Studio JBR)
- Python 3 with Pillow (only if regenerating screenshots/crops)
- The original Chinese 1.7.5 APK and a full resource directory, legally obtained

## 1. Manifest and label

- Set the MAIN/LAUNCHER activity to `com.popcap.pvz2cthd.BootActivity`
  (`src/tools/patch_axml_index.py`).
- Set the application `android:label` and `app_label` to `植物大战僵尸2`
  (`patch_axml_string.py`, `patch_arsc_label.py`).

## 2. BootActivity

```bash
javac -source 1.8 -target 1.8 \
  -bootclasspath $ANDROID_SDK/platforms/android-34/android.jar \
  -d classes src/boot/BootActivity.java
jar cf classes.jar -C classes com
java -cp $ANDROID_STUDIO/plugins/android/lib/r8.jar \
  com.android.tools.r8.D8 --min-api 21 \
  --lib $ANDROID_SDK/platforms/android-34/android.jar \
  --output dex classes.jar
cp dex/classes.dex classes8.dex
```

## 3. GL shim

```bash
cmake -S src/glshim -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=armeabi-v7a -DANDROID_PLATFORM=android-21 \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build -j1
```

`astc-codec` is added as a subdirectory; place it next to `src/glshim`.

## 4. Resource parts

Split the resource zip into <512 MB chunks so each asset can be opened by a 32-bit
process without a huge mmap:

```
assets/pvz2data.zip.001
assets/pvz2data.zip.002
assets/pvz2data.zip.003
```

`BootActivity` concatenates them with `ConcatAssetInputStream` and feeds a
`ZipInputStream`.

## 5. Assemble and sign

`src/boot/build_single.py` removes the old launcher assets
(`assets/pvz2tool/version/`), adds `classes8.dex`, `assets/ea_logo.png`,
`assets/pvz2font.ttf`, the three data parts, the patched manifest and
`resources.arsc` (stored uncompressed and 4-byte aligned).

```bash
zipalign -p -f 4 unsigned.apk aligned.apk
apksigner sign --ks pvz2.keystore --ks-key-alias pvz2 \
  --v1-signing-enabled true --v2-signing-enabled true \
  --out 植物大战僵尸2-1.7.5.apk aligned.apk
```

`resources.arsc` **must** be `ZIP_STORED` and 4-byte aligned, otherwise
Android 11+ refuses to install (`Targeting R+ requires resources.arsc ...`).

## 6. Skip the `服务器通讯中` overlay

`AndroidHttpProxy.GetNetworkStatus()` must return `0` (NET_NOT_REACHABLE).
With the original implementation the native side keeps issuing
`POST http://cloudpvz2android.ditwan.cn/index.php` once per frame while the
notice dialog is open (the endpoint is long dead), never leaves the waiting
state, and the `服务器通讯中...` overlay stays on screen and swallows taps.

Run the dex patch after assembling and before `zipalign`:

```bash
python src/tools/patch_dex_network_status.py unsigned.apk unsigned_netpatch.apk
mv unsigned_netpatch.apk unsigned.apk
```

The script rewrites `classes.dex` (keeping the APK layout, stored entries stay
4-byte aligned) and leaves the APK unsigned, so sign afterwards as usual.
With the patch no transaction is created at all (`CreateHttpTransaction`
count stays 0 in logcat) and the notice dialog shows its built-in text without
the overlay.