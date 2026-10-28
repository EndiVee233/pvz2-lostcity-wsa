package com.popcap.events.RewardEvent;

import com.popcap.util.NtfUtil;
import java.util.ArrayList;
import java.util.Date;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SkuReward {
    private Date mLastOptTime = null;
    private RewardTimeStrage mRewardStrage;
    private int mSkuId;

    public SkuReward(int id) {
        this.mRewardStrage = null;
        this.mSkuId = 0;
        this.mSkuId = id;
        this.mRewardStrage = new RewardTimeStrage();
    }

    public void AddReward(JSONObject jsobj) {
        this.mRewardStrage.AddRewardJsonObj(jsobj);
    }

    public void SortTimeStrage() {
        this.mRewardStrage.SortRewarDistime();
    }

    public Reward GetTargetReward(long disTime) {
        return this.mRewardStrage.GetReadyReward(disTime);
    }

    public int GetSkuId() {
        return this.mSkuId;
    }

    public ArrayList<Reward> GetRewards() {
        return this.mRewardStrage.GetRewardList();
    }

    public Date getLastOptTime() {
        return this.mLastOptTime;
    }

    public void setLastOptTime(Date mLastOptTime) {
        NtfUtil.SaveLogServer("----- setLastOptTime +" + mLastOptTime.toLocaleString());
        this.mLastOptTime = mLastOptTime;
    }
}
