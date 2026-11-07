"""شاشة الهدايا: أسئلة ثم اقتراحات (عربي / English)."""
import os
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen

import core
import gift_data as gd

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


PREFS_FILE = os.path.join(core.data_dir(), 'gift_prefs.json')
GRAY = [0.45, 0.47, 0.52, 1]

# نصوص الواجهة (إنجليزي، عربي)
S = {
    'title': ('Gift Ideas', 'أفكار الهدايا'),
    'head': ('Find the perfect gift', 'اعثر على الهدية المثالية'),
    'body': ('Answer a few questions about the person and I will suggest gifts that fit them.',
             'أجب عن بعض الأسئلة حول الشخص وسأقترح عليك هدايا تناسبه.'),
    'howmany': ('How many questions?', 'كم عدد الأسئلة؟'),
    'hint': ('More questions = more accurate ideas.', 'كلما زادت الأسئلة زادت دقة الاقتراحات.'),
    'start': ('Start', 'ابدأ'),
    'progress': ('Question {i} of {n}', 'السؤال {i} من {n}'),
    'back': ('Back', 'رجوع'),
    'results': ('Top gift ideas for you', 'أفضل الأفكار لك'),
    'why': ('Why: ', 'السبب: '),
    'why_budget': ('Fits your budget', 'تناسب ميزانيتك'),
    'why_personal': ('Can be personalized', 'يمكن تخصيصها'),
    'why_general': ('A good all-round pick', 'اقتراح مناسب بوجه عام'),
    'more': ('Show more ideas', 'عرض المزيد'),
    'again': ('Start over', 'ابدأ من جديد'),
    'num': ('{n} questions', '{n} أسئلة'),
}


class GiftCard(BoxLayout):
    pass


class GiftScreen(Screen):
    title_text = StringProperty('')
    lang_label = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        prefs = core._read(PREFS_FILE, {})
        self.lang = prefs.get('lang', 'en') if isinstance(prefs, dict) else 'en'
        if self.lang not in ('en', 'ar'):
            self.lang = 'en'
        self.count = 10
        self.stage = 'intro'
        self.qs = []
        self.qi = 0
        self.answers = {}
        self.results = []
        self.shown = 5

    # ---------- دورة الحياة ----------
    def on_kv_post(self, base_widget):
        Clock.schedule_once(lambda dt: self.render(), 0.2)

    def on_pre_enter(self, *args):
        prefs = core._read(PREFS_FILE, {})
        lang = prefs.get('lang') if isinstance(prefs, dict) else None
        if lang in ('en', 'ar'):
            self.lang = lang
        self.render()

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
        """يرتّب العربية ويقسّمها لأسطر قصيرة (الإنجليزية تُترك كما هي)."""
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

    # ---------- العرض ----------
    def render(self):
        if 'content' not in self.ids:
            return
        box = self.ids.content
        box.clear_widgets()
        self.title_text = self.tx('title', 22, 150)
        self.lang_label = fix_arabic('عربي') if not self.is_ar() else 'English'
        try:
            if self.stage == 'quiz':
                self.show_quiz(box)
            elif self.stage == 'result':
                self.show_result(box)
            else:
                self.show_intro(box)
        except Exception:
            box.clear_widgets()
            box.add_widget(self.label(traceback.format_exc(), fs=11, halign='left'))
        self.ids.scroll.scroll_y = 1

    def show_intro(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('head', 22, 60), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.tx('body', 15, 60), fs=15, color=app.muted_color))
        box.add_widget(self.label(self.tx('howmany', 17, 60), fs=17, bold=True))

        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for n in gd.QUESTION_COUNTS:
            btn = Factory.StyledButton(text=str(n))
            if n != self.count:
                btn.custom_bg = GRAY
            btn.bind(on_release=lambda inst, n=n: self.set_count(n))
            row.add_widget(btn)
        box.add_widget(row)
        box.add_widget(self.label(self.tx('hint', 13, 60), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.tx('start', 16, 100), self.start))

    def show_quiz(self, box):
        app = App.get_running_app()
        n = len(self.qs)
        key, q_en, q_ar, options = self.qs[self.qi]
        box.add_widget(self.label(self.tx('progress', 13, 60, i=self.qi + 1, n=n),
                                  fs=13, color=app.muted_color))
        bar = ProgressBar(max=n, value=self.qi + 1, size_hint_y=None, height=dp(8))
        box.add_widget(bar)
        box.add_widget(self.label(self.pair(q_en, q_ar, 20, 50), fs=20, bold=True))
        for val, en, ar in options:
            box.add_widget(self.button(
                self.pair(en, ar, 15, 110),
                lambda v=val, k=key: self.answer(k, v)))
        box.add_widget(self.button(self.tx('back', 15, 100), self.go_back, gray=True))

    def show_result(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tx('results', 20, 60), fs=20, bold=True,
                                  color=app.primary_color))
        halign = 'right' if self.is_ar() else 'left'
        for r in self.results[:self.shown]:
            g = r['gift']
            card = GiftCard()
            name = g['ar'] if self.is_ar() else g['en']
            card.add_widget(self.label(self.shape(name, 17, 90), fs=17, bold=True, halign=halign))
            card.add_widget(self.label('$' * int(g['budget']), fs=14, bold=True,
                                       color=app.primary_color, halign=halign))
            card.add_widget(self.label(self.why_text(r), fs=13, color=app.muted_color,
                                       halign=halign))
            box.add_widget(card)
        if self.shown < len(self.results):
            box.add_widget(self.button(self.tx('more', 15, 100), self.show_more, gray=True))
        box.add_widget(self.button(self.tx('again', 15, 100), self.restart))

    def why_text(self, r):
        parts = []
        for k in r['why']:
            if k in ('budget', 'personal'):
                continue
            names = gd.TAG_NAMES.get(k)
            if names:
                parts.append(names[1] if self.is_ar() else names[0])
        if 'personal' in r['why']:
            parts.append(S['why_personal'][1 if self.is_ar() else 0])
        if 'budget' in r['why']:
            parts.append(S['why_budget'][1 if self.is_ar() else 0])
        parts = parts[:3]
        if not parts:
            parts = [S['why_general'][1 if self.is_ar() else 0]]
        prefix = S['why'][1 if self.is_ar() else 0]
        return self.shape(prefix + ' • '.join(parts), 13, 90)

    # ---------- الأحداث ----------
    def toggle_lang(self):
        self.lang = 'ar' if self.lang == 'en' else 'en'
        try:
            core._write(PREFS_FILE, {'lang': self.lang})
        except Exception as e:
            core.log(f"gift prefs: {e}")
        self.render()

    def set_count(self, n):
        self.count = n
        self.render()

    def start(self):
        self.qs = gd.pick_questions(self.count)
        self.qi = 0
        self.answers = {}
        self.stage = 'quiz'
        self.render()

    def answer(self, key, value):
        self.answers[key] = value
        if self.qi + 1 < len(self.qs):
            self.qi += 1
        else:
            self.results = gd.recommend(self.answers, limit=10)
            self.shown = 5
            self.stage = 'result'
        self.render()

    def go_back(self):
        if self.qi > 0:
            self.qi -= 1
        else:
            self.stage = 'intro'
        self.render()

    def show_more(self):
        self.shown = min(len(self.results), self.shown + 5)
        self.render()

    def restart(self):
        self.stage = 'intro'
        self.answers = {}
        self.qi = 0
        self.render()
