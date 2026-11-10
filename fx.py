"""مؤثرات الصوت والاهتزاز للألعاب. كل الدوال آمنة: لا ترفع أي خطأ مهما حدث،
فإذا تعذّر الصوت أو الاهتزاز تستمر اللعبة بصمت. إعدادات التشغيل/الإيقاف تُحفظ في ملف صغير مستقل."""
import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
_state = {'loaded': False, 'sound': True, 'vibrate': True}
_sounds = {}
_vib = {'obj': None, 'tried': False}


def _path():
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None and app.user_data_dir:
            return os.path.join(app.user_data_dir, 'fx.json')
    except Exception:
        pass
    return None


def _load():
    if _state['loaded']:
        return
    p = _path()
    if not p:
        return                     # التطبيق لم يجهز بعد: نجرّب في الاستدعاء التالي
    _state['loaded'] = True
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k in ('sound', 'vibrate'):
                if k in data:
                    _state[k] = bool(data[k])
        except Exception:
            pass


def _save():
    p = _path()
    if not p:
        return
    try:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({'sound': _state['sound'], 'vibrate': _state['vibrate']}, f)
    except Exception:
        pass


def is_on(which):
    _load()
    return bool(_state.get(which, True))


def set_on(which, value):
    _load()
    _state[which] = bool(value)
    _save()


_last_error = ['']


def _log(msg):
    _last_error[0] = msg
    try:
        import core
        core.log('fx: ' + msg)
    except Exception:
        pass


_pool = {'obj': None, 'ids': {}, 'tried': False}
_dir = {'path': None}


def _tone(freq, ms, vol=0.5, square=False):
    import math
    rate = 22050
    n = int(rate * ms / 1000)
    out = []
    for i in range(n):
        ph = 2 * math.pi * freq * i / rate
        v = (1 if math.sin(ph) >= 0 else -1) * 0.6 if square else math.sin(ph)
        env = min(1.0, i / (rate * 0.004), (n - i) / (rate * 0.02))     # دخول وخروج ناعمان
        out.append(v * env * vol)
    return out


def _gap(ms):
    return [0.0] * int(22050 * ms / 1000)


def _make_wavs(d):
    """يولّد مؤثرات الصوت (نغمات بسيطة) في المجلد d إن لم تكن موجودة. لا يحتاج أي ملف خارجي."""
    import struct
    import wave
    sounds = {
        'tap': _tone(880, 28, 0.45),
        'skip': _tone(440, 90, 0.4),
        'ok': _tone(660, 110) + _tone(880, 170),
        'bad': _tone(200, 280, 0.5, True),
        'win': _tone(523, 110) + _tone(659, 110) + _tone(784, 110) + _tone(1047, 300),
        'end': _tone(784, 130) + _gap(30) + _tone(659, 130) + _gap(30) + _tone(523, 260),
    }
    for name, samples in sounds.items():
        path = os.path.join(d, name + '.wav')
        if os.path.exists(path) and os.path.getsize(path) > 100:
            continue
        data = b''.join(struct.pack('<h', int(max(-1.0, min(1.0, x)) * 32000)) for x in samples)
        with wave.open(path, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(22050)
            w.writeframes(data)


_RATE = 16000


def _tone(freq, ms, vol=0.5, square=False):
    import math
    n = int(_RATE * ms / 1000)
    out = []
    for i in range(n):
        ph = 2 * math.pi * freq * i / _RATE
        v = math.sin(ph)
        if square:
            v = 0.6 if v >= 0 else -0.6
        env = min(1.0, i / (_RATE * 0.004), (n - i) / (_RATE * 0.02))
        out.append(v * env * vol)
    return out


def _gap(ms):
    return [0.0] * int(_RATE * ms / 1000)


def _recipes():
    return {
        'tap': _tone(880, 28, 0.45),
        'skip': _tone(440, 90, 0.4),
        'ok': _tone(660, 110) + _tone(880, 170),
        'bad': _tone(200, 280, 0.5, True),
        'win': _tone(523, 110) + _tone(659, 110) + _tone(784, 110) + _tone(1047, 300),
        'end': _tone(784, 130) + _gap(30) + _tone(659, 130) + _gap(30) + _tone(523, 260),
    }


def _write_wav(path, samples):
    import struct
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_RATE)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1.0, min(1.0, x)) * 30000)) for x in samples))


