package com.popcap.util;

import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.IBinder;
import android.os.RemoteException;
import android.util.Log;
import java.util.Date;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapDaemonService extends Service {
    public PopCapNotificationConfigManger popcapNotificationConfig;
    public PopCapNotificationManager popcapNotificationManager;
    public NotificationManager systemNotificationManager;
    public String targetClassName;
    public String targetPackageName;
    private int s_version = 2;
    private final IRemoteService.Stub mBinder = new IRemoteService.Stub() { // from class: com.popcap.util.PopCapDaemonService.1
        @Override // com.popcap.util.IRemoteService
        public boolean sendNotification(int nId, int nAction) throws RemoteException {
            return PopCapDaemonService.this.sendNotificationImpl(nId, nAction);
        }

        @Override // com.popcap.util.IRemoteService
        public boolean setCoinReamins(int nId, int coinRemains) throws RemoteException {
            return PopCapDaemonService.this.setCoinRemainsImpl(nId, coinRemains);
        }

        @Override // com.popcap.util.IRemoteService
        public boolean setCoinSettings(int nId, int coinMax, int coinIncraseRatePerMinute) throws RemoteException {
            return PopCapDaemonService.this.setCoinSettingsImpl(nId, coinMax, coinIncraseRatePerMinute);
        }

        @Override // com.popcap.util.IRemoteService
        public float GetServiceVerion() throws RemoteException {
            return PopCapDaemonService.this.GetServiceVesion();
        }

        @Override // com.popcap.util.IRemoteService
        public void StopService() throws RemoteException {
            PopCapDaemonService.this.stopSelf();
        }

        @Override // com.popcap.util.IRemoteService
        public void SetUserLastOpt() throws RemoteException {
            if (PopCapDaemonService.this.popcapNotificationManager != null) {
                PopCapDaemonService.this.popcapNotificationManager.UpdateSkedualTime(null);
            }
        }

        @Override // com.popcap.util.IRemoteService
        public void SetSkuUserLastOpt(String pckName) throws RemoteException {
            NtfUtil.SaveUserLastOpt();
            Integer skuId = PCPLocalGameMgr.Instance().GetGameId(pckName);
            if (skuId != null) {
                UserOpt.Instance().UpateUserOpt(skuId.intValue());
            }
            if (PopCapDaemonService.this.popcapNotificationManager != null) {
                PopCapDaemonService.this.popcapNotificationManager.UpdateSkedualTime(pckName);
            }
        }
    };

    public int GetServiceVesion() {
        return this.s_version;
    }

    public boolean sendNotificationImpl(int nId, int nAction) {
        return this.popcapNotificationManager != null;
    }

    public boolean setCoinRemainsImpl(int nId, int coinRemains) {
        return this.popcapNotificationManager != null;
    }

    public boolean setCoinSettingsImpl(int nId, int coinMax, int coinIncraseRatePerMinute) {
        return this.popcapNotificationManager != null;
    }

    @Override // android.app.Service
    public void onCreate() {
        super.onCreate();
        if (this.popcapNotificationManager != null) {
            NtfUtil.SaveLogServer("service onCreate");
        }
    }

    @Override // android.app.Service
    public void onStart(Intent intent, int startId) {
        NtfUtil.SaveLogServer("service onStart");
        super.onStart(intent, startId);
        if (this.popcapNotificationManager == null) {
        }
    }

    @Override // android.app.Service
    public IBinder onBind(Intent intent) {
        return this.mBinder;
    }

    @Override // android.app.Service
    public boolean onUnbind(Intent intent) {
        super.onUnbind(intent);
        return true;
    }

    @Override // android.app.Service
    public void onRebind(Intent intent) {
    }

    @Override // android.app.Service
    public void onDestroy() {
        super.onDestroy();
        if (this.popcapNotificationManager != null) {
            stopNotifications();
        }
    }

    private boolean IsDebugVerion() {
        SharedPreferences pref = getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        String version = pref.getString("ver", "none");
        if (version.equals("none")) {
            return false;
        }
        if (version.equals(PopCapNotificationConfigManger.Debug)) {
            return true;
        }
        if (version.equals("release")) {
        }
        return false;
    }

    private void SaveVersion(String ver) {
        SharedPreferences pref = getSharedPreferences(PopCapNotificationConfigManger.configFileName, 0);
        SharedPreferences.Editor prefEditor = pref.edit();
        prefEditor.putString("ver", ver);
        prefEditor.commit();
    }

    @Override // android.app.Service
    public int onStartCommand(Intent intent, int flags, int startId) {
        NtfUtil.mPcpService = this;
        Bundle bundle = null;
        if (intent != null) {
            bundle = intent.getExtras();
        }
        if (bundle == null) {
            boolean bDebug = IsDebugVerion();
            NtfUtil.SetVerion(bDebug);
            this.popcapNotificationManager = PopCapNotificationManager.getInstance(this);
            if (bDebug) {
                this.popcapNotificationManager.SetDebugVersionConfig();
            } else {
                this.popcapNotificationManager.SetReleaseVersionConfig();
            }
        } else {
            this.popcapNotificationManager = PopCapNotificationManager.getInstance(this);
            int data = bundle.getInt("version");
            String pckName = bundle.getString("pck");
            if (pckName != null) {
                String key = PopCapNotificationConfigManger.LastStartTime + pckName;
                Date now = new Date();
                NtfUtil.SaveDatalocal(key, NtfUtil.GetDateStr(now));
            }
            this.popcapNotificationManager.OnUserStartGameEvent(pckName);
            boolean bDebug2 = data == 2;
            NtfUtil.SetVerion(bDebug2);
            if (bDebug2) {
                this.popcapNotificationManager.SetDebugVersionConfig();
                SaveVersion(PopCapNotificationConfigManger.Debug);
            } else if (data == 1) {
                this.popcapNotificationManager.SetReleaseVersionConfig();
                SaveVersion("release");
            } else {
                Log.e("+++ errror ", "what you pass value = " + data);
            }
        }
        this.popcapNotificationManager.StartPopcapService();
        return 1;
    }

    public void stopNotifications() {
        if (this.popcapNotificationManager != null) {
            this.popcapNotificationManager.stopNotifications();
        }
    }

    public void saveNotifications() {
    }
}
