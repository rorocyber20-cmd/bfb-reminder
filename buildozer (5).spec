[app]

title = BFB Reminder
package.name = bfbreminder
package.domain = org.bfb

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,wav

version = 0.2

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,plyer,certifi,pyjnius,android,arabic-reshaper,python-bidi==0.4.2,six

orientation = portrait
fullscreen = 0

services = reminder:service.py:foreground:sticky:foregroundServiceType=specialUse

# الأيقونة وشاشة التحميل
icon.filename = icon.png
presplash.filename = presplash.png
android.presplash_color = #3919CB

# Android
android.api = 36
android.minapi = 21
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.permissions = POST_NOTIFICATIONS, VIBRATE, WAKE_LOCK, RECEIVE_BOOT_COMPLETED, FOREGROUND_SERVICE, FOREGROUND_SERVICE_SPECIAL_USE

# python-for-android: النسخة القديمة v2024.01.21 لا تدعم API 36، فنستعمل develop مؤقتًا
# (سنثبّته على رقم commit محدد بعد التأكد من نجاح البناء)
p4a.branch = develop
p4a.commit = 1c9a4b4f817847bd8505d972d1a0e6f965929a88

# تشغيل خدمة التذكير بعد إقلاع الهاتف: ملف Java صغير + تسجيل المستقبِل في المانيفست
android.add_src = java
p4a.extra_args = --extra-manifest-application-xml='<receiver android:name="org.bfb.bfbreminder.BootReceiver" android:enabled="true" android:exported="true"><intent-filter><action android:name="android.intent.action.BOOT_COMPLETED"/><action android:name="android.intent.action.QUICKBOOT_POWERON"/><action android:name="android.intent.action.MY_PACKAGE_REPLACED"/></intent-filter></receiver>'

[buildozer]

log_level = 2
warn_on_root = 1
