package com.popcap.util;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.util.Log;
import com.popcap.events.IEventTick;
import java.util.ArrayList;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapNotificationThread extends Thread {
    public static PopCapNotificationThread m_sNotificationThread = null;
    private PopCapDaemonService _daemonService;
    private NotificationManager _systemNotificationManager;
    private boolean _isInitialized = false;
    private boolean _isInterrupted = false;
    private int _notificationIconResId = -1;
    private Notification _notification = null;
    private ArrayList<IEventTick> mEventArray = null;

    public void SetService(PopCapDaemonService service) {
        this._daemonService = service;
    }

    private PopCapNotificationThread(PopCapDaemonService service) {
        this._daemonService = null;
        this._daemonService = service;
        initNotificationComponents();
    }

    public static PopCapNotificationThread Instance(PopCapDaemonService service) {
        if (m_sNotificationThread == null) {
            m_sNotificationThread = new PopCapNotificationThread(service);
        }
        return m_sNotificationThread;
    }

    @Override // java.lang.Thread, java.lang.Runnable
    public void run() {
        if (this._isInitialized) {
            while (!this._isInterrupted) {
                for (IEventTick event : this.mEventArray) {
                    event.Tick();
                }
                ThreadSleep(120000);
            }
        }
    }

    public void UpdateSkedualTime(String pckName) {
        for (IEventTick event : this.mEventArray) {
            event.UpdateUserOpt();
            if (pckName != null) {
                event.UpdateSkuUserOpt(pckName);
            }
        }
    }

    public void onUserStartGameEvent(String pckName) {
        for (IEventTick event : this.mEventArray) {
            event.OnUserStartGameEvent(pckName);
        }
    }

    private void ThreadSleep(int ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
        }
    }

    public void stopThread() {
        this._isInterrupted = true;
    }

    public void RegistEvent(IEventTick event) {
        this.mEventArray.add(event);
    }

    private void initNotificationComponents() {
        this._systemNotificationManager = (NotificationManager) this._daemonService.getSystemService(PopCapConfigXmlElement.NOTIFICATION);
        String dstPackageName = this._daemonService.getPackageName();
        PackageManager packageMananger = this._daemonService.getPackageManager();
        ComponentName dstComponentName = packageMananger.getLaunchIntentForPackage(dstPackageName).getComponent();
        String dstPackageName2 = dstComponentName.getPackageName();
        PackageInfo packageInfo = null;
        try {
            packageInfo = packageMananger.getPackageInfo(dstPackageName2, 1);
        } catch (PackageManager.NameNotFoundException e) {
            Log.e("DEBUG", "ERROR: failed to get Packa geInfo");
            e.printStackTrace();
            this._isInitialized = false;
        }
        ApplicationInfo appInfo = packageInfo.applicationInfo;
        this._notificationIconResId = appInfo.icon;
        Intent intent = new Intent();
        intent.setComponent(dstComponentName);
        intent.addFlags(268435456);
        this._isInitialized = true;
        this._notification = new Notification();
        this.mEventArray = new ArrayList<>();
    }

    public int GetPackageIcon(String packName) {
        return this._notificationIconResId;
    }

    public void PlayNotification(PopCapNotificationAbstract notification) {
        String gamePackege = PCPLocalGameMgr.Instance().GetPackage(Integer.valueOf(notification.GetSkuId()));
        if (gamePackege == null) {
            int resid = this._notificationIconResId;
            return;
        }
        int resid2 = GetPackageIcon(gamePackege);
        this._notification = new Notification(resid2, notification.text, System.currentTimeMillis());
        this._notification.tickerText = notification.text;
        PendingIntent pendingIntent = NtfAction.Instance().GetUserOptAction(notification);
        this._notification.setLatestEventInfo(this._daemonService, notification.title, notification.text, pendingIntent);
        this._notification.flags = 16;
        this._systemNotificationManager.notify(notification.getId(), this._notification);
    }
}
