"""شاشة الألعاب: قائمة ألعاب (تُضاف ألعاب جديدة تباعًا). أولها: من يعرفني أكثر؟"""
import os
import re
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen

import core
import game_data as gd

# الألعاب الإضافية: إن فشل تحميل إحداها تبقى بقية الألعاب تعمل
try:
    from game_party import PartyMixin
    PARTY_OK = True
except Exception:
    core.log(traceback.format_exc())
    PARTY_OK = False

    class PartyMixin:
        def party_init(self):
            pass

def _safe_import(modname, clsname, init_names):
    try:
        mod = __import__(modname)
        return getattr(mod, clsname), True
    except Exception:
        core.log(traceback.format_exc())
        ns = {n: (lambda self: None) for n in init_names}
        return type(clsname, (), ns), False


LieMixin, LIE_OK = _safe_import('game_lie', 'LieMixin', ['lie_init'])
ImpostorMixin, IMP_OK = _safe_import('game_impostor', 'ImpostorMixin', ['imp_init'])
BrainMixin, BRAIN_OK = _safe_import('game_brain', 'BrainMixin', ['brain_init'])
FakeTimerMixin, FAKE_OK = _safe_import('game_fake', 'FakeTimerMixin', ['ft_init'])
SurvivorMixin, SURV_OK = _safe_import('game_survivor', 'SurvivorMixin', ['ls_init'])
BombMixin, BOMB_OK = _safe_import('game_bomb', 'BombMixin', ['bc_init'])
OutbreakMixin, OB_OK = _safe_import('game_outbreak', 'OutbreakMixin', ['ob_init'])

try:
    from game_tools import ToolsMixin
    TOOLS_OK = True
except Exception:
    core.log(traceback.format_exc())
    TOOLS_OK = False

    class ToolsMixin:
        def tools_init(self):
            pass

        def stop_anim(self):
            pass

try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    # خط Cairo المرفق ينقصه الشكل المنفصل (isolated) للحروف، فنستعمل الحرف الأصلي بدله
    try:
        _reshape = arabic_reshaper.ArabicReshaper(
            configuration={'use_unshaped_instead_of_isolated': True}).reshape
    except Exception:
        _reshape = arabic_reshaper.reshape

    def fix_arabic(text):
        try:
            return get_display(_reshape(text))
        except Exception:
            return text
except Exception:
    def fix_arabic(text):
        return text


PLAYED_FILE = os.path.join(core.data_dir(), 'played_codes.json')
HOSTED_FILE = os.path.join(core.data_dir(), 'knowme_hosted.json')
PREFS_FILE = os.path.join(core.data_dir(), 'gift_prefs.json')   # اللغة مشتركة مع تبويب الهدايا
GRAY = [0.45, 0.47, 0.52, 1]
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]
HAS_ARABIC = re.compile('[؀-ۿ]')

