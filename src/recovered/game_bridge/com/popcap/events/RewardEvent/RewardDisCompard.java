package com.popcap.events.RewardEvent;

import java.util.Comparator;

/* JADX INFO: compiled from: RewardTimeStrage.java */
/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
class RewardDisCompard implements Comparator<Object> {
    RewardDisCompard() {
    }

    @Override // java.util.Comparator
    public int compare(Object arg0, Object arg1) {
        Reward reward1 = (Reward) arg0;
        Reward reward2 = (Reward) arg1;
        if (reward1.getDisTime() > reward2.getDisTime()) {
            return 1;
        }
        if (reward1.getDisTime() == reward2.getDisTime()) {
            reward1.setDisTime(reward1.getDisTime() + 180000);
            return 1;
        }
        return -1;
    }
}
