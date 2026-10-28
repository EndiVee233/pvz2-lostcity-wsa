package com.popcap.util;

import android.util.Log;
import java.util.ArrayList;
import org.xml.sax.Attributes;
import org.xml.sax.ContentHandler;
import org.xml.sax.Locator;
import org.xml.sax.SAXException;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapConfigHandler implements ContentHandler {
    private ArrayList<PopCapNotificationAbstract> notification_list;
    private boolean in_server_url = false;
    private boolean in_notification = false;
    private boolean in_id = false;
    private boolean in_type = false;
    private boolean in_action = false;
    private boolean in_title = false;
    private boolean in_text = false;
    private boolean in_interval = false;
    private boolean in_lastTimeSend = false;
    private boolean in_coin_remains = false;
    private boolean in_coin_max = false;
    private boolean in_coin_rate = false;
    private String server_url = null;
    private int notification_id = -1;
    private int notification_type = -1;
    private int notification_action = -1;
    private String notification_title = null;
    private String notification_text = null;
    private long notification_interval = -1;
    private long lastTimeSend = -1;
    private int coin_remains = -1;
    private int coin_max = -1;
    private int coin_rate = -1;

    public PopCapConfigHandler() {
        this.notification_list = null;
        this.notification_list = new ArrayList<>();
    }

    @Override // org.xml.sax.ContentHandler
    public void startElement(String uri, String localName, String qName, Attributes atts) throws SAXException {
        String tagName = (localName.length() != 0 ? localName : qName).toLowerCase().trim();
        if (tagName.equals(PopCapConfigXmlElement.SERVER_URL)) {
            this.in_server_url = true;
            this.server_url = null;
        }
        if (tagName.equals(PopCapConfigXmlElement.NOTIFICATION)) {
            this.in_notification = true;
            this.notification_type = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.ID)) {
            this.in_id = true;
            this.notification_id = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.TYPE)) {
            this.in_type = true;
            this.notification_type = -1;
        }
        if (tagName.equals("action")) {
            this.in_action = true;
            this.notification_action = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.TITLE)) {
            this.in_title = true;
            this.notification_title = null;
        }
        if (tagName.equals(PopCapConfigXmlElement.TEXT)) {
            this.in_text = true;
            this.notification_text = null;
        }
        if (tagName.equals(PopCapConfigXmlElement.INTERVAL)) {
            this.in_interval = true;
            this.notification_interval = -1L;
        }
        if (tagName.equals(PopCapConfigXmlElement.LAST_SEND_TIME)) {
            this.in_lastTimeSend = true;
            this.lastTimeSend = -1L;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_REMAINS)) {
            this.in_coin_remains = true;
            this.coin_remains = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_MAX)) {
            this.in_coin_max = true;
            this.coin_max = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_RATE)) {
            this.in_coin_rate = true;
            this.coin_rate = -1;
        }
    }

    @Override // org.xml.sax.ContentHandler
    public void endElement(String uri, String localName, String qName) throws SAXException {
        String tagName = (localName.length() != 0 ? localName : qName).toLowerCase().trim();
        if (tagName.equals(PopCapConfigXmlElement.SERVER_URL)) {
            this.in_server_url = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.NOTIFICATION)) {
            this.in_notification = false;
            initNotificationByType();
            this.notification_type = -1;
        }
        if (tagName.equals(PopCapConfigXmlElement.ID)) {
            this.in_id = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.TYPE)) {
            this.in_type = false;
        }
        if (tagName.equals("action")) {
            this.in_action = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.TITLE)) {
            this.in_title = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.TEXT)) {
            this.in_text = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.INTERVAL)) {
            this.in_interval = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.LAST_SEND_TIME)) {
            this.in_lastTimeSend = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_REMAINS)) {
            this.in_coin_remains = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_MAX)) {
            this.in_coin_max = false;
        }
        if (tagName.equals(PopCapConfigXmlElement.COIN_RATE)) {
            this.in_coin_rate = false;
        }
    }

    @Override // org.xml.sax.ContentHandler
    public void characters(char[] ch, int start, int length) throws SAXException {
        String str = new String(ch, start, length).trim();
        if (str.length() != 0) {
            if (this.in_server_url) {
                this.server_url = str;
            }
            if (this.in_notification) {
                if (this.in_id) {
                    try {
                        this.notification_id = Integer.parseInt(str);
                    } catch (Exception e) {
                        throw new SAXException("notification_id error in parse: " + str);
                    }
                }
                if (this.in_type) {
                    try {
                        this.notification_type = Integer.parseInt(str);
                    } catch (Exception e2) {
                        throw new SAXException("notification_id error in parse: " + str);
                    }
                }
                if (this.in_action) {
                    try {
                        this.notification_action = Integer.parseInt(str);
                    } catch (Exception e3) {
                        throw new SAXException("notification_action error in parse: " + str);
                    }
                }
                if (this.in_title) {
                    this.notification_title = str;
                }
                if (this.in_text) {
                    this.notification_text = str;
                }
                if (this.in_interval) {
                    try {
                        this.notification_interval = Long.parseLong(str);
                    } catch (Exception e4) {
                        throw new SAXException("notification_interval error in parse: " + str);
                    }
                }
                if (this.in_lastTimeSend) {
                    try {
                        this.lastTimeSend = Long.parseLong(str);
                    } catch (Exception e5) {
                        throw new SAXException("lastTimeSend error in parse: " + str);
                    }
                }
                if (this.in_coin_remains) {
                    try {
                        this.coin_remains = Integer.parseInt(str);
                    } catch (Exception e6) {
                        throw new SAXException("coin_remains error in parse: " + str);
                    }
                }
                if (this.in_coin_max) {
                    try {
                        this.coin_max = Integer.parseInt(str);
                    } catch (Exception e7) {
                        throw new SAXException("coin_max error in parse: " + str);
                    }
                }
                if (this.in_coin_rate) {
                    try {
                        this.coin_rate = Integer.parseInt(str);
                    } catch (Exception e8) {
                        throw new SAXException("coin_rate error in parse: " + str);
                    }
                }
            }
        }
    }

    public void initNotificationByType() {
        switch (this.notification_type) {
            case 16:
                PopCapNotificationForPlay notificationForPlay = new PopCapNotificationForPlay(this.notification_id, this.notification_title, this.notification_text, this.notification_interval, this.notification_action);
                if (this.lastTimeSend > 0) {
                    notificationForPlay.lastSendTime = this.lastTimeSend;
                }
                this.notification_list.add(notificationForPlay);
                break;
            default:
                Log.e("DEBUG", "Undefined notification type!");
                break;
        }
    }

    public String getServerUrl() {
        return this.server_url;
    }

    public ArrayList<PopCapNotificationAbstract> getNotificationList() {
        return this.notification_list;
    }

    @Override // org.xml.sax.ContentHandler
    public void endDocument() throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void endPrefixMapping(String prefix) throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void ignorableWhitespace(char[] ch, int start, int length) throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void processingInstruction(String target, String data) throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void setDocumentLocator(Locator locator) {
    }

    @Override // org.xml.sax.ContentHandler
    public void skippedEntity(String name) throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void startDocument() throws SAXException {
    }

    @Override // org.xml.sax.ContentHandler
    public void startPrefixMapping(String prefix, String uri) throws SAXException {
    }

    public static void printNotificationList(ArrayList<PopCapNotificationAbstract> list) {
        if (list == null) {
            Log.d("DEBUG", "null");
            return;
        }
        if (list.size() == 0) {
            Log.d("DEBUG", "listsize = 0");
        }
        for (PopCapNotificationAbstract n : list) {
            Log.d("DEBUG", n.toString());
        }
    }
}
