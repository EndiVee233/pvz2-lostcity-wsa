package com.popcap.purchase.TW;

import android.util.Log;
import com.alipay.sdk.cons.c;
import com.popcap.SexyAppFramework.SexyAppFrameworkActivity;
import com.popcap.SexyAppFramework.ThirdpartyPurchaseDriver;
import com.talkweb.twOfflineSdk.TwOfflineSDK;
import com.talkweb.twOfflineSdk.bean.ExitResultBean;
import com.talkweb.twOfflineSdk.bean.InitResultBean;
import com.talkweb.twOfflineSdk.bean.LoginResultBean;
import com.talkweb.twOfflineSdk.bean.PayResultBean;
import com.talkweb.twOfflineSdk.callback.ReturnCode;
import com.talkweb.twOfflineSdk.callback.TwOfflineCallback;
import com.talkweb.twOfflineSdk.tools.Tools;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
class TWPurchase extends ThirdpartyPurchaseDriver {
    String mPurchaseCode;

    public native void FirePaymentComplete(long j, int i);

    public native void Native_ExitGame(long j);

    public TWPurchase(long nativeDriverPtr) {
        super(nativeDriverPtr);
        this.mPurchaseCode = "";
    }

    public void InitializeSDK(final String appid) {
        Log.v("TWPurchase", "TW_InitializeSDK");
        SexyAppFrameworkActivity.instance().runOnUiThread(new Runnable() { // from class: com.popcap.purchase.TW.TWPurchase.1
            @Override // java.lang.Runnable
            public void run() {
                TwOfflineSDK.init(SexyAppFrameworkActivity.instance(), appid, new TwOfflineCallback() { // from class: com.popcap.purchase.TW.TWPurchase.1.1
                    @Override // com.talkweb.twOfflineSdk.callback.TwOfflineCallback
                    public void onResponse(int eventCode, String result) {
                        System.out.println("onResponse result is " + result);
                        InitResultBean initResultBean = (InitResultBean) Tools.ToObject(result, InitResultBean.class);
                        switch (initResultBean.code) {
                            case 4000:
                                TwOfflineSDK.login(SexyAppFrameworkActivity.instance(), new TwOfflineCallback() { // from class: com.popcap.purchase.TW.TWPurchase.1.1.1
                                    /* JADX WARN: Failed to find 'out' block for switch in B:3:0x0022. Please report as an issue. */
                                    @Override // com.talkweb.twOfflineSdk.callback.TwOfflineCallback
                                    public void onResponse(int eventCode2, String result2) {
                                        System.out.println("onResponse result is " + result2);
                                        LoginResultBean loginResultBean = (LoginResultBean) Tools.ToObject(result2, LoginResultBean.class);
                                        switch (loginResultBean.code) {
                                        }
                                    }
                                });
                                break;
                        }
                    }
                });
            }
        });
    }

    public void OnExit() {
        Log.v("TWPurchase", "TW_OnExit");
        TwOfflineSDK.destory(SexyAppFrameworkActivity.instance(), new TwOfflineCallback() { // from class: com.popcap.purchase.TW.TWPurchase.2
            @Override // com.talkweb.twOfflineSdk.callback.TwOfflineCallback
            public void onResponse(int eventCode, String result) {
                System.out.println("onResponse result is " + result);
                ExitResultBean exitResultBean = (ExitResultBean) Tools.ToObject(result, ExitResultBean.class);
                switch (exitResultBean.code) {
                    case 5000:
                        TWPurchase.this.Native_ExitGame(TWPurchase.this.mNativeDriverPtr);
                        break;
                }
            }
        });
    }

    public void RequestPay(final String code) {
        Log.v("TWPurchase", "TW_RequestPay( " + code + " )");
        SexyAppFrameworkActivity.instance().runOnUiThread(new Runnable() { // from class: com.popcap.purchase.TW.TWPurchase.3
            @Override // java.lang.Runnable
            public void run() {
                TWPurchase.this.mPurchaseCode = code;
                String payCode = code;
                String orderNumber = UUID.randomUUID().toString().substring(0, 17);
                System.out.println("orderNumber is " + orderNumber);
                TwOfflineSDK.pay(payCode, orderNumber, SexyAppFrameworkActivity.instance(), new TwOfflineCallback() { // from class: com.popcap.purchase.TW.TWPurchase.3.1
                    @Override // com.talkweb.twOfflineSdk.callback.TwOfflineCallback
                    public void onResponse(int eventCode, String result) {
                        System.out.println("onResponse result is " + result);
                        PayResultBean payResultBean = (PayResultBean) Tools.ToObject(result, PayResultBean.class);
                        switch (payResultBean.code) {
                            case 1000:
                                TWPurchase.this.FirePaymentComplete(TWPurchase.this.mNativeDriverPtr, 1);
                                break;
                            case 2000:
                                TWPurchase.this.FirePaymentComplete(TWPurchase.this.mNativeDriverPtr, 2);
                                break;
                            case ReturnCode.PAY_MSG_SUCCESS /* 9999 */:
                                TWPurchase.this.FirePaymentComplete(TWPurchase.this.mNativeDriverPtr, 0);
                                break;
                            default:
                                TWPurchase.this.FirePaymentComplete(TWPurchase.this.mNativeDriverPtr, 1);
                                break;
                        }
                    }
                });
            }
        });
    }

    public String GetDeclare() {
        String msg = "";
        String msgList = TwOfflineSDK.getDeclareMsg();
        System.out.println(msgList);
        try {
            JSONArray msgArray = new JSONArray(msgList);
            for (int i = 0; i < msgArray.length(); i++) {
                JSONObject msgJson = (JSONObject) msgArray.get(i);
                System.out.println(msgJson.toString());
                if (msgJson.getInt("type") == 1) {
                    msg = msgJson.getString(c.b);
                }
            }
        } catch (JSONException e) {
            e.printStackTrace();
        }
        return msg;
    }
}
