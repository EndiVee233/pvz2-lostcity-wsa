package com.popcap.events.RewardEvent;

import com.popcap.util.PCPLocalGameMgr;
import com.popcap.util.UserOpt;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SkuRewardsMgr {
    public static SkuRewardsMgr sSkuRwMgr = null;
    private ArrayList<SkuReward> mSkuRewards;

    public static SkuRewardsMgr Instance() {
        if (sSkuRwMgr == null) {
            sSkuRwMgr = new SkuRewardsMgr();
        }
        return sSkuRwMgr;
    }

    private SkuRewardsMgr() {
        this.mSkuRewards = null;
        this.mSkuRewards = new ArrayList<>();
    }

    public void AddSkuReward(JSONArray jsonArray) {
        this.mSkuRewards.clear();
        for (int i = 0; i < jsonArray.length(); i++) {
            try {
                JSONObject jsObj = (JSONObject) jsonArray.get(i);
                int skuId = Integer.parseInt(jsObj.getString("s"));
                SkuReward skRwd = GetSkuReward(skuId);
                if (skRwd == null) {
                    skRwd = new SkuReward(skuId);
                    this.mSkuRewards.add(skRwd);
                }
                skRwd.AddReward(jsObj);
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
    }

    public ArrayList<Reward> GetTargetRewards() {
        Reward rwd;
        ArrayList<Reward> rewards = new ArrayList<>();
        ArrayList<Integer> skuIdList = PCPLocalGameMgr.Instance().GetSkuIdList();
        for (Integer skuIdObj : skuIdList) {
            SkuReward skReward = GetSkuReward(skuIdObj.intValue());
            long disTime = UserOpt.Instance().GetSkuOptDis(skuIdObj.intValue());
            if (skReward != null && (rwd = skReward.GetTargetReward(disTime)) != null) {
                rewards.add(rwd);
            }
        }
        return rewards;
    }

    public void SortTimeStrate() {
        for (SkuReward skRwd : this.mSkuRewards) {
            skRwd.SortTimeStrage();
        }
    }

    public SkuReward GetSkuReward(int skuId) {
        for (SkuReward skRwd : this.mSkuRewards) {
            if (skRwd.GetSkuId() == skuId) {
                return skRwd;
            }
        }
        return null;
    }

    public ArrayList<SkuReward> GetSkuRewardList() {
        return this.mSkuRewards;
    }
}
