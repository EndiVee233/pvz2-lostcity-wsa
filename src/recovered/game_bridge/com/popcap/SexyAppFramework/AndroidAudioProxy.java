package com.popcap.SexyAppFramework;

import android.media.AudioTrack;
import android.util.Log;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidAudioProxy {
    private byte[] mAudioBuffer;
    private int mAudioFetchSize;
    private int mAudioSkipAheadThreshold;
    public int mBitsPerSample;
    public int mBufferSize;
    private int mFrameSize;
    public int mNativeSampleRate;
    public long mNativeSoundManagerContext;
    public int mNumChannels;
    public int mSampleRate;
    public AudioTrack mTrack;

    public final native int FetchAudioDataCallback(long j, byte[] bArr, int i);

    public final native int SkipAudioDataCallback(long j, int i);

    private boolean Sound_Startup(long InNativeSoundManagerContext) {
        this.mNativeSoundManagerContext = InNativeSoundManagerContext;
        return true;
    }

    private void Sound_Shutdown() {
    }

    private boolean Sound_Enable(int InSampleRate, int InNumChannels, int InBitsPerSample) {
        int iChannelFormat;
        this.mSampleRate = InSampleRate;
        this.mNumChannels = InNumChannels;
        this.mBitsPerSample = InBitsPerSample;
        this.mFrameSize = (this.mBitsPerSample * this.mNumChannels) / 8;
        int iSampleType = GetSampleType();
        if (iSampleType == 0 || (iChannelFormat = GetChannelFormat()) == 0) {
            return false;
        }
        this.mNativeSampleRate = AudioTrack.getNativeOutputSampleRate(3);
        this.mBufferSize = AudioTrack.getMinBufferSize(this.mSampleRate, iChannelFormat, iSampleType);
        if (this.mBufferSize < 4096) {
            this.mBufferSize = 4096;
        }
        this.mAudioFetchSize = this.mBufferSize / this.mFrameSize;
        this.mAudioSkipAheadThreshold = (this.mAudioFetchSize * 3) / 2;
        this.mAudioBuffer = new byte[this.mBufferSize];
        this.mTrack = new AudioTrack(3, this.mSampleRate, iChannelFormat, iSampleType, this.mBufferSize * 2, 1);
        this.mTrack.play();
        FlushAudioTrack();
        return this.mTrack != null;
    }

    private void Sound_Disable() {
        if (this.mTrack != null) {
            this.mTrack.stop();
            FlushAudioTrack();
            this.mTrack.release();
            this.mTrack = null;
        }
    }

    private void Sound_NotifyAudioAvailable(int numFramesAvailable) {
        int iWriteResult;
        int framesAvailable = numFramesAvailable;
        if (framesAvailable >= this.mAudioFetchSize) {
            if (framesAvailable > this.mAudioSkipAheadThreshold) {
                int numFramesToSkip = framesAvailable - this.mAudioSkipAheadThreshold;
                Log.w("AUDIODEBUG", String.format("Skipping ahead in audio stream by %d frames", Integer.valueOf(numFramesToSkip)));
                SkipAudioDataCallback(this.mNativeSoundManagerContext, numFramesToSkip);
                framesAvailable -= numFramesToSkip;
            }
            while (framesAvailable > this.mAudioFetchSize) {
                int iNumFramesRead = FetchAudioDataCallback(this.mNativeSoundManagerContext, this.mAudioBuffer, this.mAudioFetchSize);
                if (iNumFramesRead >= 0 && (iWriteResult = this.mTrack.write(this.mAudioBuffer, 0, this.mFrameSize * iNumFramesRead)) < 0) {
                    Log.e("AUDIOERROR", String.format("FAILED TO WRITE - %s State: %d - Got bad write result: %d - Tried to write %d bytes", this.mTrack.toString(), Integer.valueOf(this.mTrack.getState()), Integer.valueOf(iWriteResult), Integer.valueOf(this.mFrameSize * iNumFramesRead)));
                    this.mTrack.stop();
                    FlushAudioTrack();
                }
                framesAvailable -= this.mAudioFetchSize;
            }
        }
    }

    private int Sound_GetAudioFetchSize() {
        return this.mAudioFetchSize;
    }

    private void Sound_FlushAudioTrack() {
        Log.w("AUDIODEBUG", "Calling FlushAudioTrack!!");
        FlushAudioTrack();
    }

    int GetChannelFormat() {
        if (this.mNumChannels == 2) {
            return 12;
        }
        if (this.mNumChannels == 1) {
            return 4;
        }
        return 0;
    }

    int GetSampleType() {
        if (this.mBitsPerSample == 16) {
            return 2;
        }
        if (this.mBitsPerSample == 8) {
            return 3;
        }
        return 0;
    }

    private void FlushAudioTrack() {
        if (this.mTrack != null) {
            synchronized (this) {
                this.mTrack.pause();
                this.mTrack.flush();
                this.mTrack.play();
            }
        }
    }

    private void ResetAudioTrack() {
        FlushAudioTrack();
    }
}
