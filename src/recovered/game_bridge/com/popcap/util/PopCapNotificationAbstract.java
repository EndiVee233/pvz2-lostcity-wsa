package com.popcap.util;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public abstract class PopCapNotificationAbstract {
    public int action;
    protected int id;
    protected long interval;
    protected String text;
    protected String title;
    long lastSendTime = -1;
    protected int type = -1;
    protected int skuId = -1;
    protected int ntType = -1;
    protected String url = null;

    public int getId() {
        return this.id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getUrl() {
        return this.url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public int getNtType() {
        return this.ntType;
    }

    public void setNtType(int ntType) {
        this.ntType = ntType;
    }

    public PopCapNotificationAbstract(int initId, String initTitle, String initText, long initInterval, int initAction) {
        this.title = null;
        this.text = null;
        this.interval = -1L;
        this.id = -1;
        this.action = -1;
        this.id = initId;
        this.title = initTitle;
        this.text = initText;
        this.interval = initInterval;
        this.action = initAction;
    }

    public void SetSkuId(int skuId) {
        this.skuId = skuId;
    }

    public int GetSkuId() {
        return this.skuId;
    }

    public long getNextSendTime() {
        if (this.lastSendTime < 0) {
            this.lastSendTime = System.currentTimeMillis();
        }
        return this.lastSendTime + this.interval;
    }

    public void updateNextSendTime() {
        this.lastSendTime = System.currentTimeMillis();
    }

    public static void updateNotification(PopCapNotificationAbstract dst, PopCapNotificationAbstract src) {
        if (src.title != null) {
            dst.title = src.title;
        }
        if (src.text != null) {
            dst.text = src.text;
        }
        if (src.interval > 0) {
            dst.interval = src.interval;
        }
        if (src.type > 0) {
            dst.type = src.type;
        }
        if (src.action > 0) {
            dst.action = src.action;
        }
        if (src.lastSendTime > 0) {
            dst.lastSendTime = src.lastSendTime;
        }
    }

    public String toString() {
        StringBuilder rtn = new StringBuilder();
        return rtn.toString();
    }

    public String statusToHtml() {
        return null;
    }
}
