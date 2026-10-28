package com.popcap.util;

import android.os.*;
import com.popcap.events.RewardEvent.*;
import java.io.*;
import java.net.*;
import java.util.*;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.*;
import org.json.*;

/** In-memory/loopback checks only: never sends notifications or connects to payment services. */
public final class ServicesProbe {
    private static int checks;
    private static void check(boolean ok,String label) {checks++;if(!ok)throw new AssertionError(label);}
    private static PopCapConfigHandler parse(String xml) throws Exception {
        PopCapConfigHandler handler=new PopCapConfigHandler();
        XMLReader reader=SAXParserFactory.newInstance().newSAXParser().getXMLReader();
        reader.setContentHandler(handler);reader.parse(new InputSource(new StringReader(xml)));return handler;
    }
    private static void xml() throws Exception {
        String xml="<config><server_url>https://example.invalid/local-only</server_url><notification>"
            +"<id>42</id><type>16</type><action>3</action><title>sample</title><text>message</text>"
            +"<interval>1234</interval><last_send_time>7</last_send_time></notification></config>";
        PopCapConfigHandler h=parse(xml);check(h.getServerUrl().equals("https://example.invalid/local-only"),"XML server string");
        check(h.getNotificationList().size()==1,"XML count");PopCapNotificationAbstract n=h.getNotificationList().get(0);
        check(n instanceof PopCapNotificationForPlay,"XML subtype");check(n.getId()==42,"XML id");check(n.type==16,"XML type");
        check(n.action==3,"XML action");check(n.title.equals("sample"),"XML title");check(n.text.equals("message"),"XML text");
        check(n.interval==1234&&n.lastSendTime==7,"XML times");check(n.getNextSendTime()==1241,"next notification time");
        check(parse(xml.replace("notification","NOTIFICATION")).getNotificationList().size()==1,"case insensitive element");
        check(parse(xml.replace("<type>16</type>","<type>999</type>")).getNotificationList().isEmpty(),"unknown type ignored");
        for(String field:new String[]{"id","type","action","interval","last_send_time"}) {
            String broken=xml.replaceAll("<"+field+">[^<]*</"+field+">","<"+field+">bad</"+field+">");
            try {parse(broken);throw new AssertionError("Accepted invalid "+field);} catch(SAXException expected) {checks++;}
        }
    }
    private static void schedule() throws Exception {
        TimeStrategy strategy=TimeStrategy.Instance();check(strategy==TimeStrategy.Instance(),"strategy singleton");
        strategy.LoadServerTimeStrage(new JSONArray("[{\"l\":8,\"d\":12},{\"l\":0,\"d\":1},{\"l\":2,\"d\":4}]"));
        long hour=3600000L;
        for(long t:new long[]{0,1,2*hour-1})check(strategy.GetNotficationSkedulTime(t)==hour,"first time bucket");
        for(long t:new long[]{2*hour,3*hour,8*hour-1})check(strategy.GetNotficationSkedulTime(t)==4*hour,"middle time bucket");
        for(long t:new long[]{8*hour,9*hour,Long.MAX_VALUE})check(strategy.GetNotficationSkedulTime(t)==12*hour,"last time bucket");
        strategy.LoadServerTimeStrage(null);check(strategy.GetNotficationSkedulTime(3*hour)==4*hour,"null preserves schedule");
        strategy.LoadServerTimeStrage(new JSONArray());check(strategy.GetNotficationSkedulTime(0)==28800000L,"empty default");
        check(strategy.GetSkuSkeduTime()==86400000L,"SKU period");
        RewardTimeStrage reward=new RewardTimeStrage();reward.LoadData(new JSONArray("[{\"dis\":30},{\"dis\":10},{\"dis\":20}]"));
        check(reward.GetRewardList().get(0).getDisTime()==10,"reward sort");
        check(reward.GetReadyReward(9)==null,"reward before first");
        for(long t:new long[]{10,19,20,29,30,31})check(reward.GetReadyReward(t).getDisTime()==(t<20?10:t<30?20:30),"reward boundary");
        reward.AddRewardJsonObj(new JSONObject("{\"t\":\"2\",\"u\":\"local\",\"i\":\"title\",\"c\":\"body\",\"r\":\"3\",\"s\":\"17\",\"p\":\"8\"}"));
        Reward r=reward.GetRewardList().get(3);check(r.getDisTime()==3*hour,"reward unit conversion");
        check(r.getType()==2&&r.getSkuId()==17&&r.getId()==8,"reward integer fields");
        check(r.getTile().equals("title")&&r.getContent().equals("body")&&r.getUrl().equals("local"),"reward strings");
        Class<?> comparator=Class.forName("com.popcap.events.RewardEvent.RewardDisCompard");
        java.lang.reflect.Constructor<?> ctor=comparator.getDeclaredConstructor();ctor.setAccessible(true);
        java.lang.reflect.Method compare=comparator.getDeclaredMethod("compare",Object.class,Object.class);compare.setAccessible(true);
        Reward a=new Reward(),b=new Reward();a.setDisTime(10);b.setDisTime(10);
        check(((Integer)compare.invoke(ctor.newInstance(),a,b))==1&&a.getDisTime()==180010,"original equal-time comparator side effect");
        try {new RewardTimeStrage().GetReadyReward(0);throw new AssertionError("Empty reward behavior changed");}
        catch(IndexOutOfBoundsException expected) {checks++;}
    }
    private static void coin() {
        PopCapNotificationForCoin c=new PopCapNotificationForCoin(1,"title","text",1,3);
        check(c.type==32&&c._coinMax==100&&c._coinRemains==0&&c._coinIncraseRatePerMinute==1,"coin defaults");
        check(c.interval==6000000L,"coin interval default");c.resetCoinRemains(40);check(c.interval==3600000L,"coin interval remaining");
        c.resetCoinSettings(200,2);check(c._coinMax==100&&c._coinIncraseRatePerMinute==1,"original positive settings behavior");
        c._coinMax=-1;c._coinIncraseRatePerMinute=-1;c.resetCoinSettings(200,2);check(c.interval==4800000L,"negative settings initialization");
        c._coinIncraseRatePerMinute=0;try {c.resetInterval();throw new AssertionError("Division by zero behavior changed");}catch(ArithmeticException expected){checks++;}
        PopCapNotificationForPlay dst=new PopCapNotificationForPlay(1,"old","old",10,1),src=new PopCapNotificationForPlay(2,"new","new",20,3);
        src.lastSendTime=7;PopCapNotificationForPlay.updateNotification(dst,src);
        check(dst.getId()==1&&dst.title.equals("new")&&dst.interval==20&&dst.action==3&&dst.lastSendTime==7,"notification merge");
        src.title=null;src.text=null;src.interval=0;src.action=0;src.lastSendTime=0;PopCapNotificationForPlay.updateNotification(dst,src);
        check(dst.title.equals("new")&&dst.interval==20&&dst.action==3&&dst.lastSendTime==7,"notification ignores unset fields");
    }
    private static final class Stub extends IRemoteService.Stub {
        String args="";boolean touched;int stopped;
        public boolean sendNotification(int a,int b){args=a+":"+b;return true;}
        public boolean setCoinReamins(int a,int b){args=a+":"+b;return false;}
        public boolean setCoinSettings(int a,int b,int c){args=a+":"+b+":"+c;return true;}
        public float GetServiceVerion(){return 1.25f;}
        public void SetUserLastOpt(){touched=true;}
        public void SetSkuUserLastOpt(String p){args=p;}
        public void StopService(){stopped++;}
    }
    private static final class Remote extends Binder {
        final Stub target;Remote(Stub t){target=t;}
        @Override public IInterface queryLocalInterface(String descriptor){return null;}
        @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{return target.onTransact(code,data,reply,flags);}
    }
    private static void binder() throws Exception {
        Stub stub=new Stub();check(IRemoteService.Stub.asInterface(null)==null,"null binder");
        check(IRemoteService.Stub.asInterface(stub)==stub,"local binder shortcut");
        IRemoteService proxy=IRemoteService.Stub.asInterface(new Remote(stub));check(proxy!=stub,"remote proxy");
        check(proxy.sendNotification(11,16)&&stub.args.equals("11:16"),"IPC notification args and true");
        check(!proxy.setCoinReamins(99,33)&&stub.args.equals("99:33"),"IPC coin args and false");
        check(proxy.setCoinSettings(7,100,3)&&stub.args.equals("7:100:3"),"IPC three arguments");
        check(proxy.GetServiceVerion()==1.25f,"IPC float result");proxy.SetUserLastOpt();check(stub.touched,"IPC user flag");
        proxy.SetSkuUserLastOpt("test.package.local");check(stub.args.equals("test.package.local"),"IPC string");
        proxy.StopService();check(stub.stopped==1,"IPC stop callback");
        Parcel data=Parcel.obtain(),reply=Parcel.obtain();try {check(!stub.onTransact(999,data,reply,0),"IPC unknown transaction");}finally{reply.recycle();data.recycle();}
    }
    private static String line(InputStream in)throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();int c;while((c=in.read())!=-1&&c!=10)if(c!=13)out.write(c);return out.toString("US-ASCII");
    }
    private static void http(final int status,Map<String,String> params,String expectedBody)throws Exception {
        final ServerSocket server=new ServerSocket(0,1,InetAddress.getByName("127.0.0.1"));final String[] received=new String[2];final Throwable[] failure=new Throwable[1];
        Thread thread=new Thread(new Runnable(){public void run(){try(Socket socket=server.accept()){
            socket.setSoTimeout(3000);InputStream input=socket.getInputStream();received[0]=line(input);String header;int length=0;
            while(!(header=line(input)).isEmpty())if(header.toLowerCase(Locale.ROOT).startsWith("content-length:"))length=Integer.parseInt(header.substring(15).trim());
            byte[] body=new byte[length];int i=0;while(i<length){int n=input.read(body,i,length-i);if(n<0)throw new EOFException();i+=n;}received[1]=new String(body,"UTF-8");
            socket.getOutputStream().write(("HTTP/1.1 "+status+(status==200?" OK":" Not Found")+"\r\nContent-Length: 12\r\nConnection: close\r\n\r\nalpha\r\nbeta\n").getBytes("US-ASCII"));
        }catch(Throwable error){failure[0]=error;}}});thread.setDaemon(true);thread.start();
        String result=NetWorkHttp.HttpReq("http://127.0.0.1:"+server.getLocalPort()+"/probe",params);
        thread.join(4000);server.close();check(!thread.isAlive()&&failure[0]==null,"legacy HTTP server");
        check(received[0].startsWith("POST /probe "),"legacy HTTP method");check(expectedBody.equals(received[1]),"legacy HTTP exact form body");
        check(result.equals(status==200?"alpha\nbeta\n":""),"legacy HTTP response lines");
    }
    public static void main(String[] args)throws Exception {
        xml();int xml=checks;schedule();int schedules=checks-xml;coin();int coins=checks-xml-schedules;
        binder();int ipc=checks-xml-schedules-coins;
        Map<String,String> params=new LinkedHashMap<String,String>();params.put("a","hello world");params.put("b","2");
        http(200,params,"a=hello world&b=2&");http(200,null,"");http(404,null,"");
        try {NetWorkHttp.HttpReq("http://127.0.0.1:1/not-used",new LinkedHashMap<String,String>());throw new AssertionError("Empty form behavior changed");}catch(StringIndexOutOfBoundsException expected){checks++;}
        System.out.println("{\"passed\":true,\"checks\":"+checks+",\"xml_checks\":"+xml+",\"schedule_checks\":"+schedules+",\"coin_checks\":"+coins+",\"ipc_checks\":"+ipc+",\"legacy_http_checks\":"+(checks-xml-schedules-coins-ipc)+"}");
    }
}
