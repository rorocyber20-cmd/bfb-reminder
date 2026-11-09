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


def _log(msg):
    try:
        import core
        core.log('fx: ' + msg)
    except Exception:
        pass


_pool = {'obj': None, 'ids': {}, 'tried': False}


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
        d = os.path.join(_BASE, 'sounds')
        names = [f[:-4] for f in os.listdir(d) if f.endswith('.wav')] if os.path.isdir(d) else []
        if not names:
            _log('sounds folder is missing or empty: ' + d)
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
            snd = SoundLoader.load(os.path.join(_BASE, 'sounds', name + '.wav'))
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