# نصوص الواجهة (إنجليزي، عربي)
S = {
    'title': ('Games', 'الألعاب'),
    'choose': ('Choose a game', 'اختر لعبة'),
    'soon': ('More games are coming soon...', 'المزيد من الألعاب قريبًا...'),
    'play': ('Play', 'العب'),
    'td_title': ('Truth or Dare', 'صراحة وتحدي'),
    'td_desc': ('Pass the phone around: pick truth or dare and let the fun begin.',
                'مرّروا الهاتف بين الأصدقاء، اختر صراحة أو تحدي وابدأ المرح.'),
    'ml_title': ('Who is most likely to...', 'من الأكثر احتمالًا أن ...'),
    'ml_desc': ('3 or more players vote in secret on funny questions about the group.',
                'من 3 لاعبين فأكثر يصوّتون سرًّا على أسئلة طريفة عن أفراد المجموعة.'),
    'tl_title': ('Decision tools', 'أدوات القرار'),
    'tl_desc': ('Random picker, wheel and coin flip: who pays? where do we eat?',
                'اختيار عشوائي وعجلة وقطعة نقود: من يدفع؟ أين نأكل؟'),
    'my_quizzes': ('Results', 'نتائج'),
    'results_title': ('Results', 'النتائج'),
    'added_n': ('Added {n} result(s).', 'تمت إضافة {n} نتيجة.'),
    'no_quizzes': ('You have not created a quiz yet.', 'لم تنشئ أي اختبار بعد.'),
    'quiz_line': ('Quiz {i}  -  {n} friend(s) answered', 'الاختبار {i}  -  أجاب {n} من الأصدقاء'),
    'view': ('View results', 'عرض النتائج'),
    'view_res': ('Results', 'نتائج'),
    'res_head': ('Friends who answered your quiz', 'الأصدقاء الذين أجابوا عن اختبارك'),
    'res_hint': ('Ask each friend to send you their result code. Copy it and open this page: it is added automatically. You can also paste it here.',
                 'اطلب من كل صديق أن يرسل لك كود نتيجته. انسخه وافتح هذه الصفحة وسيُضاف تلقائيًا، أو الصقه هنا.'),
    'res_ph': ('BFBR-XXXXX-XXXXX-...', 'BFBR-XXXXX-XXXXX-...'),
    'add_res': ('Add result', 'إضافة النتيجة'),
    'bad_result': ('This is not a valid result code. Check that you copied all of it.',
                   'هذا ليس كود نتيجة صالحًا. تأكد أنك نسخته كاملًا.'),
    'wrong_quiz': ('This result belongs to a different quiz.', 'هذه النتيجة تخص اختبارًا آخر.'),
    'added': ('Added: {name} got {s} / {n}', 'تمت الإضافة: {name} حصل على {s} / {n}'),
    'no_res': ('No results yet.', 'لا توجد نتائج بعد.'),
    'rank_line': ('{i}. {name}  -  {s} / {n}', '{i}. {name}  -  {s} / {n}'),
    'your_name_head': ('What is your name?', 'ما اسمك؟'),
    'your_name_hint': ('So {name} knows who answered.', 'ليعرف {name} من الذي أجاب.'),
    'send_res': ('Send this result code to {name} so they can see your score:',
                 'أرسل كود النتيجة هذا إلى {name} ليرى نتيجتك:'),
    'copy_res': ('Copy result code', 'نسخ كود النتيجة'),
    'share_res': ('Share result', 'مشاركة النتيجة'),
    'res_share_en': ('Here is my result in "Who knows me best?". In the BFB app open Games > Who knows me best? > '
                     'My quizzes and results, and paste this code:',
                     ''),
    'res_share_ar': ('', 'هذه نتيجتي في لعبة «من يعرفني أكثر؟». في تطبيق BFB افتح الألعاب ثم من يعرفني أكثر؟ '
                         'ثم اختباراتي والنتائج، والصق هذا الكود:'),
    'lie_title': ('Two Truths and a Lie', 'الكذبة والحقيقة'),
    'lie_desc': ('Write 2 truths and 1 lie about yourself; your friend finds the lie.',
                 'اكتب حقيقتين وكذبة عن نفسك، وصديقك يكتشف الكذبة.'),
    'imp_title': ('The Impostor', 'المحتال'),
    'imp_desc': ('One player has a different word. Pass the phone and find the impostor.',
                 'لاعب واحد يملك كلمة مختلفة. مرّروا الهاتف واكتشفوا المحتال.'),
    'tv_title': ('General Knowledge', 'ثقافة عامة'),
    'tv_desc': ('10 questions and a best score to beat.', '10 أسئلة ورقم قياسي لتتجاوزه.'),
    'rd_title': ('Riddles', 'ألغاز'),
    'rd_desc': ('Brain teasers with hints and answers.', 'ألغاز للتفكير مع تلميحات وأجوبة.'),
    'played': ('You already played this challenge. Ask your friend for a new one.',
               'لعبت هذا التحدي من قبل. اطلب من صديقك تحديًا جديدًا.'),
    'cat_friends': ('Friends Games', 'ألعاب الأصدقاء'),
    'cat_friends_d': ('Play with friends: by sending a code or passing one phone.',
                      'العبوها مع أصدقائكم: بإرسال كود أو بتمرير هاتف واحد.'),
    'cat_quick': ('Quick Games', 'ألعاب سريعة'),
    'cat_quick_d': ('Short and fast games, a minute or two each.', 'ألعاب قصيرة وسريعة، دقيقة أو دقيقتان لكل جولة.'),
    'cat_brain': ('Brain Games', 'ألعاب العقل'),
    'cat_brain_d': ('Questions and riddles, solo or as a group.', 'أسئلة وألغاز، فردية أو جماعية.'),
    'cat_tools': ('Tools', 'أدوات'),
    'cat_tools_d': ('Wheel, random picker and coin flip.', 'عجلة واختيار عشوائي وقطعة نقود.'),
    'choose_cat': ('Choose a category', 'اختر صنفًا'),
    'all_cats': ('All categories', 'كل الأصناف'),
    'ob_title': ('Who is infected?', 'من المصاب؟'),
    'ob_desc': ('4+ players on one phone. Find the secret infected player before they eliminate everyone. Optional Doctor.',
                'من 4 لاعبين على هاتف واحد. اكتشفوا المصاب السري قبل أن يقصي الجميع. مع طبيب اختياري.'),
    'bc_title': ('Bomb Code', 'كود القنبلة'),
    'bc_desc': ('Cut a wire in 5 seconds. One wire blows up the bomb. Last player standing wins.',
                'اقطع سلكًا في 5 ثوانٍ. سلك واحد يفجّر القنبلة. آخر لاعب يبقى يفوز.'),
    'ft_title': ('Fake Timer', 'المؤقت المخادع'),
    'ft_desc': ('Fake signals try to trick you. Press only on the GREEN GO!',
                'إشارات مزيفة تحاول خداعك. اضغط فقط عند انطلق! الخضراء.'),
    'k_title': ('Who knows me best?', 'من يعرفني أكثر؟'),
    'k_desc': ('Answer 10 questions about yourself, send the code to a friend, and see how many they guess right.',
               'أجب عن 10 أسئلة عن نفسك، وأرسل الكود إلى صديقك لترى كم إجابة سيخمّنها صحيحة.'),
    'create': ('Create my quiz', 'أنشئ اختباري'),
    'have_code': ('I received a code', 'وصلني كود من صديق'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'back': ('Back', 'رجوع'),
    'name_head': ('What is your name?', 'ما اسمك؟'),
    'name_hint': ('Your friend will see this name.', 'سيرى صديقك هذا الاسم.'),
    'name_ph': ('Your name', 'اسمك'),
    'cont': ('Continue', 'متابعة'),
    'empty_name': ('Please enter your name.', 'الرجاء إدخال اسمك.'),
    'about_you': ('Answer about yourself', 'أجب عن نفسك'),
    'guess': ("Guess {name}'s answer", 'خمّن إجابة {name}'),
    'progress': ('Question {i} of {n}', 'السؤال {i} من {n}'),
    'done_head': ('Your quiz is ready!', 'اختبارك جاهز!'),
    'done_body': ('Send this code to your friend. They open the app, go to Games, and paste it.',
                  'أرسل هذا الكود إلى صديقك. يفتح التطبيق ثم الألعاب ثم يلصقه.'),
    'copy': ('Copy code', 'نسخ الكود'),
    'copied': ('Code copied.', 'تم نسخ الكود.'),
    'share': ('Share', 'مشاركة'),
    'newquiz': ('Create another quiz', 'أنشئ اختبارًا آخر'),
    'code_head': ('Paste the code you received', 'الصق الكود الذي وصلك'),
    'code_ph': ('BFB-XXXXX-XXXXX-...', 'BFB-XXXXX-XXXXX-...'),
    'paste': ('Paste', 'لصق'),
    'start': ('Start', 'ابدأ'),
    'bad_code': ('This code is not valid. Check that you copied all of it.',
                 'هذا الكود غير صالح. تأكد أنك نسخته كاملًا.'),
    'guest_head': ('How well do you know {name}?', 'هل تعرف {name} جيدًا؟'),
    'score_head': ('Your score', 'نتيجتك'),
    'right': ('Correct', 'صحيحة'),
    'wrong': ('Wrong', 'خاطئة'),
    'correct_ans': ('Correct answer: {a}', 'الإجابة الصحيحة: {a}'),
    'your_ans': ('Your answer: {a}', 'إجابتك: {a}'),
    'again': ('Try another code', 'جرّب كودًا آخر'),
    'res10': ('Perfect! You know {name} better than anyone!', 'ممتاز! تعرف {name} أكثر من أي أحد!'),
    'res8': ("Amazing! You are one of {name}'s closest friends.", 'رائع! أنت من أقرب أصدقاء {name}.'),
    'res5': ('Not bad! You know {name} quite well.', 'ليس سيئًا! تعرف {name} جيدًا.'),
    'res3': ('Hmm... you still have things to learn about {name}.', 'همم... ما زال عليك أن تتعرف على {name} أكثر.'),
    'res0': ('Oops! Time to spend more time with {name}!', 'حان وقت قضاء وقت أطول مع {name}!'),
    'share_en': ('Think you know me well? Open the BFB app > Games > Who knows me best? > '
                 'I received a code, and paste the code below:'),
    'share_ar': ('هل تعرفني جيدًا؟ افتح تطبيق BFB ثم الألعاب ثم من يعرفني أكثر؟ '
                 'ثم وصلني كود، والصق الكود أدناه:'),
}

# قائمة الألعاب: (المعرّف، العنوان، الوصف). لإضافة لعبة جديدة أضف سطرًا هنا وفرعًا في open_game.
# الأصناف: (المعرّف، عنوانها، وصفها)
CATS = [('friends', 'cat_friends', 'cat_friends_d'),
        ('quick', 'cat_quick', 'cat_quick_d'),
        ('brain', 'cat_brain', 'cat_brain_d'),
        ('tools', 'cat_tools', 'cat_tools_d')]

# الألعاب: (المعرّف، العنوان، الوصف، الصنف). لإضافة لعبة جديدة: أضف سطرًا هنا وفرعًا في open_game.
GAMES = [('knowme', 'k_title', 'k_desc', 'friends')]
if LIE_OK:
    GAMES += [('lie', 'lie_title', 'lie_desc', 'friends')]
if PARTY_OK:
    GAMES += [('likely', 'ml_title', 'ml_desc', 'friends'),
              ('truthdare', 'td_title', 'td_desc', 'friends')]
if IMP_OK:
    GAMES += [('impostor', 'imp_title', 'imp_desc', 'friends')]
if OB_OK:
    GAMES += [('outbreak', 'ob_title', 'ob_desc', 'friends')]
if FAKE_OK:
    GAMES += [('faketimer', 'ft_title', 'ft_desc', 'quick')]
if BOMB_OK:
    GAMES += [('bomb', 'bc_title', 'bc_desc', 'quick')]
if BRAIN_OK:
    GAMES += [('trivia', 'tv_title', 'tv_desc', 'brain'), ('riddles', 'rd_title', 'rd_desc', 'brain')]
if TOOLS_OK:
    GAMES += [('tools', 'tl_title', 'tl_desc', 'tools')]


def share_text(text):
    """يفتح قائمة المشاركة في أندرويد (إنستغرام، واتساب...)."""
    from kivy.utils import platform
    if platform != 'android':
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)
        raise RuntimeError('Sharing works on Android only (text was copied).')
    from jnius import autoclass, cast
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    JString = autoclass('java.lang.String')
    intent = Intent(Intent.ACTION_SEND)
    intent.setType('text/plain')
    intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', JString(text)))
    chooser = Intent.createChooser(intent, cast('java.lang.CharSequence', JString('BFB')))
    PythonActivity.mActivity.startActivity(chooser)


