package com.popcap.util;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class UserOpt {
    public static UserOpt sUserOpt = null;
    private ArrayList<SkuUserOpt> vSkuUserOpts;

    private UserOpt() {
        this.vSkuUserOpts = null;
        this.vSkuUserOpts = new ArrayList<>();
        Init();
    }

    public static UserOpt Instance() {
        if (sUserOpt == null) {
            sUserOpt = new UserOpt();
        }
        return sUserOpt;
    }

    private Date ParserDate(int skuId, String data) {
        Date date;
        if (data.equals("none")) {
            UpateUserOpt(skuId);
            return new Date();
        }
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            date = myFormatter.parse(data);
        } catch (Exception e) {
            e.printStackTrace();
            date = new Date();
        }
        return date;
    }

    private void Init() {
        ArrayList<Integer> skuIdList = PCPLocalGameMgr.Instance().GetSkuIdList();
        for (Integer skuIdObj : skuIdList) {
            String strDate = NtfUtil.GetLocalString(PopCapNotificationConfigManger.UserLstOpt + skuIdObj.intValue());
            SkuUserOpt skOpt = new SkuUserOpt();
            skOpt.dOptDate = ParserDate(skuIdObj.intValue(), strDate);
            skOpt.nSkuId = skuIdObj.intValue();
            this.vSkuUserOpts.add(skOpt);
            NtfUtil.SaveLogServer("----- skuId = " + skuIdObj.intValue() + " optdate = " + skOpt.dOptDate.toString());
        }
    }

    public void UpateUserOpt(int skuId) {
        String key = PopCapNotificationConfigManger.UserLstOpt + skuId;
        String value = NtfUtil.GetLocalTime();
        NtfUtil.SaveDatalocal(key, value);
        SkuUserOpt skuOpt = GetSkuUserOpt(skuId);
        if (skuOpt != null) {
            skuOpt.dOptDate = new Date();
        } else {
            NtfUtil.SaveLogServer("UpateUserOpt  no this skuId = " + skuId);
        }
    }

    public ArrayList<SkuUserOpt> GetOptArray() {
        Date now = new Date();
        for (SkuUserOpt skuOpt : this.vSkuUserOpts) {
            skuOpt.ndisTime = now.getTime() - skuOpt.dOptDate.getTime();
        }
        return this.vSkuUserOpts;
    }

    public long GetSkuOptDis(int skuId) {
        for (SkuUserOpt skuOpt : this.vSkuUserOpts) {
            if (skuOpt.nSkuId == skuId) {
                Date now = new Date();
                return now.getTime() - skuOpt.dOptDate.getTime();
            }
        }
        NtfUtil.SaveLogServer("error ++++++++++++ GetSkuOptDis ");
        return 0L;
    }

    public SkuUserOpt GetSkuUserOpt(int skuId) {
        for (SkuUserOpt skuOpt : this.vSkuUserOpts) {
            if (skuOpt.nSkuId == skuId) {
                return skuOpt;
            }
        }
        return null;
    }
}
