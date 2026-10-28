package com.popcap.SexyAppFramework;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import com.tencent.mm.sdk.modelmsg.SendMessageToWX;
import com.tencent.mm.sdk.modelmsg.WXMediaMessage;
import com.tencent.mm.sdk.modelmsg.WXWebpageObject;
import com.tencent.mm.sdk.openapi.IWXAPI;
import com.tencent.mm.sdk.openapi.WXAPIFactory;
import java.io.IOException;
import java.io.InputStream;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class WechatPlatform {
    private static IWXAPI mApi;
    public static long mNativeDriverPtr;

    public static native void Native_ShareComplete(long j, int i);

    public WechatPlatform(long nativeDriverPtr) {
        mNativeDriverPtr = nativeDriverPtr;
    }

    public void InitializeSDK(String APP_ID) {
        mApi = WXAPIFactory.createWXAPI(SexyAppFrameworkActivity.instance(), APP_ID, true);
        mApi.registerApp(APP_ID);
    }

    public static IWXAPI getIWXAPI() {
        return mApi;
    }

    public void DoShare(String url, boolean toTimeLine) {
        SendMessageToWX.Req req = new SendMessageToWX.Req();
        WXWebpageObject webpageObj = new WXWebpageObject();
        webpageObj.webpageUrl = url;
        WXMediaMessage msg = new WXMediaMessage();
        msg.mediaObject = webpageObj;
        msg.description = "嗨，亲爱的邻居！你有权保持沉默，僵尸协会发来投诉！";
        try {
            InputStream is = SexyAppFrameworkActivity.instance().getAssets().open("wechaticon.png");
            Bitmap icon = BitmapFactory.decodeStream(is);
            is.close();
            msg.setThumbImage(icon);
            if (toTimeLine) {
                msg.title = "嗨，亲爱的邻居！你有权保持沉默，僵尸协会发来投诉！";
                req.scene = 1;
            } else {
                msg.title = "回忆一下你虐了多少僵尸吧？！";
                req.scene = 0;
            }
            req.transaction = buildTransaction("text");
            req.message = msg;
            mApi.sendReq(req);
        } catch (IOException e) {
        }
    }

    public static void FinishShare(int code) {
        Native_ShareComplete(mNativeDriverPtr, code);
    }

    private String buildTransaction(String type) {
        return type == null ? String.valueOf(System.currentTimeMillis()) : type + System.currentTimeMillis();
    }

    public boolean IsWechatInstalled() {
        return mApi.isWXAppInstalled() && mApi.isWXAppSupportAPI();
    }
}
