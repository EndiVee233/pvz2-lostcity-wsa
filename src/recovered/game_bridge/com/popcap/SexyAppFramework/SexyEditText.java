package com.popcap.SexyAppFramework;

import android.content.Context;
import android.util.AttributeSet;
import android.view.KeyEvent;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class SexyEditText extends EditText {
    private SexyAppFrameworkActivity mSexyAppFrameworkActivity;

    public SexyEditText(Context context) {
        super(context);
    }

    public SexyEditText(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public SexyEditText(Context context, AttributeSet attrs, int defStyle) {
        super(context, attrs, defStyle);
    }

    public void setSexyAppFrameworkActivity(SexyAppFrameworkActivity pSexyAppFrameworkActivity) {
        this.mSexyAppFrameworkActivity = pSexyAppFrameworkActivity;
    }

    @Override // android.widget.TextView, android.view.View, android.view.KeyEvent.Callback
    public boolean onKeyDown(int pKeyCode, KeyEvent pKeyEvent) {
        super.onKeyDown(pKeyCode, pKeyEvent);
        if (pKeyCode == 4) {
            this.mSexyAppFrameworkActivity.closeIMEKeyboard();
        }
        boolean rc = this.mSexyAppFrameworkActivity.getUIEventMgr().HandleKeyEvent(pKeyEvent);
        return rc ? rc : super.onKeyDown(pKeyCode, pKeyEvent);
    }

    @Override // android.view.View
    public boolean dispatchKeyEventPreIme(KeyEvent event) {
        if (this.mSexyAppFrameworkActivity != null) {
            InputMethodManager imm = (InputMethodManager) this.mSexyAppFrameworkActivity.getSystemService("input_method");
            if (imm.isActive() && event.getKeyCode() == 4) {
                this.mSexyAppFrameworkActivity.closeIMEKeyboard();
            }
        }
        return super.dispatchKeyEventPreIme(event);
    }

    @Override // android.widget.TextView, android.view.View, android.view.KeyEvent.Callback
    public boolean onKeyUp(int pKeyCode, KeyEvent pKeyEvent) {
        boolean rc = this.mSexyAppFrameworkActivity.getUIEventMgr().HandleKeyEvent(pKeyEvent);
        return rc ? rc : super.onKeyUp(pKeyCode, pKeyEvent);
    }

    @Override // android.widget.TextView
    public void onEditorAction(int actionCode) {
        super.onEditorAction(actionCode);
        if (actionCode == 6) {
            this.mSexyAppFrameworkActivity.closeIMEKeyboard();
        }
    }
}
