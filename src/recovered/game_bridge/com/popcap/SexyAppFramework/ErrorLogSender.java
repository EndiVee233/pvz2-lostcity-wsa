package com.popcap.SexyAppFramework;

import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetAddress;
import java.net.Socket;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class ErrorLogSender {
    public void SendErroLog(String msg) {
        try {
            String targMsg = GetAppendMsg() + msg + "|\r\n";
            TcpSocket tcpSocket = new TcpSocket();
            tcpSocket.SendMsg(targMsg);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private String GetAppendMsg() {
        AndroidGameApp gameApp;
        AndroidSurfaceView surfaceView;
        if (SexyAppFrameworkActivity.instance() != null && (gameApp = SexyAppFrameworkActivity.instance().getGameApp()) != null && (surfaceView = SexyAppFrameworkActivity.instance().getSurfaceView()) != null) {
            String strResult = "12crash_1|" + gameApp.Diag_GetHardwareModel();
            String strResult2 = ((strResult + "|") + gameApp.Diag_GetOSVersion()) + "|";
            int[] solution = new int[2];
            surfaceView.Graphics_GetScreenSizeInPixels(solution);
            String strResult3 = ((((((((((((((strResult2 + Integer.toString(solution[0]) + "x" + Integer.toString(solution[1])) + "|") + gameApp.Diag_GetDeviceIMEI()) + "|") + Integer.toString(gameApp.Diag_GetMobileCardType())) + "|") + Long.toString(gameApp.Diag_GetUsedMemory())) + "-") + Long.toString(gameApp.Diag_GetAvailMemory())) + "|") + gameApp.Util_GetPackageName()) + "|") + gameApp.Info_SysGetProductVersionString()) + "|") + gameApp.Diag_GetNetworkType();
            AndroidHttpProxy httpProxy = new AndroidHttpProxy(SexyAppFrameworkActivity.instance());
            return ((strResult3 + "-") + Integer.toString(httpProxy.GetNetworkStatus())) + "|";
        }
        return "";
    }

    class TcpSocket {
        private String logSrvAddr = "pvz2logandroid.intelligent.popcap.com.cn";
        Socket mSocket = null;
        DataOutputStream mDos = null;

        public TcpSocket() {
        }

        public boolean keepLive() {
            try {
                if (this.mSocket != null && this.mSocket.isConnected() && !this.mSocket.isClosed()) {
                    return true;
                }
                InetAddress netAddress = InetAddress.getByName(this.logSrvAddr);
                this.mSocket = new Socket(netAddress, 4346);
                this.mSocket.setKeepAlive(true);
                this.mDos = new DataOutputStream(this.mSocket.getOutputStream());
                return true;
            } catch (IOException e) {
                if (this.mSocket != null) {
                    NetWorkReset();
                }
                try {
                    Thread.sleep(5000L);
                } catch (InterruptedException e1) {
                    e1.printStackTrace();
                }
                return false;
            }
        }

        public void NetWorkReset() {
            try {
                if (this.mDos != null) {
                    this.mDos.close();
                }
                if (this.mSocket != null) {
                    this.mSocket.close();
                }
                this.mSocket = null;
                this.mDos = null;
            } catch (IOException e) {
            }
        }

        public void SendMsg(String msg) throws IOException {
            int tryCount = 0;
            while (!keepLive()) {
                tryCount++;
                if (tryCount > 2) {
                    return;
                }
            }
            this.mDos.write(msg.getBytes());
            this.mDos.flush();
            NetWorkReset();
        }
    }
}
