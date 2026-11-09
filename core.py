import json
import os
import time
from datetime import date, datetime

CHANNEL_ID = 'bfb_birthdays'


def data_dir():
    """مجلد بيانات التطبيق: على أندرويد مجلد خاص يبقى بعد التحديثات."""
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except Exception:
        return os.path.dirname(os.path.abspath(__file__))


DATA_FILE = os.path.join(data_dir(), 'birthdays.json')
NOTIFIED_FILE = os.path.join(data_dir(), 'notified.json')
LOG_FILE = os.path.join(data_dir(), 'log.txt')


def log(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    except Exception:
        pass


def _read(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _write(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)
        f.flush()
        os.fsync(f.fileno())


def load_birthdays():
    data = _read(DATA_FILE, [])
    if not isinstance(data, list):
        return []
    return [
        {'name': b.get('name', ''), 'date': b.get('date', '')}
        for b in data
        if isinstance(b, dict) and b.get('name') and b.get('date')
    ]


def save_birthdays(items):
    _write(DATA_FILE, items)


# ---------------------------------------------------------------
# إعدادات المظهر
# ---------------------------------------------------------------
SETTINGS_FILE = os.path.join(data_dir(), 'settings.json')

DEFAULT_SETTINGS = {
    'theme': 'light',
    'accent': 'blue',
    'radius': 10,
    'btn_height': 50,
    'font_scale': 1.0,
    'help_seen': False,
    'notify_week': 1,
    'notify_day': 1,
    'notify_hour': 9,
}


def load_settings():
    data = _read(SETTINGS_FILE, {})
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(data, dict):
        merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    return merged


def save_settings(prefs):
    _write(SETTINGS_FILE, prefs)


# ---------------------------------------------------------------
# النسخ الاحتياطي: نص واحد يحوي أعياد الميلاد وإعدادات المظهر
# ---------------------------------------------------------------
BACKUP_PREFIX = 'BFBK-'


def export_backup():
    import base64
    import zlib
    payload = {'v': 1, 'birthdays': load_birthdays(), 'settings': load_settings()}
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return BACKUP_PREFIX + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode('ascii')


def import_backup(text):
    """يدمج النسخة الاحتياطية: يضيف الأعياد غير الموجودة ويستعيد الإعدادات.
    يرجع (عدد الأعياد المضافة، عدد الأعياد الموجودة مسبقًا). يرفع ValueError إن كان النص غير صالح."""
    import base64
    import re
    import zlib
    m = re.search(BACKUP_PREFIX + r'([A-Za-z0-9_\-=]+)', text or '')
    if not m:
        raise ValueError('no backup code')
    try:
        data = json.loads(zlib.decompress(base64.urlsafe_b64decode(m.group(1))).decode('utf-8'))
        items = data['birthdays']
        prefs = data.get('settings', {})
        if not isinstance(items, list) or not isinstance(prefs, dict):
            raise ValueError('bad structure')
    except Exception:
        raise ValueError('bad backup code')
    current = load_birthdays()
    seen = {(b['name'], b['date']) for b in current}
    added = skipped = 0
    for b in items:
        if not (isinstance(b, dict) and b.get('name') and b.get('date')):
            continue
        key = (str(b['name']), str(b['date']))
        try:
            datetime.strptime(key[1], '%Y-%m-%d')
        except ValueError:
            continue
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        current.append({'name': key[0], 'date': key[1]})
        added += 1
    save_birthdays(current)
    merged = load_settings()
    for k, default in DEFAULT_SETTINGS.items():
        v = prefs.get(k)
        if isinstance(default, str) and isinstance(v, str):
            merged[k] = v
        elif isinstance(default, (int, float)) and isinstance(v, (int, float)) \
                and not isinstance(v, bool):
            merged[k] = v
    save_settings(merged)
    return added, skipped


def _safe_replace_year(d, year):
    try:
        return d.replace(year=year)
    except ValueError:  # 29 فبراير في سنة غير كبيسة
        return date(year, 3, 1)


def days_until(date_str, today=None):
    """عدد الأيام المتبقية لعيد الميلاد القادم (0 = اليوم)."""
    today = today or date.today()
    born = datetime.strptime(date_str, "%Y-%m-%d").date()
    nxt = _safe_replace_year(born, today.year)
    if nxt < today:
        nxt = _safe_replace_year(born, today.year + 1)
    return (nxt - today).days


def next_age(date_str, today=None):
    """العمر الذي سيكمله صاحب عيد الميلاد القادم."""
    today = today or date.today()
    born = datetime.strptime(date_str, "%Y-%m-%d").date()
    nxt = _safe_replace_year(born, today.year)
    if nxt < today:
        nxt = _safe_replace_year(born, today.year + 1)
    return max(nxt.year - born.year, 1)


def check_birth(date_str, today=None):
    """يرجع '' إن كان التاريخ صالحًا، وإلا نص الخطأ."""
    today = today or date.today()
    try:
        born = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "Wrong date format. Use YYYY-MM-DD"
    if born > today:
        return "That date is in the future"
    return ""


# ---------------------------------------------------------------
# الإشعارات (مباشرة عبر نظام أندرويد، بدون plyer)
# ---------------------------------------------------------------
def _get_context():
    from jnius import autoclass
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    if activity is not None:
        return activity
    return autoclass('org.kivy.android.PythonService').mService


def send_notification(title, message):
    """يرجع (True, '') عند النجاح، أو (False, سبب الفشل)."""
    try:
        from kivy.utils import platform
    except Exception:
        platform = ''

    if platform != 'android':
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=10)
            return True, ''
        except Exception as e:
            return False, str(e)

    try:
        from jnius import autoclass

        Context = autoclass('android.content.Context')
        VERSION = autoclass('android.os.Build$VERSION')
        JString = autoclass('java.lang.String')
        Builder = autoclass('android.app.Notification$Builder')

        ctx = _get_context()
        if ctx is None:
            return False, 'No Android context'

        nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)

        if not nm.areNotificationsEnabled():
            return False, 'Notifications are OFF for this app (phone settings)'

        if VERSION.SDK_INT >= 26:
            NChannel = autoclass('android.app.NotificationChannel')
            NManager = autoclass('android.app.NotificationManager')
            channel = NChannel(
                CHANNEL_ID,
                JString('Birthday reminders'.encode('utf-8')),
                NManager.IMPORTANCE_HIGH,
            )
            nm.createNotificationChannel(channel)
            builder = Builder(ctx, CHANNEL_ID)
        else:
            builder = Builder(ctx)

        icon = ctx.getApplicationInfo().icon
        if not icon:
            icon = autoclass('android.R$drawable').ic_dialog_info
        builder.setSmallIcon(icon)
        builder.setContentTitle(JString(title.encode('utf-8')))
        builder.setContentText(JString(message.encode('utf-8')))
        builder.setAutoCancel(True)

        # الضغط على الإشعار يفتح التطبيق (اختياري، لا يوقف الإشعار إن فشل)
        try:
            PendingIntent = autoclass('android.app.PendingIntent')
            intent = ctx.getPackageManager().getLaunchIntentForPackage(
                ctx.getPackageName())
            flags = PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
            builder.setContentIntent(
                PendingIntent.getActivity(ctx, 0, intent, flags))
        except Exception as e:
            log(f"pending intent: {e}")

        nm.notify(int(time.time()) % 100000, builder.build())
        return True, ''
    except Exception as e:
        log(f"send_notification failed: {e}")
        return False, str(e)


