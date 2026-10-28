package com.popcap.pvz2cmhd;

import android.app.Activity;
import android.app.ProgressDialog;
import android.os.AsyncTask;
import android.os.Environment;
import android.util.Log;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;

/* JADX INFO: compiled from: CrashHandler.java */
/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
class LogTask extends AsyncTask<Void, Void, Void> {
    Activity activity;
    String logDir;
    String logFileName;
    Process process;
    ProgressDialog progress;

    LogTask(Activity a, ProgressDialog p, String d, String f) {
        this.activity = a;
        this.progress = p;
        this.logDir = d;
        this.logFileName = f;
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // android.os.AsyncTask
    protected Void doInBackground(Void... v) {
        try {
            Log.e("crash", "doInBackground begin");
            this.process = Runtime.getRuntime().exec(new String[]{"logcat", "-d", "-t", "5000"});
            BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(this.process.getInputStream()));
            new ArrayList();
            StringBuffer sb = new StringBuffer();
            while (true) {
                String str = bufferedReader.readLine();
                if (str == null) {
                    break;
                }
                if (str.contains("pc 00") || str.contains("at ")) {
                    System.out.println(str);
                    sb.append(str + "\n\n");
                }
            }
            if (Environment.getExternalStorageState().equals("mounted")) {
                File dir = new File(this.logDir);
                Log.i(CrashHandler.TAG, dir.toString());
                if (!dir.exists()) {
                    dir.mkdir();
                }
                Log.i(CrashHandler.TAG, this.logFileName);
                FileOutputStream fos = new FileOutputStream(dir + "/" + this.logFileName);
                Log.i(CrashHandler.TAG, "111");
                fos.write(sb.toString().getBytes());
                Log.i(CrashHandler.TAG, "111");
                fos.close();
                Log.i(CrashHandler.TAG, this.logFileName);
                Log.i(CrashHandler.TAG, "log ok");
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e2) {
            Log.e("crash", "get logText fail");
            e2.printStackTrace();
            Toast.makeText(this.activity, e2.toString(), 1).show();
        } catch (Exception e3) {
            Log.e("crash", "save to file fail");
            e3.printStackTrace();
        }
        return null;
    }

    @Override // android.os.AsyncTask
    protected void onCancelled() {
        Log.e("crash", "onCancelled");
        this.process.destroy();
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // android.os.AsyncTask
    protected void onPostExecute(Void v) {
        Log.e("crash", "onPostExecute");
        this.progress.dismiss();
        this.activity.finish();
        Log.e("crash", "onPostExecute over");
    }
}
