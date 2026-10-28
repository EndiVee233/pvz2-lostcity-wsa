package com.popcap.SexyAppFramework;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ConfigurationInfo;
import android.content.res.Configuration;
import android.graphics.Rect;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.util.Log;
import android.view.Display;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.inputmethod.InputMethodManager;
import android.widget.RelativeLayout;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SexyAppFrameworkActivity extends Activity {
    public static final String Cache_Lib_Dir = "/libsrc.so";
    private static final int HANDLER_CLOSE_IME_KEYBOARD = 3;
    private static final int HANDLER_OPEN_IME_KEYBOARD = 2;
    private List<OnActivityResultListener> mActivityResultListeners;
    private AndroidSurfaceView mGLView;
    private AndroidGameApp mGameApp;
    private Handler mIMEKeyboardHandler;
    private SexyEditText mSexyEditText;
    private SexyTextWatcher mSexyTextWatcher = null;
    private AndroidSplashScreen mSplashScreen = null;
    private AndroidUIEventManager mUIEventManager;
    static boolean DEBUG = true;
    private static SexyAppFrameworkActivity sTheActivity = null;
    private static ArrayList<AndroidSplashScreen.SplashImage> mSplashScreenImages = null;
    private static int mSplashScreenBackgroudColor = -16777216;
    private static int mTelecomChannelID = 41000002;
    private static String mChinaMobileMMChannelID = "";
    private static boolean mEnablePNS = false;
    private static ArrayList<AndroidSplashScreen.SplashImage> mFirstSplashScreenImage = null;
    private static AndroidSplashScreen.SplashImage mProgressBarImage = null;
    private static AndroidSplashScreen.SplashImage mProgressBarBgImage = null;

    public interface OnActivityResultListener {
        void onActivityResult(int i, int i2, Intent intent);
    }

    public AndroidUIEventManager getUIEventMgr() {
        return this.mUIEventManager;
    }

    public AndroidGameApp getGameApp() {
        return this.mGameApp;
    }

    public AndroidSurfaceView getSurfaceView() {
        return this.mGLView;
    }

    public static SexyAppFrameworkActivity instance() {
        return sTheActivity;
    }

    public SexyAppFrameworkActivity() {
        this.mActivityResultListeners = null;
        sTheActivity = this;
        this.mActivityResultListeners = new ArrayList();
    }

    public void addOnActivityResultListener(OnActivityResultListener listener) {
        this.mActivityResultListeners.add(listener);
    }

    public void removeOnActivityResultListener(OnActivityResultListener listener) {
        this.mActivityResultListeners.remove(listener);
    }

    public void AddSplashScreen() {
        if (mSplashScreenImages != null && !mSplashScreenImages.isEmpty()) {
            runOnUiThread(new Runnable() { // from class: com.popcap.SexyAppFramework.SexyAppFrameworkActivity.1
                @Override // java.lang.Runnable
                public void run() {
                    if (SexyAppFrameworkActivity.this.mSplashScreen == null) {
                        SexyAppFrameworkActivity.this.mSplashScreen = new AndroidSplashScreen(SexyAppFrameworkActivity.this.getApplicationContext());
                        ViewGroup.LayoutParams lp = new ViewGroup.LayoutParams(-2, -2);
                        SexyAppFrameworkActivity.this.addContentView(SexyAppFrameworkActivity.this.mSplashScreen, lp);
                    }
                }
            });
        } else {
            Log.e("SexyAppFramework", "No splash screen specified for app. Add a call AddSplashScreenImage in your source wrapper to enable a splash screen.");
        }
    }

    public void RemoveSplashScreen() {
        if (SplashScreenShowing()) {
            runOnUiThread(new Runnable() { // from class: com.popcap.SexyAppFramework.SexyAppFrameworkActivity.2
                @Override // java.lang.Runnable
                public void run() {
                    if (SexyAppFrameworkActivity.this.SplashScreenShowing()) {
                        ViewGroup vg = (ViewGroup) SexyAppFrameworkActivity.this.mSplashScreen.getParent();
                        vg.removeView(SexyAppFrameworkActivity.this.mSplashScreen);
                        SexyAppFrameworkActivity.this.mSplashScreen = null;
                    }
                }
            });
        }
    }

    public boolean SplashScreenShowing() {
        return this.mSplashScreen != null;
    }

    public void InitIMEKeyboardHandler() {
        this.mIMEKeyboardHandler = new Handler() { // from class: com.popcap.SexyAppFramework.SexyAppFrameworkActivity.3
            @Override // android.os.Handler
            public void handleMessage(Message msg) {
                switch (msg.what) {
                    case 2:
                        if (SexyAppFrameworkActivity.this.mSexyEditText != null && SexyAppFrameworkActivity.this.mSexyEditText.requestFocus()) {
                            if (SexyAppFrameworkActivity.this.mSexyTextWatcher == null) {
                                SexyAppFrameworkActivity.this.mSexyTextWatcher = new SexyTextWatcher(SexyAppFrameworkActivity.this.mGameApp);
                            }
                            SexyAppFrameworkActivity.this.mSexyEditText.removeTextChangedListener(SexyAppFrameworkActivity.this.mSexyTextWatcher);
                            SexyAppFrameworkActivity.this.mSexyEditText.setText("");
                            SexyAppFrameworkActivity.this.mSexyEditText.append(SexyAppFrameworkActivity.this.mGameApp.getEditText());
                            SexyAppFrameworkActivity.this.mSexyEditText.addTextChangedListener(SexyAppFrameworkActivity.this.mSexyTextWatcher);
                            InputMethodManager imm = (InputMethodManager) SexyAppFrameworkActivity.this.mGLView.getContext().getSystemService("input_method");
                            imm.showSoftInput(SexyAppFrameworkActivity.this.mSexyEditText, 0);
                            Log.v("SexyAppFrameworkActivity", "openIMEKeyboard");
                            break;
                        }
                        break;
                    case 3:
                        if (SexyAppFrameworkActivity.this.mSexyEditText != null) {
                            SexyAppFrameworkActivity.this.mSexyEditText.removeTextChangedListener(SexyAppFrameworkActivity.this.mSexyTextWatcher);
                            InputMethodManager imm2 = (InputMethodManager) SexyAppFrameworkActivity.this.mGLView.getContext().getSystemService("input_method");
                            imm2.hideSoftInputFromWindow(SexyAppFrameworkActivity.this.mSexyEditText.getWindowToken(), 0);
                            SexyAppFrameworkActivity.this.mGLView.requestFocus();
                            Log.v("SexyAppFrameworkActivity", "closeIMEKeyboard");
                        }
                        break;
                }
            }
        };
    }

    public void InitUncaughtExceptionHandler() {
        Thread.setDefaultUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() { // from class: com.popcap.SexyAppFramework.SexyAppFrameworkActivity.4
            @Override // java.lang.Thread.UncaughtExceptionHandler
            public void uncaughtException(Thread t, Throwable e) {
                e.printStackTrace();
                Log.e("handller", "uncaughtException");
                SexyAppFrameworkActivity.this.handleNativeCrash(e.toString());
            }
        });
    }

    public void openIMEKeyboard() {
        Message msg = new Message();
        msg.what = 2;
        this.mIMEKeyboardHandler.sendMessage(msg);
    }

    public void closeIMEKeyboard() {
        Message msg = new Message();
        msg.what = 3;
        this.mIMEKeyboardHandler.sendMessage(msg);
    }

    public void handleNativeCrash(String errorMsg) {
        Log.e("handller", "handller");
        ErrorLogSender errSender = new ErrorLogSender();
        errSender.SendErroLog(errorMsg);
        new RuntimeException("crashed here (native trace should follow after the Java trace)").printStackTrace();
    }

    @Override // android.app.Activity
    public void onCreate(Bundle savedInstanceState) {
        if (DEBUG) {
            Log.i("Activity", "onCreate.");
        }
        super.onCreate(savedInstanceState);
        if (!NeedLoadCacheLib()) {
            String downloadSOPath = GetUserDataFolder() + Cache_Lib_Dir;
            System.load(downloadSOPath);
        } else {
            System.loadLibrary("Src");
            System.loadLibrary("czProject");
            System.loadLibrary("HookPVZ2");
            System.loadLibrary("Restart");
        }
        ActivityManager am = (ActivityManager) getSystemService("activity");
        ConfigurationInfo info = am.getDeviceConfigurationInfo();
        boolean bGLES2Supported = info.reqGlEsVersion >= 131072 || Build.FINGERPRINT.startsWith("generic");
        int iGLESVersionSupported = bGLES2Supported ? 2 : 1;
        this.mUIEventManager = new AndroidUIEventManager();
        this.mGLView = new AndroidSurfaceView(getApplicationContext(), getWindowManager(), this.mUIEventManager, iGLESVersionSupported);
        this.mGameApp = new AndroidGameApp(this, this.mGLView, this.mUIEventManager);
        Display display = ((WindowManager) getSystemService("window")).getDefaultDisplay();
        this.mGLView.SetScreenSizeInPixels(display.getWidth(), display.getHeight());
        this.mGLView.init(5, 6, 5, 0, 0, 0);
        RelativeLayout layout = new RelativeLayout(this);
        RelativeLayout.LayoutParams layout_params = new RelativeLayout.LayoutParams(-2, -2);
        layout.setLayoutParams(layout_params);
        RelativeLayout.LayoutParams edittext_layout_params = new RelativeLayout.LayoutParams(20, 30);
        edittext_layout_params.leftMargin = -50;
        edittext_layout_params.topMargin = 100;
        this.mSexyEditText = new SexyEditText(this);
        this.mSexyEditText.setSexyAppFrameworkActivity(this);
        this.mSexyEditText.setSingleLine();
        this.mSexyEditText.setLayoutParams(edittext_layout_params);
        layout.addView(this.mGLView);
        layout.addView(this.mSexyEditText);
        setContentView(layout);
        InitIMEKeyboardHandler();
        InitUncaughtExceptionHandler();
        AddSplashScreen();
        this.mGameApp.onActivityCreate(savedInstanceState, getIntent());
    }

    @Override // android.app.Activity
    public void onStart() {
        if (DEBUG) {
            Log.i("Activity", "onStart.");
        }
        super.onStart();
        Uri data = getIntent().getData();
        if (data != null) {
            this.mGameApp.setStartUrl(data.toString());
            getIntent().setData(null);
        }
        this.mGameApp.onActivityStart();
    }

    @Override // android.app.Activity
    public void onRestart() {
        if (DEBUG) {
            Log.i("Activity", "onRestart.");
        }
        super.onRestart();
        if (this.mGameApp != null) {
            this.mGameApp.onActivityRestart();
        }
    }

    @Override // android.app.Activity
    public void onResume() {
        if (DEBUG) {
            Log.i("Activity", "onResume.");
        }
        super.onResume();
        this.mGameApp.onActivityResume();
        this.mGLView.onResume();
    }

    @Override // android.app.Activity
    public void onPause() {
        if (DEBUG) {
            Log.i("Activity", "onPause.");
        }
        super.onPause();
        this.mGLView.onPause();
        this.mGameApp.onActivityPause();
    }

    @Override // android.app.Activity
    public void onStop() {
        if (DEBUG) {
            Log.i("Activity", "onStop.");
        }
        super.onStop();
        this.mGameApp.onActivityStop();
    }

    @Override // android.app.Activity
    public void onDestroy() {
        if (DEBUG) {
            Log.i("Activity", "onDestroy.");
        }
        super.onDestroy();
        if (this.mGameApp != null) {
            this.mGameApp.onActivityDestroy();
            this.mGameApp = null;
        }
        this.mGLView = null;
        this.mUIEventManager = null;
        sTheActivity = null;
    }

    public void ShowExitGame() {
    }

    @Override // android.app.Activity
    public void onSaveInstanceState(Bundle outState) {
        if (DEBUG) {
            Log.i("Activity", "onSaveInstanceState.");
        }
        super.onSaveInstanceState(outState);
        if (this.mGameApp != null) {
            this.mGameApp.onSaveInstanceState(outState);
        }
    }

    @Override // android.app.Activity, android.content.ComponentCallbacks
    public void onConfigurationChanged(Configuration newConfig) {
        if (DEBUG) {
            Log.i("Activity", "onConfigurationChanged.");
        }
        super.onConfigurationChanged(newConfig);
        this.mGameApp.HandleOnConfigurationChanged(newConfig);
    }

    @Override // android.app.Activity, android.view.Window.Callback
    public void onWindowFocusChanged(boolean hasFocus) {
        if (DEBUG) {
            Log.i("Activity", "onWindowFocusChanged.");
        }
        super.onWindowFocusChanged(hasFocus);
        this.mGameApp.onWindowFocusChanged(hasFocus);
    }

    @Override // android.app.Activity
    protected void onNewIntent(Intent intent) {
        if (DEBUG) {
            Log.i("Activity", "onNewIntent.");
        }
        setIntent(intent);
    }

    @Override // android.app.Activity
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (DEBUG) {
            Log.i("Activity", "onActivityResult.");
        }
        super.onActivityResult(requestCode, resultCode, data);
        for (OnActivityResultListener listener : this.mActivityResultListeners) {
            listener.onActivityResult(requestCode, resultCode, data);
        }
        if (this.mGameApp != null && requestCode != 9216358) {
            this.mGameApp.onActivityResult(requestCode, resultCode, data);
        }
    }

    private boolean NeedLoadCacheLib() {
        String downloadSOPath = GetUserDataFolder() + Cache_Lib_Dir;
        File soFile = new File(downloadSOPath);
        return !soFile.exists();
    }

    private String GetUserDataFolder() {
        Context ctxt = getApplicationContext();
        ctxt.getExternalFilesDir(null);
        File dirFile = null;
        if (0 == 0) {
            dirFile = ctxt.getFilesDir();
        }
        if (dirFile == null) {
            return null;
        }
        String dirName = dirFile.getAbsolutePath();
        return dirName;
    }

    protected static void AddSplashScreenImage(int aBGResourceID, int aBGResourceWidth, int aBGResourceHeight) {
        if (mSplashScreenImages == null) {
            mSplashScreenImages = new ArrayList<>();
        }
        mSplashScreenImages.add(new AndroidSplashScreen.SplashImage(aBGResourceID, aBGResourceWidth, aBGResourceHeight));
    }

    protected static void AddFirstSplashScreenImage(int aBGResourceID, int aBGResourceWidth, int aBGResourceHeight) {
        if (mFirstSplashScreenImage == null) {
            mFirstSplashScreenImage = new ArrayList<>();
        }
        mFirstSplashScreenImage.add(new AndroidSplashScreen.SplashImage(aBGResourceID, aBGResourceWidth, aBGResourceHeight));
    }

    protected static void AddProgressBarImage(int aBGResourceID, int aBGResourceWidth, int aBGResourceHeight) {
        if (mProgressBarImage == null) {
            mProgressBarImage = new AndroidSplashScreen.SplashImage(aBGResourceID, aBGResourceWidth, aBGResourceHeight);
        }
    }

    protected static void AddProgressBarBgImage(int aBGResourceID, int aBGResourceWidth, int aBGResourceHeight) {
        if (mProgressBarBgImage == null) {
            mProgressBarBgImage = new AndroidSplashScreen.SplashImage(aBGResourceID, aBGResourceWidth, aBGResourceHeight);
        }
    }

    public static class SplashImageComparator implements Comparator<AndroidSplashScreen.SplashImage> {
        @Override // java.util.Comparator
        public int compare(AndroidSplashScreen.SplashImage lhs, AndroidSplashScreen.SplashImage rhs) {
            return lhs.GetIntendedArea().compareTo(rhs.GetIntendedArea());
        }
    }

    public static int GetBestFitSplashImage(int aDisplayWidth, int aDisplayHeight) {
        int aSplashResourceID = -1;
        if (mSplashScreenImages.isEmpty()) {
            return -1;
        }
        Collections.sort(mSplashScreenImages, new SplashImageComparator());
        Rect aDisplayRect = new Rect(0, 0, aDisplayWidth, aDisplayHeight);
        for (AndroidSplashScreen.SplashImage img : mSplashScreenImages) {
            Rect aIntendedDisplayRect = img.GetIntendedDisplayRect();
            if (aIntendedDisplayRect.contains(aDisplayRect)) {
                aSplashResourceID = img.GetResourceID();
                break;
            }
        }
        if (aSplashResourceID == -1) {
            int aSplashResourceID2 = mSplashScreenImages.get(0).GetResourceID();
            return aSplashResourceID2;
        }
        return aSplashResourceID;
    }

    public static int GetBestFitFirstSplashImage(int aDisplayWidth, int aDisplayHeight) {
        int aSplashResourceID = -1;
        if (mFirstSplashScreenImage.isEmpty()) {
            return -1;
        }
        Collections.sort(mFirstSplashScreenImage, new SplashImageComparator());
        Rect aDisplayRect = new Rect(0, 0, aDisplayWidth, aDisplayHeight);
        for (AndroidSplashScreen.SplashImage img : mFirstSplashScreenImage) {
            Rect aIntendedDisplayRect = img.GetIntendedDisplayRect();
            if (aIntendedDisplayRect.contains(aDisplayRect)) {
                aSplashResourceID = img.GetResourceID();
                break;
            }
        }
        if (aSplashResourceID == -1) {
            int aSplashResourceID2 = mFirstSplashScreenImage.get(0).GetResourceID();
            return aSplashResourceID2;
        }
        return aSplashResourceID;
    }

    public static AndroidSplashScreen.SplashImage GetProgressBarSplashImage() {
        return mProgressBarImage;
    }

    public static AndroidSplashScreen.SplashImage GetProgressBarBgSplashImage() {
        return mProgressBarBgImage;
    }

    protected static void SetSplashScreenBackgroudColor(int aColor) {
        mSplashScreenBackgroudColor = aColor;
    }

    public static int GetSplashScreenBackgroudColor() {
        return mSplashScreenBackgroudColor;
    }

    protected static void SetTelecomChannelID(int channel) {
        mTelecomChannelID = channel;
    }

    public static int GetTelecomChannelID() {
        return mTelecomChannelID;
    }

    protected static void SetChinaMobileMMChannelID(String channel) {
        mChinaMobileMMChannelID = channel;
    }

    public static String GetChinaMobileMMChannelID() {
        return mChinaMobileMMChannelID;
    }

    public static boolean IsEnablePNS() {
        return mEnablePNS;
    }

    public static void SetEnablePNS(boolean isEnable) {
        mEnablePNS = isEnable;
    }
}
