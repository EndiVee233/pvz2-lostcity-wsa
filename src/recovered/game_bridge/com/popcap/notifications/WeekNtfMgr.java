package com.popcap.notifications;

import com.popcap.events.IEventTick;
import com.popcap.util.NtfUtil;
import com.popcap.util.PopCapNotificationAbstract;
import com.popcap.util.PopCapNotificationConfigManger;
import com.popcap.util.PopCapNotificationForPlay;
import com.popcap.util.PopCapNotificationThread;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class WeekNtfMgr extends NtfMgr implements IEventTick {
    public static WeekNtfMgr mWeekNtfMgr = null;
    private ArrayList<PopCapNotificationAbstract> _notificationList;
    private Date mWeekDate = null;
    private long maxWeeklyIndex = 0;

    public static WeekNtfMgr Instance() {
        if (mWeekNtfMgr == null) {
            mWeekNtfMgr = new WeekNtfMgr();
        }
        return mWeekNtfMgr;
    }

    public WeekNtfMgr() {
        this._notificationList = null;
        mWeekNtfMgr = this;
        this._notificationList = new ArrayList<>();
    }

    @Override // com.popcap.events.IEventTick
    public void Tick() {
        OperByDate();
    }

    @Override // com.popcap.notifications.NtfMgr
    public void FillData(String data) {
    }

    public void FillData(JSONArray jsArray) {
        ClearNotificationList();
        for (int i = 0; i < jsArray.length(); i++) {
            try {
                JSONObject ctnObj = (JSONObject) jsArray.get(i);
                PopCapNotificationForPlay notificationForPlay = new PopCapNotificationForPlay(1, ctnObj.getString("i"), ctnObj.getString("c"), -1L, 3);
                String ss = ctnObj.getString("s");
                notificationForPlay.SetSkuId(Integer.parseInt(ss));
                String ss2 = ctnObj.getString("t");
                notificationForPlay.setNtType(Integer.parseInt(ss2));
                notificationForPlay.setUrl(ctnObj.getString("u"));
                String ss3 = ctnObj.getString("p");
                int index = Integer.parseInt(ss3);
                if (index > this.maxWeeklyIndex) {
                    NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.MaxWeekIndex, Long.toString(this.maxWeeklyIndex));
                    this.maxWeeklyIndex = index;
                }
                notificationForPlay.setId(index);
                this._notificationList.add(notificationForPlay);
            } catch (JSONException e) {
                e.printStackTrace();
                return;
            }
        }
        sendNotificationList();
    }

    private void sendNotificationList() {
        for (PopCapNotificationAbstract n : this._notificationList) {
            PopCapNotificationThread.Instance(NtfUtil.GetPCPService()).PlayNotification(n);
        }
    }

    public long GetMaxWeeklyIndex() {
        OperByDate();
        return this.maxWeeklyIndex;
    }

    private void OperByDate() {
        Date now = new Date();
        Calendar c = Calendar.getInstance();
        c.setTime(now);
        int nowDay = c.get(5);
        c.setTime(this.mWeekDate);
        int lastDay = c.get(5);
        if (nowDay != lastDay) {
            this.maxWeeklyIndex = 0L;
            String strDate = NtfUtil.GetDateStr(now);
            this.mWeekDate = now;
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.WeeklyDate, strDate);
            NtfUtil.SaveLogServer(String.valueOf(NtfUtil.GetWifiMac()) + " today is pass");
        }
    }

    private void ClearNotificationList() {
        this._notificationList.clear();
    }

    public void SetWeekDate(String data) {
        if (data.equals("none")) {
            this.mWeekDate = new Date();
            String strDate = NtfUtil.GetDateStr(this.mWeekDate);
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.WeeklyDate, strDate);
        } else {
            SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            try {
                this.mWeekDate = myFormatter.parse(data);
            } catch (Exception e) {
                e.printStackTrace();
                this.mWeekDate = new Date();
            }
        }
    }

    public void SetMaxWkIndex(String data) {
        if (data.equals("none")) {
            this.maxWeeklyIndex = 0L;
            return;
        }
        try {
            this.maxWeeklyIndex = Integer.parseInt(data);
        } catch (NumberFormatException e) {
            this.maxWeeklyIndex = 0L;
            e.printStackTrace();
        }
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateUserOpt() {
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateSkuUserOpt(String pckName) {
    }

    @Override // com.popcap.events.IEventTick
    public void OnUserStartGameEvent(String pckName) {
    }
}
