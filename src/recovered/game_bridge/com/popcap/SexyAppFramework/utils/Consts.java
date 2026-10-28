package com.popcap.SexyAppFramework.utils;

import android.os.Bundle;
import java.util.Set;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class Consts {
    public static final String ACTION_BILLING_REQUEST = "com.popcap.framework.purchase.BILLING_REQUEST";
    public static final String ACTION_IN_APP_NOTIFY = "com.android.vending.billing.IN_APP_NOTIFY";
    public static final String ACTION_PURCHASE_STATE_CHANGED = "com.android.vending.billing.PURCHASE_STATE_CHANGED";
    public static final String ACTION_RESPONSE_CODE = "com.android.vending.billing.RESPONSE_CODE";
    public static final String BILLING_REQUEST_API_VERSION = "API_VERSION";
    public static final String BILLING_REQUEST_DEVELOPER_PAYLOAD = "DEVELOPER_PAYLOAD";
    public static final String BILLING_REQUEST_ITEM_ID = "ITEM_ID";
    public static final String BILLING_REQUEST_ITEM_TYPE = "ITEM_TYPE";
    public static final String BILLING_REQUEST_METHOD = "BILLING_REQUEST";
    public static final String BILLING_REQUEST_NONCE = "NONCE";
    public static final String BILLING_REQUEST_NOTIFY_IDS = "NOTIFY_IDS";
    public static final String BILLING_REQUEST_PACKAGE_NAME = "PACKAGE_NAME";
    public static long BILLING_RESPONSE_INVALID_REQUEST_ID = -1;
    public static final String BILLING_RESPONSE_PURCHASE_INTENT = "PURCHASE_INTENT";
    public static final String BILLING_RESPONSE_REQUEST_ID = "REQUEST_ID";
    public static final String BILLING_RESPONSE_RESPONSE_CODE = "RESPONSE_CODE";
    public static final boolean DEBUG = true;
    public static final String EXTRA_INAPP_SIGNATURE = "inapp_signature";
    public static final String EXTRA_INAPP_SIGNED_DATA = "inapp_signed_data";
    public static final String EXTRA_NOTIFICATION_ID = "notification_id";
    public static final String EXTRA_REQUEST_BUNDLE = "request_bundle";
    public static final String EXTRA_REQUEST_ID = "request_id";
    public static final String EXTRA_RESPONSE_CODE = "response_code";
    public static final String ITEM_TYPE_INAPP = "inapp";
    public static final String ITEM_TYPE_SUBSCRIPTION = "subs";
    public static final String MARKET_BILLING_SERVICE_ACTION = "com.android.vending.billing.MarketBillingService.BIND";

    enum BillingRequestMethod {
        CHECK_BILLING_SUPPORTED,
        REQUEST_PURCHASE,
        GET_PURCHASE_INFORMATION,
        CONFIRM_NOTIFICATIONS,
        RESTORE_TRANSACTIONS;

        public boolean equals(String s) {
            return s.equals(toString());
        }
    }

    public enum ResponseCode {
        RESULT_OK,
        RESULT_USER_CANCELED,
        RESULT_SERVICE_UNAVAILABLE,
        RESULT_BILLING_UNAVAILABLE,
        RESULT_ITEM_UNAVAILABLE,
        RESULT_DEVELOPER_ERROR,
        RESULT_ERROR;

        public static ResponseCode fromOrdinal(int ordinal) {
            ResponseCode[] values = values();
            return (ordinal < 0 || ordinal >= values.length) ? RESULT_ERROR : values[ordinal];
        }

        public boolean isOk() {
            return this == RESULT_OK;
        }

        public static boolean isOk(int ordinal) {
            return ordinal == RESULT_OK.ordinal();
        }
    }

    public static String formatBundle(Bundle bundle) {
        StringBuilder builder = new StringBuilder("{ ");
        if (bundle != null && !bundle.isEmpty()) {
            Set<String> keys = bundle.keySet();
            for (String key : keys) {
                builder.append(String.format("\"%s\": %s, ", key, bundle.get(key).toString()));
            }
        }
        builder.append("}");
        return builder.toString();
    }

    public static String formatArray(String[] array) {
        StringBuilder builder = new StringBuilder("[ ");
        if (array != null) {
            for (String s : array) {
                builder.append(String.format("\"%s\", ", s));
            }
        }
        builder.append("]");
        return builder.toString();
    }
}
