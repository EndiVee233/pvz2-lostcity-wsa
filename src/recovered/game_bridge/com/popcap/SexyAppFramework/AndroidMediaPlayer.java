package com.popcap.SexyAppFramework;

import android.content.Context;
import android.media.MediaPlayer;
import android.net.Uri;
import android.util.Log;
import java.io.FileDescriptor;
import java.io.IOException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidMediaPlayer extends MediaPlayer {
    static final int State_Completed = 7;
    static final int State_End = 8;
    static final int State_Idle = 0;
    static final int State_Initialized = 2;
    static final int State_Paused = 6;
    static final int State_Prepared = 3;
    static final int State_Preparing = 1;
    static final int State_Started = 4;
    static final int State_Stopped = 5;
    static final int State_Unknown = -1;
    int mPlayerState = -1;
    boolean mbIsSeeking = false;
    MediaListenerProxy mListenerProxy = new MediaListenerProxy(this);

    class MediaListenerProxy implements MediaPlayer.OnCompletionListener, MediaPlayer.OnErrorListener, MediaPlayer.OnPreparedListener, MediaPlayer.OnSeekCompleteListener {
        public MediaPlayer.OnCompletionListener mOnCompletionListener;
        public MediaPlayer.OnErrorListener mOnErrorListener;
        public MediaPlayer.OnPreparedListener mOnPreparedListener;
        public MediaPlayer.OnSeekCompleteListener mOnSeekCompleteListener;
        AndroidMediaPlayer mParent;

        public MediaListenerProxy(AndroidMediaPlayer InParent) {
            this.mParent = InParent;
        }

        @Override // android.media.MediaPlayer.OnPreparedListener
        public void onPrepared(MediaPlayer mp) {
            this.mParent.HandleOnPrepared((AndroidMediaPlayer) mp);
            if (this.mOnPreparedListener != null) {
                this.mOnPreparedListener.onPrepared(mp);
            }
        }

        @Override // android.media.MediaPlayer.OnErrorListener
        public boolean onError(MediaPlayer mp, int what, int extra) {
            this.mParent.HandleOnError((AndroidMediaPlayer) mp, what, extra);
            if (this.mOnErrorListener != null) {
                this.mOnErrorListener.onError(mp, what, extra);
                return false;
            }
            return false;
        }

        @Override // android.media.MediaPlayer.OnCompletionListener
        public void onCompletion(MediaPlayer mp) {
            this.mParent.HandleOnCompletion((AndroidMediaPlayer) mp);
            if (this.mOnCompletionListener != null) {
                this.mOnCompletionListener.onCompletion(mp);
            }
        }

        @Override // android.media.MediaPlayer.OnSeekCompleteListener
        public void onSeekComplete(MediaPlayer mp) {
            this.mParent.HandleOnSeekComplete((AndroidMediaPlayer) mp);
            if (this.mOnSeekCompleteListener != null) {
                this.mOnSeekCompleteListener.onSeekComplete(mp);
            }
        }
    }

    AndroidMediaPlayer() {
        super.setOnPreparedListener(this.mListenerProxy);
        super.setOnErrorListener(this.mListenerProxy);
        super.setOnSeekCompleteListener(this.mListenerProxy);
        super.setOnCompletionListener(this.mListenerProxy);
    }

    public final int GetPlayerState() {
        return this.mPlayerState;
    }

    @Override // android.media.MediaPlayer
    public void start() {
        super.start();
        this.mPlayerState = 4;
    }

    @Override // android.media.MediaPlayer
    public void stop() {
        super.stop();
        this.mPlayerState = 5;
    }

    @Override // android.media.MediaPlayer
    public void pause() {
        super.pause();
        this.mPlayerState = 6;
    }

    @Override // android.media.MediaPlayer
    public void prepare() throws IOException {
        super.prepare();
        this.mPlayerState = 3;
    }

    @Override // android.media.MediaPlayer
    public void prepareAsync() {
        super.prepareAsync();
        this.mPlayerState = 1;
    }

    @Override // android.media.MediaPlayer
    public void reset() {
        super.reset();
        this.mPlayerState = 0;
    }

    @Override // android.media.MediaPlayer
    public void release() {
        super.release();
        this.mPlayerState = -1;
    }

    @Override // android.media.MediaPlayer
    public void setDataSource(FileDescriptor fd) throws IOException {
        super.setDataSource(fd);
        this.mPlayerState = 2;
    }

    @Override // android.media.MediaPlayer
    public void setDataSource(FileDescriptor fd, long offset, long length) throws IOException {
        super.setDataSource(fd, offset, length);
        this.mPlayerState = 2;
    }

    @Override // android.media.MediaPlayer
    public void setDataSource(String path) throws IOException {
        super.setDataSource(path);
        this.mPlayerState = 2;
    }

    @Override // android.media.MediaPlayer
    public void setDataSource(Context context, Uri uri) throws IOException {
        super.setDataSource(context, uri);
        this.mPlayerState = 2;
    }

    @Override // android.media.MediaPlayer
    public void seekTo(int iNewPosition) {
        if (this.mbIsSeeking) {
            Log.w("Music", "Seeking while another seek is in progress!!");
        }
        this.mbIsSeeking = true;
        super.seekTo(iNewPosition);
    }

    @Override // android.media.MediaPlayer
    public void setOnPreparedListener(MediaPlayer.OnPreparedListener listener) {
        this.mListenerProxy.mOnPreparedListener = listener;
    }

    @Override // android.media.MediaPlayer
    public void setOnErrorListener(MediaPlayer.OnErrorListener listener) {
        this.mListenerProxy.mOnErrorListener = listener;
    }

    @Override // android.media.MediaPlayer
    public void setOnSeekCompleteListener(MediaPlayer.OnSeekCompleteListener listener) {
        this.mListenerProxy.mOnSeekCompleteListener = listener;
    }

    @Override // android.media.MediaPlayer
    public void setOnCompletionListener(MediaPlayer.OnCompletionListener listener) {
        this.mListenerProxy.mOnCompletionListener = listener;
    }

    /* JADX INFO: Access modifiers changed from: private */
    private void HandleOnPrepared(AndroidMediaPlayer mp) {
        if (this.mPlayerState != 1) {
            Log.w("Music", "Got a prepare-complete callback while not preparing!");
        }
        mp.mPlayerState = 3;
    }

    /* JADX INFO: Access modifiers changed from: private */
    private void HandleOnError(AndroidMediaPlayer mp, int what, int extra) {
    }

    /* JADX INFO: Access modifiers changed from: private */
    private void HandleOnSeekComplete(AndroidMediaPlayer mp) {
        if (!this.mbIsSeeking) {
            Log.w("Music", "Got a seek-complete callback while not seeking!");
        }
        this.mbIsSeeking = false;
    }

    public void HandleOnCompletion(AndroidMediaPlayer mp) {
    }
}
