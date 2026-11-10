package org.bfb.bfbreminder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/**
 * يعيد تشغيل خدمة التذكير تلقائيًا بعد إقلاع الهاتف (أو بعد تحديث التطبيق).
 * ServiceReminder يولّده python-for-android من السطر: services = reminder:service.py:foreground
 */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) {
            return;
        }
        String action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action)
                || "android.intent.action.QUICKBOOT_POWERON".equals(action)
                || Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) {
            try {
                ServiceReminder.start(context, "boot");
            } catch (Exception e) {
                // لا نكسر النظام إن تعذّر التشغيل؛ يبدأ التذكير عند فتح التطبيق
            }
        }
    }
}
