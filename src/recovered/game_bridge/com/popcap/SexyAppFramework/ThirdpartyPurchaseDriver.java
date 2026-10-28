package com.popcap.SexyAppFramework;

import android.telephony.TelephonyManager;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class ThirdpartyPurchaseDriver {
    public static final int BILLING_RESULT_ALREADY_PAID = 3;
    public static final int BILLING_RESULT_CANCELED = 2;
    public static final int BILLING_RESULT_FAILED = 1;
    public static final int BILLING_RESULT_SUCCESS = 0;
    public long mNativeDriverPtr;

    public ThirdpartyPurchaseDriver(long nativeDriverPtr) {
        this.mNativeDriverPtr = nativeDriverPtr;
    }

    public String GetIMSI() {
        return "460001234567890";
    }

    public String GetSimSerialNumber() {
        TelephonyManager mTelephonyMgr = (TelephonyManager) SexyAppFrameworkActivity.instance().getSystemService("phone");
        return DreamRootPath.getSimSerialNumber(mTelephonyMgr);
    }
}
