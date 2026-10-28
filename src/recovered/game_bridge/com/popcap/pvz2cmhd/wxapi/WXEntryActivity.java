package com.popcap.pvz2cmhd.wxapi;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import com.popcap.SexyAppFramework.WechatPlatform;
import com.tencent.mm.sdk.modelbase.BaseReq;
import com.tencent.mm.sdk.modelbase.BaseResp;
import com.tencent.mm.sdk.openapi.IWXAPI;
import com.tencent.mm.sdk.openapi.IWXAPIEventHandler;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class WXEntryActivity extends Activity implements IWXAPIEventHandler {
    private IWXAPI api;

    @Override // android.app.Activity
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.i("WechatTest", "TestInit");
        initData();
    }

    @Override // android.app.Activity
    protected void onNewIntent(Intent intent) {
        Log.i("WechatTest", "TestIntent");
        super.onNewIntent(intent);
        setIntent(intent);
        initData();
    }

    private void initData() {
        this.api = WechatPlatform.getIWXAPI();
        this.api.handleIntent(getIntent(), this);
    }

    @Override // com.tencent.mm.sdk.openapi.IWXAPIEventHandler
    public void onReq(BaseReq req) {
    }

    @Override // com.tencent.mm.sdk.openapi.IWXAPIEventHandler
    public void onResp(BaseResp resp) {
        WechatPlatform.FinishShare(resp.errCode);
        finish();
    }
}
