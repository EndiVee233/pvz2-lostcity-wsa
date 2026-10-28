package com.popcap.events;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public interface IEventTick {
    void OnUserStartGameEvent(String str);

    void Tick();

    void UpdateSkuUserOpt(String str);

    void UpdateUserOpt();
}
