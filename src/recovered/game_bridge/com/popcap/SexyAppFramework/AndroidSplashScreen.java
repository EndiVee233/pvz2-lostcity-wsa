package com.popcap.SexyAppFramework;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import java.io.File;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class AndroidSplashScreen extends RelativeLayout {
    public boolean mRemoveSplashSurface;
    private AndroidSplashSurface mSplashSurface;
    private ProgressBar progressBar_widget;
    public static boolean mStartShowProgressBarFlag = false;
    public static boolean mFinishShowProgressBarFlag = false;
    public static boolean mIsFirstInit = false;

    public static class SplashImage {
        private Rect mIntendedDisplayRect;
        private int mResourceID;

        SplashImage(int aResourceID, int aIntendedDisplayWidth, int aIntendedDisplayHeight) {
            this.mResourceID = aResourceID;
            this.mIntendedDisplayRect = new Rect(0, 0, aIntendedDisplayWidth, aIntendedDisplayHeight);
        }

        public int GetResourceID() {
            return this.mResourceID;
        }

        public Rect GetIntendedDisplayRect() {
            return this.mIntendedDisplayRect;
        }

        public Integer GetIntendedArea() {
            return Integer.valueOf(this.mIntendedDisplayRect.width() * this.mIntendedDisplayRect.height());
        }
    }

    public AndroidSplashScreen(Context context) {
        super(context);
        this.mRemoveSplashSurface = false;
        setVerticalGravity(16);
        setHorizontalGravity(1);
        this.mSplashSurface = new AndroidSplashSurface(context);
        addView(this.mSplashSurface);
        this.progressBar_widget = new ProgressBar(context);
        this.progressBar_widget.setIndeterminate(true);
        RelativeLayout.LayoutParams lp = new RelativeLayout.LayoutParams(-2, -2);
        lp.addRule(13);
        addView(this.progressBar_widget, lp);
        mIsFirstInit = false;
    }

    private class AndroidSplashSurface extends SurfaceView implements SurfaceHolder.Callback {
        private Bitmap mBGBitmap;
        private Bitmap mBGBitmapTitle;
        private int mBarBgMaxHeight;
        private int mBarBgMaxWidth;
        private int mBarMaxHeight;
        private int mBarMaxWidth;
        private int mCurrentBarBgHeight;
        private int mCurrentBarBgWidth;
        private int mCurrentBarHeight;
        private int mCurrentBarWidth;
        private int mHeight;
        private Bitmap mProgressBar;
        private Bitmap mProgressBarBg;
        private int mScreenMaxHeight;
        private int mScreenMaxWidth;
        private int mUpdateCount;
        private int mValue;
        private int mValueX;
        private int mWidth;

        public AndroidSplashSurface(Context aContext) {
            super(aContext);
            getHolder().addCallback(this);
            getHolder().setFormat(1);
            setWillNotDraw(false);
            setVisibility(0);
            this.mProgressBarBg = null;
            this.mProgressBar = null;
            this.mValueX = 4;
            this.mBGBitmap = null;
            this.mWidth = -1;
            this.mHeight = -1;
            this.mValue = 0;
            this.mUpdateCount = 0;
            this.mScreenMaxWidth = 2560;
            this.mScreenMaxHeight = 1715;
            this.mBarMaxWidth = 0;
            this.mBarMaxHeight = 0;
            this.mCurrentBarWidth = 0;
            this.mCurrentBarHeight = 0;
            this.mBarBgMaxWidth = 0;
            this.mBarBgMaxHeight = 0;
            this.mCurrentBarBgWidth = 0;
            this.mCurrentBarBgHeight = 0;
        }

        @Override // android.view.SurfaceHolder.Callback
        public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
            invalidate();
        }

        @Override // android.view.SurfaceHolder.Callback
        public void surfaceCreated(SurfaceHolder holder) {
            invalidate();
        }

        @Override // android.view.SurfaceHolder.Callback
        public void surfaceDestroyed(SurfaceHolder holder) {
        }

        @Override // android.view.SurfaceView, android.view.View
        protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
            this.mWidth = View.MeasureSpec.getSize(widthMeasureSpec);
            this.mHeight = View.MeasureSpec.getSize(heightMeasureSpec);
            setMeasuredDimension(this.mWidth, this.mHeight);
            BitmapFactory.Options bfOptions = new BitmapFactory.Options();
            bfOptions.inScaled = false;
            this.mBGBitmapTitle = BitmapFactory.decodeResource(getContext().getResources(), SexyAppFrameworkActivity.GetBestFitFirstSplashImage(this.mWidth, this.mHeight), bfOptions);
            this.mBGBitmapTitle.setDensity(0);
            this.mBGBitmap = BitmapFactory.decodeResource(getContext().getResources(), SexyAppFrameworkActivity.GetBestFitSplashImage(this.mWidth, this.mHeight), bfOptions);
            this.mBGBitmap.setDensity(0);
            if (SexyAppFrameworkActivity.GetProgressBarBgSplashImage() != null && SexyAppFrameworkActivity.GetProgressBarBgSplashImage() != null) {
                this.mBarMaxWidth = SexyAppFrameworkActivity.GetProgressBarSplashImage().GetIntendedDisplayRect().width();
                this.mBarMaxHeight = SexyAppFrameworkActivity.GetProgressBarSplashImage().GetIntendedDisplayRect().height();
                this.mBarBgMaxWidth = SexyAppFrameworkActivity.GetProgressBarBgSplashImage().GetIntendedDisplayRect().width();
                this.mBarBgMaxHeight = SexyAppFrameworkActivity.GetProgressBarBgSplashImage().GetIntendedDisplayRect().height();
                this.mProgressBarBg = BitmapFactory.decodeResource(getContext().getResources(), SexyAppFrameworkActivity.GetProgressBarBgSplashImage().GetResourceID(), bfOptions);
                this.mProgressBar = BitmapFactory.decodeResource(getContext().getResources(), SexyAppFrameworkActivity.GetProgressBarSplashImage().GetResourceID(), bfOptions);
                this.mProgressBarBg.setDensity(0);
                this.mProgressBar.setDensity(0);
                this.mCurrentBarHeight = (this.mBarMaxHeight * this.mHeight) / this.mScreenMaxHeight;
                this.mCurrentBarWidth = (this.mCurrentBarHeight * this.mBarMaxWidth) / this.mBarMaxHeight;
                this.mCurrentBarBgHeight = (this.mBarBgMaxHeight * this.mHeight) / this.mScreenMaxHeight;
                this.mCurrentBarBgWidth = (this.mCurrentBarBgHeight * this.mBarBgMaxWidth) / this.mBarBgMaxHeight;
                this.mProgressBarBg = Bitmap.createScaledBitmap(this.mProgressBarBg, this.mCurrentBarBgWidth, this.mCurrentBarBgHeight, true);
                this.mProgressBar = Bitmap.createScaledBitmap(this.mProgressBar, this.mCurrentBarWidth, this.mCurrentBarHeight, true);
            }
        }

        public boolean DatafileIsExists() {
            String targetPhonePath = AndroidGameApp.GetUserDataFolder() + "/initrsb.tag.smf";
            String targetSdPath = AndroidGameApp.GetExternalFilesDirectory() + "/initrsb.tag.smf";
            File filePhone = new File(targetPhonePath);
            File fileSD = new File(targetSdPath);
            if (filePhone.exists() || fileSD.exists()) {
                return true;
            }
            return false;
        }

        private void RenderPorgressBarBackground(Canvas canvas) {
            int bgX = (this.mWidth - this.mCurrentBarBgWidth) / 2;
            int bgY = (int) (((double) this.mHeight) * 0.88d);
            canvas.drawBitmap(this.mProgressBarBg, bgX, bgY, (Paint) null);
        }

        private void RenderProgressBar(Canvas canvas, Bitmap blt, int localX, int localY, int bitmapWidth, int bitmapHeight, int bx, int by, int nValueX) {
            int currentValueX;
            if (nValueX < bitmapWidth) {
                currentValueX = nValueX;
            } else {
                currentValueX = bitmapWidth;
            }
            Rect src = new Rect(bx, by, bx + bitmapWidth, by + bitmapHeight);
            Rect dst = new Rect(localX, localY, localX + currentValueX, localY + bitmapHeight);
            canvas.drawBitmap(blt, src, dst, (Paint) null);
        }

        @Override // android.view.View
        public void onDraw(Canvas canvas) {
            if (this.mBGBitmap != null && this.mProgressBarBg != null && this.mProgressBar != null) {
                canvas.drawColor(SexyAppFrameworkActivity.GetSplashScreenBackgroudColor());
                int cx = (this.mWidth - this.mBGBitmap.getWidth()) / 2;
                int cy = (this.mHeight - this.mBGBitmap.getHeight()) / 2;
                if (AndroidSplashScreen.mIsFirstInit) {
                    cy = (int) (((double) (this.mHeight - this.mBGBitmap.getHeight())) * 0.44d);
                }
                canvas.drawBitmap(this.mBGBitmap, cx, cy, (Paint) null);
                if (AndroidSplashScreen.mStartShowProgressBarFlag) {
                    if (AndroidSplashScreen.this.progressBar_widget != null) {
                        AndroidSplashScreen.this.progressBar_widget.setVisibility(8);
                    }
                    if ((!AndroidSplashScreen.mIsFirstInit || this.mBGBitmapTitle != null) && AndroidSplashScreen.mIsFirstInit) {
                        int titleX = (this.mWidth - this.mBGBitmapTitle.getWidth()) / 2;
                        int titleY = cy + ((int) (((double) this.mBGBitmap.getHeight()) * 0.7d));
                        canvas.drawBitmap(this.mBGBitmapTitle, titleX, titleY, (Paint) null);
                        RenderPorgressBarBackground(canvas);
                        if (this.mUpdateCount % 5 == 0) {
                            if (!AndroidSplashScreen.mStartShowProgressBarFlag || AndroidSplashScreen.mFinishShowProgressBarFlag) {
                                if (AndroidSplashScreen.mFinishShowProgressBarFlag) {
                                    this.mValue += this.mValueX * 2;
                                } else {
                                    this.mValue += this.mValueX * 2;
                                }
                            } else if (this.mValue < ((double) this.mProgressBar.getWidth()) * 0.85d) {
                                this.mValue = (int) (((double) this.mValue) + (((double) this.mValueX) * 0.5d));
                            }
                        }
                        int x = ((this.mWidth - this.mCurrentBarBgWidth) / 2) + ((this.mCurrentBarBgWidth - this.mCurrentBarWidth) / 2);
                        int y = ((int) (((double) this.mHeight) * 0.88d)) + ((this.mCurrentBarBgHeight - this.mCurrentBarHeight) / 2);
                        RenderProgressBar(canvas, this.mProgressBar, x, y, this.mProgressBar.getWidth(), this.mProgressBar.getHeight(), 0, 0, this.mValue);
                        this.mUpdateCount++;
                        invalidate();
                    }
                }
            }
        }

        @Override // android.view.View
        public boolean onTouchEvent(MotionEvent InEvent) {
            return true;
        }
    }
}
