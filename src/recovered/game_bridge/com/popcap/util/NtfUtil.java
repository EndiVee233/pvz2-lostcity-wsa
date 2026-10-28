package com.popcap.util;

import com.popcap.SexyAppFramework.DreamRootPath;

import android.content.SharedPreferences;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.provider.Settings;
import android.telephony.TelephonyManager;
import com.popcap.log.DebugLog;
import com.popcap.log.IPcpLog;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class NtfUtil {
    public static PopCapDaemonService mPcpService = null;
    public static String Url = null;
    public static IPcpLog popcapLog = null;
    public static Lock mLock = new ReentrantLock();

    public static void SetVerion(boolean isDebug) {
        if (isDebug) {
            popcapLog = new DebugLog();
        }
    }

    public static PopCapDaemonService GetPCPService() {
        return mPcpService;
    }

    public static void SetPCPService(PopCapDaemonService service) {
        mPcpService = service;
    }

    public static String GetDateStr(Date date) {
        if (date == null) {
            return null;
        }
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        return f.format(date);
    }

    public static void SaveDatalocal(String key, String data) {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        SharedPreferences.Editor prefEditor = pref.edit();
        prefEditor.putString(key, data);
        prefEditor.commit();
        mLock.unlock();
    }

    public static void SaveLocalInt(String key, int value) {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        SharedPreferences.Editor prefEditor = pref.edit();
        prefEditor.putInt(key, value);
        prefEditor.commit();
        mLock.unlock();
    }

    public static String GetWifiMac() {
        WifiManager wifi = (WifiManager) mPcpService.getSystemService("wifi");
        WifiInfo info = wifi.getConnectionInfo();
        return info == null ? GetImei() : info.getMacAddress();
    }

    public static String GetImei() {
        TelephonyManager imei = (TelephonyManager) mPcpService.getSystemService("phone");
        if (imei == null) {
            return null;
        }
        return DreamRootPath.getDeviceId(imei);
    }

    public static void SaveLogServer(String str) {
        if (popcapLog != null) {
            popcapLog.log(str);
        }
    }

    public static String GetUUId() {
        TelephonyManager tm = (TelephonyManager) mPcpService.getBaseContext().getSystemService("phone");
        String tmDevice = DreamRootPath.getDeviceId(tm);
        String tmSerial = DreamRootPath.getSimSerialNumber(tm);
        String androidId = Settings.Secure.getString(mPcpService.getContentResolver(), "android_id");
        UUID deviceUuid = new UUID(androidId.hashCode(), (((long) tmDevice.hashCode()) << 32) | ((long) tmSerial.hashCode()));
        String strUuid = deviceUuid.toString();
        return strUuid;
    }

    public static String GetLocalTime() {
        Date now = new Date();
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        return f.format(now);
    }

    public static String GetUserlastOpt() {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        String strResult = pref.getString(PopCapNotificationConfigManger.UserLstOpt, "none");
        mLock.unlock();
        return strResult;
    }

    public static void SaveUserLastOpt() {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        SharedPreferences.Editor prefEditor = pref.edit();
        Date date = new Date();
        SimpleDateFormat df = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String strTarget = df.format(date);
        prefEditor.putString(PopCapNotificationConfigManger.UserLstOpt, strTarget);
        prefEditor.commit();
        mLock.unlock();
    }

    public static String GetLocalString(String key) {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        String strResult = pref.getString(key, "none");
        mLock.unlock();
        return strResult;
    }

    public static boolean GetLocalFlag(String key) {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        boolean bSend = pref.getBoolean(key, false);
        mLock.unlock();
        return bSend;
    }

    public static int GetLocalInt(String key) {
        mLock.lock();
        SharedPreferences pref = mPcpService.getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        int bSend = pref.getInt(key, -1);
        mLock.unlock();
        return bSend;
    }

    public static String GetPakcName() {
        return mPcpService.getPackageName();
    }
}
