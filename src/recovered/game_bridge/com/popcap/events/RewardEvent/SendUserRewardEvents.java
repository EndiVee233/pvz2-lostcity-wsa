package com.popcap.events.RewardEvent;

import android.os.Build;
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
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SendUserRewardEvents implements IEventTick {
    private Map<String, String> params;
    private int nRwdSkd = -1;
    private Date mLastGetRewardTime = null;
    private ArrayList<Reward> mTargetRewards = null;
    private long mGetServerSkedulTime = 0;

    public SendUserRewardEvents() {
        this.params = null;
        this.params = new HashMap();
    }

    @Override // com.popcap.events.IEventTick
    public void Tick() {
        CheckGetRewardStrage();
        CheckSendNtf();
    }

    private void CheckGetRewardStrage() {
        Date now = new Date();
        long disTime = now.getTime() - this.mLastGetRewardTime.getTime();
        if (disTime > this.mGetServerSkedulTime) {
            String rwdData = GetServerRewardStrageTime();
            if (rwdData.length() == 0) {
                NtfUtil.SaveLocalInt(PopCapNotificationConfigManger.RwdSkdStrage, 0);
            }
            FillServerDate(rwdData);
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.LastGetRewardTime, NtfUtil.GetDateStr(now));
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.RewardData, rwdData);
            InitWithDisTime();
            NtfUtil.SaveLogServer("mac=" + NtfUtil.GetWifiMac() + "  CheckGetRewardStrage  locaTime= " + NtfUtil.GetLocalTime());
        }
    }

    public void FillLocaDateSkuRewardLastSendTime() {
        ArrayList<SkuReward> skuRewardList = SkuRewardsMgr.Instance().GetSkuRewardList();
        for (SkuReward skuRwd : skuRewardList) {
            for (Reward rwd : skuRwd.GetRewards()) {
                SetLastSendDate(rwd);
                SetRewardSendRecord(rwd);
            }
        }
    }

    public void SetRewardSendRecord(Reward rwd) {
        String key = new StringBuilder().append(rwd.getSkuId()).append(rwd.getId()).toString();
        int nSend = NtfUtil.GetLocalInt(key);
        if (nSend == -1) {
            NtfUtil.SaveLocalInt(key, 0);
            rwd.setnSend(0);
        } else {
            rwd.setnSend(nSend);
        }
    }

    private String GetServerRewardStrageTime() {
        this.params.clear();
        this.params.put("req", "I3");
        String andrVerion = Build.VERSION.SDK;
        this.params.put("m", NtfUtil.GetUUId());
        this.params.put("v", andrVerion);
        JSONArray jsArray = PCPLocalGameMgr.Instance().GetLocalIdArray();
        this.params.put("s", jsArray.toString());
        return PCPNetWork.GetNetData(this.params);
    }

    private void FillServerDate(String data) {
        try {
            JSONObject jsonObj = new JSONObject(data);
            int result = jsonObj.getInt("r");
            if (result != 0) {
                NtfUtil.SaveLocalInt(PopCapNotificationConfigManger.RwdSkdStrage, 0);
            } else {
                NtfUtil.SaveLocalInt(PopCapNotificationConfigManger.RwdSkdStrage, 1);
                JSONObject objD = jsonObj.getJSONObject("d");
                JSONArray ntfArray = objD.getJSONArray("rnl");
                SkuRewardsMgr.Instance().AddSkuReward(ntfArray);
                SkuRewardsMgr.Instance().SortTimeStrate();
                FillLocaDateSkuRewardLastSendTime();
            }
        } catch (JSONException e) {
            NtfUtil.SaveLocalInt(PopCapNotificationConfigManger.RwdSkdStrage, 0);
            e.printStackTrace();
        }
    }

    private void CheckSendNtf() {
        this.mTargetRewards = SkuRewardsMgr.Instance().GetTargetRewards();
        Date now = new Date();
        Calendar c = Calendar.getInstance();
        c.setTime(now);
        int nowDay = c.get(5);
        for (Reward rwd : this.mTargetRewards) {
            SkuReward skrwd = SkuRewardsMgr.Instance().GetSkuReward(rwd.getSkuId());
            if (skrwd == null) {
                NtfUtil.SaveLogServer(" error skuRwad == null");
            } else if (skrwd.getLastOptTime() == null) {
                NtfUtil.SaveLogServer("====skrwd.getLastOptTime()   ===== null");
            } else {
                long nowDis = now.getTime() - skrwd.getLastOptTime().getTime();
                c.setTime(rwd.getLstSendDate());
                int lastSendDay = c.get(5);
                if (nowDis > rwd.getDisTime() && (lastSendDay != nowDay || rwd.getnSend() == 0)) {
                    PopCapNotificationAbstract notificationForPlay = new PopCapNotificationForPlay(0, rwd.getTile(), rwd.getContent(), -1L, 3);
                    notificationForPlay.setNtType(rwd.getType());
                    notificationForPlay.setUrl(rwd.getUrl());
                    notificationForPlay.setId(rwd.getId());
                    notificationForPlay.SetSkuId(rwd.getSkuId());
                    PopCapNotificationThread.Instance(NtfUtil.GetPCPService()).PlayNotification(notificationForPlay);
                    NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.LastSendRewardTime + skrwd.GetSkuId() + rwd.getId(), NtfUtil.GetDateStr(now));
                    NtfUtil.SaveLocalInt(new StringBuilder().append(skrwd.GetSkuId()).append(rwd.getId()).toString(), 1);
                    rwd.setnSend(1);
                    rwd.setLstSendDate(now);
                }
            }
        }
        ResetUserTargetReward();
    }

    public void FillTimeStrageData(String data) {
        NtfUtil.SaveLogServer("######### get local RewardStrageTime = " + data);
        if (!data.equals("none")) {
            FillServerDate(data);
        }
    }

    public void InitWithDisTime() {
        String strLastGetRewardData = NtfUtil.GetLocalString(PopCapNotificationConfigManger.LastGetRewardTime);
        SetSkusLastOptDate();
        SetLastGetRewardDate(strLastGetRewardData);
        this.mTargetRewards = SkuRewardsMgr.Instance().GetTargetRewards();
        setnRwdSkd(NtfUtil.GetLocalInt(PopCapNotificationConfigManger.RwdSkdStrage));
        if (getnRwdSkd() == 1) {
            this.mGetServerSkedulTime = TimeStrategy.Instance().GetRewardSkudualTime();
            NtfUtil.SaveLogServer(" g&&&&&  get reward skedual = " + this.mGetServerSkedulTime);
            return;
        }
        Date now = new Date();
        long rwdDisTime = TimeStrategy.Instance().GetNotficationSkedulTime(now.getTime() - this.mLastGetRewardTime.getTime());
        if (rwdDisTime < PopCapNotificationConfigManger.Release_GetNtfList_DisTime) {
            rwdDisTime = PopCapNotificationConfigManger.Release_GetNtfList_DisTime;
        }
        this.mGetServerSkedulTime = rwdDisTime;
    }

    public void ResetUserTargetReward() {
        this.mTargetRewards = SkuRewardsMgr.Instance().GetTargetRewards();
    }

    public void SetSkusLastOptDate() {
        ArrayList<SkuReward> skuRwds = SkuRewardsMgr.Instance().GetSkuRewardList();
        NtfUtil.SaveLogServer("******  SetSkusLastOptDate size = " + skuRwds.size());
        for (SkuReward skuRwd : skuRwds) {
            String data = NtfUtil.GetLocalString(PopCapNotificationConfigManger.UserLstOpt + skuRwd.GetSkuId());
            if (data.equals("none")) {
                Date date = new Date();
                skuRwd.setLastOptTime(date);
            } else {
                SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                try {
                    Date date2 = myFormatter.parse(data);
                    skuRwd.setLastOptTime(date2);
                } catch (Exception e) {
                    e.printStackTrace();
                    Date date3 = new Date();
                    skuRwd.setLastOptTime(date3);
                }
            }
        }
    }

    private void SetLastSendDate(Reward rwd) {
        String data = NtfUtil.GetLocalString(PopCapNotificationConfigManger.LastSendRewardTime + rwd.getSkuId() + rwd.getId());
        NtfUtil.SaveLogServer("get local date = " + data);
        if (data.equals("none")) {
            Date date = new Date();
            rwd.setLstSendDate(date);
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.LastSendRewardTime + rwd.getSkuId() + rwd.getId(), NtfUtil.GetDateStr(date));
            return;
        }
        SimpleDateFormat dtFormater = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            Date lstSendDate = dtFormater.parse(data);
            rwd.setLstSendDate(lstSendDate);
        } catch (Exception e) {
            e.printStackTrace();
            Date date2 = new Date();
            rwd.setLstSendDate(date2);
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.LastSendRewardTime + rwd.getSkuId() + rwd.getId(), NtfUtil.GetDateStr(date2));
        }
    }

    public void SetLastGetRewardDate(String data) {
        if (data.equals("none")) {
            this.mLastGetRewardTime = new Date();
            this.mLastGetRewardTime.setTime(0L);
            return;
        }
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            this.mLastGetRewardTime = myFormatter.parse(data);
        } catch (Exception e) {
            e.printStackTrace();
            this.mLastGetRewardTime = new Date();
        }
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateUserOpt() {
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateSkuUserOpt(String pckName) {
        Integer skuId = PCPLocalGameMgr.Instance().GetGameId(pckName);
        if (skuId == null) {
            NtfUtil.SaveLogServer("pakcName = " + pckName + "not found");
            return;
        }
        SkuReward skRwd = SkuRewardsMgr.Instance().GetSkuReward(skuId.intValue());
        if (skRwd != null) {
            skRwd.setLastOptTime(new Date());
            this.mTargetRewards = SkuRewardsMgr.Instance().GetTargetRewards();
        } else {
            NtfUtil.SaveLogServer(" pckName = " + pckName + " not found");
        }
    }

    public int getnRwdSkd() {
        return this.nRwdSkd;
    }

    public void setnRwdSkd(int nRwdSkd) {
        this.nRwdSkd = nRwdSkd;
    }

    @Override // com.popcap.events.IEventTick
    public void OnUserStartGameEvent(String pckName) {
    }
}
