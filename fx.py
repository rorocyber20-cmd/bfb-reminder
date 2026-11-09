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


def play(name, volume=0.8):
    """تشغيل مؤثر صوتي: tap, ok, bad, skip, win, end."""
    try:
        if not is_on('sound'):
            return
        snd = _sounds.get(name)
        if snd is None:
            from kivy.core.audio import SoundLoader
            snd = SoundLoader.load(os.path.join(_BASE, 'sounds', name + '.wav'))
            _sounds[name] = snd or False
        if snd:
            snd.volume = volume
            snd.stop()
            snd.play()
    except Exception:
        pass


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
