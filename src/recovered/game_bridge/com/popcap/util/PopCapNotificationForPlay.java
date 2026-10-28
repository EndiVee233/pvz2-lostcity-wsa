package com.popcap.util;

import com.example.assetexam.ShellUtils;

/* JADX INFO: loaded from: K:\反编译PvZ2\raw\classes.dex */
public class PopCapNotificationForPlay extends PopCapNotificationAbstract {
    public PopCapNotificationForPlay(int initId, String initTitle, String initText, long initInterval, int initAction) {
        super(initId, initTitle, initText, initInterval, initAction);
        this.type = 16;
    }

    public static void updateNotification(PopCapNotificationAbstract dst, PopCapNotificationAbstract src) {
        if (dst.type == 16 && src.type == 16) {
            PopCapNotificationAbstract.updateNotification(dst, src);
        }
    }

    @Override // com.popcap.util.PopCapNotificationAbstract
    public String statusToHtml() {
        return "<" + PopCapConfigXmlElement.NOTIFICATION + ">" + ShellUtils.COMMAND_LINE_END + super.statusToHtml() + "</" + PopCapConfigXmlElement.NOTIFICATION + ">" + ShellUtils.COMMAND_LINE_END;
    }
}
