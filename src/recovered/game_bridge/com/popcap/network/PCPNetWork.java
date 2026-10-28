package com.popcap.network;

import com.popcap.util.NetWorkHttp;
import com.popcap.util.NtfUtil;
import java.util.Map;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PCPNetWork {
    public static String sUrl = null;

    public static String GetNetData(Map<String, String> params) {
        if (sUrl == null) {
            return new String();
        }
        String strResult = NetWorkHttp.HttpReq(sUrl, params);
        NtfUtil.SaveLogServer(strResult);
        return strResult;
    }

    public static void SetURl(String url) {
        sUrl = url;
    }
}
