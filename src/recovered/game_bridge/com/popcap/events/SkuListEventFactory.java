package com.popcap.events;

import com.popcap.util.NtfUtil;
import com.popcap.util.PopCapNotificationConfigManger;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SkuListEventFactory extends EventFactory {
    @Override // com.popcap.events.EventFactory
    public IEventTick CreteEvent() {
        SkuListMgr skuMgr = new SkuListMgr();
        skuMgr.SetLastGetSkuListTime(NtfUtil.GetLocalString(PopCapNotificationConfigManger.lastGetSkuListTime));
        skuMgr.FillSkuList(NtfUtil.GetLocalString(PopCapNotificationConfigManger.skuList));
        skuMgr.SetSkuDisTime();
        return skuMgr;
    }
}
