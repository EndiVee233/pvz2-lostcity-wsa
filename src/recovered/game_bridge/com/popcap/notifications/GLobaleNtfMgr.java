package com.popcap.notifications;

import android.os.Build;
import android.util.Log;
import com.popcap.events.IEventTick;
import com.popcap.network.PCPNetWork;
import com.popcap.util.NtfUtil;
import com.popcap.util.PCPLocalGameMgr;
import com.popcap.util.PopCapNotificationAbstract;
import com.popcap.util.PopCapNotificationConfigManger;
import com.popcap.util.PopCapNotificationForPlay;
import com.popcap.util.PopCapNotificationThread;
import com.popcap.util.TimeStrategy;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class GLobaleNtfMgr extends NtfMgr implements IEventTick {
    private ArrayList<PopCapNotificationAbstract> _notificationList;
    private Map<String, String> params;
    private int intKey = 0;
    private int maxNotfIndex = 0;
    private long mGetNtfDisTime = 0;
    private Date mLastGetNtfcTime = null;

    public GLobaleNtfMgr() {
        this.params = null;
        this._notificationList = null;
        this._notificationList = new ArrayList<>();
        this.params = new HashMap();
    }

    @Override // com.popcap.notifications.NtfMgr
    public void FillData(String data) {
        if (data.length() != 0) {
            ClearNotificationList();
            try {
                JSONObject jsonObj = new JSONObject(data);
                    int result = jsonObj.getInt("r");
                    if (result == 0) {
                        JSONObject objD = jsonObj.getJSONObject("d");
                        if (this.intKey > 128) {
                            this.intKey = 0;
                        }
                        JSONArray ctnList = objD.getJSONArray("nl");
                        int nowIndex = SaveNotificationList(ctnList);
                        if (this.maxNotfIndex < nowIndex) {
                            this.maxNotfIndex = nowIndex;
                            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.MaxNotifIndex, Integer.toString(this.maxNotfIndex));
                        }
                        if (objD.has("wnl")) {
                            WeekNtfMgr.Instance().FillData(objD.getJSONArray("wnl"));
                        }
                        if (objD.has("tml")) {
                            TimeStrategy.Instance().LoadServerTimeStrage(objD.getJSONArray("tml"));
                        }
                        sendNotificationList();
                    }
            } catch (JSONException e) {
                    e.printStackTrace();
            }
        }
    }

    private int SaveNotificationList(JSONArray jsArray) {
        int notIndex = 0;
        for (int i = 0; i < jsArray.length(); i++) {
            try {
                JSONObject ctnObj = (JSONObject) jsArray.get(i);
                PopCapNotificationForPlay notificationForPlay = new PopCapNotificationForPlay(0, ctnObj.getString("i"), ctnObj.getString("c"), -1L, 3);
                String ss = ctnObj.getString("s");
                notificationForPlay.SetSkuId(Integer.parseInt(ss));
                String ss2 = ctnObj.getString("t");
                notificationForPlay.setNtType(Integer.parseInt(ss2));
                notificationForPlay.setUrl(ctnObj.getString("u"));
                String ss3 = ctnObj.getString("p");
                int index = Integer.parseInt(ss3);
                if (index > notIndex) {
                    notIndex = index;
                }
                notificationForPlay.setId(index);
                this._notificationList.add(notificationForPlay);
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
        return notIndex;
    }

    @Override // com.popcap.events.IEventTick
    public void Tick() {
        if (IsGetNotificationTimeOut()) {
            GetServerNotificatonList();
        }
    }

    public void SetMaxNotIndex(String data) {
        if (data.equals("none")) {
            this.maxNotfIndex = 0;
            return;
        }
        try {
            this.maxNotfIndex = Integer.parseInt(data);
        } catch (NumberFormatException e) {
            this.maxNotfIndex = 0;
            e.printStackTrace();
        }
    }

    private void sendNotificationList() {
        for (PopCapNotificationAbstract n : this._notificationList) {
            PopCapNotificationThread.Instance(NtfUtil.GetPCPService()).PlayNotification(n);
        }
    }

    private void ClearNotificationList() {
        this._notificationList.clear();
    }

    public void SetNtfDisTime(long dis) {
        this.mGetNtfDisTime = dis;
    }

    public void SetLastGetNtfcTime(String data) {
        if (data.equals("none")) {
            this.mLastGetNtfcTime = new Date();
            this.mLastGetNtfcTime.setTime(0L);
            return;
        }
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            this.mLastGetNtfcTime = myFormatter.parse(data);
        } catch (Exception e) {
            e.printStackTrace();
            this.mLastGetNtfcTime = new Date();
            this.mLastGetNtfcTime.setTime(0L);
        }
    }

    private boolean IsGetNotificationTimeOut() {
        Date now = new Date();
        long disTime = now.getTime() - this.mLastGetNtfcTime.getTime();
        Log.d("++++++++", "IsGetNotificationTimeOut = " + disTime + " dis = " + this.mGetNtfDisTime);
        if (disTime < this.mGetNtfDisTime) {
            return false;
        }
        if (this.mGetNtfDisTime == 0) {
            SetNtfDisTime(PopCapNotificationConfigManger.Release_GetNtfList_DisTime);
        }
        this.mLastGetNtfcTime = now;
        String strTime = NtfUtil.GetDateStr(now);
        NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.lastGetNotificatonTime, strTime);
        return true;
    }

    private void GetServerNotificatonList() {
        String data = GetNotificationList();
        FillData(data);
        SetSkedulDisTime();
        NtfUtil.SaveLogServer("mac=" + NtfUtil.GetWifiMac() + "  getnotificationlist  locaTime= " + NtfUtil.GetLocalTime());
    }

    public void SetSkedulDisTime() {
        Date lstDate;
        String strLastTime = NtfUtil.GetUserlastOpt();
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        if (strLastTime.equals("none")) {
            new Date();
            SetNtfDisTime(0L);
            PCPLocalGameMgr.Instance().GetSkuIdList();
            NtfUtil.SaveUserLastOpt();
            return;
        }
        try {
            lstDate = myFormatter.parse(strLastTime);
        } catch (Exception e) {
            e.printStackTrace();
            lstDate = new Date();
            SetNtfDisTime(0L);
        }
        Date now = new Date();
        long ntldisTime = TimeStrategy.Instance().GetNotficationSkedulTime(now.getTime() - lstDate.getTime());
        if (ntldisTime < PopCapNotificationConfigManger.Release_GetNtfList_DisTime) {
            ntldisTime = PopCapNotificationConfigManger.Release_GetNtfList_DisTime;
        }
        SetNtfDisTime(ntldisTime);
        String strTarget = "mac=" + NtfUtil.GetWifiMac() + "SetSkedulDisTime = " + ntldisTime;
        NtfUtil.SaveLogServer(strTarget);
    }

    private String GetNotificationList() {
        Map<String, String> prama = GetNotiReqParams();
        String strResult = PCPNetWork.GetNetData(prama);
        if (strResult.length() > 0) {
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.skedulTime, strResult);
        }
        return strResult;
    }

    private Map<String, String> GetNotiReqParams() {
        String andrVerion = Build.VERSION.SDK;
        this.params.clear();
        this.params.put("req", "I1");
        this.params.put("m", NtfUtil.GetUUId());
        this.params.put("v", andrVerion);
        this.params.put("l", String.valueOf(this.maxNotfIndex));
        this.params.put("w", String.valueOf(WeekNtfMgr.Instance().GetMaxWeeklyIndex()));
        this.params.put("e", "2");
        JSONArray jsArray = PCPLocalGameMgr.Instance().GetLocalIdArray();
        this.params.put("s", jsArray.toString());
        this.params.put("c", "[]");
        return this.params;
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateUserOpt() {
        long ntldisTime = TimeStrategy.Instance().GetNotficationSkedulTime(0L);
        if (ntldisTime < PopCapNotificationConfigManger.Release_GetNtfList_DisTime) {
            ntldisTime = PopCapNotificationConfigManger.Release_GetNtfList_DisTime;
        }
        SetNtfDisTime(ntldisTime);
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateSkuUserOpt(String pckName) {
    }

    @Override // com.popcap.events.IEventTick
    public void OnUserStartGameEvent(String pckName) {
    }
}
