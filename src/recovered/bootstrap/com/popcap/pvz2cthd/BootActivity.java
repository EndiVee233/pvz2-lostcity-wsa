package com.popcap.pvz2cthd;

import android.R;
import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.content.res.ColorStateList;
import android.graphics.BitmapFactory;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Source reconstruction from this APK's classes8.dex.
 * Anonymous-class syntax and two exception/cleanup blocks were repaired for javac.
 * This is a maintained reconstruction, not the original developer source.
 * Build validation does not establish device/runtime equivalence.
 */
public class BootActivity extends Activity {
    private static final String[] PARTS = {"pvz2data.zip.001", "pvz2data.zip.002", "pvz2data.zip.003"};
    private static final String PREFIX = "com.popcap.pvz2cthd/files/";
    private static final String TAG = "PvZ2Bootstrap";
    private static final long TOTAL_BYTES = 2746000000L;
    private ProgressBar progressBar;
    private TextView statusView;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private volatile long written = 0;
    private volatile boolean done = false;
    private volatile String error = null;
    private boolean gameStarted = false;
    private volatile long cacheWritten = 0;
    private volatile boolean cacheDone = false;
    private volatile boolean cacheFailed = false;
    private long cacheTotal = 1;
    private boolean speedResourceStarted = false;
    private boolean speedResourceReady = false;
    private static final String SPEED_RESOURCE_SHA = "0aae11cf23e05377026323816f6e458264bdc193b312177bca6824589fa1d29f";
    private static final String BASE_RESOURCE_SHA = "12af3e81260ee7ad2a438a9175506839474a1ec4b7aa39b61ed9bda7fdda5835";

