package com.popcap.util;

import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PCPLocalGameMgr {
    public static PCPLocalGameMgr m_PcpLocalGameMgr = null;
    private Map<Integer, String> IdMapPackage;
    private List<LocalPackageInfo> popcapGameList;

    private PCPLocalGameMgr() {
        this.IdMapPackage = null;
        this.popcapGameList = null;
        this.popcapGameList = new ArrayList();
        this.IdMapPackage = new HashMap();
    }

    public static PCPLocalGameMgr Instance() {
        if (m_PcpLocalGameMgr == null) {
            m_PcpLocalGameMgr = new PCPLocalGameMgr();
        }
        return m_PcpLocalGameMgr;
    }

    public Integer GetGameId(String strPackage) {
        for (Map.Entry<Integer, String> entry : this.IdMapPackage.entrySet()) {
            Object key = entry.getKey();
            Object val = entry.getValue();
            String strVal = (String) val;
            if (strVal.equals(strPackage)) {
                return (Integer) key;
            }
        }
        return null;
    }

    public void AddPackId(int id, String pn) {
        this.IdMapPackage.put(new Integer(id), pn);
    }

    public ArrayList<Integer> GetSkuIdList() {
        ArrayList<Integer> skuIdList = new ArrayList<>();
        Iterator<Map.Entry<Integer, String>> iter = this.IdMapPackage.entrySet().iterator();
        while (iter.hasNext()) {
            Object key = iter.next().getKey();
            skuIdList.add((Integer) key);
        }
        return skuIdList;
    }

    public void ClearIdMap() {
        this.IdMapPackage.clear();
    }

    public String GetPackage(Integer gameId) {
        return this.IdMapPackage.get(gameId);
    }

    public boolean IsPackgeExist(String packName) {
        for (int i = 0; i < this.popcapGameList.size(); i++) {
            LocalPackageInfo localPack = this.popcapGameList.get(i);
            if (localPack != null && localPack.getPackageName().equalsIgnoreCase(packName)) {
                return true;
            }
        }
        return false;
    }

    public void GetExistPopcapGame() {
        if (this.popcapGameList != null) {
            this.popcapGameList.clear();
            PackageManager manager = NtfUtil.GetPCPService().getPackageManager();
            List<PackageInfo> pkgList = manager.getInstalledPackages(0);
            for (int i = 0; i < pkgList.size(); i++) {
                PackageInfo pI = pkgList.get(i);
                if (pI.packageName.equals(NtfUtil.GetPakcName())) {
                    LocalPackageInfo localPackageInfo = new LocalPackageInfo();
                    localPackageInfo.setPackageName(pI.packageName);
                    localPackageInfo.setVersion(pI.versionName);
                    this.popcapGameList.add(localPackageInfo);
                }
            }
        }
    }

    public LocalPackageInfo Get(int index) {
        return this.popcapGameList.get(index);
    }

    public int GetGameListCount() {
        return this.popcapGameList.size();
    }

    public JSONArray GetLocalIdArray() {
        Integer gameId;
        GetExistPopcapGame();
        JSONArray jsArray = new JSONArray();
        for (int i = 0; i < this.popcapGameList.size(); i++) {
            JSONObject jsObj = new JSONObject();
            LocalPackageInfo localObj = this.popcapGameList.get(i);
            if (localObj != null && (gameId = GetGameId(localObj.getPackageName())) != null) {
                try {
                    jsObj.put("s", gameId.intValue());
                    jsObj.put("v", localObj.getVersion());
                    jsArray.put(jsObj);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }
        return jsArray;
    }
}
