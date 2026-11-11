import time
from datetime import datetime

import core

import os
core.log(f"service started v3 pid={os.getpid()}")

# خدمة خلفية: تفحص كل 10 دقائق. الدالة check_and_notify تحترم الساعة المختارة في الإعدادات
# (لا ترسل قبلها)، وترسل كل موعد مرة واحدة فقط في اليوم.
while True:
    try:
        errors = core.check_and_notify()
        core.log(f"service tick hour={datetime.now().hour} errors={len(errors) if errors else 0}")
        if errors:
            core.log(f"service errors: {errors}")
    except Exception as e:
        core.log(f"service crash: {e}")
    time.sleep(600)