def test_notification():
    return send_notification("BFB Reminder", "اختبار الإشعارات ✅")


def notify_hour():
    try:
        return max(0, min(23, int(load_settings().get('notify_hour', 9))))
    except Exception:
        return 9


def check_and_notify(respect_hour=True):
    """يرسل إشعار قبل أسبوع وقبل يوم، مرة واحدة فقط لكل موعد.
    لا يرسل شيئًا قبل الساعة المختارة في الإعدادات (يرسل بعدها في نفس اليوم إن فات الموعد).
    يرجع قائمة بأخطاء الإرسال (فارغة إن لم يحدث خطأ)."""
    errors = []
    if respect_hour and datetime.now().hour < notify_hour():
        return errors
    today_str = date.today().isoformat()
    notified = _read(NOTIFIED_FILE, {})
    changed = False

    prefs = load_settings()
    wanted = set()
    if prefs.get('notify_week', 1):
        wanted.add(7)
    if prefs.get('notify_day', 1):
        wanted.add(1)
    if not wanted:
        return errors

    for item in load_birthdays():
        try:
            d = days_until(item['date'])
        except Exception:
            continue

        if d not in wanted:
            continue

        key = f"{item['name']}|{item['date']}|{d}"
        if notified.get(key) == today_str:
            continue

        if d == 7:
            msg = f"باقي أسبوع واحد على عيد ميلاد: {item['name']}!"
        else:
            msg = f"باقي يوم واحد فقط على عيد ميلاد: {item['name']}!"

        ok, err = send_notification("تنبيه عيد ميلاد 🎂", msg)
        if ok:
            notified[key] = today_str
            changed = True
        else:
            errors.append(err)

    if changed:
        try:
            _write(NOTIFIED_FILE, notified)
        except Exception as e:
            log(f"save notified: {e}")

    return errors
