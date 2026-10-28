package com.popcap.util;

import android.util.Log;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.StringReader;
import java.util.ArrayList;
import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.ContentHandler;
import org.xml.sax.InputSource;
import org.xml.sax.XMLReader;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapNotificationConfigManger {
    public static final String Debug = "debug";
    public static final int Debug_DisTime = 60000;
    public static final String Debug_URL = "http://testpnserver.popcap.com.cn/index.php?";
    public static final int Debug_Version = 2;
    public static final long Get_RewardStrage_DisTime = 604800000;
    public static final String LastGetRewardTime = "lstRwdTime";
    public static final String LastSendEveryDayRewarTime = "lstEveryDayReward_";
    public static final String LastSendRewardTime = "lstSendRwdTime";
    public static final String LastStartTime = "lstStartTime_";
    public static final String MaxNotifIndex = "maxNtfIndex";
    public static final String MaxWeekIndex = "maxWkIndex";
    public static final String NotificationVerion = "2";
    public static final long OneDayTime = 86400000;
    public static final String PacketName = "pckName";
    public static final String Release = "release";
    public static final long Release_GetNtfList_DisTime = 28800000;
    public static final long Release_GetSkuList_DisTime = 86400000;
    public static final String Release_URL = "http://pnserver.intelligent.popcap.com.cn/index.php?";
    public static final int Release_Version = 1;
    public static final String RewardData = "rwdData";
    public static final String RwdSkdStrage = "rwdskd";
    public static final String UserLstOpt = "ulstOpt";
    public static final String WeeklyDate = "wkDate";
    public static final String configFileName = "PushService";
    private static final String configPathInJar = "/assets/notification_config.xml";
    public static final String lastGetNotificatonTime = "lstNtfcTime";
    public static final String lastGetSkuListTime = "lstSkuTime";
    public static final String skedulTime = "skedul";
    public static final String skuList = "skus";
    private static String serverUrl = null;
    private static ArrayList<PopCapNotificationAbstract> notificationBuffer = null;
    private static byte[] buffer = new byte[1024];

    private PopCapNotificationConfigManger() {
    }

    public static ArrayList<PopCapNotificationAbstract> fillNotificationList(PopCapDaemonService service) {
        notificationBuffer = null;
        String configContent = readConfigFromPrivate(service);
        if (configContent != null) {
            PopCapConfigHandler contentHandler = new PopCapConfigHandler();
            Log.d("DEBUG", "parseConfigFromPrivate");
            if (parseXml(configContent, contentHandler)) {
                notificationBuffer = contentHandler.getNotificationList();
                serverUrl = contentHandler.getServerUrl();
            } else {
                notificationBuffer = null;
            }
        } else {
            notificationBuffer = null;
        }
        if (notificationBuffer == null) {
            Log.d("DEBUG", "error in parseConfigFromPrivate");
        }
        if (notificationBuffer == null) {
            Log.d("DEBUG", "readConfigFromJar");
            String configContent2 = readConfigFromJar();
            if (configContent2 != null) {
                Log.d("DEBUG", "parseConfigFromJar");
                PopCapConfigHandler contentHandler2 = new PopCapConfigHandler();
                Log.d("DEBUG", "parseConfigFromJar");
                if (parseXml(configContent2, contentHandler2)) {
                    notificationBuffer = contentHandler2.getNotificationList();
                    serverUrl = contentHandler2.getServerUrl();
                } else {
                    notificationBuffer = null;
                }
            }
        }
        if (notificationBuffer == null) {
            Log.d("DEBUG", "error in parseConfigFromPrivate");
        }
        return notificationBuffer;
    }

    private static boolean parseXml(String xmlStr, ContentHandler contentHandler) {
        InputSource is = new InputSource();
        is.setCharacterStream(new StringReader(xmlStr));
        SAXParserFactory spf = SAXParserFactory.newInstance();
        try {
            SAXParser sp = spf.newSAXParser();
            XMLReader xr = sp.getXMLReader();
            xr.setContentHandler(contentHandler);
            xr.parse(is);
            return true;
        } catch (Exception e) {
            Log.d("DEBUG", "error in parserXml : " + xmlStr);
            e.printStackTrace();
            return false;
        }
    }

    public static String readConfigFromJar() {
        if (buffer == null) {
            buffer = new byte[1024];
        }
        String fileContents = "";
        try {
            InputStream in = PopCapNotificationConfigManger.class.getResourceAsStream(configPathInJar);
            for (int length = in.read(buffer); length > 0; length = in.read(buffer)) {
                fileContents = String.valueOf(fileContents) + new String(buffer, 0, length, "UTF-8");
            }
            in.close();
            return fileContents;
        } catch (Exception e) {
            Log.d("DEBUG", "error in read jar file: /assets/notification_config.xml");
            e.printStackTrace();
            return null;
        }
    }

    public static String readConfigFromPrivate(PopCapDaemonService service) {
        if (buffer == null) {
            buffer = new byte[1024];
        }
        String fileContents = "";
        try {
            FileInputStream fis = service.openFileInput(configFileName);
            for (int length = fis.read(buffer); length > 0; length = fis.read(buffer)) {
                fileContents = String.valueOf(fileContents) + new String(buffer, 0, length, "UTF-8");
            }
            fis.close();
            return fileContents;
        } catch (Exception e) {
            Log.d("DEBUG", "error in read private file: PushService");
            e.printStackTrace();
            return null;
        }
    }

    public static void writeConfigToPrivateFile(String status, PopCapDaemonService service) {
        try {
            FileOutputStream fos = service.openFileOutput(configFileName, 0);
            fos.write(status.getBytes("UTF-8"));
            fos.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void updateStatusToNotificationList(ArrayList<PopCapNotificationAbstract> notificationList) {
    }

    public static String getServerUrl() {
        return serverUrl;
    }

    public static void updateNotificationList(ArrayList<PopCapNotificationAbstract> dst, ArrayList<PopCapNotificationAbstract> src) {
        if (dst != null && src != null) {
            for (PopCapNotificationAbstract n : src) {
                PopCapNotificationAbstract toUpdate = findNotificationById(dst, n.id);
                updateNotification(toUpdate, n);
            }
        }
    }

    private static PopCapNotificationAbstract findNotificationById(ArrayList<PopCapNotificationAbstract> list, int id) {
        int notificationListSize = list.size();
        for (int i = 0; i < notificationListSize; i++) {
            PopCapNotificationAbstract pNotification = list.get(i);
            int nid = pNotification.id;
            if (nid == id) {
                return pNotification;
            }
        }
        Log.d("DEBUG", "No such notification id for id : " + id);
        return null;
    }

    /* JADX WARN: Failed to find 'out' block for switch in B:3:0x0002. Please report as an issue. */
    public static void updateNotification(PopCapNotificationAbstract dst, PopCapNotificationAbstract src) {
        switch (dst.type) {
        }
    }

    public static void printNotificationList(ArrayList<PopCapNotificationAbstract> list) {
        if (list == null) {
            Log.d("DEBUG", "null");
            return;
        }
        if (list.size() == 0) {
            Log.d("DEBUG", "listsize = 0");
        }
        for (PopCapNotificationAbstract n : list) {
            Log.d("DEBUG", n.toString());
        }
    }
}