class GamesScreen(PartyMixin, LieMixin, ImpostorMixin, BrainMixin, FakeTimerMixin,
                  SurvivorMixin, BombMixin, OutbreakMixin, ToolsMixin, Screen):
    title_text = StringProperty('')
    lang_label = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lang = self.saved_lang()
        self.stage = 'menu'
        self.status = ''
        self.status_ok = False
        self.host_name = ''
        self.host_qids = []
        self.host_answers = []
        self.code = ''
        self.code_text = ''
        self.guest = None
        self.guest_name = ''
        self.result_code = ''
        self.sel_id = None
        self.last_clip = ''
        self.guest_answers = []
        self.qi = 0
        self._name_ti = None
        self._code_ti = None
        self.form = {}
        self._tis = {}
        self.party_init()
        self.lie_init()
        self.imp_init()
        self.brain_init()
        self.ft_init()
        self.ls_init()
        self.bc_init()
        self.ob_init()
        self.cat = None
        self.tools_init()

    # ---------- دورة الحياة ----------
    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda dt: self.render(), 0.2)

    def on_pre_enter(self, *args):
        self.lang = self.saved_lang()
        self.render()

    def saved_lang(self):
        prefs = core._read(PREFS_FILE, {})
        lang = prefs.get('lang') if isinstance(prefs, dict) else None
        return lang if lang in ('en', 'ar') else 'en'

    # ---------- مساعدات النص ----------
    def is_ar(self):
        return self.lang == 'ar'

    def tx(self, key, fs=16, pad=60, **fmt):
        en, ar = S[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def pair(self, en, ar, fs=16, pad=60, **fmt):
        text = ar if self.is_ar() else en
        if fmt:
            text = text.format(**fmt)
        return self.shape(text, fs, pad)

    def shape(self, text, fs=16, pad=60):
        if not self.is_ar():
            return text
        width_dp = Window.width / dp(1)
        max_chars = max(12, int((width_dp - pad) / (fs * 0.55)))
        lines, cur = [], ''
        for w in text.split():
            if cur and len(cur) + 1 + len(w) > max_chars:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + ' ' + w) if cur else w
        if cur:
            lines.append(cur)
        return '\n'.join(fix_arabic(l) for l in lines)

    def tt(self, table, key, fs=16, pad=60, **fmt):
        en, ar = table[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def wrap_user(self, text, fs=16, pad=100):
        """نص كتبه المستخدم (قد يكون عربيًا أو إنجليزيًا): يُقسَّم لأسطر ويُشكَّل العربي منه."""
        width_dp = Window.width / dp(1)
        max_chars = max(12, int((width_dp - pad) / (fs * 0.55)))
        lines, cur = [], ''
        for w in (text or '').split():
            if cur and len(cur) + 1 + len(w) > max_chars:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + ' ' + w) if cur else w
        if cur:
            lines.append(cur)
        return '\n'.join(fix_arabic(l) if HAS_ARABIC.search(l) else l for l in lines)

    def do_copy(self, text):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(text)
            self.set_status(self.tx('copied', 13, 60), ok=True)
        except Exception as e:
            self.set_status(f"Error: {e}")

    def do_share(self, text):
        try:
            share_text(text)
        except Exception as e:
            self.set_status(f"{e}")

    def claim_code(self, game, payload):
        """فرصة واحدة لكل كود تحدٍّ: يرجع False إن سبق لعبه على هذا الهاتف، وإلا يسجّله.
        يُستعمل في كل لعبة تعتمد على كود يستقبله الصديق (حتى لا يعيد لصقه ليعرف الإجابات)."""
        import hashlib
        cid = hashlib.md5(str(payload).upper().replace('-', '').encode()).hexdigest()[:12]
        data = core._read(PLAYED_FILE, {})
        data = data if isinstance(data, dict) else {}
        seen = data.get(game, [])
        if cid in seen:
            return False
        data[game] = (seen + [cid])[-200:]
        try:
            core._write(PLAYED_FILE, data)
        except Exception as e:
            core.log(f"played codes: {e}")
        return True

    def disp_name(self, name):
        """اسم الصديق: في الواجهة الإنجليزية نشكّله بنفسنا، وفي العربية يشكّله shape()."""
        if not self.is_ar() and HAS_ARABIC.search(name or ''):
            return fix_arabic(name)
        return name

    def opt_text(self, qid, idx):
        en, ar = gd.POOL[qid][2][idx]
        return ar if self.is_ar() else en

    # ---------- بناء العناصر ----------
    def label(self, text, fs=16, bold=False, color=None, halign='center'):
        app = App.get_running_app()
        lbl = Label(
            text=text, font_name=app.font, font_size=sp(fs) * app.font_scale,
            bold=bold, color=color or app.text_color,
            halign=halign, valign='middle', size_hint_y=None, height=dp(30),
        )
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda inst, s: setattr(inst, 'height', s[1] + dp(8)))
        return lbl

    def button(self, text, on_release, gray=False):
        app = App.get_running_app()
        btn = Factory.StyledButton(text=text)
        if gray:
            btn.custom_bg = GRAY
        lines = text.count('\n') + 1
        btn.height = max(dp(app.btn_height), dp(22) * lines + dp(26))
        btn.bind(on_release=lambda *a: on_release())
        return btn

    def entry(self, hint, text='', multiline=False, height=None, key=None):
        app = App.get_running_app()
        box = BoxLayout(size_hint_y=None, height=height or dp(app.btn_height))
        with box.canvas.before:
            Color(*app.card_color)
            rect = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(app.radius)])
        box.bind(pos=lambda i, v: setattr(rect, 'pos', i.pos),
                 size=lambda i, v: setattr(rect, 'size', i.size))
        if key:
            text = self.form.get(key, text)
        ti = Factory.CustomTextInput(hint_text=hint, text=text, multiline=multiline)
        if key:
            self._tis[key] = ti
        box.add_widget(ti)
        return box, ti

    # ---------- العرض ----------
    def snapshot(self):
        """يقرأ ما كتبه المستخدم دون مسح الحقول."""
        try:
            if self._name_ti is not None:
                self.host_name = self._name_ti.text
            if self._code_ti is not None:
                self.code_text = self._code_ti.text
            for k, ti in self._tis.items():
                self.form[k] = ti.text
        except Exception:
            pass

    def capture(self):
        """يحفظ ما كتبه المستخدم قبل إعادة بناء الشاشة."""
        self.stop_anim()
        for fn in ('ft_stop', 'ls_stop', 'bc_stop', 'ob_stop'):
            getattr(self, fn, lambda: None)()
        self.snapshot()
        self._name_ti = None
        self._code_ti = None
        self._tis = {}

    def render(self):
        if 'content' not in self.ids:
            return
        self.capture()
        box = self.ids.content
        box.clear_widgets()
        self.title_text = self.tx('title', 22, 150)
        self.lang_label = fix_arabic('عربي') if not self.is_ar() else 'English'
        try:
            getattr(self, 'show_' + self.stage)(box)
            if self.status:
                app = App.get_running_app()
                box.add_widget(self.label(self.status, fs=13,
                                          color=GREEN if self.status_ok else RED))
        except Exception:
            box.clear_widgets()
            box.add_widget(self.label(traceback.format_exc(), fs=11, halign='left'))
        self.ids.scroll.scroll_y = 1
        # في لعبة المؤقت المخادع نمنع التمرير كي لا يتأخر وصول اللمسة للأزرار
        self.ids.scroll.do_scroll_y = self.stage != 'ft_play'

    def go(self, stage):
        self.capture()
        self.stage = stage
        self.status = ''
        self.status_ok = False
        if stage == 'host_list':
            msg = self.auto_clipboard()
            if msg:
                self.status, self.status_ok = msg, True
        self.render()

    def set_status(self, text, ok=False):
        self.status = text
        self.status_ok = ok
        self.render()

    # ---------- قائمة الألعاب ----------
    def show_menu(self, box):
        app = App.get_running_app()
        halign = 'right' if self.is_ar() else 'left'
        if self.cat is None:
            box.add_widget(self.label(self.tx('choose_cat', 20, 60), fs=20, bold=True,
                                      color=app.primary_color))
            for cid, tkey, dkey in CATS:
                if not any(g[3] == cid for g in GAMES):
                    continue
                card = Factory.GiftCard()
                card.add_widget(self.label(self.tx(tkey, 18, 90), fs=18, bold=True, halign=halign))
                card.add_widget(self.label(self.tx(dkey, 13, 90), fs=13, color=app.muted_color,
                                           halign=halign))
                card.add_widget(self.button(self.tx('play', 16, 100),
                                            lambda c=cid: self.open_cat(c)))
                box.add_widget(card)
            box.add_widget(self.label(self.tx('soon', 13, 60), fs=13, color=app.muted_color))
            return
        title = next((c[1] for c in CATS if c[0] == self.cat), 'choose')
        box.add_widget(self.label(self.tx(title, 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        for gid, tkey, dkey, cid in GAMES:
            if cid != self.cat:
                continue
            card = Factory.GiftCard()
            card.add_widget(self.label(self.tx(tkey, 18, 90), fs=18, bold=True, halign=halign))
            card.add_widget(self.label(self.tx(dkey, 13, 90), fs=13, color=app.muted_color,
                                       halign=halign))
            card.add_widget(self.button(self.tx('play', 16, 100),
                                        lambda g=gid: self.open_game(g)))
            box.add_widget(card)
        box.add_widget(self.button(self.tx('all_cats', 15, 100), lambda: self.open_cat(None),
                                   gray=True))

    def open_cat(self, cid):
        self.cat = cid
        self.go('menu')

    def open_game(self, gid):
        self.cat = next((g[3] for g in GAMES if g[0] == gid), self.cat)
        if gid == 'knowme':
            self.go('home')
        elif gid == 'truthdare':
            self.go('td_setup')
        elif gid == 'likely':
            self.go('ml_setup')
        elif gid == 'tools':
            self.go('tools_menu')
        elif gid == 'lie':
            self.go('lie_home')
        elif gid == 'impostor':
            self.go('imp_setup')
        elif gid == 'trivia':
            self.go('tv_mode' if SURV_OK else 'tv_home')
        elif gid == 'riddles':
            self.go('rd_mode' if SURV_OK else 'rd_home')
        elif gid == 'faketimer':
            self.go('ft_setup')
        elif gid == 'bomb':
            self.go('bc_setup')
        elif gid == 'outbreak':
            self.go('ob_setup')

    # ---------- من يعرفني أكثر: الصفحة الأولى ----------
    def show_home(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('k_title', 22, 60), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('k_desc', 15, 60), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.tx('create', 16, 100), self.start_host))
        box.add_widget(self.button(self.tx('have_code', 16, 100),
                                   lambda: self.go('guest_code')))
        box.add_widget(self.button(self.tx('my_quizzes', 16, 100), lambda: self.go('host_list')))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    # ---------- المضيف: الاسم ثم الأسئلة ثم الكود ----------
    def start_host(self):
        self.go('host_name')

    def show_host_name(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('name_head', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('name_hint', 14, 60), fs=14, color=app.muted_color))
        row, self._name_ti = self.entry(self.tx('name_ph', 16, 100), text=self.host_name)
        box.add_widget(row)
        box.add_widget(self.button(self.tx('cont', 16, 100), self.begin_host_quiz))
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('home'), gray=True))

    def begin_host_quiz(self):
        self.capture()
        name = (self.host_name or '').strip()
        if not name:
            self.set_status(self.tx('empty_name', 13, 60))
            return
        self.host_name = name
        self.host_qids = gd.pick_question_ids()
        self.host_answers = []
        self.qi = 0
        self.go('host_quiz')

    def show_host_quiz(self, box):
        app = App.get_running_app()
        n = len(self.host_qids)
        qid = self.host_qids[self.qi]
        box.add_widget(self.label(self.tx('progress', 13, 60, i=self.qi + 1, n=n),
                                  fs=13, color=app.muted_color))
        box.add_widget(ProgressBar(max=n, value=self.qi + 1, size_hint_y=None, height=dp(8)))
        box.add_widget(self.label(self.tx('about_you', 14, 60), fs=14, color=app.primary_color))
        self.question_widgets(box, qid, self.host_answer, self.host_back)

    def question_widgets(self, box, qid, on_pick, on_back):
        en, ar, options = gd.POOL[qid]
        box.add_widget(self.label(self.pair(en, ar, 20, 50), fs=20, bold=True))
        for idx, (o_en, o_ar) in enumerate(options):
            box.add_widget(self.button(self.pair(o_en, o_ar, 15, 110),
                                       lambda i=idx: on_pick(i)))
        box.add_widget(self.button(self.tx('back', 15, 100), on_back, gray=True))

    def host_answer(self, idx):
        self.host_answers.append(idx)
        if len(self.host_answers) < len(self.host_qids):
            self.qi += 1
            self.render()
        else:
            qa = list(zip(self.host_qids, self.host_answers))
            self.code = gd.encode(self.host_name, qa)
            self.save_hosted(qa)
            self.go('host_done')

    def host_back(self):
        if self.host_answers:
            self.host_answers.pop()
            self.qi = max(0, self.qi - 1)
            self.render()
        else:
            self.go('host_name')

    def show_host_done(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('done_head', 22, 60), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('done_body', 15, 60), fs=15, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.code, fs=15, bold=True))
        box.add_widget(card)
        box.add_widget(self.button(self.tx('copy', 16, 100), self.copy_code))
        box.add_widget(self.button(self.tx('share', 16, 100), self.share_code))
        box.add_widget(self.button(self.tx('view_res', 16, 100), lambda: self.go('host_list')))
        box.add_widget(self.button(self.tx('newquiz', 15, 100), self.start_host, gray=True))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def copy_code(self):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.code)
            self.set_status(self.tx('copied', 13, 60), ok=True)
        except Exception as e:
            self.set_status(f"Error: {e}")

    def share_code(self):
        text = f"\U0001F382 {S['share_en']}\n{S['share_ar']}\n\n{self.code}"
        try:
            share_text(text)
        except Exception as e:
            self.set_status(f"{e}")

    # ---------- الصديق: لصق الكود ثم الأسئلة ثم النتيجة ----------
    def show_guest_code(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('code_head', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        row, self._code_ti = self.entry(self.tx('code_ph', 14, 100), text=self.code_text,
                                        multiline=True, height=dp(110))
        box.add_widget(row)
        box.add_widget(self.button(self.tx('paste', 15, 100), self.paste_code, gray=True))
        box.add_widget(self.button(self.tx('start', 16, 100), self.begin_guest))
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('home'), gray=True))

    def paste_code(self):
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste() or ''
        except Exception as e:
            self.set_status(f"Error: {e}")
            return
        self.code_text = text
        if self._code_ti is not None:
            self._code_ti.text = text

    def begin_guest(self):
        self.capture()
        try:
            self.guest = gd.decode(self.code_text)
        except ValueError:
            self.set_status(self.tx('bad_code', 13, 60))
            return
        if not self.claim_code('knowme', gd.extract_code(self.code_text)):
            self.set_status(self.tx('played', 13, 60))
            return
        self.guest_answers = []
        self.qi = 0
        self.go('guest_name')

    def show_guest_name(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('your_name_head', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('your_name_hint', 14, 60,
                                          name=self.disp_name(self.guest['name'])),
                                  fs=14, color=app.muted_color))
        row, _ = self.entry(self.tx('name_ph', 16, 100), key='guest_name')
        box.add_widget(row)
        box.add_widget(self.button(self.tx('cont', 16, 100), self.begin_guest_quiz))
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('guest_code'),
                                   gray=True))

    def begin_guest_quiz(self):
        self.snapshot()
        name = (self.form.get('guest_name') or '').strip()
        if not name:
            self.set_status(self.tx('empty_name', 13, 60))
            return
        self.guest_name = name
        self.go('guest_quiz')

    def show_guest_quiz(self, box):
        app = App.get_running_app()
        qa = self.guest['qa']
        n = len(qa)
        name = self.disp_name(self.guest['name'])
        qid = qa[self.qi][0]
        box.add_widget(self.label(self.tx('progress', 13, 60, i=self.qi + 1, n=n),
                                  fs=13, color=app.muted_color))
        box.add_widget(ProgressBar(max=n, value=self.qi + 1, size_hint_y=None, height=dp(8)))
        box.add_widget(self.label(self.tx('guess', 14, 60, name=name), fs=14,
                                  color=app.primary_color))
        self.question_widgets(box, qid, self.guest_answer, self.guest_back)

    def guest_answer(self, idx):
        self.guest_answers.append(idx)
        if len(self.guest_answers) < len(self.guest['qa']):
            self.qi += 1
            self.render()
        else:
            self.go('guest_result')

    def guest_back(self):
        if self.guest_answers:
            self.guest_answers.pop()
            self.qi = max(0, self.qi - 1)
            self.render()
        else:
            self.go('guest_code')

    def show_guest_result(self, box):
        app = App.get_running_app()
        qa = self.guest['qa']
        n = len(qa)
        name = self.disp_name(self.guest['name'])
        s = gd.score(qa, self.guest_answers)
        key = 'res10' if s == n else 'res8' if s >= 8 else 'res5' if s >= 5 else 'res3' if s >= 3 else 'res0'
        box.add_widget(self.label(self.tx('score_head', 16, 60), fs=16, color=app.muted_color))
        box.add_widget(self.label(f"{s} / {n}", fs=40, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.tx(key, 17, 60, name=name), fs=17, bold=True))

        try:
            self.result_code = gd.encode_result(gd.quiz_id(qa), self.guest_name, self.guest_answers)
            box.add_widget(self.label(self.tx('send_res', 14, 60, name=name), fs=14,
                                      color=app.muted_color))
            card = Factory.GiftCard()
            card.add_widget(self.label(self.result_code, fs=14, bold=True))
            box.add_widget(card)
            box.add_widget(self.button(self.tx('copy_res', 15, 100), self.copy_result))
            box.add_widget(self.button(self.tx('share_res', 15, 100), self.share_result))
        except Exception as e:
            core.log(f"result code: {e}")

        halign = 'right' if self.is_ar() else 'left'
        for (qid, correct), guess in zip(qa, self.guest_answers):
            q_en, q_ar, _ = gd.POOL[qid]
            ok = guess == correct
            card = Factory.GiftCard()
            card.add_widget(self.label(self.pair(q_en, q_ar, 15, 90), fs=15, bold=True,
                                       halign=halign))
            card.add_widget(self.label(self.tx('right' if ok else 'wrong', 13, 90), fs=13,
                                       bold=True, color=GREEN if ok else RED, halign=halign))
            card.add_widget(self.label(
                self.tx('your_ans', 13, 90, a=self.opt_text(qid, guess)),
                fs=13, color=app.muted_color, halign=halign))
            if not ok:
                card.add_widget(self.label(
                    self.tx('correct_ans', 13, 90, a=self.opt_text(qid, correct)),
                    fs=13, color=app.muted_color, halign=halign))
            box.add_widget(card)
        box.add_widget(self.button(self.tx('again', 15, 100), lambda: self.go('guest_code')))
        box.add_widget(self.button(self.tx('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def copy_result(self):
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(self.result_code)
            self.set_status(self.tx('copied', 13, 60), ok=True)
        except Exception as e:
            self.set_status(f"Error: {e}")

    def share_result(self):
        text = f"\U0001F382 {S['res_share_en'][0]}\n{S['res_share_ar'][1]}\n\n{self.result_code}"
        try:
            share_text(text)
        except Exception as e:
            self.set_status(f"{e}")

    # ---------- المضيف: اختباراتي ونتائج الأصدقاء ----------
    def load_hosted(self):
        data = core._read(HOSTED_FILE, [])
        return data if isinstance(data, list) else []

    def save_hosted_list(self, items):
        try:
            core._write(HOSTED_FILE, items[-20:])
        except Exception as e:
            core.log(f"hosted save: {e}")

    def save_hosted(self, qa):
        qid = gd.quiz_id(qa)
        self.sel_id = qid
        items = self.load_hosted()
        if any(q.get('id') == qid for q in items):
            return
        items.append({'id': qid, 'name': self.host_name,
                      'qa': [[a, b] for a, b in qa], 'results': {}})
        self.save_hosted_list(items)

    def find_quiz(self, qid):
        for q in self.load_hosted():
            if q.get('id') == qid:
                return q
        return None

    def show_host_list(self, box):
        """قسم «نتائج»: يضم كل اختباراتك وترتيب الأصدقاء فيها."""
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('results_title', 22, 60), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tx('res_hint', 14, 60), fs=14, color=app.muted_color))
        row, _ = self.entry(self.tx('res_ph', 14, 100), multiline=True, height=dp(100),
                            key='res_code')
        box.add_widget(row)
        box.add_widget(self.button(self.tx('paste', 15, 100), lambda: self.paste_into('res_code'),
                                   gray=True))
        box.add_widget(self.button(self.tx('add_res', 16, 100), self.add_result))
        items = self.load_hosted()
        if not items:
            box.add_widget(self.label(self.tx('no_quizzes', 15, 60), fs=15, color=app.muted_color))
        for i, q in reversed(list(enumerate(items, 1))):
            n = len(q['qa'])
            card = Factory.GiftCard()
            card.add_widget(self.label(self.tx('quiz_line', 16, 90, i=i, n=len(q.get('results', {}))),
                                       fs=16, bold=True, color=app.primary_color))
            rows = sorted(q.get('results', {}).values(), key=lambda r: -r[1])
            if not rows:
                card.add_widget(self.label(self.tx('no_res', 14, 90), fs=14, color=app.muted_color))
            for k, (nm, sc) in enumerate(rows, 1):
                card.add_widget(self.label(
                    self.tx('rank_line', 17, 90, i=k, name=self.disp_name(nm), s=sc, n=n),
                    fs=17, bold=(k == 1)))
            box.add_widget(card)
        box.add_widget(self.button(self.tx('back', 15, 100), lambda: self.go('home'), gray=True))

    def paste_into(self, key):
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste() or ''
        except Exception as e:
            self.set_status(f"Error: {e}")
            return
        self.form[key] = text
        if key in self._tis:
            self._tis[key].text = text

    def import_results(self, text):
        """يضيف كل النتائج في النص إلى الاختبارات المناسبة. يرجع (المضاف، غير المعروف)."""
        found = gd.decode_all_results(text)
        if not found:
            return 0, 0
        items = self.load_hosted()
        added = unknown = 0
        for r in found:
            q = next((x for x in items if x.get('id') == r['quiz_id']), None)
            if q is None:
                unknown += 1
                continue
            sc = gd.score(q['qa'], r['answers'])
            name = r['name'].strip() or '?'
            q.setdefault('results', {})[name.lower()] = [name, sc]
            added += 1
        if added:
            self.save_hosted_list(items)
        return added, unknown

    def auto_clipboard(self):
        """عند فتح قسم النتائج: إن كان الكود منسوخًا فيُضاف تلقائيًا."""
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste() or ''
        except Exception:
            return ''
        if 'BFBR' not in text.upper() or text == self.last_clip:
            return ''
        self.last_clip = text
        added, _ = self.import_results(text)
        return self.tx('added_n', 13, 60, n=added) if added else ''

    def add_result(self):
        self.snapshot()
        text = self.form.get('res_code', '')
        added, unknown = self.import_results(text)
        if added:
            self.form['res_code'] = ''
            if 'res_code' in self._tis:
                self._tis['res_code'].text = ''
            self.set_status(self.tx('added_n', 13, 60, n=added), ok=True)
        elif unknown:
            self.set_status(self.tx('wrong_quiz', 13, 60))
        else:
            self.set_status(self.tx('bad_result', 13, 60))

    # ---------- اللغة ----------
    def toggle_lang(self):
        self.capture()
        self.lang = 'ar' if self.lang == 'en' else 'en'
        try:
            core._write(PREFS_FILE, {'lang': self.lang})
        except Exception as e:
            core.log(f"games prefs: {e}")
        self.render()
