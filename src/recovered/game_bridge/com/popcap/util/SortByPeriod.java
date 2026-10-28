package com.popcap.util;

import java.util.Comparator;

/* JADX INFO: compiled from: TimeStrategy.java */
/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
class SortByPeriod implements Comparator<Object> {
    SortByPeriod() {
    }

    @Override // java.util.Comparator
    public int compare(Object arg0, Object arg1) {
        TimePeriodTarget target1 = (TimePeriodTarget) arg0;
        TimePeriodTarget target2 = (TimePeriodTarget) arg1;
        return target1.period >= target2.period ? 1 : -1;
    }
}
