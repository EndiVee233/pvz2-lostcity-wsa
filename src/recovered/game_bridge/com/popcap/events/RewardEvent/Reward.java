package com.popcap.events.RewardEvent;

import java.util.Date;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class Reward {
    private int type;
    private long disTime = 0;
    private String Tile = "";
    private String Content = "";
    private String Url = "";
    private int skuId = 0;
    private int id = 0;
    private Date lstSendDate = null;
    private int nSend = -1;

    public int getnSend() {
        return this.nSend;
    }

    public void setnSend(int nSend) {
        this.nSend = nSend;
    }

    public Date getLstSendDate() {
        return this.lstSendDate;
    }

    public void setLstSendDate(Date lstSendDate) {
        this.lstSendDate = lstSendDate;
    }

    public int getId() {
        return this.id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public int getSkuId() {
        return this.skuId;
    }

    public void setSkuId(int skuId) {
        this.skuId = skuId;
    }

    public int getType() {
        return this.type;
    }

    public void setType(int type) {
        this.type = type;
    }

    public String getUrl() {
        return this.Url;
    }

    public void setUrl(String url) {
        this.Url = url;
    }

    public long getDisTime() {
        return this.disTime;
    }

    public void setDisTime(long disTime) {
        this.disTime = disTime;
    }

    public String getTile() {
        return this.Tile;
    }

    public void setTile(String tile) {
        this.Tile = tile;
    }

    public String getContent() {
        return this.Content;
    }

    public void setContent(String content) {
        this.Content = content;
    }
}
