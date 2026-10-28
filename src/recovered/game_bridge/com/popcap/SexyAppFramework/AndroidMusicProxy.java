package com.popcap.SexyAppFramework;

import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.media.MediaPlayer;
import android.util.Log;
import java.io.FileDescriptor;
import java.io.IOException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidMusicProxy implements MediaPlayer.OnCompletionListener, MediaPlayer.OnErrorListener, MediaPlayer.OnPreparedListener, MediaPlayer.OnSeekCompleteListener {
    private String mCurrentMusicFilename;
    private int mFileLength;
    private int mFileOffset;
    private AndroidMediaPlayer mMusicPlayer = null;
    private long mNativeContext = 0;
    private int mCurrentMusicId = -1;
    private boolean mbLoopMusicPlayer = false;
    private boolean mbPlayWhenReady = false;
    private boolean mbCriticalError = false;
    private int mSuspendedPlaybackPosition = 0;

    native void NotifyMusicCompletedCallback(long j, String str, int i);

    native void NotifyMusicErrorCallback(long j, String str, int i, int i2);

    public boolean Music_Startup(long InNativeContext) {
        this.mSuspendedPlaybackPosition = 0;
        this.mNativeContext = InNativeContext;
        CreateMediaPlayer();
        return true;
    }

    public void Music_Shutdown() {
        if (this.mMusicPlayer != null) {
            if (this.mMusicPlayer.isPlaying()) {
                this.mMusicPlayer.stop();
            }
            DestroyMediaPlayer();
        }
    }

    private void Music_Enable(boolean bShouldEnable) {
        if (bShouldEnable) {
            CreateMediaPlayer();
            if (this.mCurrentMusicFilename != null) {
                Prepare();
                ResumeMusic();
                return;
            }
            return;
        }
        SuspendMusic();
        DestroyMediaPlayer();
    }

    private void ResumeMusic() {
        this.mMusicPlayer.seekTo(this.mSuspendedPlaybackPosition);
        this.mMusicPlayer.start();
    }

    private void SuspendMusic() {
        if (this.mMusicPlayer != null && this.mMusicPlayer.isPlaying()) {
            this.mSuspendedPlaybackPosition = this.mMusicPlayer.getCurrentPosition();
        } else {
            this.mSuspendedPlaybackPosition = 0;
        }
    }

    private boolean Music_SetCurrentMusicStream(String InFilename, int InOffset, int InLength) {
        if (this.mbCriticalError || this.mMusicPlayer == null) {
            this.mbCriticalError = false;
            CreateMediaPlayer();
        }
        this.mSuspendedPlaybackPosition = 0;
        if (this.mMusicPlayer.isPlaying()) {
            this.mMusicPlayer.stop();
        }
        if (this.mCurrentMusicFilename != null && this.mCurrentMusicFilename.equals(InFilename) && this.mFileOffset == InOffset && this.mFileLength == InLength) {
            this.mMusicPlayer.seekTo(0);
            return true;
        }
        this.mMusicPlayer.reset();
        this.mCurrentMusicFilename = InFilename;
        this.mFileOffset = InOffset;
        this.mFileLength = InLength;
        Prepare();
        return true;
    }

    private void Music_SetLooping(boolean bDoLooping) {
        this.mbLoopMusicPlayer = bDoLooping;
        if (this.mMusicPlayer != null) {
            this.mMusicPlayer.setLooping(bDoLooping);
        }
    }

    private void Music_SetCurrentStreamPosition(int InNewPosition) {
        if (this.mMusicPlayer != null) {
            this.mMusicPlayer.seekTo(InNewPosition);
        } else {
            this.mSuspendedPlaybackPosition = InNewPosition;
        }
    }

    private boolean Music_PlayCurrentStream() {
        synchronized (this) {
            int playerState = this.mMusicPlayer.GetPlayerState();
            if (playerState != 4) {
                if (CanPlay()) {
                    this.mMusicPlayer.start();
                } else if (playerState == 1) {
                    this.mbPlayWhenReady = true;
                }
            }
        }
        return true;
    }

    boolean CanPlay() {
        if (this.mMusicPlayer != null) {
            int playerState = this.mMusicPlayer.GetPlayerState();
            switch (playerState) {
                case 3:
                case 6:
                case 7:
                    return true;
            }
        }
        return false;
    }

    private void Music_PauseCurrentStream() {
        if (this.mMusicPlayer != null && this.mMusicPlayer.isPlaying()) {
            this.mMusicPlayer.pause();
        }
    }

    private void Music_ResumeCurrentStream() {
        if (this.mMusicPlayer != null && !this.mMusicPlayer.isPlaying()) {
            this.mMusicPlayer.start();
        }
    }

    private void Music_StopCurrentStream() {
        if (this.mMusicPlayer != null && this.mMusicPlayer.isPlaying()) {
            this.mMusicPlayer.stop();
        }
    }

    private boolean Music_IsStreamPlaying(int InMusicId) {
        if (InMusicId == -1 || InMusicId == this.mCurrentMusicId) {
            return this.mMusicPlayer.isPlaying();
        }
        return false;
    }

    private void Music_SetDeviceVolume(float InLeftVolume, float InRightVolume) {
        if (this.mMusicPlayer != null) {
            this.mMusicPlayer.setVolume(InLeftVolume, InRightVolume);
        }
    }

    private void CreateMediaPlayer() {
        DestroyMediaPlayer();
        this.mMusicPlayer = new AndroidMediaPlayer();
        this.mMusicPlayer.setOnCompletionListener(this);
        this.mMusicPlayer.setOnErrorListener(this);
        this.mMusicPlayer.setOnSeekCompleteListener(this);
        this.mMusicPlayer.setOnPreparedListener(this);
    }

    private void DestroyMediaPlayer() {
        if (this.mMusicPlayer != null) {
            this.mMusicPlayer.reset();
            this.mMusicPlayer.release();
        }
        this.mMusicPlayer = null;
    }

    void Prepare() {
        FileDescriptor fd;
        if (this.mMusicPlayer.GetPlayerState() == 1) {
            Log.e("Music", "Calling Prepare while another prepare is in progress!!");
        }
        AssetManager assetMgr = SexyAppFrameworkActivity.instance().getAssets();
        String assetName = AndroidAssetUtils.GetAssetNameFromFileName(this.mCurrentMusicFilename);
        try {
            AssetFileDescriptor afd = assetMgr.openFd(assetName);
            if (afd != null && (fd = afd.getFileDescriptor()) != null) {
                this.mMusicPlayer.setDataSource(fd, this.mFileOffset, this.mFileLength);
            }
        } catch (IOException ex) {
            Log.e("Music", ex.toString());
        }
        this.mMusicPlayer.setAudioStreamType(3);
        this.mMusicPlayer.prepareAsync();
    }

    @Override // android.media.MediaPlayer.OnPreparedListener
    public void onPrepared(MediaPlayer mp) {
        synchronized (this) {
            if (this.mbPlayWhenReady) {
                mp.start();
                this.mbPlayWhenReady = false;
            }
        }
    }

    @Override // android.media.MediaPlayer.OnSeekCompleteListener
    public void onSeekComplete(MediaPlayer mp) {
        synchronized (this) {
            if (this.mbPlayWhenReady) {
            }
        }
    }

    @Override // android.media.MediaPlayer.OnErrorListener
    public boolean onError(MediaPlayer mp, int what, int extra) {
        Log.e("Music", String.format("MediaPlayer error: %d reported!", Integer.valueOf(what)));
        NotifyMusicErrorCallback(this.mNativeContext, this.mCurrentMusicFilename, this.mCurrentMusicId, what);
        this.mbCriticalError = true;
        return false;
    }

    @Override // android.media.MediaPlayer.OnCompletionListener
    public void onCompletion(MediaPlayer mp) {
        NotifyMusicCompletedCallback(this.mNativeContext, this.mCurrentMusicFilename, this.mCurrentMusicId);
    }
}
