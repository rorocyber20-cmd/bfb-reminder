"""لعبة «المشنقة» (فردية): خمّن الكلمة السرية حرفًا حرفًا قبل أن يكتمل رسم المشنقة (6 أخطاء).
الكلمات بالعربية أو الإنجليزية حسب لغة واجهة الألعاب، مع تلميح بفئة الكلمة."""
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.factory import Factory

import hangman_data as hd

try:
    from fx import play as fx_play, buzz as fx_buzz
except Exception:                      # الصوت اختياري: لا يجب أن يكسر اللعبة
    def fx_play(*a, **k):
        pass

    def fx_buzz(*a, **k):
        pass

MAX_WRONG = 6
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]
EN_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
AR_LETTERS = 'ابتثجحخدذرزسشصضطظعغفقكلمنهويء'
_NORM = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ة': 'ه', 'ى': 'ي', 'ؤ': 'و', 'ئ': 'ي'}

HM = {
    'head': ('Hangman', 'المشنقة'),
    'rules': ('Guess the secret word one letter at a time. Every wrong letter adds a part to the '
              'hanging man. You can make 6 mistakes. Complete the word before the drawing '
              'is finished!',
              'خمّن الكلمة السرية حرفًا حرفًا. كل حرف خاطئ يضيف جزءًا إلى المشنوق. '
              'يمكنك ارتكاب 6 أخطاء. أكمل الكلمة قبل أن يكتمل الرسم!'),
    'pick': ('Choose a category', 'اختر الفئة'),
    'mix': ('Mixed (all categories)', 'مختلطة (كل الفئات)'),
    'hint': ('Hint: {cat}', 'التلميح: {cat}'),
    'mistakes': ('Mistakes: {n} / {m}', 'الأخطاء: {n} / {m}'),
    'quit': ('Quit game', 'إنهاء اللعبة'),
    'quit_sure': ('Tap again to quit', 'اضغط مرة أخرى للإنهاء'),
    'win': ('You saved him!', 'أنقذته!'),
    'lose': ('Game over!', 'انتهت اللعبة!'),
    'was': ('The word was:', 'الكلمة كانت:'),
    'score': ('Wins: {a}   |   Losses: {b}', 'الفوز: {a}   |   الخسارة: {b}'),
    'again': ('Next word', 'كلمة جديدة'),
    'change': ('Change category', 'تغيير الفئة'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def norm(ch):
    return _NORM.get(ch, ch.upper())


def pool(cat):
    """قائمة كلمات الفئة (أو كل الفئات إن كانت cat فارغة): [(إنجليزي، عربي، معرّف الفئة)]."""
    out = []
    for cid, words in hd.WORDS.items():
        if cat and cid != cat:
            continue
        for en, ar in words:
            out.append((en, ar, cid))
    return out


def cat_name(cid, ar):
    for c in hd.CATS:
        if c[0] == cid:
            return c[2] if ar else c[1]
    return ''


def keyboard_rows(ar):
    """صفوف لوحة الحروف. في العربية يُعكس كل صف ليبدأ الألف من اليمين."""
    letters = AR_LETTERS if ar else EN_LETTERS
    cols = 8 if ar else 7
    rows = []
    for i in range(0, len(letters), cols):
        chunk = list(letters[i:i + cols])
        pad = [None] * (cols - len(chunk))
        rows.append(pad + chunk[::-1] if ar else chunk + pad)
    return cols, rows


class HangDraw(Widget):
    """رسم المشنقة: الأعمدة ثابتة والجسم يظهر قطعة قطعة حسب عدد الأخطاء."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wrong = 0
        self.bind(pos=self.redraw, size=self.redraw)

    def set_wrong(self, n):
        self.wrong = n
        self.redraw()

    def redraw(self, *args):
        app = App.get_running_app()
        self.canvas.clear()
        w, h = self.width, self.height
        if w < 10 or h < 10:
            return
        x0, y0 = self.x, self.y
        lw = dp(3)
        with self.canvas:
            Color(*app.muted_color)
            base_y = y0 + dp(6)
            top_y = y0 + h - dp(6)
            px = x0 + w * 0.30
            rx = x0 + w * 0.58
            Line(points=[x0 + w * 0.15, base_y, x0 + w * 0.60, base_y], width=lw)   # القاعدة
            Line(points=[px, base_y, px, top_y], width=lw)                          # العمود
            Line(points=[px, top_y, rx, top_y], width=lw)                           # الذراع
            Line(points=[rx, top_y, rx, top_y - h * 0.14], width=lw)                # الحبل
            Color(*app.text_color)
            hr = h * 0.095
            hy = top_y - h * 0.14 - hr
            by = hy - hr
            n = self.wrong
            if n >= 1:
                Line(circle=(rx, hy, hr), width=lw)
            body_end = by - h * 0.26
            if n >= 2:
                Line(points=[rx, by, rx, body_end], width=lw)
            sh = by - h * 0.06
            if n >= 3:
                Line(points=[rx, sh, rx - h * 0.13, sh - h * 0.12], width=lw)
            if n >= 4:
                Line(points=[rx, sh, rx + h * 0.13, sh - h * 0.12], width=lw)
            if n >= 5:
                Line(points=[rx, body_end, rx - h * 0.12, body_end - h * 0.2], width=lw)
            if n >= 6:
                Line(points=[rx, body_end, rx + h * 0.12, body_end - h * 0.2], width=lw)


class HangmanMixin:
    def hm_init(self):
        self.hm_cat = None
        self.hm_word = ('', '', '')
        self.hm_ar = False
        self.hm_target = ''
        self.hm_guessed = set()
        self.hm_wrong = 0
        self.hm_won = False
        self.hm_score = [0, 0]
        self.hm_used = set()
        self.hm_live = False
        self._hm_ev = None
        self._hm_exit_ev = None
        self._hm_armed = False
        self._hm_cells = []
        self._hm_keys = {}
        self._hm_draw = None
        self._hm_info = None
        self._hm_back = None

    def hm_stop(self):
        for name in ('_hm_ev', '_hm_exit_ev'):
            ev = getattr(self, name, None)
            if ev is not None:
                try:
                    ev.cancel()
                except Exception:
                    pass
            setattr(self, name, None)
        self._hm_armed = False

    def hm_t(self, key, fs=16, pad=60, **fmt):
        en, ar = HM[key]
        return self.pair(en, ar, fs, pad, **fmt)

    # ---------- الإعداد ----------
    def show_hm_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.hm_t('head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.hm_t('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.hm_t('pick', 18), fs=18, bold=True))
        box.add_widget(self.button(self.hm_t('mix', 16, 100), lambda: self.hm_begin(None)))
        for cid, en, ar in hd.CATS:
            name = self.shape(ar if self.is_ar() else en, 16, 100)
            box.add_widget(self.button(name, lambda c=cid: self.hm_begin(c)))
        box.add_widget(self.button(self.hm_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))

    def hm_begin(self, cat):
        self.hm_cat = cat
        self.hm_score = [0, 0]
        self.hm_used = set()
        self.hm_new_word()

    def hm_new_word(self):
        words = pool(self.hm_cat)
        fresh = [w for w in words if (w[0], w[2]) not in self.hm_used]
        if not fresh:
            self.hm_used = set()
            fresh = words
        self.hm_word = random.choice(fresh)
        self.hm_used.add((self.hm_word[0], self.hm_word[2]))
        self.hm_ar = self.is_ar()
        self.hm_target = self.hm_word[1] if self.hm_ar else self.hm_word[0].upper()
        self.hm_guessed = set()
        self.hm_wrong = 0
        self.hm_won = False
        self.go('hm_play')

    # ---------- اللعب ----------
    def hm_revealed(self, ch):
        return norm(ch) in self.hm_guessed

    def hm_complete(self):
        return all(self.hm_revealed(c) for c in self.hm_target)

    def show_hm_play(self, box):
        app = App.get_running_app()
        self.hm_live = True
        cname = self.shape(cat_name(self.hm_word[2], self.is_ar()), 16, 100)
        box.add_widget(self.label(self.hm_t('hint', 17, 60, cat=cname), fs=17, bold=True,
                                  color=app.primary_color))
        self._hm_info = self.label(self.hm_t('mistakes', 14, 60, n=self.hm_wrong, m=MAX_WRONG),
                                   fs=14, color=app.muted_color)
        box.add_widget(self._hm_info)
        draw = HangDraw(size_hint_y=None, height=dp(165))
        draw.set_wrong(self.hm_wrong)
        self._hm_draw = draw
        box.add_widget(draw)
        # الكلمة: خلية لكل حرف (في العربية الحرف الأول على اليمين)
        n = len(self.hm_target)
        cell_w = min(dp(40), (Window.width - dp(40)) / max(n, 1))
        row = BoxLayout(size_hint=(None, None), height=dp(52), width=cell_w * n)
        self._hm_cells = []
        order = list(range(n))
        if self.hm_ar:
            order.reverse()
        for i in order:
            lbl = Label(text='', font_name=app.font, font_size=sp(28) * app.font_scale,
                        bold=True, color=app.text_color, halign='center', valign='middle')
            lbl.bind(size=lambda inst, v: setattr(inst, 'text_size', v))
            self._hm_cells.append((i, lbl))
            row.add_widget(lbl)
        holder = AnchorLayout(size_hint_y=None, height=dp(56))
        holder.add_widget(row)
        box.add_widget(holder)
        # لوحة الحروف
        cols, rows = keyboard_rows(self.hm_ar)
        gap = dp(4)
        grid = GridLayout(cols=cols, spacing=gap, size_hint_y=None,
                          row_default_height=dp(42), row_force_default=True)
        grid.bind(minimum_height=grid.setter('height'))
        self._hm_keys = {}
        for r in rows:
            for ch in r:
                if ch is None:
                    grid.add_widget(Widget(size_hint_y=None, height=dp(42)))
                    continue
                shown = self.shape(ch, 18, 0) if self.hm_ar else ch
                btn = Factory.StyledButton(text=shown)
                btn.font_size = sp(18) * app.font_scale
                btn.height = dp(42)
                btn.bind(on_release=lambda b, c=ch: self.hm_guess(c))
                self._hm_keys[norm(ch)] = btn
                grid.add_widget(btn)
        box.add_widget(grid)
        back = self.button(self.hm_t('quit', 15, 100), self.hm_exit, gray=True)
        self._hm_back = back
        box.add_widget(back)
        self.hm_refresh()

    def hm_refresh(self):
        for i, lbl in self._hm_cells:
            ch = self.hm_target[i]
            lbl.text = (self.shape(ch, 28, 0) if self.hm_ar else ch) if self.hm_revealed(ch) \
                else '_'
        if self._hm_draw is not None:
            self._hm_draw.set_wrong(self.hm_wrong)
        if self._hm_info is not None:
            self._hm_info.text = self.hm_t('mistakes', 14, 60, n=self.hm_wrong, m=MAX_WRONG)

    def hm_guess(self, ch):
        if not self.hm_live:
            return
        key = norm(ch)
        if key in self.hm_guessed:
            return
        self.hm_guessed.add(key)
        btn = self._hm_keys.get(key)
        hit = any(norm(c) == key for c in self.hm_target)
        if btn is not None:
            btn.custom_bg = GREEN if hit else RED
        if hit:
            fx_play('ok', 0.6)
        else:
            self.hm_wrong += 1
            fx_play('bad', 0.6)
        self.hm_refresh()
        if self.hm_complete():
            self.hm_finish(True)
        elif self.hm_wrong >= MAX_WRONG:
            self.hm_finish(False)

    def hm_finish(self, won):
        self.hm_live = False
        self.hm_won = won
        self.hm_score[0 if won else 1] += 1
        if won:
            fx_play('win')
            fx_buzz(150)
        else:
            fx_play('end')
            fx_buzz(300)
        self._hm_ev = Clock.schedule_once(lambda dt: self.go('hm_end'), 0.9)

    def hm_exit(self):
        """ضغطتان للخروج كي لا يحدث بالخطأ."""
        if self._hm_armed:
            self.hm_live = False
            self.go('hm_setup')
            return
        self._hm_armed = True
        if self._hm_back is not None:
            self._hm_back.text = self.hm_t('quit_sure', 15, 100)
        self._hm_exit_ev = Clock.schedule_once(self._hm_disarm, 2.0)

    def _hm_disarm(self, dt):
        self._hm_armed = False
        self._hm_exit_ev = None
        if self._hm_back is not None:
            self._hm_back.text = self.hm_t('quit', 15, 100)

    # ---------- النتيجة ----------
    def show_hm_end(self, box):
        app = App.get_running_app()
        self.hm_live = False
        box.add_widget(self.label(self.hm_t('win' if self.hm_won else 'lose', 28, 60), fs=28,
                                  bold=True, color=GREEN if self.hm_won else RED))
        word = self.hm_target
        shown = self.shape(word, 26, 60) if self.hm_ar else word
        box.add_widget(self.label(self.hm_t('was', 20, 60), fs=20))
        box.add_widget(self.label(shown, fs=30, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.hm_t('score', 18, 60, a=self.hm_score[0],
                                            b=self.hm_score[1]), fs=18, bold=True))
        box.add_widget(self.button(self.hm_t('again', 16, 100), self.hm_new_word))
        box.add_widget(self.button(self.hm_t('change', 15, 100), lambda: self.go('hm_setup'),
                                   gray=True))
        box.add_widget(self.button(self.hm_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))
