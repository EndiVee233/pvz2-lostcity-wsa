package com.popcap.SexyAppFramework;

import android.util.Log;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidHttpTransaction implements Runnable {
    private HttpURLConnection mConnection;
    private long mNativeTransaction;
    private byte[] mRequestBody;
    private Thread mThread;

    native void HttpReceivedData(long j, byte[] bArr, int i);

    native void HttpReceivedResponse(long j);

    native void HttpTransactionCleanup(long j);

    native void HttpTransactionComplete(long j);

    native void HttpTransactionError(long j);

    public AndroidHttpTransaction(long nativeTransaction, String method, String url) throws IOException {
        Log.v("AndroidHttpTransaction.java", String.format("AndroidHttpTransaction( \"%s\", \"%s\" )\n", method, url));
        this.mNativeTransaction = nativeTransaction;
        this.mConnection = (HttpURLConnection) new URL(url).openConnection();
        String userAgent = System.getProperties().getProperty("http.agent");
        this.mConnection.setRequestProperty("User-Agent", userAgent);
        this.mConnection.setRequestMethod(method);
        this.mConnection.setDoInput(true);
    }

    public void SetRequestHeader(String name, String value) {
        this.mConnection.setRequestProperty(name, value);
    }

    public void SetRequestBody(byte[] body) {
        this.mRequestBody = body;
        this.mConnection.setDoOutput(true);
    }

    public void SetTimeout(int seconds) {
        this.mConnection.setReadTimeout((seconds * 1000) / 2);
        this.mConnection.setConnectTimeout((seconds * 1000) / 2);
        Log.v("AndroidHttpTransaction.java", "SetTimeout():" + this + ":" + Thread.currentThread().getName() + " connectTimeout = " + this.mConnection.getConnectTimeout() + ", readTimeout" + this.mConnection.getReadTimeout());
    }

    public void Start() {
        Log.v("AndroidHttpTransaction.java", "Start():" + this + ":" + Thread.currentThread().getName());
        this.mThread = new Thread(this);
        this.mThread.start();
    }

    @Override // java.lang.Runnable
    public void run() {
        if (AndroidHttpProxy.IsOffline()) {
            Log.i("PvZ2Offline", "Request failed locally in offline mode");
            FireTransactionError();
            return;
        }
        int bytesRead;
        try {
            Log.v("AndroidHttpTransaction.java", "run():" + this + ":" + Thread.currentThread().getName() + " connectTimeout = " + this.mConnection.getConnectTimeout() + ", readTimeout" + this.mConnection.getReadTimeout());
            this.mConnection.connect();
            if (this.mRequestBody != null) {
                OutputStream requestStream = this.mConnection.getOutputStream();
                requestStream.write(this.mRequestBody);
                requestStream.close();
            }
            InputStream responseStream = this.mConnection.getInputStream();
            FireReceivedResponse();
            byte[] buffer = new byte[16384];
            while (0 != this.mNativeTransaction && (bytesRead = responseStream.read(buffer)) != -1) {
                FireReceivedData(buffer, bytesRead);
            }
            responseStream.close();
            FireTransactionComplete();
        } catch (IOException ex) {
            Log.v("AndroidHttpTransaction.java", "IOExcp():" + ex.toString() + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
            FireTransactionError();
        }
    }

    public void Release() {
        synchronized (this) {
            Log.v("AndroidHttpTransaction.java", "Release():" + this + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
            HttpTransactionCleanup(this.mNativeTransaction);
            this.mNativeTransaction = 0L;
        }
    }

    private synchronized void FireReceivedResponse() {
        Log.v("AndroidHttpTransaction.java", "FireReceivedResponse():" + this + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
        if (0 != this.mNativeTransaction) {
            HttpReceivedResponse(this.mNativeTransaction);
        }
    }

    private synchronized void FireReceivedData(byte[] data, int dataSize) {
        Log.v("AndroidHttpTransaction.java", "FireReceivedData():" + this + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
        if (0 != this.mNativeTransaction) {
            HttpReceivedData(this.mNativeTransaction, data, dataSize);
        }
    }

    private synchronized void FireTransactionComplete() {
        Log.v("AndroidHttpTransaction.java", "FireTransactionComplete():" + this + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
        if (0 != this.mNativeTransaction) {
            HttpTransactionComplete(this.mNativeTransaction);
        }
    }

    private synchronized void FireTransactionError() {
        Log.v("AndroidHttpTransaction.java", "FireTransactionError():" + this + ":" + Thread.currentThread().getName() + ", nativePtr:" + this.mNativeTransaction);
        if (0 != this.mNativeTransaction) {
            HttpTransactionError(this.mNativeTransaction);
        }
    }

    public int GetStatusCode() {
        try {
            int statusCode = this.mConnection.getResponseCode();
            Log.v("AndroidHttpTransaction.java", String.format("%d <- GetStatusCode()", Integer.valueOf(statusCode)));
            return statusCode;
        } catch (IOException e) {
            return 0;
        }
    }

    public String GetStatusLine() {
        try {
            String statusLine = this.mConnection.getResponseMessage();
            Log.v("AndroidHttpTransaction.java", String.format("\"%s\" <- GetStatusLine()", statusLine));
            return statusLine;
        } catch (IOException e) {
            return null;
        }
    }

    public int GetResponseLength() {
        return this.mConnection.getContentLength();
    }

    public String GetResponseHeader(String key) {
        String responseHeader = this.mConnection.getHeaderField(key);
        Log.v("AndroidHttpTransaction.java", String.format("\"%s\" <- GetResponseHeader( \"%s\" )", responseHeader, key));
        return responseHeader;
    }
}
