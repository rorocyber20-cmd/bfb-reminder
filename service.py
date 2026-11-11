import os
import time
import traceback


def _trace(msg):
    """سجل مستقل لا يعتمد على أي ملف آخر: يكتب حتى لو فشل استيراد core."""
    try:
        base = os.environ.get('ANDROID_PRIVATE') or os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, 'svc_trace.txt'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('%d %H:%M:%S ') + msg + '\n')
    except Exception:
        pass


_trace('service.py begins pid=%d' % os.getpid())

try:
    from datetime import datetime
    import core
except Exception:
    _trace('IMPORT FAILED: ' + traceback.format_exc()[-400:].replace('\n', ' / '))
    raise

core.log(f"service started v4 pid={os.getpid()}")
_trace('core imported, loop starts')

# خدمة خلفية: تفحص كل 10 دقائق. الدالة check_and_notify تحترم الساعة المختارة في الإعدادات
# (لا ترسل قبلها)، وترسل كل موعد مرة واحدة فقط في اليوم.
while True:
    try:
        errors = core.check_and_notify()
        core.log(f"service tick hour={datetime.now().hour} errors={len(errors) if errors else 0}")
        _trace('tick ok')
        if errors:
            core.log(f"service errors: {errors}")
    except Exception as e:
        core.log(f"service crash: {e}")
        _trace('tick crash: ' + repr(e)[:200])
    time.sleep(600)
