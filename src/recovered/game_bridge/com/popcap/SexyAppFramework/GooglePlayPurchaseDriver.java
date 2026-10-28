package com.popcap.SexyAppFramework;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import com.popcap.SexyAppFramework.utils.Base64;
import com.popcap.SexyAppFramework.utils.IabHelper;
import com.popcap.SexyAppFramework.utils.IabResult;
import com.popcap.SexyAppFramework.utils.Inventory;
import com.popcap.SexyAppFramework.utils.Purchase;
import com.popcap.SexyAppFramework.utils.SkuDetails;
import java.io.UnsupportedEncodingException;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Queue;
import org.json.JSONException;
import org.json.JSONObject;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class GooglePlayPurchaseDriver {
    private static final String TAG = "Billing.Driver";
    private IabHelper mIabHelper;
    private long mNativeDriverPtr;
    private final int RC_REQUEST = 9216358;
    private SupportStatus mPaymentsStatus = SupportStatus.UNKNOWN;
    private HashMap<String, Purchase> mUnconsumedPurchases = new HashMap<>();
    private Queue<PendingOperation> pendingOperations = new LinkedList();
    public GooglePlayPurchaseDriver(long nativeDriverPtr, String publicKey) {
        this.mNativeDriverPtr = nativeDriverPtr;
        SexyAppFrameworkActivity.instance().addOnActivityResultListener(this.mOnActivityResultListener);
        Context context = SexyAppFrameworkActivity.instance();
        this.mIabHelper = new IabHelper(context, publicKey);
        this.mIabHelper.startSetup(this.mOnIabSetupFinishedListener);
    }

    private void startOperation(final Runnable runnable, final String name) {
        Log.v(TAG, String.format("StartOperation: %s", name));
        Activity activity = SexyAppFrameworkActivity.instance();
        activity.runOnUiThread(new Runnable() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.1
            @Override // java.lang.Runnable
            public void run() {
                PendingOperation operation = GooglePlayPurchaseDriver.this.new PendingOperation(runnable, name);
                boolean run = GooglePlayPurchaseDriver.this.pendingOperations.peek() == null;
                GooglePlayPurchaseDriver.this.pendingOperations.offer(operation);
                if (run) {
                    operation.getOperation().run();
                } else {
                    Log.v(GooglePlayPurchaseDriver.TAG, String.format("operation %s queued; %s is currently running", name, ((PendingOperation) GooglePlayPurchaseDriver.this.pendingOperations.peek()).getName()));
                }
            }
        });
    }

    private IabHelper.OnIabSetupFinishedListener mOnIabSetupFinishedListener = new IabHelper.OnIabSetupFinishedListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.2
        @Override // com.popcap.SexyAppFramework.utils.IabHelper.OnIabSetupFinishedListener
        public void onIabSetupFinished(IabResult result) {
            if (result.isSuccess()) {
                if (GooglePlayPurchaseDriver.this.mPaymentsStatus == SupportStatus.UNKNOWN) {
                    Log.v(GooglePlayPurchaseDriver.TAG, "Setup succeeded, looking for pending transactions");
                    GooglePlayPurchaseDriver.this.mIabHelper.queryInventoryAsync(false, null, GooglePlayPurchaseDriver.this.mOnSetupInventoryFinishedListener);
                }
                GooglePlayPurchaseDriver.this.mPaymentsStatus = SupportStatus.SUPPORTED;
                return;
            }
            Log.v(GooglePlayPurchaseDriver.TAG, "Setup failed: " + result);
            GooglePlayPurchaseDriver.this.mPaymentsStatus = SupportStatus.UNSUPPORTED;
        }
    };
    private IabHelper.QueryInventoryFinishedListener mOnSetupInventoryFinishedListener = new IabHelper.QueryInventoryFinishedListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.3
        @Override // com.popcap.SexyAppFramework.utils.IabHelper.QueryInventoryFinishedListener
        public void onQueryInventoryFinished(IabResult result, Inventory inventory) {
            GooglePlayPurchaseDriver.this.mPaymentsStatus = SupportStatus.SUPPORTED;
            if (result.isSuccess()) {
                for (Purchase info : inventory.getAllPurchases()) {
                    GooglePlayPurchaseDriver.this.CallPaymentCompleteHook(info);
                }
            }
            Log.v(GooglePlayPurchaseDriver.TAG, "Setup completed");
        }
    };


    public void Refresh(final String[] skus) {
        Log.v(TAG, "Refresh()");
        if (!CanMakePayments()) {
            FireDidRefresh(this.mNativeDriverPtr, null);
        } else {
            startOperation(new Runnable() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.4
                @Override // java.lang.Runnable
                public void run() {
                    GooglePlayPurchaseDriver.this.mIabHelper.queryInventoryAsync(true, Arrays.asList(skus), GooglePlayPurchaseDriver.this.mQueryInventoryFinishedListener);
                }
            }, "queryInventoryAsync");
        }
    }

    private IabHelper.QueryInventoryFinishedListener mQueryInventoryFinishedListener = new IabHelper.QueryInventoryFinishedListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.5
        @Override // com.popcap.SexyAppFramework.utils.IabHelper.QueryInventoryFinishedListener
        public void onQueryInventoryFinished(IabResult result, Inventory inventory) {
            if (!result.isSuccess()) {
                GooglePlayPurchaseDriver.this.FireDidRefresh(GooglePlayPurchaseDriver.this.mNativeDriverPtr, null);
            } else {
                for (Purchase info : inventory.getAllPurchases()) {
                    GooglePlayPurchaseDriver.this.CallPaymentCompleteHook(info);
                }
                Collection<SkuDetails> skus = inventory.getAllSkuDetails();
                GooglePlayPurchaseDriver.this.FireDidRefresh(GooglePlayPurchaseDriver.this.mNativeDriverPtr, (SkuDetails[]) skus.toArray(new SkuDetails[0]));
            }
            GooglePlayPurchaseDriver.this.finishOperation("queryInventoryAsync");
        }
    };
    private SexyAppFrameworkActivity.OnActivityResultListener mOnActivityResultListener = new SexyAppFrameworkActivity.OnActivityResultListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.6
        @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity.OnActivityResultListener
        public void onActivityResult(int requestCode, int resultCode, Intent data) {
            Log.v(GooglePlayPurchaseDriver.TAG, String.format("SexyAppFrameworkActivity.OnActivityResultListener %d %d %s", Integer.valueOf(requestCode), Integer.valueOf(resultCode), data));
            GooglePlayPurchaseDriver.this.mIabHelper.handleActivityResult(requestCode, resultCode, data);
        }
    };


    public void RequestPayment(final String productId) {
        Log.v(TAG, String.format("RequestPayment( %s )", productId));
        if (!CanMakePayments()) {
            Log.v(TAG, String.format("RequestPayment( %s ) - cannot make payments", productId));
            FirePaymentIncomplete(this.mNativeDriverPtr, productId, CauseForIncompletion.ServiceUnavailable.ordinal());
        } else {
            final Activity activity = SexyAppFrameworkActivity.instance();
            startOperation(new Runnable() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.7
                @Override // java.lang.Runnable
                public void run() {
                    GooglePlayPurchaseDriver.this.mIabHelper.launchPurchaseFlow(activity, productId, 9216358, GooglePlayPurchaseDriver.this.mOnIabPurchaseFinishedListener);
                }
            }, "launchPurchaseFlow");
        }
    }

    private IabHelper.OnIabPurchaseFinishedListener mOnIabPurchaseFinishedListener = new IabHelper.OnIabPurchaseFinishedListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.8
        @Override // com.popcap.SexyAppFramework.utils.IabHelper.OnIabPurchaseFinishedListener
        public void onIabPurchaseFinished(IabResult result, Purchase info) {
            CauseForIncompletion cause;
            if (result.isSuccess()) {
                Log.v(GooglePlayPurchaseDriver.TAG, "purchaseFinished completed");
                if (!GooglePlayPurchaseDriver.this.CallPaymentCompleteHook(info)) {
                    GooglePlayPurchaseDriver.this.FirePaymentIncomplete(GooglePlayPurchaseDriver.this.mNativeDriverPtr, info.getSku(), CauseForIncompletion.Error.ordinal());
                }
            } else {
                CauseForIncompletion causeForIncompletion = CauseForIncompletion.Error;
                switch (result.getResponse()) {
                    case IabHelper.IABHELPER_USER_CANCELLED /* -1005 */:
                    case 1:
                        cause = CauseForIncompletion.Canceled;
                        break;
                    case 7:
                        cause = CauseForIncompletion.Pending;
                        break;
                    default:
                        cause = CauseForIncompletion.Error;
                        break;
                }
                Log.v(GooglePlayPurchaseDriver.TAG, String.format("purchaseFinished failed %d", Integer.valueOf(cause.ordinal())));
                String sku = "";
                if (info != null && info.getSku() != null) {
                    sku = info.getSku();
                }
                GooglePlayPurchaseDriver.this.FirePaymentIncomplete(GooglePlayPurchaseDriver.this.mNativeDriverPtr, sku, cause.ordinal());
            }
            GooglePlayPurchaseDriver.this.finishOperation("launchPurchaseFlow");
        }
    };


    private IabHelper.OnConsumeFinishedListener mOnConsumeFinishedListener = new IabHelper.OnConsumeFinishedListener() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.9
        @Override // com.popcap.SexyAppFramework.utils.IabHelper.OnConsumeFinishedListener
        public void onConsumeFinished(Purchase purchase, IabResult result) {
            if (result.isSuccess()) {
                Log.v(GooglePlayPurchaseDriver.TAG, String.format("ConfirmDelivery: %s %s", purchase.toString(), result.toString()));
                GooglePlayPurchaseDriver.this.mUnconsumedPurchases.remove(purchase.getToken());
            } else {
                Log.v(GooglePlayPurchaseDriver.TAG, "ConfirmDelivery failed");
            }
            GooglePlayPurchaseDriver.this.finishOperation("consumeAsync");
        }
    };

    native void FireDidRefresh(long j, SkuDetails[] skuDetailsArr);

    native void FirePaymentComplete(long j, String str, String str2);

    native void FirePaymentIncomplete(long j, String str, int i);

    private enum SupportStatus {
        UNKNOWN,
        SUPPORTED,
        UNSUPPORTED;

        public boolean isSupported() {
            return this == SUPPORTED;
        }

        public boolean isKnown() {
            return this != UNKNOWN;
        }
    }

    public enum PurchaseState {
        PURCHASED,
        CANCELED,
        REFUNDED;

        public static PurchaseState fromOrdinal(int ordinal) {
            PurchaseState[] values = values();
            return (ordinal < 0 || ordinal >= values.length) ? CANCELED : values[ordinal];
        }
    }

    public enum ProductType {
        Consumable,
        Restorable,
        Subscription;

        public static ProductType fromOrdinal(int ordinal) {
            ProductType[] values = values();
            return (ordinal < 0 || ordinal >= values.length) ? Consumable : values[ordinal];
        }
    }

    public enum CauseForIncompletion {
        Error,
        Canceled,
        UserNotAuthorized,
        ServiceUnavailable,
        Pending;

        public static CauseForIncompletion fromOrdinal(int ordinal) {
            CauseForIncompletion[] values = values();
            return (ordinal < 0 || ordinal >= values.length) ? Error : values[ordinal];
        }
    }



    public void Close() {
        Log.v(TAG, "Close");
        SexyAppFrameworkActivity.instance().removeOnActivityResultListener(this.mOnActivityResultListener);
    }

    private class PendingOperation {
        private final String mName;
        private final Runnable mOperation;

        public PendingOperation(Runnable operation, String name) {
            this.mOperation = operation;
            this.mName = name;
        }

        public Runnable getOperation() {
            return this.mOperation;
        }

        public String getName() {
            return this.mName;
        }
    }



    /* JADX INFO: Access modifiers changed from: private */
    private void finishOperation(String name) {
        PendingOperation completedOperation = this.pendingOperations.poll();
        Object[] objArr = new Object[2];
        objArr[0] = name;
        objArr[1] = completedOperation != null ? completedOperation.getName() : "<none>";
        Log.v(TAG, String.format("finishOperation: expected [%s] actual [%s]", objArr));
        PendingOperation nextOperation = this.pendingOperations.peek();
        if (nextOperation != null) {
            nextOperation.getOperation().run();
        }
    }



    public boolean CanMakePayments() {
        Log.v(TAG, "CanMakePayments()");
        return this.mPaymentsStatus.isSupported();
    }

    public boolean ProductTypeIsSupported(int prodType) {
        Log.v(TAG, String.format("ProductTypeIsSupported( %d )", Integer.valueOf(prodType)));
        switch (ProductType.fromOrdinal(prodType)) {
            case Consumable:
            case Restorable:
                return this.mPaymentsStatus.isSupported();
            case Subscription:
            default:
                return false;
        }
    }



    /* JADX INFO: Access modifiers changed from: private */
    private boolean CallPaymentCompleteHook(Purchase info) {
        String receiptId = info.getToken();
        Log.v(TAG, String.format("Calling payment complete hook for %s", receiptId));
        this.mUnconsumedPurchases.put(receiptId, info);
        byte[] purchaseBytes = null;
        try {
            JSONObject purchase = new JSONObject();
            purchase.put("signedData", info.getOriginalJson());
            purchase.put("signature", info.getSignature());
            purchaseBytes = purchase.toString().getBytes("UTF-8");
        } catch (UnsupportedEncodingException e) {
            Log.e(TAG, "Failed to build purchase JSON - bad encoding UTF-8");
        } catch (JSONException e2) {
            Log.e(TAG, "Failed to build purchase JSON");
        }
        if (purchaseBytes == null) {
            return false;
        }
        FirePaymentComplete(this.mNativeDriverPtr, receiptId, Base64.encodeWebSafe(purchaseBytes, false));
        return true;
    }



    public boolean HasUnconfirmedPayments() {
        Log.v(TAG, "HasUnconfirmedTransactions()");
        return !this.mUnconsumedPurchases.isEmpty();
    }
    public void ConfirmDelivery(String receiptId) {
        Log.v(TAG, String.format("ConfirmDelivery( %s )", receiptId));
        if (!CanMakePayments()) {
            Log.v(TAG, String.format("ConfirmDelivery( %s ) - failed, not initialized", receiptId));
            return;
        }
        final Purchase purchase = this.mUnconsumedPurchases.get(receiptId);
        if (purchase == null) {
            Log.v(TAG, String.format("ConfirmDelivery( %s ): no such receipt pending", receiptId));
        } else {
            startOperation(new Runnable() { // from class: com.popcap.SexyAppFramework.GooglePlayPurchaseDriver.10
                @Override // java.lang.Runnable
                public void run() {
                    GooglePlayPurchaseDriver.this.mIabHelper.consumeAsync(purchase, GooglePlayPurchaseDriver.this.mOnConsumeFinishedListener);
                }
            }, "consumeAsync");
        }
    }

}
