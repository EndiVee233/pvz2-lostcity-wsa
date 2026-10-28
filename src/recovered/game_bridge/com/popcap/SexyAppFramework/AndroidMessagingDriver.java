package com.popcap.SexyAppFramework;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.text.Html;
import android.util.Log;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
class AndroidMessagingDriver {
    private static final String TAG = "Messaging.Driver";

    AndroidMessagingDriver() {
    }

    public boolean composeTextMessage(String recipient, String message) {
        Log.v(TAG, "AndroidMessagingDriver.composeTextMessage");
        Intent intent = new Intent("android.intent.action.VIEW");
        intent.putExtra("address", recipient);
        intent.putExtra("sms_body", message);
        intent.setData(Uri.parse("smsto:" + recipient));
        try {
            SexyAppFrameworkActivity.instance().startActivity(intent);
            return true;
        } catch (ActivityNotFoundException e) {
            Log.v(TAG, "AndroidMessagingDriver.composeTextMessage: no client");
            return false;
        }
    }

    public boolean composeEmailMessage(String recipient, String title, String body, String to, String mimeType) {
        Log.v(TAG, "AndroidMessagingDriver.composeEmailMessage");
        Intent intent = new Intent("android.intent.action.SENDTO", Uri.fromParts("mailto", to, null));
        intent.putExtra("android.intent.extra.SUBJECT", title);
        if (mimeType.equals("text/html")) {
            intent.putExtra("android.intent.extra.TEXT", Html.fromHtml(body));
        } else {
            intent.putExtra("android.intent.extra.TEXT", body);
        }
        try {
            SexyAppFrameworkActivity.instance().startActivity(Intent.createChooser(intent, "Send mail..."));
            return true;
        } catch (ActivityNotFoundException e) {
            Log.v(TAG, "AndroidMessagingDriver.composeEmailMessage: no client");
            return false;
        }
    }
}
