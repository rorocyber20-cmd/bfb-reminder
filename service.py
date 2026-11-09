import time

import core

core.log("service started")

# خدمة خلفية: تفحص كل 10 دقائق. الدالة check_and_notify تحترم الساعة المختارة في الإعدادات
# (لا ترسل قبلها)، وترسل كل موعد مرة واحدة فقط في اليوم.
while True:
    try:
        errors = core.check_and_notify()
        if errors:
            core.log(f"service errors: {errors}")
    except Exception as e:
        core.log(f"service crash: {e}")
    time.sleep(600)
