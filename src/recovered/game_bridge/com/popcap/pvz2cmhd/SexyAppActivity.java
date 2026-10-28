package com.popcap.pvz2cmhd;

import android.content.Intent;
import android.os.Bundle;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import com.popcap.SexyAppFramework.SexyAppFrameworkActivity;
import com.talkweb.twOfflineSdk.TwOfflineSDK;
import com.z.ick.ext.action.TL;

/* Reconstructed source. Splash dimension 1200 is restored from the original constant; SDK references remain real runtime classes. */
public class SexyAppActivity extends SexyAppFrameworkActivity {
    static {
        AddSplashScreenImage(2130837580, 320, 480);
        AddSplashScreenImage(2130837588, 480, 800);
        AddSplashScreenImage(2130837578, 480, 854);
        AddSplashScreenImage(2130837582, 540, 960);
        AddSplashScreenImage(2130837586, 600, 1024);
        AddSplashScreenImage(2130837590, 768, 1280);
        AddSplashScreenImage(2130837576, 800, 1200);
        AddSplashScreenImage(2130837574, 1080, 1920);
        AddSplashScreenImage(2130837584, 1600, 2560);
        AddSplashScreenImage(2130837584, 2560, 1600);
        AddFirstSplashScreenImage(2130837581, 320, 480);
        AddFirstSplashScreenImage(2130837589, 480, 800);
        AddFirstSplashScreenImage(2130837579, 480, 854);
        AddFirstSplashScreenImage(2130837583, 540, 960);
        AddFirstSplashScreenImage(2130837587, 600, 1024);
        AddFirstSplashScreenImage(2130837591, 768, 1280);
        AddFirstSplashScreenImage(2130837577, 800, 1200);
        AddFirstSplashScreenImage(2130837575, 1080, 1920);
        AddFirstSplashScreenImage(2130837585, 1600, 2560);
        AddFirstSplashScreenImage(2130837585, 2560, 1600);
        AddProgressBarImage(2130837572, 661, 62);
        AddProgressBarBgImage(2130837573, 685, 84);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        checkPermissions();
        TwOfflineSDK.onCreate(this);
    }

    private void checkPermissions() {
        try {
            if (ContextCompat.checkSelfPermission(this, "android.permission.READ_PHONE_STATE") != 0) {
                ActivityCompat.requestPermissions(this, new String[]{"android.permission.READ_PHONE_STATE"}, 1);
            } else {
                TL.init(this, "yuyang_waigua");
            }
        } catch (Throwable th) {
        }
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity
    public void handleNativeCrash(String errorMsg) {
        super.handleNativeCrash(errorMsg);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onResume() {
        super.onResume();
        TwOfflineSDK.onResume(this);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onPause() {
        super.onPause();
        TwOfflineSDK.onPause(this);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onStop() {
        TwOfflineSDK.onStop(this);
        super.onStop();
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onRestart() {
        TwOfflineSDK.onRestart(this);
        super.onRestart();
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onNewIntent(Intent intent) {
        TwOfflineSDK.onNewIntent(intent);
        super.onNewIntent(intent);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        TwOfflineSDK.onActivityResult(requestCode, resultCode, data);
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onDestroy() {
        TwOfflineSDK.onDestroy(this);
        super.onDestroy();
    }

    @Override // com.popcap.SexyAppFramework.SexyAppFrameworkActivity, android.app.Activity
    public void onStart() {
        TwOfflineSDK.onStart(this);
        super.onStart();
    }
}
