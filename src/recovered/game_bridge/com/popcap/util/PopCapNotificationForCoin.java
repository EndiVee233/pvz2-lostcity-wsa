package com.popcap.util;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapNotificationForCoin extends PopCapNotificationAbstract {
    public int _coinIncraseRatePerMinute;
    public int _coinMax;
    public int _coinRemains;

    public PopCapNotificationForCoin(int initId, String initTitle, String initText, long initInterval, int initAction) {
        super(initId, initTitle, initText, initInterval, initAction);
        this._coinRemains = 0;
        this._coinIncraseRatePerMinute = 1;
        this._coinMax = 100;
        this.type = 32;
        resetInterval();
    }

    public void resetCoinRemains(int coinRemains) {
        this._coinRemains = coinRemains;
        resetInterval();
    }

    public void resetCoinSettings(int coinMax, int coinIncraseRatePerMinute) {
        if (this._coinIncraseRatePerMinute < 0) {
            this._coinIncraseRatePerMinute = coinIncraseRatePerMinute;
        }
        if (this._coinMax < 0) {
            this._coinMax = coinMax;
        }
        resetInterval();
    }

    @Override // com.popcap.util.PopCapNotificationAbstract
    public void updateNextSendTime() {
        this._coinRemains = 0;
    }

    public void resetInterval() {
        this.interval = ((long) ((this._coinMax - this._coinRemains) / this._coinIncraseRatePerMinute)) * 1000 * 60;
    }

    public static void updateNotification(PopCapNotificationAbstract dst, PopCapNotificationAbstract src) {
        if (dst.type == 32 && src.type == 32) {
            PopCapNotificationAbstract.updateNotification(dst, src);
            PopCapNotificationForCoin aDst = (PopCapNotificationForCoin) dst;
            PopCapNotificationForCoin aSrc = (PopCapNotificationForCoin) src;
            if (aDst._coinRemains > 0) {
                aDst._coinRemains = aSrc._coinRemains;
            }
        }
    }

    @Override // com.popcap.util.PopCapNotificationAbstract
    public String statusToHtml() {
        return null;
    }
}
