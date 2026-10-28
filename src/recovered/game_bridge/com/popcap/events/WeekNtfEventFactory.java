package com.popcap.events;

import com.popcap.notifications.WeekNtfMgr;
import com.popcap.util.NtfUtil;
import com.popcap.util.PopCapNotificationConfigManger;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class WeekNtfEventFactory extends EventFactory {
    @Override // com.popcap.events.EventFactory
    public IEventTick CreteEvent() {
        WeekNtfMgr wkNtfMgr = new WeekNtfMgr();
        wkNtfMgr.SetMaxWkIndex(NtfUtil.GetLocalString(PopCapNotificationConfigManger.MaxWeekIndex));
        wkNtfMgr.SetWeekDate(NtfUtil.GetLocalString(PopCapNotificationConfigManger.WeeklyDate));
        return wkNtfMgr;
    }
}
