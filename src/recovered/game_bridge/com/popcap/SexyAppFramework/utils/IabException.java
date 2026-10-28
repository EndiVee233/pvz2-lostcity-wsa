package com.popcap.SexyAppFramework.utils;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class IabException extends Exception {
    IabResult mResult;

    public IabException(IabResult r) {
        this(r, (Exception) null);
    }

    public IabException(int response, String message) {
        this(new IabResult(response, message));
    }

    public IabException(IabResult r, Exception cause) {
        super(r.getMessage(), cause);
        this.mResult = r;
    }

    public IabException(int response, String message, Exception cause) {
        this(new IabResult(response, message), cause);
    }

    public IabResult getResult() {
        return this.mResult;
    }
}
