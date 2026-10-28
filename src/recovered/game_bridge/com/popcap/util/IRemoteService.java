package com.popcap.util;

import android.os.Binder;
import android.os.IBinder;
import android.os.IInterface;
import android.os.Parcel;
import android.os.RemoteException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public interface IRemoteService extends IInterface {
    float GetServiceVerion() throws RemoteException;

    void SetSkuUserLastOpt(String str) throws RemoteException;

    void SetUserLastOpt() throws RemoteException;

    void StopService() throws RemoteException;

    boolean sendNotification(int i, int i2) throws RemoteException;

    boolean setCoinReamins(int i, int i2) throws RemoteException;

    boolean setCoinSettings(int i, int i2, int i3) throws RemoteException;

    public static abstract class Stub extends Binder implements IRemoteService {
        private static final String DESCRIPTOR = "com.popcap.util.IRemoteService";
        static final int TRANSACTION_GetServiceVerion = 4;
        static final int TRANSACTION_SetSkuUserLastOpt = 6;
        static final int TRANSACTION_SetUserLastOpt = 5;
        static final int TRANSACTION_StopService = 7;
        static final int TRANSACTION_sendNotification = 1;
        static final int TRANSACTION_setCoinReamins = 2;
        static final int TRANSACTION_setCoinSettings = 3;

        public Stub() {
            attachInterface(this, DESCRIPTOR);
        }

        public static IRemoteService asInterface(IBinder obj) {
            if (obj == null) {
                return null;
            }
            IInterface iin = obj.queryLocalInterface(DESCRIPTOR);
            if (iin != null && (iin instanceof IRemoteService)) {
                return (IRemoteService) iin;
            }
            return new Proxy(obj);
        }

        @Override // android.os.IInterface
        public IBinder asBinder() {
            return this;
        }

        @Override // android.os.Binder
        public boolean onTransact(int code, Parcel data, Parcel reply, int flags) throws RemoteException {
            switch (code) {
                case 1:
                    data.enforceInterface(DESCRIPTOR);
                    int _arg0 = data.readInt();
                    int _arg1 = data.readInt();
                    boolean _result = sendNotification(_arg0, _arg1);
                    reply.writeNoException();
                    reply.writeInt(_result ? 1 : 0);
                    return true;
                case 2:
                    data.enforceInterface(DESCRIPTOR);
                    int _arg2 = data.readInt();
                    int _arg3 = data.readInt();
                    boolean _result2 = setCoinReamins(_arg2, _arg3);
                    reply.writeNoException();
                    reply.writeInt(_result2 ? 1 : 0);
                    return true;
                case 3:
                    data.enforceInterface(DESCRIPTOR);
                    int _arg4 = data.readInt();
                    int _arg5 = data.readInt();
                    int _arg6 = data.readInt();
                    boolean _result3 = setCoinSettings(_arg4, _arg5, _arg6);
                    reply.writeNoException();
                    reply.writeInt(_result3 ? 1 : 0);
                    return true;
                case 4:
                    data.enforceInterface(DESCRIPTOR);
                    float _result4 = GetServiceVerion();
                    reply.writeNoException();
                    reply.writeFloat(_result4);
                    return true;
                case 5:
                    data.enforceInterface(DESCRIPTOR);
                    SetUserLastOpt();
                    reply.writeNoException();
                    return true;
                case 6:
                    data.enforceInterface(DESCRIPTOR);
                    String _arg7 = data.readString();
                    SetSkuUserLastOpt(_arg7);
                    reply.writeNoException();
                    return true;
                case 7:
                    data.enforceInterface(DESCRIPTOR);
                    StopService();
                    reply.writeNoException();
                    return true;
                case 1598968902:
                    reply.writeString(DESCRIPTOR);
                    return true;
                default:
                    return super.onTransact(code, data, reply, flags);
            }
        }

        private static class Proxy implements IRemoteService {
            private IBinder mRemote;

            Proxy(IBinder remote) {
                this.mRemote = remote;
            }

            @Override // android.os.IInterface
            public IBinder asBinder() {
                return this.mRemote;
            }

            public String getInterfaceDescriptor() {
                return Stub.DESCRIPTOR;
            }

            @Override // com.popcap.util.IRemoteService
            public boolean sendNotification(int nId, int nAction) throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    _data.writeInt(nId);
                    _data.writeInt(nAction);
                    this.mRemote.transact(1, _data, _reply, 0);
                    _reply.readException();
                    boolean _result = _reply.readInt() != 0;
                    return _result;
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public boolean setCoinReamins(int nId, int coinRemains) throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    _data.writeInt(nId);
                    _data.writeInt(coinRemains);
                    this.mRemote.transact(2, _data, _reply, 0);
                    _reply.readException();
                    boolean _result = _reply.readInt() != 0;
                    return _result;
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public boolean setCoinSettings(int nId, int coinMax, int coinIncraseRatePerMinute) throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    _data.writeInt(nId);
                    _data.writeInt(coinMax);
                    _data.writeInt(coinIncraseRatePerMinute);
                    this.mRemote.transact(3, _data, _reply, 0);
                    _reply.readException();
                    boolean _result = _reply.readInt() != 0;
                    return _result;
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public float GetServiceVerion() throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    this.mRemote.transact(4, _data, _reply, 0);
                    _reply.readException();
                    float _result = _reply.readFloat();
                    return _result;
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public void SetUserLastOpt() throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    this.mRemote.transact(5, _data, _reply, 0);
                    _reply.readException();
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public void SetSkuUserLastOpt(String pckName) throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    _data.writeString(pckName);
                    this.mRemote.transact(6, _data, _reply, 0);
                    _reply.readException();
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }

            @Override // com.popcap.util.IRemoteService
            public void StopService() throws RemoteException {
                Parcel _data = Parcel.obtain();
                Parcel _reply = Parcel.obtain();
                try {
                    _data.writeInterfaceToken(Stub.DESCRIPTOR);
                    this.mRemote.transact(7, _data, _reply, 0);
                    _reply.readException();
                } finally {
                    _reply.recycle();
                    _data.recycle();
                }
            }
        }
    }
}
