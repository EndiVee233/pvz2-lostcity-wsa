package com.popcap.log;

import android.util.Log;
import java.util.HashMap;
import java.util.Map;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class DebugLog implements IPcpLog {
    private Map<String, String> params;

    public DebugLog() {
        this.params = null;
        this.params = new HashMap();
    }

    @Override // com.popcap.log.IPcpLog
    public void log(String msg) {
        Debug(msg);
    }

    public void Debug(String msg) {
        Log.d("PopCapDebug++++", msg);
    }
}
