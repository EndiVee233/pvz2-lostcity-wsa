package com.popcap.events;

import com.popcap.network.PCPNetWork;
import com.popcap.util.NtfUtil;
import com.popcap.util.PCPLocalGameMgr;
import com.popcap.util.PopCapNotificationConfigManger;
import com.popcap.util.TimeStrategy;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SkuListMgr implements IEventTick {
    private long mGetSkuDisTime = 0;
    private Date mLastGetSkuListTime = null;
    private Map<String, String> params;

    public SkuListMgr() {
        this.params = null;
        this.params = new HashMap();
    }

    @Override // com.popcap.events.IEventTick
    public void Tick() {
        if (IsGetSkuTimeOut()) {
            GetServerBaserInfo();
            RestSkuDisTime(TimeStrategy.Instance().GetSkuSkeduTime());
        }
    }

    public void SetSkuDisTime() {
        RestSkuDisTime(TimeStrategy.Instance().GetSkuSkeduTime());
    }

    public void SetLastGetSkuListTime(String data) {
        if (data.equals("none")) {
            this.mLastGetSkuListTime = new Date();
            this.mLastGetSkuListTime.setTime(0L);
            return;
        }
        SimpleDateFormat myFormatter = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        try {
            this.mLastGetSkuListTime = myFormatter.parse(data);
        } catch (Exception e) {
            e.printStackTrace();
            this.mLastGetSkuListTime = new Date();
            this.mLastGetSkuListTime.setTime(0L);
        }
    }

    private boolean IsGetSkuTimeOut() {
        Date now = new Date();
        long disTime = now.getTime() - this.mLastGetSkuListTime.getTime();
        if (disTime < this.mGetSkuDisTime) {
            return false;
        }
        NtfUtil.SaveLogServer("mac=" + NtfUtil.GetWifiMac() + "  GetSkuTimeOut  locaTime= " + NtfUtil.GetDateStr(now));
        String strTime = NtfUtil.GetDateStr(now);
        NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.lastGetSkuListTime, strTime);
        if (this.mGetSkuDisTime == 0) {
            this.mGetSkuDisTime = 86400000L;
        }
        this.mLastGetSkuListTime = now;
        return true;
    }

    private void RestSkuDisTime(long dis) {
        this.mGetSkuDisTime = dis;
    }

    public void SetSkuTime(long dis) {
        this.mGetSkuDisTime = dis;
    }

    private void GetServerBaserInfo() {
        String data = GetGameConfig();
        FillSkuList(data);
        NtfUtil.SaveLogServer("mac=" + NtfUtil.GetWifiMac() + "  getskuList locaTime= " + NtfUtil.GetLocalTime());
    }

    private String GetGameConfig() {
        Map<String, String> prama = GetConfigXmlParams();
        String strResult = PCPNetWork.GetNetData(prama);
        if (strResult.length() > 0) {
            NtfUtil.SaveDatalocal(PopCapNotificationConfigManger.skuList, strResult);
        }
        return strResult;
    }

    public void FillSkuList(String data) {
        if (data != null && data.length() != 0 && !data.equals("none")) {
            try {
                JSONObject jsonObj = new JSONObject(data);
                    int result = jsonObj.getInt("r");
                    if (result == 0) {
                        JSONObject objD = jsonObj.getJSONObject("d");
                        PCPLocalGameMgr.Instance().ClearIdMap();
                        if (objD.has("tml")) {
                            TimeStrategy.Instance().LoadServerTimeStrage(objD.getJSONArray("tml"));
                        }
                        JSONArray ctnList = objD.getJSONArray("sl");
                        PCPLocalGameMgr.Instance().GetExistPopcapGame();
                        for (int i = 0; i < ctnList.length(); i++) {
                            JSONObject ctnObj = (JSONObject) ctnList.get(i);
                            String strId = ctnObj.getString("si");
                            int skuId = Integer.parseInt(strId);
                            String packName = ctnObj.getString("pn");
                            if (PCPLocalGameMgr.Instance().IsPackgeExist(packName)) {
                                PCPLocalGameMgr.Instance().AddPackId(skuId, packName);
                            }
                        }
                    }
            } catch (JSONException e) {
                    e.printStackTrace();
            }
        }
    }

    private Map<String, String> GetConfigXmlParams() {
        this.params.clear();
        this.params.put("req", "I2");
        return this.params;
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateUserOpt() {
        RestSkuDisTime(TimeStrategy.Instance().GetSkuSkeduTime());
    }

    @Override // com.popcap.events.IEventTick
    public void UpdateSkuUserOpt(String pckName) {
    }

    @Override // com.popcap.events.IEventTick
    public void OnUserStartGameEvent(String pckName) {
    }
}
