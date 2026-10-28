package com.popcap.SexyAppFramework;

import android.util.Log;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidAssetUtils {
    private static final String sAssetPrefix = "ASSET:";

    public static String GetAssetNameFromFileName(String InFilename) {
        try {
            String actualFilename = InFilename.substring(sAssetPrefix.length());
            return actualFilename.replace('\\', '/') + ".smf";
        } catch (Exception ex) {
            ex.printStackTrace();
            Log.e("Error", ex.toString());
            return "";
        }
    }
}
