package com.popcap.util;

import android.util.Log;
import com.example.assetexam.ShellUtils;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Map;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class NetWorkHttp {
    public static String HttpReq(String url, Map<String, String> params) {
        HttpURLConnection con = null;
        StringBuffer sb = new StringBuffer();
        if (params != null) {
            for (Map.Entry<String, String> e : params.entrySet()) {
                sb.append(e.getKey());
                sb.append("=");
                sb.append(e.getValue());
                sb.append("&");
            }
            sb.substring(0, sb.length() - 1);
            Log.d("**************** ", String.valueOf(sb.toString()) + " url = " + url);
        }
        try {
            URL u = new URL(url);
                con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setDoOutput(true);
                con.setDoInput(true);
                con.setUseCaches(false);
                con.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                OutputStreamWriter osw = new OutputStreamWriter(con.getOutputStream(), "UTF-8");
                osw.write(sb.toString());
                osw.flush();
                osw.close();
        } catch (Exception e) {
                e.printStackTrace();
        }
        StringBuffer buffer = new StringBuffer();
        try {
            try {
                BufferedReader br = new BufferedReader(new InputStreamReader(con.getInputStream(), "UTF-8"));
                while (true) {
                    String temp = br.readLine();
                    if (temp == null) {
                        break;
                    }
                    buffer.append(temp);
                    buffer.append(ShellUtils.COMMAND_LINE_END);
                }
                if (con != null) {
                    con.disconnect();
                }
            } catch (Throwable th) {
                if (con != null) {
                    con.disconnect();
                }
                throw th;
            }
        } catch (Exception e4) {
            e4.printStackTrace();
            if (con != null) {
                con.disconnect();
            }
        }
        return buffer.toString();
    }
}
