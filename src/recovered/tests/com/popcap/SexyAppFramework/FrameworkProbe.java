package com.popcap.SexyAppFramework;

import com.popcap.SexyAppFramework.utils.Base64;
import com.popcap.SexyAppFramework.utils.Base64DecoderException;
import java.io.*;
import java.net.*;
import java.nio.*;
import java.util.*;
import java.util.concurrent.*;

/** Behavioral checks against fixed wire vectors and an in-process HTTP server. Never packaged. */
public final class FrameworkProbe {
    private static int checks;
    private static void check(boolean condition, String label) {
        checks++;
        if (!condition) throw new AssertionError(label);
    }
    private static String hex(byte[] bytes) {
        StringBuilder result = new StringBuilder();
        for (byte b : bytes) result.append(String.format("%02x", b & 255));
        return result.toString();
    }
    private static void base64() throws Exception {
        String[] raw = {"", "f", "fo", "foo", "foob", "fooba", "foobar"};
        String[] encoded = {"", "Zg==", "Zm8=", "Zm9v", "Zm9vYg==", "Zm9vYmE=", "Zm9vYmFy"};
        for (int i=0;i<raw.length;i++) {
            check(encoded[i].equals(Base64.encode(raw[i].getBytes("UTF-8"))), "Base64 RFC encode " + i);
            check(raw[i].equals(new String(Base64.decode(encoded[i]), "UTF-8")), "Base64 RFC decode " + i);
        }
        check(Arrays.equals(new byte[]{(byte)251,(byte)255,(byte)239},Base64.decodeWebSafe("-__v")),"URL alphabet decode");
        check("-__v".equals(Base64.encodeWebSafe(new byte[]{(byte)251,(byte)255,(byte)239},false)),"URL alphabet encode");
        check("M".equals(new String(Base64.decode(" TQ==\n"),"UTF-8")),"Whitespace decode");
        for (String bad : new String[]{"$","a","=","AA=A"}) {
            try { Base64.decode(bad); throw new AssertionError("Accepted invalid Base64 " + bad); }
            catch (Base64DecoderException expected) { checks++; }
        }
        Random random = new Random(747);
        for (int length=0;length<=128;length++) {
            byte[] bytes=new byte[length];random.nextBytes(bytes);
            check(Arrays.equals(bytes,Base64.decode(Base64.encode(bytes))),"binary roundtrip " + length);
            check(Arrays.equals(bytes,Base64.decodeWebSafe(Base64.encodeWebSafe(bytes,false))),"URL unpadded roundtrip " + length);
        }
    }
    private static void vector(AndroidUIEventManager.UIEvent event,String expected,String label) {
        ByteBuffer buffer=ByteBuffer.allocate(128).order(ByteOrder.LITTLE_ENDIAN);
        check(event.Serialize(buffer),label+" serialize");
        check(expected.equals(hex(Arrays.copyOf(buffer.array(),buffer.position()))),label+" native wire bytes");
        check(!event.Serialize(ByteBuffer.allocate(1)),label+" overflow");
    }
    private static void events() {
        AndroidUIEventManager manager=new AndroidUIEventManager();
        AndroidUIEventManager.UITouchTracker touch=manager.new UITouchTracker();
        touch.mPointerId=1;touch.X=10;touch.Y=20;touch.previousX=8;touch.previousY=18;
        touch.mTimestampMS=1.5;touch.phase=3;
        vector(manager.new UITouchEvent(touch),"00000000020000000a00000014000000080000001200000001000000000000000000f83f03000000efbeaddeefbeadde","touch");
        vector(manager.new UIPinchEvent(10,20,4.0f,0.5f),"030000000a00000014000000000080400000003fefbeaddeefbeaddeefbeadde","pinch");
        vector(manager.new UIFlickEvent(10,20,1.5f,-2.0f),"040000000a00000014000000000000000000f83f00000000000000c0efbeadde","flick");
        vector(manager.new UIBackButtonEvent(),"05000000efbeaddeefbeaddeefbeadde","back");
        touch.mPointerId=-1;
        boolean threw=false;
        try { manager.new UITouchEvent(touch); } catch (AssertionError expected) { threw=true; }
        check(threw==AndroidUIEventManager.class.desiredAssertionStatus(),"assertion state preserved");
    }
    private static final class Transaction extends AndroidHttpTransaction {
        final List<String> events=new ArrayList<String>();
        final ByteArrayOutputStream data=new ByteArrayOutputStream();
        final CountDownLatch terminal=new CountDownLatch(1);
        final boolean releaseOnData;
        Transaction(String method,String url,boolean cancel) throws IOException {super(747,method,url);releaseOnData=cancel;}
        @Override void HttpReceivedResponse(long ptr) {check(ptr==747,"response native pointer");events.add("response");}
        @Override void HttpReceivedData(long ptr,byte[] buffer,int length) {
            check(ptr==747,"data native pointer");events.add("data");data.write(buffer,0,length);
            if (releaseOnData) {Release();terminal.countDown();}
        }
        @Override void HttpTransactionComplete(long ptr) {check(ptr==747,"complete native pointer");events.add("complete");terminal.countDown();}
        @Override void HttpTransactionError(long ptr) {check(ptr==747,"error native pointer");events.add("error");terminal.countDown();}
        @Override void HttpTransactionCleanup(long ptr) {check(ptr==747,"cleanup native pointer");events.add("cleanup");}
    }
    private static String line(InputStream in) throws IOException {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();int b;
        while ((b=in.read())!=-1 && b!='\n') if (b!='\r') bytes.write(b);
        return bytes.toString("US-ASCII");
    }
    private static void http(final int status,boolean post,boolean cancel,final int delay) throws Exception {
        final ServerSocket server=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"));
        final String[] request=new String[2];final Throwable[] failure=new Throwable[1];
        Thread responder=new Thread(new Runnable() {public void run() {
            try (Socket socket=server.accept()) {
                socket.setSoTimeout(3000);InputStream input=new BufferedInputStream(socket.getInputStream());
                request[0]=line(input);String header;int length=0;
                while (!(header=line(input)).isEmpty()) if (header.toLowerCase(Locale.ROOT).startsWith("content-length:")) length=Integer.parseInt(header.substring(15).trim());
                byte[] body=new byte[length];int offset=0;
                while(offset<length) {int n=input.read(body,offset,length-offset);if(n<0)throw new EOFException();offset+=n;}
                request[1]=new String(body,"US-ASCII");
                if (delay>0) Thread.sleep(delay);
                OutputStream output=socket.getOutputStream();
                output.write(("HTTP/1.1 "+status+(status==200?" OK":" Not Found")+"\r\nContent-Length: 5\r\nX-Probe: restored\r\nConnection: close\r\n\r\nhello").getBytes("US-ASCII"));output.flush();
            } catch(Throwable error) {if(delay==0)failure[0]=error;}
        }});
        responder.setDaemon(true);responder.start();
        Transaction transaction=new Transaction(post?"POST":"GET","http://127.0.0.1:"+server.getLocalPort()+"/probe",cancel);
        transaction.SetTimeout(delay>0?1:4);transaction.SetRequestHeader("X-Input","checked");
        if(post)transaction.SetRequestBody("abc".getBytes("US-ASCII"));
        transaction.Start();check(transaction.terminal.await(5,TimeUnit.SECONDS),"HTTP callback completion");
        java.lang.reflect.Field worker=AndroidHttpTransaction.class.getDeclaredField("mThread");worker.setAccessible(true);
        ((Thread)worker.get(transaction)).join(3000);check(!((Thread)worker.get(transaction)).isAlive(),"HTTP worker stopped");
        responder.join(2000);server.close();check(failure[0]==null,"HTTP test server");
        check(request[0].startsWith(post?"POST /probe ":"GET /probe "),"HTTP method and target");
        check((post?"abc":"").equals(request[1]),"HTTP request body");
        if(status!=200||delay>0)check(transaction.events.equals(Arrays.asList("error")),"HTTP error callback order");
        else {
            check("response".equals(transaction.events.get(0)),"HTTP response before data");
            check("hello".equals(transaction.data.toString("US-ASCII")),"HTTP response bytes");
            check((cancel?"cleanup":"complete").equals(transaction.events.get(transaction.events.size()-1)),"HTTP terminal order");
            check(!cancel||!transaction.events.contains("complete"),"Cancellation suppresses completion");
            check(transaction.GetStatusCode()==200,"HTTP status");
            check("OK".equals(transaction.GetStatusLine()),"HTTP status line");
            check(transaction.GetResponseLength()==5,"HTTP length");
            check("restored".equals(transaction.GetResponseHeader("X-Probe")),"HTTP response header");
        }
        if(!cancel)transaction.Release();
    }
    public static void main(String[] args) throws Exception {
        base64();int base64=checks;
        events();int events=checks-base64;
        http(200,false,false,0);http(200,true,false,0);http(404,false,false,0);http(200,false,true,0);http(200,false,false,900);
        System.out.println("{\"passed\":true,\"checks\":"+checks+",\"base64_checks\":"+base64+",\"input_event_checks\":"+events+",\"http_cases\":5,\"assertions_enabled\":"+AndroidUIEventManager.class.desiredAssertionStatus()+"}");
    }
}
