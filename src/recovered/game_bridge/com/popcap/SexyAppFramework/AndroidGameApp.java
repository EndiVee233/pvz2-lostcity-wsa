package com.popcap.SexyAppFramework;

import android.app.ActivityManager;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.content.res.Configuration;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Debug;
import android.os.Environment;
import android.os.PowerManager;
import android.os.Process;
import android.os.StatFs;
import android.os.SystemClock;
import android.os.Vibrator;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import android.util.Log;
import android.view.Display;
import android.view.inputmethod.InputMethodManager;
import com.popcap.util.PopCapPushNotificationService;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.util.Currency;
import java.util.Locale;
import java.util.UUID;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidGameApp {
    static final int MobileCard_ChinaMobile = 1;
    static final int MobileCard_Null = 0;
    static final int MobileCard_Telecom = 4;
    static final int MobileCard_Unicom = 2;
    private static final int UI_ORIENTATION_FACE_DOWN = 6;
    private static final int UI_ORIENTATION_FACE_UP = 5;
    private static final int UI_ORIENTATION_LANDSCAPE_LEFT = 4;
    private static final int UI_ORIENTATION_LANDSCAPE_RIGHT = 3;
    private static final int UI_ORIENTATION_PORTRAIT = 1;
    private static final int UI_ORIENTATION_PORTRAIT_UPSIDE_DOWN = 2;
    private static final int UI_ORIENTATION_UNKNOWN = 0;
    private SexyAppFrameworkActivity mActivity;
    private int mCurrentOrientation;
    private AndroidSurfaceView mGLView;
    private AndroidHttpProxy mHttpProxy;
    private AndroidUIEventManager mUIEventManager;
    public boolean mbAppIsSuspended;
    public boolean mbNativeInitialized;
    private static SexyAppFrameworkActivity activity = null;
    static boolean DEBUG = true;
    private PowerManager.WakeLock mlWakeLock = null;
    private String mCommandLineFlag = null;
    private boolean mbGotFocusEvent = false;
    private boolean mbGotResumedEvent = false;
    private boolean mbAppIsFocusedState = false;

    private int Device_GetCurrentUIOrientation() {
        try {
            Display defaultDisplay = this.mActivity.getWindowManager().getDefaultDisplay();
            int width = defaultDisplay.getWidth();
            int height = defaultDisplay.getHeight();
            int rotation = defaultDisplay.getRotation();
            if (width > 0 && height > 0 && width < height) {
            }
            if (2 == 2) {
                return (rotation == 0 || rotation == 1) ? 4 : 3;
            }
            if (2 == 1) {
                return (rotation == 0 || rotation == 1) ? 1 : 2;
            }
            return 0;
        } catch (Exception e) {
            Log.e("Exception", e.toString());
            return 0;
        }
    }

    private native boolean Native_GameAppInitialize(AndroidSurfaceView androidSurfaceView, AndroidHttpProxy androidHttpProxy, PackageManager packageManager);

    private native void Native_GameAppTeardown();

    private native void Native_applicationDidBecomeActive();

    private native void Native_applicationDidEnterBackground();

    private native void Native_applicationDidFinishLaunching();

    private native void Native_applicationWillBecomeForeground();

    private native void Native_applicationWillFinishLaunching(String str);

    private native void Native_applicationWillLoseFocus();

    private native void Native_applicationWillResignActive();

    private native void Native_applicationWillTerminate();

    private native String Native_getEditText();

    private native void Native_onOrientationChanged(int i, int i2);

    private native void Native_setEditText(String str);

    private native void Native_setStartUrl(String str);

    private int getTypeByIMSI(String i_imsi) {
        return 4;
    }

    private String Resources_GetUserDataFolder() {
        if ("com.popcap.pvz2cthd.reconstruction".equals(this.mActivity.getPackageName())) {
            File isolated = new File(this.mActivity.getFilesDir(), "userdata");
            isolated.mkdirs();
            return isolated.getAbsolutePath();
        }
        String string = new StringBuffer().append("/sdcard/Android/data/com.popcap.pvz2cthd").append(new StringBuffer().append("/").append(this.mActivity.getApplicationContext().getPackageName()).toString()).toString();
        File file = new File(string);
        if (!file.exists()) {
            file.mkdirs();
        }
        return string;
    }

    public AndroidGameApp(SexyAppFrameworkActivity InActivity, AndroidSurfaceView InGLView, AndroidUIEventManager InUIEventManager) {
        this.mActivity = InActivity;
        this.mGLView = InGLView;
        activity = InActivity;
        this.mHttpProxy = new AndroidHttpProxy(this.mActivity.getApplicationContext());
        this.mHttpProxy.Startup();
        this.mUIEventManager = InUIEventManager;
        this.mbAppIsSuspended = false;
        PackageManager aPackageMgr = this.mActivity.getPackageManager();
        this.mbNativeInitialized = Native_GameAppInitialize(this.mGLView, this.mHttpProxy, aPackageMgr);
        this.mCurrentOrientation = Device_GetCurrentUIOrientation();
    }

    public void onActivityCreate(Bundle savedInstanceState, Intent intent) {
        this.mCommandLineFlag = intent.getStringExtra("commandLine");
        if (DEBUG) {
            Log.i("Game", String.format("onActivityCreate - Native_applicationWillFinishLaunching :: commandLine = %s", this.mCommandLineFlag));
        }
        Native_applicationWillFinishLaunching(this.mCommandLineFlag);
        if (this.mlWakeLock == null) {
            PowerManager pm = (PowerManager) this.mActivity.getSystemService("power");
            this.mlWakeLock = pm.newWakeLock(268435466, "PopCapWakeLock");
            this.mlWakeLock.acquire();
        }
    }

    public void onActivityStart() {
        if (DEBUG) {
            Log.i("Game", "onActivityStart - Native_applicationDidFinishLaunching");
        }
        Native_applicationDidFinishLaunching();
    }

    public void onActivityRestart() {
        if (DEBUG) {
            Log.i("Game", "onActivityRestart - Do nothing for Native");
        }
    }

    public void onActivityResume() {
        this.mbGotResumedEvent = true;
        TryGainFocus();
        if (DEBUG) {
            Log.i("Game", "onActivityResume - Native_applicationWillBecomeForeground");
        }
        Native_applicationWillBecomeForeground();
        if (this.mlWakeLock == null) {
            PowerManager pm = (PowerManager) this.mActivity.getSystemService("power");
            this.mlWakeLock = pm.newWakeLock(10, "PopCapWakeLock");
        }
        if (!this.mlWakeLock.isHeld()) {
            this.mlWakeLock.acquire();
        }
        if (DEBUG) {
            Log.i("Game", "onActivityResume - Native_applicationDidBecomeActive");
        }
        Native_applicationDidBecomeActive();
    }

    public void onActivityPause() {
        this.mbGotResumedEvent = false;
        if (DEBUG) {
            Log.i("Game", "onActivityPause - Native_applicationWillResignActive");
        }
        Native_applicationWillResignActive();
        if (this.mlWakeLock != null && this.mlWakeLock.isHeld()) {
            this.mlWakeLock.release();
        }
        if (DEBUG) {
            Log.i("Game", "onActivityPause - Native_applicationDidEnterBackground");
        }
        Native_applicationDidEnterBackground();
        if (this.mGLView.mbDrawingFrames) {
            Object waitObj = new Object();
            synchronized (waitObj) {
                this.mGLView.mbNotifyOnDrawEventObject = waitObj;
                try {
                    waitObj.wait();
                } catch (InterruptedException ex) {
                    ex.printStackTrace();
                }
            }
        }
        if (DEBUG) {
            Log.i("Game", "onActivityPause - synchron wait obj over!!!!");
        }
        TryLoseFocus();
        this.mGLView.mbDrawingFrames = false;
        if (SexyAppFrameworkActivity.IsEnablePNS()) {
            PopCapPushNotificationService.Instance().SetUserLastOpt(Info_SysGetPackageName());
        }
    }

    public void onActivityStop() {
        if (!this.mGLView.HasDrawnFirstFrame()) {
            this.mActivity.finish();
            Process.killProcess(Process.myPid());
        } else {
            if (DEBUG) {
                Log.i("Game", "onActivityStop - TryLoseFocus");
            }
            TryLoseFocus();
        }
    }

    public void onActivityDestroy() {
        if (DEBUG) {
            Log.i("Game", "onActivityDestroy - Native_applicationWillTerminate");
        }
        Native_applicationWillTerminate();
        this.mlWakeLock = null;
        this.mHttpProxy.Shutdown();
        this.mGLView = null;
        this.mHttpProxy = null;
        this.mUIEventManager = null;
        if (SexyAppFrameworkActivity.IsEnablePNS()) {
            PopCapPushNotificationService.Instance().SetUserLastOpt(Info_SysGetPackageName());
        }
    }

    public void onSaveInstanceState(Bundle outState) {
        if (DEBUG) {
            Log.i("Game", "onSaveInstanceState - Do nothing for Native");
        }
    }

    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (DEBUG) {
            Log.i("Game", "onActivityResult - Do nothing for Native");
        }
    }

    public void HandleOnConfigurationChanged(Configuration newConfig) {
        int newOrientation = Device_GetCurrentUIOrientation();
        if (this.mCurrentOrientation != newOrientation) {
            Native_onOrientationChanged(this.mCurrentOrientation, newOrientation);
            this.mCurrentOrientation = newOrientation;
        }
    }

    public String Util_GetUUIDString() {
        String i_str = UUID.randomUUID().toString();
        return i_str;
    }

    public long Util_GetElapsedRealtime() {
        long elapse = SystemClock.elapsedRealtime() / 1000;
        return elapse;
    }

    public void Util_StartPNS(int version) {
        if (SexyAppFrameworkActivity.IsEnablePNS()) {
            PopCapPushNotificationService.Instance().SetOwnActivity(this.mActivity);
            PopCapPushNotificationService.Instance().StartService(version, Info_SysGetPackageName());
        }
    }

    public String Util_GetPackageName() {
        return this.mActivity.getPackageName();
    }

    public void Util_CallNativeCrashed(String errorMsg) {
        this.mActivity.handleNativeCrash(errorMsg);
    }

    public void Util_OpenSystemSetting() {
        this.mActivity.startActivity(new Intent("android.settings.SETTINGS"));
    }

    public void onWindowFocusChanged(boolean hasFocus) {
        if (hasFocus) {
            this.mbGotFocusEvent = true;
            if (DEBUG) {
                Log.i("Game", "onWindowFocusChanged - TryGainFocus");
            }
            TryGainFocus();
            return;
        }
        this.mbGotFocusEvent = false;
        if (DEBUG) {
            Log.i("Game", "onWindowFocusChanged - TryLoseFocus");
        }
        TryLoseFocus();
    }

    private void TryGainFocus() {
        if (!this.mbAppIsFocusedState) {
            if (this.mbGotFocusEvent || this.mbGotResumedEvent) {
                this.mGLView.SetFocusState(true);
                this.mUIEventManager.HandleGotFocus();
                this.mbAppIsFocusedState = true;
            }
        }
    }

    private void TryLoseFocus() {
        if (this.mbAppIsFocusedState) {
            if (!this.mbGotFocusEvent || !this.mbGotResumedEvent) {
                this.mbAppIsFocusedState = false;
                this.mGLView.SetFocusState(false);
                this.mUIEventManager.HandleLostFocus();
            }
        }
    }

    public void setStartUrl(String $startUrl) {
        if (DEBUG) {
            Log.i("Game", "setStartUrl - Native_setStartUrl");
        }
        Native_setStartUrl($startUrl);
    }

    public void setEditText(String strText) {
        if (DEBUG) {
            Log.i("Game", "setEditText - Native_setEditText");
        }
        Native_setEditText(strText);
    }

    public String getEditText() {
        if (DEBUG) {
            Log.i("Game", "getEditText - Native_getEditText");
        }
        return Native_getEditText();
    }

    public boolean Config_ConfigKeyExists(String InKeyName) {
        SharedPreferences prefs = this.mActivity.getPreferences(0);
        return prefs.contains(InKeyName);
    }

    public void Config_ConfigEraseKey(String InKeyName) {
        SharedPreferences.Editor prefsEditor = this.mActivity.getPreferences(0).edit();
        prefsEditor.remove(InKeyName).commit();
    }

    private String Config_ConfigReadString(String InKeyName) {
        SharedPreferences prefs = this.mActivity.getPreferences(0);
        try {
            String result = prefs.getString(InKeyName, null);
            return result;
        } catch (ClassCastException e) {
            return null;
        }
    }

    private String Config_ConfigReadStringEx(String InKeyName) {
        SharedPreferences prefs = this.mActivity.getSharedPreferences("com.popcap.SexyApp.SexyAppActivity", 0);
        try {
            String result = prefs.getString(InKeyName, null);
            return result;
        } catch (ClassCastException e) {
            return null;
        }
    }

    private int Config_ConfigReadInteger(String InKeyName) {
        SharedPreferences prefs = this.mActivity.getPreferences(0);
        try {
            int result = prefs.getInt(InKeyName, 0);
            return result;
        } catch (ClassCastException e) {
            return 0;
        }
    }

    private boolean Config_ConfigReadBoolean(String InKeyName) {
        SharedPreferences prefs = this.mActivity.getPreferences(0);
        try {
            boolean result = prefs.getBoolean(InKeyName, false);
            return result;
        } catch (ClassCastException e) {
            return false;
        }
    }

    private boolean Config_ConfigWriteString(String InKeyName, String InValue) {
        SharedPreferences.Editor prefsEditor = this.mActivity.getPreferences(0).edit();
        return prefsEditor.putString(InKeyName, InValue).commit();
    }

    private boolean Config_ConfigWriteInteger(String InKeyName, int InValue) {
        SharedPreferences.Editor prefsEditor = this.mActivity.getPreferences(0).edit();
        return prefsEditor.putInt(InKeyName, InValue).commit();
    }

    private boolean Config_ConfigWriteBoolean(String InKeyName, boolean InValue) {
        SharedPreferences.Editor prefsEditor = this.mActivity.getPreferences(0).edit();
        return prefsEditor.putBoolean(InKeyName, InValue).commit();
    }

    private boolean UI_ProcessEvents(ByteBuffer OutData) {
        return this.mUIEventManager.ProcessEvents(OutData);
    }

    private boolean UI_ProcessTouchEvents(ByteBuffer OutData) {
        return true;
    }

    private boolean UI_ProcessGesturePinchEvents(ByteBuffer OutData) {
        return true;
    }

    private boolean UI_ProcessKeyEvents(ByteBuffer OutData) {
        return true;
    }

    private void UI_DidRecieveFocus() {
    }

    private int UI_Dip2Pixels(int dip) {
        return (int) (this.mGLView.getResources().getDisplayMetrics().density * dip);
    }

    private void UI_ShowAlertDialog(final String i_title, final String i_msg, final String i_ok, final boolean i_exitApp) {
        this.mActivity.runOnUiThread(new Runnable() { // from class: com.popcap.SexyAppFramework.AndroidGameApp.1
            @Override // java.lang.Runnable
            public void run() {
                new AlertDialog.Builder(AndroidGameApp.this.mActivity).setTitle(i_title).setMessage(i_msg).setPositiveButton(i_ok, new DialogInterface.OnClickListener() { // from class: com.popcap.SexyAppFramework.AndroidGameApp.1.1
                    @Override // android.content.DialogInterface.OnClickListener
                    public void onClick(DialogInterface i_dialog, int i_which) {
                        if (i_exitApp) {
                            AndroidGameApp.this.Device_ExitApp();
                        }
                        i_dialog.cancel();
                    }
                }).show();
            }
        });
    }

    private void UI_StartShowProgressbar() {
        Log.v("ZXCpro", "AndroidGameApp.UI_StartShowProgressbar()!");
        AndroidSplashScreen.mStartShowProgressBarFlag = true;
        AndroidSplashScreen.mIsFirstInit = true;
    }

    private void UI_FinishShowProgressBar() {
        Log.v("ZXCpro", "AndroidGameApp.UI_FinishShowProgressBar()!");
        AndroidSplashScreen.mFinishShowProgressBarFlag = true;
    }

    private void UI_ShowExitGame() {
        Log.v("ZXCpro", "AndroidGameApp.UI_ShowExitGame()!");
        this.mActivity.ShowExitGame();
    }

    private String Info_SysGetProductVersion() {
        PackageInfo pInfo;
        int version = -1;
        Context ctxt = this.mActivity.getApplicationContext();
        try {
            pInfo = ctxt.getPackageManager().getPackageInfo(ctxt.getPackageName(), 0);
        } catch (PackageManager.NameNotFoundException e) {
            pInfo = null;
        }
        if (pInfo != null) {
            version = pInfo.versionCode;
        }
        return Integer.toString(version);
    }

    public String Info_SysGetProductVersionString() {
        String aProductVersion = null;
        Context ctxt = this.mActivity.getApplicationContext();
        PackageInfo pInfo = null;
        try {
            pInfo = ctxt.getPackageManager().getPackageInfo(ctxt.getPackageName(), 0);
        } catch (PackageManager.NameNotFoundException e) {
            aProductVersion = null;
        }
        if (pInfo != null) {
            String aProductVersion2 = pInfo.versionName;
            return aProductVersion2;
        }
        return aProductVersion;
    }

    private String Info_SysGetPackageName() {
        Context ctxt = this.mActivity.getApplicationContext();
        return ctxt.getPackageName();
    }

    private String Info_SysGetUserCurrencySymbol() {
        Currency aCurrency = Currency.getInstance(Locale.getDefault());
        String aUserCurrencySymbol = aCurrency.getSymbol(Locale.getDefault());
        return aUserCurrencySymbol;
    }

    private boolean Device_IsSupportedUIOrientation(int UIOrientation) {
        return UIOrientation == 4 || UIOrientation == 3 || UIOrientation == 1 || UIOrientation == 2;
    }

    private void Device_Vibrate(long milliseconds) {
        Vibrator vibrator = (Vibrator) this.mActivity.getSystemService("vibrator");
        if (vibrator != null) {
            vibrator.vibrate(milliseconds);
        }
    }

    private void Device_VibrateWithPattern(long[] pattern, int isRepeat) {
        Vibrator vibrator = (Vibrator) this.mActivity.getSystemService("vibrator");
        if (vibrator != null) {
            vibrator.vibrate(pattern, isRepeat);
        }
    }

    private void Device_CancelVibrate() {
        Vibrator vibrator = (Vibrator) this.mActivity.getSystemService("vibrator");
        if (vibrator != null) {
            vibrator.cancel();
        }
    }

    private boolean Device_IsKeyboardShowing(boolean bIncludeHardKeyboard) {
        InputMethodManager imm = (InputMethodManager) this.mActivity.getSystemService("input_method");
        boolean is_accepting_text = imm.isAcceptingText();
        return is_accepting_text;
    }

    private boolean Device_ShowKeyboard() {
        this.mActivity.openIMEKeyboard();
        return true;
    }

    private boolean Device_HideKeyboard() {
        this.mActivity.closeIMEKeyboard();
        return true;
    }

    private String Device_GetCachesDir() {
        Context ctxt = this.mActivity.getApplicationContext();
        return ctxt.getCacheDir().getAbsolutePath();
    }

    private void Device_ExitToHome() {
        Intent aGoToHomeIntent = new Intent("android.intent.action.MAIN");
        aGoToHomeIntent.addCategory("android.intent.category.HOME");
        aGoToHomeIntent.setFlags(268435456);
        this.mActivity.startActivity(aGoToHomeIntent);
    }

    /* JADX INFO: Access modifiers changed from: private */
    private void Device_ExitApp() {
        this.mActivity.finish();
        Process.killProcess(Process.myPid());
        System.exit(0);
    }

    private String Resources_GetResourceFolder() {
        File privateFilesDir = this.mActivity.getFilesDir();
        return privateFilesDir.toString();
    }

    public static String GetUserDataFolder() {
        Context ctxt = activity.getApplicationContext();
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

    private String Resources_GetCacheDataFolder() {
        return Resources_GetUserDataFolder();
    }

    private String Resources_GetAppSupportDataFolder() {
        return Resources_GetUserDataFolder();
    }

    private String Resources_GetExternalStorageDirectory() {
        try {
            if (!Environment.getExternalStorageState().equals("mounted")) {
                return null;
            }
            String sdCardRoot = DreamRootPath.getRootFile().getAbsolutePath();
            return sdCardRoot;
        } catch (Exception e) {
            return null;
        }
    }

    private String Resources_GetExternalFilesDirectory() {
        Context ctxt = this.mActivity.getApplicationContext();
        File dirFile = ctxt.getExternalFilesDir(null);
        if (dirFile == null) {
            return null;
        }
        String dirName = dirFile.getAbsolutePath();
        return dirName;
    }

    public static String GetExternalFilesDirectory() {
        Context ctxt = activity.getApplicationContext();
        File dirFile = ctxt.getExternalFilesDir(null);
        if (dirFile == null) {
            return null;
        }
        String dirName = dirFile.getAbsolutePath();
        return dirName;
    }

    private String Resources_GetAssetFileInfo(String InFilename, long[] outFileInfo) {
        AssetManager assetMgr = this.mActivity.getAssets();
        if (assetMgr != null && InFilename.length() > 0) {
            String actualFilename = AndroidAssetUtils.GetAssetNameFromFileName(InFilename);
            try {
                AssetFileDescriptor afd = assetMgr.openFd(actualFilename);
                if (afd != null) {
                    outFileInfo[0] = afd.getStartOffset();
                    outFileInfo[1] = afd.getLength();
                    afd.close();
                    return this.mActivity.getPackageResourcePath();
                }
            } catch (IOException ex) {
                Log.e("GetAssetFileInfo", ex.toString());
            }
        }
        return null;
    }

    private boolean Resources_InstallApk(String i_filePath) {
        File apkFile = new File(i_filePath);
        if (!apkFile.exists()) {
            return false;
        }
        Intent i = new Intent("android.intent.action.VIEW");
        i.addFlags(268435456);
        i.setDataAndType(Uri.parse("file://" + apkFile.toString()), "application/vnd.android.package-archive");
        this.mActivity.startActivity(i);
        return true;
    }

    private long Resources_GetAssetFileSize(String InFilename) {
        AssetManager assetMgr = this.mActivity.getAssets();
        if (assetMgr != null && InFilename.length() > 0) {
            String actualFilename = AndroidAssetUtils.GetAssetNameFromFileName(InFilename);
            try {
                AssetFileDescriptor afd = assetMgr.openFd(actualFilename);
                return afd.getLength();
            } catch (IOException ex) {
                Log.e("GetAssetFileSize", ex.toString());
            }
        }
        return -1L;
    }

    private long Resources_GetFileSystemBlockCount(String InFilename) {
        try {
            StatFs stat = new StatFs(InFilename);
            long n = stat.getBlockCount();
            return n;
        } catch (Exception ex) {
            Log.e("GetFileSystemBlockCount", ex.toString());
            return -1L;
        }
    }

    private long Resources_GetFileSystemBlocksFree(String InFilename) {
        try {
            StatFs stat = new StatFs(InFilename);
            long n = stat.getAvailableBlocks();
            return n;
        } catch (Exception ex) {
            Log.e("GetFileSystemBlocksFree", ex.toString());
            return -1L;
        }
    }

    private long Resources_GetFileSystemBlockSize(String InFilename) {
        try {
            StatFs stat = new StatFs(InFilename);
            long n = stat.getBlockSize();
            return n;
        } catch (Exception ex) {
            Log.e("GetFileSystemBlockSize", ex.toString());
            return -1L;
        }
    }

    private String Diag_GetPrimaryMACAddress() {
        WifiInfo info;
        Context ctxt = this.mActivity.getApplicationContext();
        WifiManager wifiMgr = (WifiManager) ctxt.getSystemService("wifi");
        return (wifiMgr == null || (info = wifiMgr.getConnectionInfo()) == null) ? "00:00:00:00:00:00" : info.getMacAddress();
    }

    private String Diag_GetDeviceID() {
        String strDeviceID = Settings.Secure.getString(this.mActivity.getApplicationContext().getContentResolver(), "android_id");
        if (strDeviceID == "") {
            return "UNKNOWN/EMULATOR";
        }
        return strDeviceID;
    }

    public String Diag_GetOSVersion() {
        return Build.VERSION.RELEASE;
    }

    public String Diag_GetHardwareModel() {
        String manufacturer = Build.MANUFACTURER;
        String model = Build.MODEL;
        return model.startsWith(manufacturer) ? model : manufacturer + " " + model;
    }

    private void DEBUG_PauseInJava(String FileName, int LineNo) {
        Log.e("PauseInJava", String.format("File: \"%s\"(%d)", FileName, Integer.valueOf(LineNo)));
    }

    private boolean Web_SysOpenURL(String theURL) {
        Intent i = new Intent("android.intent.action.VIEW", Uri.parse(theURL));
        this.mActivity.startActivity(i);
        return true;
    }

    public long Diag_GetUsedMemory() {
        return Debug.getNativeHeapAllocatedSize();
    }

    public long Diag_GetAvailMemory() {
        ActivityManager am = (ActivityManager) this.mActivity.getSystemService("activity");
        ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
        am.getMemoryInfo(mi);
        return mi.availMem;
    }

    private class GeminiMethodNotFoundException extends Exception {
        public GeminiMethodNotFoundException(String info) {
            super(info);
        }
    }

    public int Diag_GetMobileCardType() {
        String i_imsi1;
        String i_imsi2;
        try {
            i_imsi1 = DreamRootPath.getIMSIBySlot(this, this.mActivity, 0);
        } catch (GeminiMethodNotFoundException e) {
            i_imsi1 = "460001234567890";
        }
        try {
            i_imsi2 = DreamRootPath.getIMSIBySlot(this, this.mActivity, 1);
        } catch (GeminiMethodNotFoundException e2) {
            i_imsi2 = null;
        }
        int i_type1 = getTypeByIMSI(i_imsi1);
        int i_type2 = getTypeByIMSI(i_imsi2);
        int i_type = i_type1 | i_type2;
        return i_type;
    }

    public int Diag_GetSimProvince() {
        TelephonyManager manager = (TelephonyManager) this.mActivity.getSystemService("phone");
        String simSN = DreamRootPath.getSimSerialNumber(manager);
        if (simSN == null) {
            return 0;
        }
        Log.d("SimInfo", "sim number: " + simSN + " length: " + simSN.length());
        int provinceRst = 0;
        switch (simSN.length()) {
            case 12:
                provinceRst = Integer.parseInt(simSN.substring(8, 10));
                break;
            case 16:
                provinceRst = Integer.parseInt(simSN.substring(0, 2));
                break;
            case 20:
                provinceRst = Integer.parseInt(simSN.substring(8, 10));
                break;
        }
        Log.d("", "provinceRst: " + provinceRst);
        return provinceRst;
    }

    private String getIMSIBySlot(Context context, int slotID) throws GeminiMethodNotFoundException {
        TelephonyManager telephony = (TelephonyManager) context.getSystemService("phone");
        try {
            Class<?> telephonyClass = Class.forName(telephony.getClass().getName());
            Class<?>[] parameter = {Integer.TYPE};
            Method getSimID = telephonyClass.getMethod("getSubscriberIdGemini", parameter);
            Object[] obParameter = {Integer.valueOf(slotID)};
            Object ob_phone = getSimID.invoke(telephony, obParameter);
            if (ob_phone == null) {
                return null;
            }
            String imsi = ob_phone.toString();
            return imsi;
        } catch (Exception e) {
            e.printStackTrace();
            throw new GeminiMethodNotFoundException("getSubscriberIdGemini");
        }
    }

    public String Diag_GetNetworkType() {
        NetworkInfo info;
        ConnectivityManager conMan = (ConnectivityManager) this.mActivity.getSystemService("connectivity");
        if (conMan.getActiveNetworkInfo() == null || (info = conMan.getActiveNetworkInfo()) == null || info.getType() != 0) {
            return "UNKNOWN";
        }
        if (info.getSubtype() == 1 || info.getSubtype() == 4 || info.getSubtype() == 2) {
            return "2G";
        }
        if (info.getSubtype() != 5 && info.getSubtype() != 6 && info.getSubtype() != 12 && info.getSubtype() != 8 && info.getSubtype() != 3) {
            return "UNKNOWN";
        }
        return "3G";
    }

    public String Diag_GetDeviceIMSI() {
        return "460001234567890";
    }

    public String Diag_GetDeviceIMEI() {
        TelephonyManager tel = (TelephonyManager) this.mActivity.getSystemService("phone");
        return DreamRootPath.getDeviceId(tel);
    }

    public String Diag_GetDeviceMODEL() {
        String model = Build.MODEL;
        return model;
    }

    public String Diag_GetDeviceBRAND() {
        String brand = Build.BRAND;
        return brand;
    }
}
