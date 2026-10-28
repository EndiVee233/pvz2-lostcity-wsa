package com.popcap.SexyAppFramework;

import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SexyTextWatcher implements TextWatcher {
    private final AndroidGameApp mAndroidGameApp;

    public SexyTextWatcher(AndroidGameApp pAndroidGameApp) {
        this.mAndroidGameApp = pAndroidGameApp;
    }

    @Override // android.text.TextWatcher
    public void afterTextChanged(Editable s) {
        this.mAndroidGameApp.setEditText(s.toString());
    }

    @Override // android.text.TextWatcher
    public void beforeTextChanged(CharSequence pCharSequence, int start, int count, int after) {
        Log.d("SexyTextWatcher", "beforeTextChanged(" + ((Object) pCharSequence) + ")start: " + start + ",count: " + count + ",after: " + after);
    }

    @Override // android.text.TextWatcher
    public void onTextChanged(CharSequence pCharSequence, int start, int before, int count) {
        Log.d("SexyTextWatcher", "onTextChanged(" + ((Object) pCharSequence) + ")start: " + start + ",count: " + count + ",before: " + before);
    }
}
