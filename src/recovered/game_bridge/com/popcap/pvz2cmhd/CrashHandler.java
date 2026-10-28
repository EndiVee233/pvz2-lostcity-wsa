package com.popcap.pvz2cmhd;

import com.popcap.SexyAppFramework.DreamRootPath;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import java.text.MessageFormat;
import java.util.Calendar;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class CrashHandler extends Activity {
    public static final String TAG = "CrashHandler";

    @Override // android.app.Activity
    protected void onCreate(Bundle state) {
        Log.e(TAG, "CrashHandler begin ");
        System.currentTimeMillis();
        Calendar cal = Calendar.getInstance();
        String time = (cal.get(2) + 1) + "_" + cal.get(5) + "_" + cal.get(11) + "_" + cal.get(12);
        final String fileName = "crash-" + time + ".log";
        final String dir = DreamRootPath.getRootFile() + "/crash/";
        super.onCreate(state);
        setTitle(R.string.crashtitle);
        setContentView(2130903040);
        TextView v = (TextView) findViewById(2131296259);
        v.setText("crash info will save to" + dir + fileName);
        Log.e(TAG, dir + fileName);
        final Button b = (Button) findViewById(2131296257);
        Button c = (Button) findViewById(2131296258);
        b.setOnClickListener(new View.OnClickListener() { // from class: com.popcap.pvz2cmhd.CrashHandler.1
            @Override // android.view.View.OnClickListener
            public void onClick(View v2) {
                final ProgressDialog progress = new ProgressDialog(CrashHandler.this);
                progress.setMessage(CrashHandler.this.getString(R.string.getting_log));
                progress.setIndeterminate(true);
                progress.setCancelable(false);
                progress.show();
                try {
                    final AsyncTask<Void, Void, Void> task = new LogTask(CrashHandler.this, progress, dir, fileName).execute(new Void[0]);
                    b.postDelayed(new Runnable() { // from class: com.popcap.pvz2cmhd.CrashHandler.1.1
                        @Override // java.lang.Runnable
                        public void run() {
                            if (task.getStatus() != AsyncTask.Status.FINISHED) {
                                progress.dismiss();
                                task.cancel(true);
                                new AlertDialog.Builder(CrashHandler.this).setMessage(MessageFormat.format(CrashHandler.this.getString(R.string.get_log_failed), CrashHandler.this.getString(R.string.author_email))).setCancelable(true).setIcon(android.R.drawable.ic_dialog_alert).show();
                            }
                        }
                    }, 20000L);
                } catch (Exception e) {
                    Log.e(CrashHandler.TAG, "CrashHandler Exception ");
                    e.printStackTrace();
                }
            }
        });
        c.setOnClickListener(new View.OnClickListener() { // from class: com.popcap.pvz2cmhd.CrashHandler.2
            @Override // android.view.View.OnClickListener
            public void onClick(View v2) {
                CrashHandler.this.finish();
            }
        });
    }

    static String getVersion(Context c) {
        try {
            return c.getPackageManager().getPackageInfo(c.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "";
        }
    }
}
