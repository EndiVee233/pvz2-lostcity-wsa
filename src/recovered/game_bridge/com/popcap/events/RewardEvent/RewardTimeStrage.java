package com.popcap.events.RewardEvent;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class RewardTimeStrage {
    private ArrayList<Reward> m_Rewardlist;

    public RewardTimeStrage() {
        this.m_Rewardlist = null;
        this.m_Rewardlist = new ArrayList<>();
    }

    public void LoadData(JSONArray jsArray) {
        for (int i = 0; i < jsArray.length(); i++) {
            try {
                JSONObject jsObj = (JSONObject) jsArray.get(i);
                Reward reward = new Reward();
                reward.setContent("");
                reward.setDisTime(jsObj.getLong("dis"));
                this.m_Rewardlist.add(reward);
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
        Collections.sort(this.m_Rewardlist, new RewardDisCompard());
    }

    private Date ParseDate(String data) {
        Date date;
        if (data.equals("none")) {
            Date date2 = new Date();
            date2.setTime(0L);
            return date2;
        }
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            date = myFormatter.parse(data);
        } catch (Exception e) {
            e.printStackTrace();
            date = new Date();
            date.setTime(0L);
        }
        return date;
    }

    public void AddRewardJsonObj(JSONObject ctnObj) {
        Reward reward = new Reward();
        try {
            String ss = ctnObj.getString("t");
            reward.setType(Integer.parseInt(ss));
            reward.setUrl(ctnObj.getString("u"));
            String ss2 = ctnObj.getString("i");
            reward.setTile(ss2);
            reward.setContent(ctnObj.getString("c"));
            String ss3 = ctnObj.getString("r");
            long disTime = Long.parseLong(ss3) * 3600000;
            reward.setDisTime(disTime);
            int skuId = Integer.parseInt(ctnObj.getString("s"));
            reward.setSkuId(skuId);
            int index = Integer.parseInt(ctnObj.getString("p"));
            reward.setId(index);
        } catch (JSONException e) {
            e.printStackTrace();
        }
        this.m_Rewardlist.add(reward);
    }

    public void SortRewarDistime() {
        Collections.sort(this.m_Rewardlist, new RewardDisCompard());
    }

    public Reward GetReadyReward(long disTime) {
        int index = 0;
        while (index < this.m_Rewardlist.size() - 1) {
            if (disTime < this.m_Rewardlist.get(index).getDisTime() || disTime >= this.m_Rewardlist.get(index + 1).getDisTime()) {
                index++;
            } else {
                return this.m_Rewardlist.get(index);
            }
        }
        if (disTime < this.m_Rewardlist.get(0).getDisTime()) {
            return null;
        }
        return this.m_Rewardlist.get(index);
    }

    public ArrayList<Reward> GetRewardList() {
        return this.m_Rewardlist;
    }
}