    @Override // android.app.Activity
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        requestWindowFeature(1);
        getWindow().setFlags(1024, 1024);
        getWindow().addFlags(128);
        buildUi();
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission("android.permission.WRITE_EXTERNAL_STORAGE") != 0) {
            requestPermissions(new String[]{"android.permission.WRITE_EXTERNAL_STORAGE", "android.permission.READ_EXTERNAL_STORAGE"}, 100);
        } else {
            begin();
        }
    }

    @Override // android.app.Activity
    public void onRequestPermissionsResult(int i, String[] strArr, int[] iArr) {
        super.onRequestPermissionsResult(i, strArr, iArr);
        if (i == 100) {
            if (iArr.length > 0 && iArr[0] == 0) {
                begin();
            } else {
                fail("需要存储权限才能解压资源");
            }
        }
    }

    private void begin() {
        final File externalFilesDir = getExternalFilesDir(null);
        if (externalFilesDir == null) {
            fail("无法访问外部存储");
            return;
        }
        if (new File(externalFilesDir, ".pvz2_extracted").exists() || (new File(externalFilesDir, "init.rsb.smf").exists() && new File(externalFilesDir, "dynamic.rsb.smf").exists())) {
            startGameWithCache();
        } else {
            new Thread(new Runnable() {
                @Override // java.lang.Runnable
                public void run() {
                    BootActivity.this.extract(externalFilesDir);
                }
            }, "pvz2-extract").start();
            this.ui.postDelayed(new Runnable() { // from class: com.popcap.pvz2cthd.BootActivity.2
                @Override // java.lang.Runnable
                public void run() {
                    BootActivity.this.updateProgress();
                }
            }, 250L);
        }
    }

    private void buildUi() {
        float f = getResources().getDisplayMetrics().density;
        int i = getResources().getDisplayMetrics().widthPixels;
        int i2 = getResources().getDisplayMetrics().heightPixels;
        Typeface typefaceCreateFromAsset = Typeface.DEFAULT_BOLD;
        try {
            typefaceCreateFromAsset = Typeface.createFromAsset(getAssets(), "pvz2font.ttf");
        } catch (Throwable th) {
        }
        FrameLayout frameLayout = new FrameLayout(this);
        frameLayout.setBackgroundColor(-16777216);
        ImageView imageView = new ImageView(this);
        try {
            imageView.setImageBitmap(BitmapFactory.decodeStream(getAssets().open("ea_logo.png")));
            imageView.setScaleType(ImageView.ScaleType.FIT_CENTER);
            float f2 = i2;
            FrameLayout.LayoutParams layoutParams = new FrameLayout.LayoutParams((int) (i * 0.55f), (int) (0.3f * f2), 49);
            layoutParams.topMargin = (int) (f2 * 0.1f);
            frameLayout.addView(imageView, layoutParams);
        } catch (Throwable th2) {
        }
        LinearLayout linearLayout = new LinearLayout(this);
        linearLayout.setOrientation(1);
        linearLayout.setGravity(1);
        int i3 = (int) (24.0f * f);
        linearLayout.setPadding(i3, i3, i3, i3);
        TextView textView = new TextView(this);
        textView.setText("正在进行首次解压");
        textView.setTextColor(-6501275);
        textView.setTextSize(30.0f);
        textView.setTypeface(typefaceCreateFromAsset);
        textView.setGravity(17);
        linearLayout.addView(textView);
        TextView textView2 = new TextView(this);
        textView2.setText("首次启动需要释放约 2.6 GB 游戏资源，请勿关闭应用");
        textView2.setTextColor(-4342339);
        textView2.setTextSize(13.0f);
        textView2.setTypeface(typefaceCreateFromAsset);
        textView2.setGravity(17);
        LinearLayout.LayoutParams layoutParams2 = new LinearLayout.LayoutParams(-2, -2);
        int i4 = (int) (f * 12.0f);
        layoutParams2.topMargin = i4;
        linearLayout.addView(textView2, layoutParams2);
        this.progressBar = new ProgressBar(this, null, R.attr.progressBarStyleHorizontal);
        this.progressBar.setMax(1000);
        this.progressBar.setProgress(0);
        this.progressBar.setProgressTintList(ColorStateList.valueOf(-8604862));
        this.progressBar.setProgressBackgroundTintList(ColorStateList.valueOf(-14995941));
        LinearLayout.LayoutParams layoutParams3 = new LinearLayout.LayoutParams((int) (i * 0.72f), (int) (16.0f * f));
        layoutParams3.topMargin = (int) (26.0f * f);
        linearLayout.addView(this.progressBar, layoutParams3);
        this.statusView = new TextView(this);
        this.statusView.setText("0%");
        this.statusView.setTextColor(-1);
        this.statusView.setTextSize(18.0f);
        this.statusView.setTypeface(typefaceCreateFromAsset);
        this.statusView.setGravity(17);
        LinearLayout.LayoutParams layoutParams4 = new LinearLayout.LayoutParams(-2, -2);
        layoutParams4.topMargin = i4;
        linearLayout.addView(this.statusView, layoutParams4);
        TextView textView3 = new TextView(this);
        textView3.setText("解压完成后会自动进入游戏");
        textView3.setTextColor(-6381922);
        textView3.setTextSize(12.0f);
        textView3.setTypeface(typefaceCreateFromAsset);
        textView3.setGravity(17);
        LinearLayout.LayoutParams layoutParams5 = new LinearLayout.LayoutParams(-2, -2);
        layoutParams5.topMargin = (int) (f * 8.0f);
        linearLayout.addView(textView3, layoutParams5);
        FrameLayout.LayoutParams layoutParams6 = new FrameLayout.LayoutParams(-1, -2, 81);
        layoutParams6.bottomMargin = (int) (i2 * 0.08f);
        frameLayout.addView(linearLayout, layoutParams6);
        setContentView(frameLayout);
    }

    private void updateProgress() {
        if (this.error != null) {
            fail(this.error);
            return;
        }
        int iMin = (int) Math.min(1000L, (this.written * 1000) / TOTAL_BYTES);
        this.progressBar.setProgress(iMin);
        this.statusView.setText(String.format("%.1f%%   %d / %d MB", Double.valueOf(((double) iMin) / 10.0d), Long.valueOf(this.written >> 20), 2618L));
        if (this.done) {
            this.progressBar.setProgress(1000);
            this.statusView.setText("解压完成，正在启动游戏...");
            this.ui.postDelayed(new Runnable() { // from class: com.popcap.pvz2cthd.BootActivity.3
                @Override // java.lang.Runnable
                public void run() {
                    BootActivity.this.startGameWithCache();
                }
            }, 600L);
            return;
        }
        this.ui.postDelayed(new Runnable() { // from class: com.popcap.pvz2cthd.BootActivity.4
            @Override // java.lang.Runnable
            public void run() {
                BootActivity.this.updateProgress();
            }
        }, 250L);
    }

    private void extract(File file) {
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
    }

    private void fail(String str) {
        if (this.statusView != null) {
            this.statusView.setText("解压失败：" + str + "\n请重启应用重试");
            this.statusView.setTextColor(-30080);
        }
    }

    private void startGameWithCache() {
        if (this.gameStarted) {
            return;
        }
        if (!speedResourceReady) {
            if (speedResourceStarted) return;
            speedResourceStarted = true;
            new Thread(new Runnable() {
                public void run() {
                    try {
                        applyOriginalSpeedResource();
                        ui.post(new Runnable() {
                            public void run() {
                                speedResourceReady = true;
                                startGameWithCache();
                            }
                        });
                    } catch (final Exception failure) {
                        Log.e(TAG, "original speed resource update failed", failure);
                        ui.post(new Runnable() {
                            public void run() { fail("资源更新失败，请重启应用重试"); }
                        });
                    }
                }
            }, "pvz2-speed-resource").start();
            return;
        }
        final File file = new File(getCacheDir(), "glcache");
        if (file.exists() && file.list() != null && file.list().length > 0) {
            startGame();
            return;
        }
        final File fileFindCachePack = findCachePack();
        if (fileFindCachePack == null) {
            startGame();
            return;
        }
        this.cacheTotal = 1992294400L;
        this.statusView.setText("正在导入纹理缓存...");
        this.progressBar.setProgress(0);
        new Thread(new Runnable() {
                @Override // java.lang.Runnable
            public void run() {
                BootActivity.this.importCache(fileFindCachePack, file);
            }
        }, "pvz2-cache").start();
        this.ui.postDelayed(new Runnable() { // from class: com.popcap.pvz2cthd.BootActivity.6
            @Override // java.lang.Runnable
            public void run() {
                BootActivity.this.updateCacheProgress();
            }
        }, 200L);
    }

    private File findCachePack() {
        try {
            File obbDir = getObbDir();
            File externalFilesDir = getExternalFilesDir(null);
            File externalStoragePublicDirectory = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            File[] fileArr = new File[4];
            fileArr[0] = new File(obbDir, "glcache-pack.zip");
            fileArr[1] = new File(obbDir, "glcache.zip");
            fileArr[2] = externalFilesDir != null ? new File(externalFilesDir.getParentFile(), "glcache.zip") : null;
            fileArr[3] = new File(externalStoragePublicDirectory, "glcache-pack.zip");
            for (int i = 0; i < 4; i++) {
                File file = fileArr[i];
                if (file != null && file.isFile()) {
                    return file;
                }
            }
        } catch (Throwable th) {
        }
        return null;
    }

    private static String resourceSha(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        InputStream input = new FileInputStream(file);
        try {
            byte[] buffer = new byte[65536];
            int count;
            while ((count = input.read(buffer)) != -1) digest.update(buffer, 0, count);
        } finally { input.close(); }
        StringBuilder text = new StringBuilder();
        for (byte b : digest.digest()) {
            int value = b & 255;
            if (value < 16) text.append('0');
            text.append(Integer.toHexString(value));
        }
        return text.toString();
    }

    private void applyOriginalSpeedResource() throws Exception {
        InputStream overlay;
        try {
            overlay = getAssets().open("reconstruction/dynamic-original-speed.rsb.smf");
        } catch (IOException noOverlay) {
            // Other build variants do not package this optional resource update.
            return;
        }
        try {
            File base = getExternalFilesDir(null);
            if (base == null) throw new IOException("Missing resource directory");
            File target = new File(base, "dynamic.rsb.smf");
            File marker = new File(base, ".original-speed-57d9c44");
            if (marker.isFile() && target.length() == 23453696L) return;
            String current = resourceSha(target);
            if (!SPEED_RESOURCE_SHA.equals(current)) {
                if (!BASE_RESOURCE_SHA.equals(current)) throw new IOException("Unexpected resource version");
                File temporary = new File(base, "dynamic-original-speed.tmp");
                FileOutputStream output = new FileOutputStream(temporary);
                try {
                    byte[] buffer = new byte[65536];
                    int count;
                    while ((count = overlay.read(buffer)) != -1) output.write(buffer, 0, count);
                    output.getFD().sync();
                } finally { output.close(); }
                if (!SPEED_RESOURCE_SHA.equals(resourceSha(temporary))) throw new IOException("Resource checksum mismatch");
                if (!temporary.renameTo(target)) throw new IOException("Resource replacement failed");
                Log.i(TAG, "original speed resource applied: 57d9c44");
            } else {
                Log.i(TAG, "original speed resource already current: 57d9c44");
            }
            if (!marker.createNewFile() && !marker.isFile()) throw new IOException("Resource marker failed");
        } finally { overlay.close(); }
    }

    private void importCache(File file, File directory) {
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
    }

    private void updateCacheProgress() {
        int iMin = (int) Math.min(1000L, (this.cacheWritten * 1000) / this.cacheTotal);
        this.progressBar.setProgress(iMin);
        this.statusView.setText(String.format("正在导入纹理缓存   %.1f%%", Double.valueOf(((double) iMin) / 10.0d)));
        if (this.cacheDone || this.cacheFailed) {
            try {
                new File(getCacheDir(), "glcache/.pack").createNewFile();
            } catch (Throwable th) {
            }
            startGame();
        } else {
            this.ui.postDelayed(new Runnable() { // from class: com.popcap.pvz2cthd.BootActivity.7
                @Override // java.lang.Runnable
                public void run() {
                    BootActivity.this.updateCacheProgress();
                }
            }, 250L);
        }
    }

    private void startGame() {
        if (this.gameStarted) {
            return;
        }
        this.gameStarted = true;
        try {
            Intent intent = new Intent();
            intent.setClassName(this, "com.popcap.pvz2cmhd.SexyAppActivity");
            intent.addFlags(268468224);
            startActivity(intent);
        } catch (Throwable th) {
            Log.e(TAG, "start game failed", th);
        }
        finish();
    }

    static class ConcatAssetInputStream extends InputStream {
        private final AssetManager am;
        private InputStream cur;
        private int idx = -1;
        private final String[] names;

        ConcatAssetInputStream(AssetManager assetManager, String[] strArr) {
            this.am = assetManager;
            this.names = strArr;
        }

        private boolean next() throws IOException {
            if (this.cur != null) {
                try {
                    this.cur.close();
                } catch (IOException e) {
                }
                this.cur = null;
            }
            this.idx++;
            if (this.idx >= this.names.length) {
                return false;
            }
            this.cur = this.am.open(this.names[this.idx], 2);
            return true;
        }

        @Override // java.io.InputStream
        public int read() throws IOException {
            byte[] bArr = new byte[1];
            if (read(bArr, 0, 1) < 0) {
                return -1;
            }
            return bArr[0] & 255;
        }

        @Override // java.io.InputStream
        public int read(byte[] bArr, int i, int i2) throws IOException {
            do {
                if (this.cur == null && !next()) {
                    return -1;
                }
                int i3 = this.cur.read(bArr, i, i2);
                if (i3 >= 0) {
                    return i3;
                }
            } while (next());
            return -1;
        }

        @Override // java.io.InputStream, java.io.Closeable, java.lang.AutoCloseable
        public void close() throws IOException {
            if (this.cur != null) {
                try {
                    this.cur.close();
                } catch (IOException e) {
                }
                this.cur = null;
            }
        }
    }
}
