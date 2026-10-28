package com.popcap.util;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import android.os.RemoteException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapPushNotificationService {
    private static PopCapPushNotificationService m_Notification = null;
    private static String srvkey = "com.popcap.notice";
    private static String srvRwdKey = "rwdKey";
    private static String srvValue = "1";
    private Activity activity = null;
    private IRemoteService mIRemoteService = null;
    private ServiceConnection connection = new ServiceConnection() { // from class: com.popcap.util.PopCapPushNotificationService.1
        @Override // android.content.ServiceConnection
        public void onServiceDisconnected(ComponentName name) {
            access$0(PopCapPushNotificationService.this, null);
        }

        @Override // android.content.ServiceConnection
        public void onServiceConnected(ComponentName name, IBinder service) {
            access$0(PopCapPushNotificationService.this, IRemoteService.Stub.asInterface(service));
            if (access$1(PopCapPushNotificationService.this) != null) {
                try {
                    if (access$2(PopCapPushNotificationService.this) != null) {
                        access$1(PopCapPushNotificationService.this).SetSkuUserLastOpt(access$2(PopCapPushNotificationService.this));
                        access$3(PopCapPushNotificationService.this, null);
                    }
                } catch (RemoteException e) {
                    e.printStackTrace();
                }
            }
            if (access$4(PopCapPushNotificationService.this) != null) {
                access$4(PopCapPushNotificationService.this).unbindService(access$5(PopCapPushNotificationService.this));
                access$0(PopCapPushNotificationService.this, null);
            }
        }
    };
    private String userOptPackName = null;

    // Preserve the original compiler's bridge names and void setter signatures.
    static void access$0(PopCapPushNotificationService self, IRemoteService service) { self.mIRemoteService = service; }
    static IRemoteService access$1(PopCapPushNotificationService self) { return self.mIRemoteService; }
    static String access$2(PopCapPushNotificationService self) { return self.userOptPackName; }
    static void access$3(PopCapPushNotificationService self, String name) { self.userOptPackName = name; }
    static Activity access$4(PopCapPushNotificationService self) { return self.activity; }
    static ServiceConnection access$5(PopCapPushNotificationService self) { return self.connection; }

    public void SetOwnActivity(Activity m_activity) {
        this.activity = m_activity;
    }

    public int StartService(int version, String packName) {
        if (this.activity == null) {
            return 1;
        }
        if (version != 1 && version != 2) {
            return 2;
        }
        Intent intent = new Intent(GetServiceName());
        Bundle mBundle = new Bundle();
        mBundle.putInt("version", version);
        mBundle.putString("pck", packName);
        intent.putExtras(mBundle);
        this.activity.startService(intent);
        return 0;
    }

    public void SetUserLastOpt(String pckName) {
        if (this.activity != null) {
            Intent intent = new Intent(GetServiceName());
            this.userOptPackName = pckName;
            this.activity.bindService(intent, this.connection, 1);
        }
    }

    public int StartService(String packName) {
        if (this.activity == null) {
            return 1;
        }
        Intent intent = new Intent(GetServiceName());
        Bundle mBundle = new Bundle();
        intent.addFlags(1073741824);
        mBundle.putInt("version", 1);
        mBundle.putString("pck", packName);
        intent.putExtras(mBundle);
        this.activity.startService(intent);
        return 0;
    }

    public static PopCapPushNotificationService Instance() {
        if (m_Notification == null) {
            m_Notification = new PopCapPushNotificationService();
        }
        return m_Notification;
    }

    public static String getSrvRwdKey() {
        return srvRwdKey;
    }

    public static void setSrvRwdKey(String srvRwdKey2) {
        srvRwdKey = srvRwdKey2;
    }

    public static String getSrvkey() {
        return srvkey;
    }

    public static String getSrvValue() {
        return srvValue;
    }

    private String GetServiceName() {
        if (this.activity == null) {
            return "";
        }
        String packName = this.activity.getPackageName();
        return String.valueOf(packName) + "_DAEMON_SERVICE";
    }
}
