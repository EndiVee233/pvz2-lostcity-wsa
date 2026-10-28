package com.popcap.SexyAppFramework.utils;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentSender;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import android.os.RemoteException;
import android.text.TextUtils;
import android.util.Log;
import com.android.vending.billing.IInAppBillingService;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class IabHelper {
    public static final int BILLING_RESPONSE_RESULT_BILLING_UNAVAILABLE = 3;
    public static final int BILLING_RESPONSE_RESULT_DEVELOPER_ERROR = 5;
    public static final int BILLING_RESPONSE_RESULT_ERROR = 6;
    public static final int BILLING_RESPONSE_RESULT_ITEM_ALREADY_OWNED = 7;
    public static final int BILLING_RESPONSE_RESULT_ITEM_NOT_OWNED = 8;
    public static final int BILLING_RESPONSE_RESULT_ITEM_UNAVAILABLE = 4;
    public static final int BILLING_RESPONSE_RESULT_OK = 0;
    public static final int BILLING_RESPONSE_RESULT_USER_CANCELED = 1;
    public static final String GET_SKU_DETAILS_ITEM_LIST = "ITEM_ID_LIST";
    public static final String GET_SKU_DETAILS_ITEM_TYPE_LIST = "ITEM_TYPE_LIST";
    public static final int IABHELPER_BAD_RESPONSE = -1002;
    public static final int IABHELPER_ERROR_BASE = -1000;
    public static final int IABHELPER_MISSING_TOKEN = -1007;
    public static final int IABHELPER_REMOTE_EXCEPTION = -1001;
    public static final int IABHELPER_SEND_INTENT_FAILED = -1004;
    public static final int IABHELPER_UNKNOWN_ERROR = -1008;
    public static final int IABHELPER_UNKNOWN_PURCHASE_RESPONSE = -1006;
    public static final int IABHELPER_USER_CANCELLED = -1005;
    public static final int IABHELPER_VERIFICATION_FAILED = -1003;
    public static final String INAPP_CONTINUATION_TOKEN = "INAPP_CONTINUATION_TOKEN";
    public static final String ITEM_TYPE_INAPP = "inapp";
    public static final String RESPONSE_BUY_INTENT = "BUY_INTENT";
    public static final String RESPONSE_CODE = "RESPONSE_CODE";
    public static final String RESPONSE_GET_SKU_DETAILS_LIST = "DETAILS_LIST";
    public static final String RESPONSE_INAPP_ITEM_LIST = "INAPP_PURCHASE_ITEM_LIST";
    public static final String RESPONSE_INAPP_PURCHASE_DATA = "INAPP_PURCHASE_DATA";
    public static final String RESPONSE_INAPP_PURCHASE_DATA_LIST = "INAPP_PURCHASE_DATA_LIST";
    public static final String RESPONSE_INAPP_SIGNATURE = "INAPP_DATA_SIGNATURE";
    public static final String RESPONSE_INAPP_SIGNATURE_LIST = "INAPP_DATA_SIGNATURE_LIST";
    Context mContext;
    OnIabPurchaseFinishedListener mPurchaseListener;
    int mRequestCode;
    IInAppBillingService mService;
    ServiceConnection mServiceConn;
    String mSignatureBase64;
    boolean mDebugLog = false;
    String mDebugTag = "IabHelper";
    boolean mSetupDone = false;
    boolean mAsyncInProgress = false;
    String mAsyncOperation = "";

    public interface OnConsumeFinishedListener {
        void onConsumeFinished(Purchase purchase, IabResult iabResult);
    }

    public interface OnConsumeMultiFinishedListener {
        void onConsumeMultiFinished(List<Purchase> list, List<IabResult> list2);
    }

    public interface OnIabPurchaseFinishedListener {
        void onIabPurchaseFinished(IabResult iabResult, Purchase purchase);
    }

    public interface OnIabSetupFinishedListener {
        void onIabSetupFinished(IabResult iabResult);
    }

    public interface QueryInventoryFinishedListener {
        void onQueryInventoryFinished(IabResult iabResult, Inventory inventory);
    }

    public IabHelper(Context ctx, String base64PublicKey) {
        this.mSignatureBase64 = null;
        this.mContext = ctx.getApplicationContext();
        this.mSignatureBase64 = base64PublicKey;
        logDebug("IAB helper created.");
    }

    public void enableDebugLogging(boolean enable, String tag) {
        this.mDebugLog = enable;
        this.mDebugTag = tag;
    }

    public void enableDebugLogging(boolean enable) {
        this.mDebugLog = enable;
    }

    public void startSetup(final OnIabSetupFinishedListener listener) {
        if (this.mSetupDone) {
            throw new IllegalStateException("IAB helper is already set up.");
        }
        logDebug("Starting in-app billing setup.");
        this.mServiceConn = new ServiceConnection() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.1
            @Override // android.content.ServiceConnection
            public void onServiceDisconnected(ComponentName name) {
                IabHelper.this.logDebug("Billing service disconnected.");
                IabHelper.this.mService = null;
            }

            @Override // android.content.ServiceConnection
            public void onServiceConnected(ComponentName name, IBinder service) {
                IabHelper.this.logDebug("Billing service connected.");
                IabHelper.this.mService = IInAppBillingService.Stub.asInterface(service);
                String packageName = IabHelper.this.mContext.getPackageName();
                try {
                    IabHelper.this.logDebug("Checking for in-app billing 3 support.");
                    int response = IabHelper.this.mService.isBillingSupported(3, packageName, "inapp");
                    if (response != 0) {
                        if (listener != null) {
                            listener.onIabSetupFinished(new IabResult(response, "Error checking for billing v3 support."));
                        }
                    } else {
                        IabHelper.this.logDebug("In-app billing version 3 supported for " + packageName);
                        IabHelper.this.mSetupDone = true;
                        if (listener != null) {
                            listener.onIabSetupFinished(new IabResult(0, "Setup successful."));
                        }
                    }
                } catch (RemoteException e) {
                    if (listener != null) {
                        listener.onIabSetupFinished(new IabResult(IabHelper.IABHELPER_REMOTE_EXCEPTION, "RemoteException while setting up in-app billing."));
                    }
                    e.printStackTrace();
                }
            }
        };
        this.mContext.bindService(new Intent("com.android.vending.billing.InAppBillingService.BIND"), this.mServiceConn, 1);
    }

    public void dispose() {
        logDebug("Disposing.");
        this.mSetupDone = false;
        if (this.mServiceConn != null) {
            logDebug("Unbinding from service.");
            if (this.mContext != null) {
                this.mContext.unbindService(this.mServiceConn);
            }
            this.mServiceConn = null;
            this.mService = null;
            this.mPurchaseListener = null;
        }
    }

    public void launchPurchaseFlow(Activity act, String sku, int requestCode, OnIabPurchaseFinishedListener listener) {
        launchPurchaseFlow(act, sku, requestCode, listener, "");
    }

    public void launchPurchaseFlow(Activity act, String sku, int requestCode, OnIabPurchaseFinishedListener listener, String extraData) {
        checkSetupDone("launchPurchaseFlow");
        flagStartAsync("launchPurchaseFlow");
        try {
            logDebug("Constructing buy intent for " + sku);
            Bundle buyIntentBundle = this.mService.getBuyIntent(3, this.mContext.getPackageName(), sku, "inapp", extraData);
            int response = getResponseCodeFromBundle(buyIntentBundle);
            if (response != 0) {
                logError("Unable to buy item, Error response: " + getResponseDesc(response));
                IabResult result = new IabResult(response, "Unable to buy item");
                if (listener != null) {
                    listener.onIabPurchaseFinished(result, null);
                }
                flagEndAsync();
                return;
            }
            PendingIntent pendingIntent = (PendingIntent) buyIntentBundle.getParcelable(RESPONSE_BUY_INTENT);
            logDebug("Launching buy intent for " + sku + ". Request code: " + requestCode);
            this.mRequestCode = requestCode;
            this.mPurchaseListener = listener;
            IntentSender intentSender = pendingIntent.getIntentSender();
            Intent intent = new Intent();
            Integer num = 0;
            int iIntValue = num.intValue();
            Integer num2 = 0;
            int iIntValue2 = num2.intValue();
            Integer num3 = 0;
            act.startIntentSenderForResult(intentSender, requestCode, intent, iIntValue, iIntValue2, num3.intValue());
        } catch (IntentSender.SendIntentException e) {
            logError("SendIntentException while launching purchase flow for sku " + sku);
            e.printStackTrace();
            IabResult result2 = new IabResult(IABHELPER_SEND_INTENT_FAILED, "Failed to send intent.");
            if (listener != null) {
                listener.onIabPurchaseFinished(result2, null);
            }
        } catch (RemoteException e2) {
            logError("RemoteException while launching purchase flow for sku " + sku);
            e2.printStackTrace();
            IabResult result3 = new IabResult(IABHELPER_REMOTE_EXCEPTION, "Remote exception while starting purchase flow");
            if (listener != null) {
                listener.onIabPurchaseFinished(result3, null);
            }
        }
    }

    public boolean handleActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode != this.mRequestCode) {
            return false;
        }
        checkSetupDone("handleActivityResult");
        flagEndAsync();
        if (data == null) {
            logError("Null data in IAB activity result.");
            IabResult result = new IabResult(IABHELPER_BAD_RESPONSE, "Null data in IAB result");
            if (this.mPurchaseListener != null) {
                this.mPurchaseListener.onIabPurchaseFinished(result, null);
            }
            return true;
        }
        int responseCode = getResponseCodeFromIntent(data);
        String purchaseData = data.getStringExtra(RESPONSE_INAPP_PURCHASE_DATA);
        String dataSignature = data.getStringExtra(RESPONSE_INAPP_SIGNATURE);
        if (resultCode == -1 && responseCode == 0) {
            logDebug("Successful resultcode from purchase activity.");
            logDebug("Purchase data: " + purchaseData);
            logDebug("Data signature: " + dataSignature);
            logDebug("Extras: " + data.getExtras());
            if (purchaseData == null || dataSignature == null) {
                logError("BUG: either purchaseData or dataSignature is null.");
                logDebug("Extras: " + data.getExtras().toString());
                IabResult result2 = new IabResult(IABHELPER_UNKNOWN_ERROR, "IAB returned null purchaseData or dataSignature");
                if (this.mPurchaseListener != null) {
                    this.mPurchaseListener.onIabPurchaseFinished(result2, null);
                }
                return true;
            }
            try {
                Purchase purchase = new Purchase(purchaseData, dataSignature);
                    String sku = purchase.getSku();
                    if (!Security.verifyPurchase(this.mSignatureBase64, purchaseData, dataSignature)) {
                        logError("Purchase signature verification FAILED for sku " + sku);
                        IabResult result3 = new IabResult(IABHELPER_VERIFICATION_FAILED, "Signature verification failed for sku " + sku);
                        if (this.mPurchaseListener != null) {
                            this.mPurchaseListener.onIabPurchaseFinished(result3, purchase);
                        }
                        return true;
                    }
                    logDebug("Purchase signature successfully verified.");
                    if (this.mPurchaseListener != null) {
                        this.mPurchaseListener.onIabPurchaseFinished(new IabResult(0, "Success"), purchase);
                    }
            } catch (JSONException e) {
                    logError("Failed to parse purchase data.");
                    e.printStackTrace();
                    IabResult result4 = new IabResult(IABHELPER_BAD_RESPONSE, "Failed to parse purchase data.");
                    if (this.mPurchaseListener != null) {
                        this.mPurchaseListener.onIabPurchaseFinished(result4, null);
                    }
                    return true;
            }
        } else if (resultCode == -1) {
            logDebug("Result code was OK but in-app billing response was not OK: " + getResponseDesc(responseCode));
            if (this.mPurchaseListener != null) {
                IabResult result5 = new IabResult(responseCode, "Problem purchashing item.");
                this.mPurchaseListener.onIabPurchaseFinished(result5, null);
            }
        } else if (resultCode == 0) {
            logDebug("Purchase canceled - Response: " + getResponseDesc(responseCode));
            IabResult result6 = new IabResult(IABHELPER_USER_CANCELLED, "User canceled.");
            if (this.mPurchaseListener != null) {
                this.mPurchaseListener.onIabPurchaseFinished(result6, null);
            }
        } else {
            logError("Purchase failed. Result code: " + Integer.toString(resultCode) + ". Response: " + getResponseDesc(responseCode));
            IabResult result7 = new IabResult(IABHELPER_UNKNOWN_PURCHASE_RESPONSE, "Unknown purchase response.");
            if (this.mPurchaseListener != null) {
                this.mPurchaseListener.onIabPurchaseFinished(result7, null);
            }
        }
        return true;
    }

    public Inventory queryInventory(boolean querySkuDetails, List<String> moreSkus) throws IabException {
        int r;
        checkSetupDone("queryInventory");
        try {
            Inventory inv = new Inventory();
            int r2 = queryPurchases(inv);
            if (r2 != 0) {
                throw new IabException(r2, "Error refreshing inventory (querying owned items).");
            }
            if (querySkuDetails && (r = querySkuDetails(inv, moreSkus)) != 0) {
                throw new IabException(r, "Error refreshing inventory (querying prices of items).");
            }
            return inv;
        } catch (RemoteException e) {
            throw new IabException(IABHELPER_REMOTE_EXCEPTION, "Remote exception while refreshing inventory.", e);
        } catch (JSONException e2) {
            throw new IabException(IABHELPER_BAD_RESPONSE, "Error parsing JSON response while refreshing inventory.", e2);
        }
    }

    public void queryInventoryAsync(final boolean querySkuDetails, final List<String> moreSkus, final QueryInventoryFinishedListener listener) {
        final Handler handler = new Handler();
        checkSetupDone("queryInventory");
        flagStartAsync("refresh inventory");
        new Thread(new Runnable() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.2
            @Override // java.lang.Runnable
            public void run() {
                IabResult result = new IabResult(0, "Inventory refresh successful.");
                Inventory inv = null;
                try {
                    inv = IabHelper.this.queryInventory(querySkuDetails, moreSkus);
                } catch (IabException ex) {
                    result = ex.getResult();
                }
                IabHelper.this.flagEndAsync();
                final IabResult result_f = result;
                final Inventory inv_f = inv;
                handler.post(new Runnable() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.2.1
                    @Override // java.lang.Runnable
                    public void run() {
                        listener.onQueryInventoryFinished(result_f, inv_f);
                    }
                });
            }
        }).start();
    }

    public void queryInventoryAsync(QueryInventoryFinishedListener listener) {
        queryInventoryAsync(true, null, listener);
    }

    public void queryInventoryAsync(boolean querySkuDetails, QueryInventoryFinishedListener listener) {
        queryInventoryAsync(querySkuDetails, null, listener);
    }

    public void consume(Purchase itemInfo) throws IabException {
        checkSetupDone("consume");
        try {
            String token = itemInfo.getToken();
            String sku = itemInfo.getSku();
            if (token == null || token.equals("")) {
                logError("Can't consume " + sku + ". No token.");
                throw new IabException(IABHELPER_MISSING_TOKEN, "PurchaseInfo is missing token for sku: " + sku + " " + itemInfo);
            }
            logDebug("Consuming sku: " + sku + ", token: " + token);
            int response = this.mService.consumePurchase(3, this.mContext.getPackageName(), token);
            if (response == 0) {
                logDebug("Successfully consumed sku: " + sku);
            } else {
                logDebug("Error consuming consuming sku " + sku + ". " + getResponseDesc(response));
                throw new IabException(response, "Error consuming sku " + sku);
            }
        } catch (RemoteException e) {
            throw new IabException(IABHELPER_REMOTE_EXCEPTION, "Remote exception while consuming. PurchaseInfo: " + itemInfo, e);
        }
    }

    public void consumeAsync(Purchase purchase, OnConsumeFinishedListener listener) {
        checkSetupDone("consume");
        List<Purchase> purchases = new ArrayList<>();
        purchases.add(purchase);
        consumeAsyncInternal(purchases, listener, null);
    }

    public void consumeAsync(List<Purchase> purchases, OnConsumeMultiFinishedListener listener) {
        checkSetupDone("consume");
        consumeAsyncInternal(purchases, null, listener);
    }

    public static String getResponseDesc(int code) {
        String[] iab_msgs = "0:OK/1:User Canceled/2:Unknown/3:Billing Unavailable/4:Item unavailable/5:Developer Error/6:Error/7:Item Already Owned/8:Item not owned".split("/");
        String[] iabhelper_msgs = "0:OK/-1001:Remote exception during initialization/-1002:Bad response received/-1003:Purchase signature verification failed/-1004:Send intent failed/-1005:User cancelled/-1006:Unknown purchase response/-1007:Missing token/-1008:Unknown error".split("/");
        if (code <= -1000) {
            int index = (-1000) - code;
            return (index < 0 || index >= iabhelper_msgs.length) ? String.valueOf(code) + ":Unknown IAB Helper Error" : iabhelper_msgs[index];
        }
        if (code < 0 || code >= iab_msgs.length) {
            return String.valueOf(code) + ":Unknown";
        }
        return iab_msgs[code];
    }

    void checkSetupDone(String operation) {
        if (!this.mSetupDone) {
            logError("Illegal state for operation (" + operation + "): IAB helper is not set up.");
            throw new IllegalStateException("IAB helper is not set up. Can't perform operation: " + operation);
        }
    }

    int getResponseCodeFromBundle(Bundle b) {
        Object o = b.get("RESPONSE_CODE");
        if (o == null) {
            logDebug("Bundle with null response code, assuming OK (known issue)");
            return 0;
        }
        if (o instanceof Integer) {
            return ((Integer) o).intValue();
        }
        if (o instanceof Long) {
            return (int) ((Long) o).longValue();
        }
        logError("Unexpected type for bundle response code.");
        logError(o.getClass().getName());
        throw new RuntimeException("Unexpected type for bundle response code: " + o.getClass().getName());
    }

    int getResponseCodeFromIntent(Intent i) {
        Object o = i.getExtras().get("RESPONSE_CODE");
        if (o == null) {
            logError("Intent with no response code, assuming OK (known issue)");
            return 0;
        }
        if (o instanceof Integer) {
            return ((Integer) o).intValue();
        }
        if (o instanceof Long) {
            return (int) ((Long) o).longValue();
        }
        logError("Unexpected type for intent response code.");
        logError(o.getClass().getName());
        throw new RuntimeException("Unexpected type for intent response code: " + o.getClass().getName());
    }

    void flagStartAsync(String operation) {
        if (this.mAsyncInProgress) {
            throw new IllegalStateException("Can't start async operation (" + operation + ") because another async operation(" + this.mAsyncOperation + ") is in progress.");
        }
        this.mAsyncOperation = operation;
        this.mAsyncInProgress = true;
        logDebug("Starting async operation: " + operation);
    }

    void flagEndAsync() {
        logDebug("Ending async operation: " + this.mAsyncOperation);
        this.mAsyncOperation = "";
        this.mAsyncInProgress = false;
    }

    int queryPurchases(Inventory inv) throws JSONException, RemoteException {
        logDebug("Querying owned items...");
        logDebug("Package name: " + this.mContext.getPackageName());
        boolean verificationFailed = false;
        String continueToken = null;
        do {
            logDebug("Calling getPurchases with continuation token: " + continueToken);
            Bundle ownedItems = this.mService.getPurchases(3, this.mContext.getPackageName(), "inapp", continueToken);
            int response = getResponseCodeFromBundle(ownedItems);
            logDebug("Owned items response: " + String.valueOf(response));
            if (response != 0) {
                logDebug("getPurchases() failed: " + getResponseDesc(response));
                return response;
            }
            if (!ownedItems.containsKey(RESPONSE_INAPP_ITEM_LIST) || !ownedItems.containsKey(RESPONSE_INAPP_PURCHASE_DATA_LIST) || !ownedItems.containsKey(RESPONSE_INAPP_SIGNATURE_LIST)) {
                logError("Bundle returned from getPurchases() doesn't contain required fields.");
                return IABHELPER_BAD_RESPONSE;
            }
            ArrayList<String> ownedSkus = ownedItems.getStringArrayList(RESPONSE_INAPP_ITEM_LIST);
            ArrayList<String> purchaseDataList = ownedItems.getStringArrayList(RESPONSE_INAPP_PURCHASE_DATA_LIST);
            ArrayList<String> signatureList = ownedItems.getStringArrayList(RESPONSE_INAPP_SIGNATURE_LIST);
            for (int i = 0; i < purchaseDataList.size(); i++) {
                String purchaseData = purchaseDataList.get(i);
                String signature = signatureList.get(i);
                String sku = ownedSkus.get(i);
                if (Security.verifyPurchase(this.mSignatureBase64, purchaseData, signature)) {
                    logDebug("Sku is owned: " + sku);
                    Purchase purchase = new Purchase(purchaseData, signature);
                    if (TextUtils.isEmpty(purchase.getToken())) {
                        logWarn("BUG: empty/null token!");
                        logDebug("Purchase data: " + purchaseData);
                    }
                    inv.addPurchase(purchase);
                } else {
                    logWarn("Purchase signature verification **FAILED**. Not adding item.");
                    logDebug("   Purchase data: " + purchaseData);
                    logDebug("   Signature: " + signature);
                    verificationFailed = true;
                }
            }
            continueToken = ownedItems.getString(INAPP_CONTINUATION_TOKEN);
            logDebug("Continuation token: " + continueToken);
        } while (!TextUtils.isEmpty(continueToken));
        return verificationFailed ? IABHELPER_VERIFICATION_FAILED : 0;
    }

    int querySkuDetails(Inventory inv, List<String> moreSkus) throws JSONException, RemoteException {
        logDebug("Querying SKU details.");
        ArrayList<String> skuList = new ArrayList<>();
        skuList.addAll(inv.getAllOwnedSkus());
        if (moreSkus != null) {
            skuList.addAll(moreSkus);
        }
        if (skuList.size() == 0) {
            logDebug("queryPrices: nothing to do because there are no SKUs.");
            return 0;
        }
        Bundle querySkus = new Bundle();
        querySkus.putStringArrayList(GET_SKU_DETAILS_ITEM_LIST, skuList);
        Bundle skuDetails = this.mService.getSkuDetails(3, this.mContext.getPackageName(), "inapp", querySkus);
        if (!skuDetails.containsKey(RESPONSE_GET_SKU_DETAILS_LIST)) {
            int response = getResponseCodeFromBundle(skuDetails);
            if (response != 0) {
                logDebug("getSkuDetails() failed: " + getResponseDesc(response));
                return response;
            }
            logError("getSkuDetails() returned a bundle with neither an error nor a detail list.");
            return IABHELPER_BAD_RESPONSE;
        }
        ArrayList<String> responseList = skuDetails.getStringArrayList(RESPONSE_GET_SKU_DETAILS_LIST);
        for (String thisResponse : responseList) {
            SkuDetails d = new SkuDetails(thisResponse);
            logDebug("Got sku details: " + d);
            inv.addSkuDetails(d);
        }
        return 0;
    }

    void consumeAsyncInternal(final List<Purchase> purchases, final OnConsumeFinishedListener singleListener, final OnConsumeMultiFinishedListener multiListener) {
        final Handler handler = new Handler();
        flagStartAsync("consume");
        new Thread(new Runnable() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.3
            @Override // java.lang.Runnable
            public void run() {
                final List<IabResult> results = new ArrayList<>();
                for (Purchase purchase : purchases) {
                    try {
                        IabHelper.this.consume(purchase);
                        results.add(new IabResult(0, "Successful consume of sku " + purchase.getSku()));
                    } catch (IabException ex) {
                        results.add(ex.getResult());
                    }
                }
                IabHelper.this.flagEndAsync();
                if (singleListener != null) {
                    handler.post(new Runnable() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.3.1
                        @Override // java.lang.Runnable
                        public void run() {
                            singleListener.onConsumeFinished((Purchase) purchases.get(0), (IabResult) results.get(0));
                        }
                    });
                }
                if (multiListener != null) {
                    handler.post(new Runnable() { // from class: com.popcap.SexyAppFramework.utils.IabHelper.3.2
                        @Override // java.lang.Runnable
                        public void run() {
                            multiListener.onConsumeMultiFinished(purchases, results);
                        }
                    });
                }
            }
        }).start();
    }

    void logDebug(String msg) {
        if (this.mDebugLog) {
            Log.d(this.mDebugTag, msg);
        }
    }

    void logError(String msg) {
        Log.e(this.mDebugTag, "In-app billing error: " + msg);
    }

    void logWarn(String msg) {
        Log.w(this.mDebugTag, "In-app billing warning: " + msg);
    }
}
