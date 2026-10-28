package com.popcap.util;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Random;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class TimeStrategy {
    public static TimeStrategy m_sTimeStrategy = null;
    ArrayList<TimePeriodTarget> mTimePerTargetList;

    private TimeStrategy() {
        this.mTimePerTargetList = null;
        this.mTimePerTargetList = new ArrayList<>();
    }

    public static TimeStrategy Instance() {
        if (m_sTimeStrategy == null) {
            m_sTimeStrategy = new TimeStrategy();
        }
        return m_sTimeStrategy;
    }

    public void LoadServerTimeStrage(JSONArray jsArray) {
        if (jsArray != null) {
            this.mTimePerTargetList.clear();
            for (int i = 0; i < jsArray.length(); i++) {
                try {
                    JSONObject ctnObj = (JSONObject) jsArray.get(i);
                    TimePeriodTarget aTarget = new TimePeriodTarget();
                    aTarget.period = ctnObj.getInt("l");
                    aTarget.period *= 3600000;
                    aTarget.target = ctnObj.getInt("d");
                    aTarget.target *= 3600000;
                    this.mTimePerTargetList.add(aTarget);
                } catch (JSONException e) {
                    e.printStackTrace();
                    return;
                }
            }
            Collections.sort(this.mTimePerTargetList, new SortByPeriod());
        }
    }

    public long GetRewardSkudualTime() {
        Random random = new Random();
        int rand = (random.nextInt() % 20) + 10;
        NtfUtil.SaveLogServer("#####  rand = " + rand);
        return PopCapNotificationConfigManger.Get_RewardStrage_DisTime + ((long) (rand * 1000 * 60));
    }

    public long GetNotficationSkedulTime(long srcTime) {
        int index = 0;
        while (index < this.mTimePerTargetList.size() - 1) {
            TimePeriodTarget lowerTarget = this.mTimePerTargetList.get(index);
            TimePeriodTarget longTarget = this.mTimePerTargetList.get(index + 1);
            if (lowerTarget.period > srcTime || srcTime >= longTarget.period) {
                index++;
            } else {
                return lowerTarget.target;
            }
        }
        if (index < this.mTimePerTargetList.size()) {
            return this.mTimePerTargetList.get(index).target;
        }
        return PopCapNotificationConfigManger.Release_GetNtfList_DisTime;
    }

    public long GetSkuSkeduTime() {
        return 86400000L;
    }
}
