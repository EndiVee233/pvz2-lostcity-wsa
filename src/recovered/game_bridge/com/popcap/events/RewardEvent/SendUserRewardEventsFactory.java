package com.popcap.events.RewardEvent;

import com.popcap.events.EventFactory;
import com.popcap.events.IEventTick;
import com.popcap.util.NtfUtil;
import com.popcap.util.PopCapNotificationConfigManger;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SendUserRewardEventsFactory extends EventFactory {
    @Override // com.popcap.events.EventFactory
    public IEventTick CreteEvent() {
        SendUserRewardEvents event = new SendUserRewardEvents();
        event.FillTimeStrageData(NtfUtil.GetLocalString(PopCapNotificationConfigManger.RewardData));
        event.InitWithDisTime();
        event.FillLocaDateSkuRewardLastSendTime();
        return event;
    }
}
