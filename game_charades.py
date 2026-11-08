"""لعبة «التمثيل الصامت»: هاتف واحد، فريقان يتبادلان الأدوار.
الممثل يرى الكلمة ويمثّلها بلا كلام، وفريقه يخمّن. 60 ثانية لكل دور."""
import math
import random
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import charades_data as cd

SECONDS = 60
ROUND_CHOICES = (2, 3, 5)
RED = [0.85, 0.22, 0.25, 1]
GREEN = [0.15, 0.62, 0.30, 1]

CM = {
    'head': ('Charades', 'التمثيل الصامت'),
    'rules': ('Two teams take turns. One player acts out the word on the screen WITHOUT speaking '
              'and their team guesses it. You have 60 seconds per turn. Press Correct for every '
              'word guessed, or Skip to change the word. Only the actor looks at the screen!',
              'فريقان يتبادلان الأدوار. لاعب واحد يمثّل الكلمة الظاهرة على الشاشة بدون كلام '
              'وفريقه يخمّنها. لديكم 60 ثانية لكل دور. اضغط «صح» عند كل كلمة تم تخمينها، '
              'أو «تخطّى» لتغيير الكلمة. الممثل وحده ينظر إلى الشاشة!'),
    'teams_hint': ('Team names (optional)', 'أسماء الفريقين (اختياري)'),
    'ph1': ('Team 1', 'الفريق 1'),
    'ph2': ('Team 2', 'الفريق 2'),
    'rounds_head': ('Turns per team', 'عدد الأدوار لكل فريق'),
    'cat_head': ('Category', 'الفئة'),
    'mix': ('Mixed (all categories)', 'مختلطة (كل الفئات)'),
    'start': ('Start', 'ابدأ'),
    'turn_of': ('Turn {i} of {n}', 'الدور {i} من {n}'),
    'pass': ('{team}: give the phone to the actor', '{team}: سلّموا الهاتف للممثل'),
    'pass_hint': ('Only the actor looks at the screen. The others must not see it.',
                  'الممثل وحده ينظر إلى الشاشة. الباقون يجب ألا يروها.'),
    'ready': ('I am ready', 'أنا جاهز'),
    'acting': ('{team} is acting', 'دور {team}'),
    'correct': ('Correct', 'صح'),
    'skip': ('Skip', 'تخطّى'),
    'turn_pts': ('This turn: {p}', 'هذا الدور: {p}'),
    'times_up': ("Time's up!", 'انتهى الوقت!'),
    'got': ('{team} scored {p} point(s) this turn.', 'حصل {team} على {p} نقطة في هذا الدور.'),
    'scores': ('{n1}: {a}   |   {n2}: {b}', '{n1}: {a}   |   {n2}: {b}'),
    'next': ('Next', 'التالي'),
    'final': ('Final result', 'النتيجة النهائية'),
    'win': ('{team} wins!', 'فاز {team}!'),
    'draw': ("It's a draw!", 'تعادل!'),
    'again': ('Play again', 'العب مجددًا'),
    'change': ('Change settings', 'تغيير الإعدادات'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


class CharadesMixin:
    def cg_init(self):
        self.cg_names = ['', '']
        self.cg_rounds = 3
        self.cg_cat = 'mix'
        self.cg_scores = [0, 0]
        self.cg_turn = 0
        self.cg_turn_pts = 0
        self.cg_deck = []
        self.cg_word = None
        self.cg_end_t = 0.0
        self.cg_ev = None
        self._cg_timer = None
        self._cg_word_lbl = None
        self._cg_pts_lbl = None

    def cg_stop(self):
        ev = getattr(self, 'cg_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.cg_ev = None

    # ---------- مساعدات ----------
    def cm(self, key, fs=16, pad=60, **fmt):
        en, ar = CM[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def cg_team(self, i):
        """اسم الفريق (الذي كتبه المستخدم أو الافتراضي)، غير مُشكَّل للعربية."""
        name = (self.cg_names[i] or '').strip()
        if name:
            return self.disp_name(name)
        en, ar = CM['ph%d' % (i + 1)]
        return ar if self.is_ar() else en

    def cg_total_turns(self):
        return self.cg_rounds * 2

    def cg_cur_team(self):
        return self.cg_turn % 2

    def cg_left(self):
        return max(0, int(math.ceil(self.cg_end_t - time.monotonic())))

    def cg_pool(self):
        if self.cg_cat == 'mix':
            return [w for c in cd.CATS for w in cd.WORDS[c[0]]]
        return list(cd.WORDS.get(self.cg_cat, []))

    def cg_draw(self):
        """كلمة جديدة دون تكرار حتى تنتهي الكلمات كلها."""
        if not self.cg_deck:
            pool = self.cg_pool()
            random.shuffle(pool)
            if pool and self.cg_word is not None and pool[-1] == self.cg_word:
                pool.insert(0, pool.pop())
            self.cg_deck = pool
        return self.cg_deck.pop() if self.cg_deck else ('?', '?')

    def cg_word_text(self):
        en, ar = self.cg_word or ('', '')
        return self.shape(ar if self.is_ar() else en, 34, 90)

    def cg_scoreboard(self, fs=17):
        return self.cm('scores', fs, 60, n1=self.cg_team(0), a=self.cg_scores[0],
                       n2=self.cg_team(1), b=self.cg_scores[1])

    # ---------- الإعداد ----------
    def show_cg_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.cm('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.cm('rules', 14), fs=14, color=app.muted_color))

        box.add_widget(self.label(self.cm('teams_hint', 16), fs=16, bold=True))
        for i in (0, 1):
            en, ar = CM['ph%d' % (i + 1)]
            row, _ = self.entry(self.pair(en, ar, 15, 100), key='cg_t%d' % (i + 1))
            box.add_widget(row)

        box.add_widget(self.label(self.cm('rounds_head', 16), fs=16, bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(8))
        for n in ROUND_CHOICES:
            b = self.button(str(n), lambda n=n: self.cg_set_rounds(n), gray=(n != self.cg_rounds))
            b.size_hint_y = 1
            row.add_widget(b)
        box.add_widget(row)

        box.add_widget(self.label(self.cm('cat_head', 16), fs=16, bold=True))
        box.add_widget(self.button(self.cm('mix', 16, 100), lambda: self.cg_set_cat('mix'),
                                   gray=(self.cg_cat != 'mix')))
        for cid, en, ar in cd.CATS:
            box.add_widget(self.button(self.pair(en, ar, 16, 100),
                                       lambda c=cid: self.cg_set_cat(c),
                                       gray=(self.cg_cat != cid)))

        box.add_widget(self.button(self.cm('start', 17, 100), self.cg_start))
        box.add_widget(self.button(self.cm('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def cg_set_rounds(self, n):
        self.cg_rounds = n
        self.render()

    def cg_set_cat(self, cid):
        self.cg_cat = cid
        self.render()

    def cg_start(self):
        self.snapshot()
        self.cg_names = [(self.form.get('cg_t1', '') or '').strip()[:14],
                         (self.form.get('cg_t2', '') or '').strip()[:14]]
        self.cg_reset()
        self.go('cg_pass')

    def cg_reset(self):
        self.cg_scores = [0, 0]
        self.cg_turn = 0
        self.cg_deck = []
        self.cg_word = None

    # ---------- تمرير الهاتف للممثل ----------
    def show_cg_pass(self, box):
        app = App.get_running_app()
        team = self.cg_team(self.cg_cur_team())
        box.add_widget(self.label(self.cm('turn_of', 14, 60, i=self.cg_turn + 1,
                                          n=self.cg_total_turns()), fs=14,
                                  color=app.muted_color))
        box.add_widget(self.label(self.cm('pass', 24, 60, team=team), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.cm('pass_hint', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.cg_scoreboard(), fs=17))
        box.add_widget(self.button(self.cm('ready', 17, 100), self.cg_ready))
        box.add_widget(self.button(self.cm('change', 15, 100), lambda: self.go('cg_setup'),
                                   gray=True))

    def cg_ready(self):
        self.cg_turn_pts = 0
        self.cg_end_t = time.monotonic() + SECONDS
        self.cg_word = self.cg_draw()
        self.go('cg_play')

    # ---------- الدور ----------
    def show_cg_play(self, box):
        app = App.get_running_app()
        left = self.cg_left()
        team = self.cg_team(self.cg_cur_team())
        box.add_widget(self.label(self.cm('acting', 16, 60, team=team), fs=16,
                                  color=app.primary_color))
        timer = self.label(str(left), fs=56, bold=True,
                           color=RED if left <= 10 else app.text_color)
        box.add_widget(timer)
        self._cg_timer = timer

        card = Factory.GiftCard()
        word = self.label(self.cg_word_text(), fs=34, bold=True)
        card.add_widget(word)
        box.add_widget(card)
        self._cg_word_lbl = word

        pts = self.label(self.cm('turn_pts', 15, 60, p=self.cg_turn_pts), fs=15,
                         color=app.muted_color)
        box.add_widget(pts)
        self._cg_pts_lbl = pts

        box.add_widget(self.button(self.cm('correct', 18, 100), self.cg_correct))
        box.add_widget(self.button(self.cm('skip', 16, 100), self.cg_skip, gray=True))

        if left > 0:
            self.cg_ev = Clock.schedule_interval(self.cg_tick, 0.25)
        else:
            Clock.schedule_once(lambda dt: self.cg_finish_turn(), 0)

    def cg_tick(self, dt):
        left = self.cg_left()
        if self._cg_timer is not None:
            self._cg_timer.text = str(left)
            if left <= 10:
                self._cg_timer.color = RED
        if left <= 0:
            self.cg_stop()
            self.cg_finish_turn()
            return False
        return True

    def cg_next_word(self):
        self.cg_word = self.cg_draw()
        if self._cg_word_lbl is not None:
            self._cg_word_lbl.text = self.cg_word_text()
        if self._cg_pts_lbl is not None:
            self._cg_pts_lbl.text = self.cm('turn_pts', 15, 60, p=self.cg_turn_pts)

    def cg_correct(self):
        if self.cg_left() <= 0:
            return
        self.cg_turn_pts += 1
        self.cg_scores[self.cg_cur_team()] += 1
        self.cg_next_word()

    def cg_skip(self):
        if self.cg_left() <= 0:
            return
        self.cg_next_word()

    def cg_finish_turn(self):
        self.go('cg_turnend')

    # ---------- نهاية الدور ----------
    def show_cg_turnend(self, box):
        app = App.get_running_app()
        team = self.cg_team(self.cg_cur_team())
        box.add_widget(self.label(self.cm('times_up', 26), fs=26, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.cm('got', 17, 60, team=team, p=self.cg_turn_pts),
                                  fs=17))
        box.add_widget(self.label(self.cg_scoreboard(), fs=17, bold=True))
        last = self.cg_turn + 1 >= self.cg_total_turns()
        box.add_widget(self.button(self.cm('final' if last else 'next', 17, 100), self.cg_next))

    def cg_next(self):
        self.cg_turn += 1
        if self.cg_turn >= self.cg_total_turns():
            self.go('cg_end')
        else:
            self.go('cg_pass')

    # ---------- النهاية ----------
    def show_cg_end(self, box):
        app = App.get_running_app()
        a, b = self.cg_scores
        box.add_widget(self.label(self.cm('final', 16), fs=16, color=app.muted_color))
        if a == b:
            box.add_widget(self.label(self.cm('draw', 28), fs=28, bold=True,
                                      color=app.primary_color))
        else:
            win = self.cg_team(0 if a > b else 1)
            box.add_widget(self.label(self.cm('win', 28, 60, team=win), fs=28, bold=True,
                                      color=app.primary_color))
        box.add_widget(self.label(self.cg_scoreboard(20), fs=20, bold=True))
        box.add_widget(self.button(self.cm('again', 16, 100), self.cg_again))
        box.add_widget(self.button(self.cm('change', 15, 100), lambda: self.go('cg_setup'),
                                   gray=True))
        box.add_widget(self.button(self.cm('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def cg_again(self):
        self.cg_reset()
        self.go('cg_pass')
