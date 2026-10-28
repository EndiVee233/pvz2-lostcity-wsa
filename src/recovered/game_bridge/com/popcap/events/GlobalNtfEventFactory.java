package com.popcap.events;

import com.popcap.notifications.GLobaleNtfMgr;
import com.popcap.util.NtfUtil;
import com.popcap.util.PopCapNotificationConfigManger;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class GlobalNtfEventFactory extends EventFactory {
    @Override // com.popcap.events.EventFactory
    public IEventTick CreteEvent() {
        GLobaleNtfMgr glbNtf = new GLobaleNtfMgr();
        glbNtf.SetMaxNotIndex(NtfUtil.GetLocalString(PopCapNotificationConfigManger.MaxNotifIndex));
        glbNtf.SetLastGetNtfcTime(NtfUtil.GetLocalString(PopCapNotificationConfigManger.lastGetNotificatonTime));
        glbNtf.SetSkedulDisTime();
        return glbNtf;
    }
}
