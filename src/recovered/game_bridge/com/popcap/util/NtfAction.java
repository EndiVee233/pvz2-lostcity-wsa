package com.popcap.util;

import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class NtfAction {
    public static NtfAction s_NtfAction = null;

    public static NtfAction Instance() {
        if (s_NtfAction == null) {
            s_NtfAction = new NtfAction();
        }
        return s_NtfAction;
    }

    private NtfAction() {
    }

    public PendingIntent GetUserOptAction(PopCapNotificationAbstract notification) {
        switch (notification.getNtType()) {
            case 0:
                return GetTextPending();
            case 1:
                PendingIntent pendingIntent = GetGamePending(notification);
                if (pendingIntent == null) {
                    return GetTextPending();
                }
                return pendingIntent;
            case 2:
                return GetUriPending(notification.getUrl());
            default:
                return null;
        }
    }

    private PendingIntent GetTextPending() {
        Intent intent = new Intent();
        PendingIntent pendingIntent = PendingIntent.getActivity(NtfUtil.GetPCPService(), 0, intent, 0);
        return pendingIntent;
    }

    private PendingIntent GetGamePending(PopCapNotificationAbstract notfication) {
        Intent intent;
        PackageManager packageMananger = NtfUtil.GetPCPService().getPackageManager();
        String gamePackege = PCPLocalGameMgr.Instance().GetPackage(Integer.valueOf(notfication.GetSkuId()));
        if (gamePackege == null || (intent = packageMananger.getLaunchIntentForPackage(gamePackege)) == null) {
            return null;
        }
        if (notfication.getUrl() == null) {
            intent.putExtra(PopCapPushNotificationService.getSrvkey(), PopCapPushNotificationService.getSrvValue());
        } else {
            intent.putExtra(PopCapPushNotificationService.getSrvRwdKey(), notfication.getUrl());
        }
        intent.setFlags(268435456);
        PendingIntent pendingIntent = PendingIntent.getActivity(NtfUtil.GetPCPService(), 0, intent, 0);
        return pendingIntent;
    }

    private PendingIntent GetUriPending(String url) {
        Uri uri = Uri.parse(url);
        Intent intent = new Intent("android.intent.action.VIEW", uri);
        intent.setFlags(268435456);
        PendingIntent pendingIntent = PendingIntent.getActivity(NtfUtil.GetPCPService(), 0, intent, 0);
        return pendingIntent;
    }
}