def _sounds_dir():
    """نولّد ملفات الصوت برمجيًا (موجات بسيطة) في مجلد بيانات التطبيق عند أول استعمال،
    فلا نحتاج أي ملف صوت جاهز ولا مجلدًا إضافيًا."""
    if _dir['path']:
        return _dir['path']
    candidates = []
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None and app.user_data_dir:
            candidates.append(os.path.join(app.user_data_dir, 'sounds'))
    except Exception:
        pass
    candidates.append(os.path.join(_BASE, 'sounds'))
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            recipes = None
            for name in ('tap', 'skip', 'ok', 'bad', 'win', 'end'):
                path = os.path.join(d, name + '.wav')
                if not os.path.exists(path) or os.path.getsize(path) < 100:
                    if recipes is None:
                        recipes = _recipes()
                    _write_wav(path, recipes[name])
            _dir['path'] = d
            return d
        except Exception as e:
            _log('create sounds failed in %s: %r' % (d, e))
    _dir['path'] = candidates[-1]
    return _dir['path']


def _soundpool():
    """على أندرويد نستعمل SoundPool: مباشر وسريع ولا يحتاج مكتبات صوت إضافية."""
    if _pool['tried']:
        return _pool['obj']
    _pool['tried'] = True
    try:
        from kivy.utils import platform
        if platform != 'android':
            return None
        from jnius import autoclass
        Builder = autoclass('android.media.SoundPool$Builder')
        AttrBuilder = autoclass('android.media.AudioAttributes$Builder')
        attrs = AttrBuilder().setUsage(14).setContentType(4).build()   # USAGE_GAME, SONIFICATION
        pool = Builder().setMaxStreams(6).setAudioAttributes(attrs).build()
        d = _sounds_dir()
        names = [f[:-4] for f in os.listdir(d) if f.endswith('.wav')] if os.path.isdir(d) else []
        if not names:
            _log('no sound files in: ' + d)
        for n in names:
            _pool['ids'][n] = pool.load(os.path.join(d, n + '.wav'), 1)
        _pool['obj'] = pool
    except Exception as e:
        _log('soundpool failed: ' + repr(e))
        _pool['obj'] = None
    return _pool['obj']


def play(name, volume=0.8):
    """تشغيل مؤثر صوتي: tap, ok, bad, skip, win, end."""
    try:
        if not is_on('sound'):
            return
        pool = _soundpool()
        if pool is not None:
            sid = _pool['ids'].get(name)
            if sid:
                pool.play(sid, volume, volume, 1, 0, 1.0)
            return
        snd = _sounds.get(name)
        if snd is None:
            from kivy.core.audio import SoundLoader
            snd = SoundLoader.load(os.path.join(_sounds_dir(), name + '.wav'))
            if not snd:
                _log('SoundLoader could not load ' + name)
            _sounds[name] = snd or False
        if snd:
            snd.volume = volume
            snd.stop()
            snd.play()
    except Exception as e:
        _log('play failed: ' + repr(e))


def _vibrator():
    if _vib['tried']:
        return _vib['obj']
    _vib['tried'] = True
    try:
        from kivy.utils import platform
        if platform != 'android':
            return None
        from jnius import autoclass
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        Context = autoclass('android.content.Context')
        _vib['obj'] = activity.getSystemService(Context.VIBRATOR_SERVICE)
    except Exception:
        _vib['obj'] = None
    return _vib['obj']


def buzz(ms=40):
    """اهتزاز قصير بالمللي ثانية."""
    try:
        if not is_on('vibrate'):
            return
        v = _vibrator()
        if v is None:
            return
        from jnius import autoclass
        sdk = autoclass('android.os.Build$VERSION').SDK_INT
        if sdk >= 26:
            VE = autoclass('android.os.VibrationEffect')
            v.vibrate(VE.createOneShot(int(ms), VE.DEFAULT_AMPLITUDE))
        else:
            v.vibrate(int(ms))
    except Exception:
        pass


def init():
    """تحميل الأصوات مبكرًا (SoundPool يحمّل في الخلفية، فنبدأه عند فتح التطبيق)."""
    try:
        _soundpool()
    except Exception as e:
        _log('init failed: ' + repr(e))


def diagnose():
    """نص قصير يوضح حالة الصوت (للعرض في الإعدادات عند الاختبار)."""
    parts = []
    try:
        d = _sounds_dir()
        files = sorted(f for f in os.listdir(d) if f.endswith('.wav')) if os.path.isdir(d) else []
        parts.append('folder ' + ('OK' if os.path.isdir(d) else 'MISSING'))
        parts.append('files %d/6' % len(files))
        pool = _soundpool()
        parts.append('engine ' + ('SoundPool' if pool is not None else 'SoundLoader'))
        if pool is not None:
            parts.append('loaded %d' % sum(1 for v in _pool['ids'].values() if v))
        if _last_error[0]:
            parts.append('error: ' + _last_error[0][:80])
    except Exception as e:
        parts.append('diag failed: ' + repr(e)[:80])
    return ' | '.join(parts)

