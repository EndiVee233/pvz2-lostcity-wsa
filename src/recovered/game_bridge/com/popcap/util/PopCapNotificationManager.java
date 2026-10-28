package com.popcap.util;

import android.util.Log;
import com.popcap.events.EventFactory;
import com.popcap.events.GlobalNtfEventFactory;
import com.popcap.events.RewardEvent.SendUserRewardEventsFactory;
import com.popcap.events.SkuListEventFactory;
import com.popcap.events.WeekNtfEventFactory;
import com.popcap.network.PCPNetWork;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapNotificationManager {
    private boolean isInitialized = false;
    private PopCapNotificationThread notifictionThread;
    private static PopCapNotificationManager _thisInstance = null;
    private static int pvz2IconId = 0;
    private static int bejeweledblitzIconId = 0;
    private static String packName = "";

    private PopCapNotificationManager(PopCapDaemonService daemonService) {
        this.notifictionThread = null;
        this.notifictionThread = PopCapNotificationThread.Instance(daemonService);
        initNotificationList();
    }

    public void UpdateSkedualTime(String pckName) {
        if (this.notifictionThread != null) {
            this.notifictionThread.UpdateSkedualTime(pckName);
        }
    }

    public void OnUserStartGameEvent(String pckName) {
        if (this.notifictionThread != null) {
            this.notifictionThread.onUserStartGameEvent(pckName);
        }
    }

    private void startNotficationThread() {
        if (this.isInitialized && this.notifictionThread != null && !this.notifictionThread.isAlive()) {
            this.notifictionThread.start();
        }
    }

    public void SetDebugVersionConfig() {
        PCPNetWork.SetURl(PopCapNotificationConfigManger.Debug_URL);
    }

    public void SetReleaseVersionConfig() {
        PCPNetWork.SetURl(PopCapNotificationConfigManger.Release_URL);
    }

    public static PopCapNotificationManager getInstance(PopCapDaemonService daemonService) {
        if (daemonService == null) {
            return null;
        }
        if (_thisInstance == null) {
            _thisInstance = new PopCapNotificationManager(daemonService);
        } else {
            Log.d("666666666666666  ", "  have the instance not new ");
        }
        if (!_thisInstance.isInitialized) {
            _thisInstance = null;
        }
        return _thisInstance;
    }

    public void StartPopcapService() {
        if (_thisInstance != null) {
            _thisInstance.startNotficationThread();
        }
    }

    private void initNotificationList() {
        this.isInitialized = true;
        EventFactory sEvent = new SkuListEventFactory();
        this.notifictionThread.RegistEvent(sEvent.CreteEvent());
        EventFactory wEvent = new WeekNtfEventFactory();
        this.notifictionThread.RegistEvent(wEvent.CreteEvent());
        EventFactory gEvent = new GlobalNtfEventFactory();
        this.notifictionThread.RegistEvent(gEvent.CreteEvent());
        EventFactory rewEvent = new SendUserRewardEventsFactory();
        this.notifictionThread.RegistEvent(rewEvent.CreteEvent());
    }

    public void stopNotifications() {
        this.notifictionThread.stopThread();
        _thisInstance = null;
    }

    public static String getStarAppPackName() {
        return packName;
    }

    public static void setStartAppPackName(String i_packName) {
        packName = i_packName;
    }

    public static int getPvz2IconId() {
        return pvz2IconId;
    }

    public static void setPvz2IconId(int i_pvz2IconId) {
        if (pvz2IconId == 0) {
            pvz2IconId = i_pvz2IconId;
        }
    }

    public static int getBejeweledblitzIconId() {
        return bejeweledblitzIconId;
    }

    public static void setBejeweledblitzIconId(int i_bejeweledblitzIconId) {
        if (i_bejeweledblitzIconId == 0) {
            bejeweledblitzIconId = i_bejeweledblitzIconId;
        }
    }

    public static int GetPackageIcon(String packName2) {
        if (!packName2.contains("pvz2")) {
            return getBejeweledblitzIconId();
        }
        Log.e("DEBUG====", "GET pakckgetName = " + packName2 + " icon id = " + pvz2IconId);
        return getPvz2IconId();
    }
}
