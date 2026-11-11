"""لعبة «الحساب السريع» (لاعبان على هاتف واحد): كل لاعب يحلّ أكبر عدد من المسائل في 30 ثانية.
المسائل نفسها للاعبين في كل جولة (عادل). الإجابة الصحيحة +1 والخاطئة -1 (لا تقل النتيجة عن 0)."""
import math
import random
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

try:
    from fx import play as fx_play, buzz as fx_buzz
except Exception:                      # الصوت اختياري: لا يجب أن يكسر اللعبة
    def fx_play(*a, **k):
        pass

    def fx_buzz(*a, **k):
        pass

SECONDS = 30
ROUND_CHOICES = (1, 3, 5)
LEVELS = ('easy', 'medium', 'hard')
RED = [0.85, 0.22, 0.25, 1]
GREEN = [0.15, 0.62, 0.30, 1]

MT = {
    'head': ('Quick Math', 'الحساب السريع'),
    'rules': ('Two players take turns on one phone. Each turn lasts 30 seconds: solve as many '
              'problems as you can by tapping the right answer. Correct = +1, wrong = -1. '
              'Both players get the same problems in every round. The higher total wins!',
              'لاعبان يتبادلان الدور على هاتف واحد. مدة كل دور 30 ثانية: حلّ أكبر عدد من '
              'المسائل بالضغط على الجواب الصحيح. الصحيح = +1 والخاطئ = -1. اللاعبان يحصلان '
              'على نفس المسائل في كل جولة. صاحب المجموع الأعلى يفوز!'),
    'names_hint': ('Player names (optional)', 'أسماء اللاعبين (اختياري)'),
    'ph1': ('Player 1', 'اللاعب 1'),
    'ph2': ('Player 2', 'اللاعب 2'),
    'level_head': ('Difficulty', 'المستوى'),
    'easy': ('Easy', 'سهل'),
    'medium': ('Medium', 'متوسط'),
    'hard': ('Hard', 'صعب'),
    'rounds_head': ('Rounds', 'عدد الجولات'),
    'start': ('Start', 'ابدأ'),
    'round_of': ('Round {i} of {n}', 'الجولة {i} من {n}'),
    'pass': ('{name}: your turn!', '{name}: دورك!'),
    'pass_hint': ('Hold the phone and press the button when you are ready.',
                  'أمسك الهاتف واضغط الزر عندما تكون جاهزًا.'),
    'ready': ('I am ready', 'أنا جاهز'),
    'turn_score': ('Score: {s}', 'النتيجة: {s}'),
    'times_up': ("Time's up!", 'انتهى الوقت!'),
    'got': ('{name}: {c} correct, {w} wrong = {s} point(s)',
            '{name}: {c} صحيحة، {w} خاطئة = {s} نقطة'),
    'scores': ('{n1}: {a}   |   {n2}: {b}', '{n1}: {a}   |   {n2}: {b}'),
    'next': ('Next', 'التالي'),
    'final': ('Final result', 'النتيجة النهائية'),
    'win': ('{name} wins!', 'فاز {name}!'),
    'draw': ("It's a draw!", 'تعادل!'),
    'again': ('Play again', 'العب مجددًا'),
    'change': ('Change settings', 'تغيير الإعدادات'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def make_question(rng, level):
    """يرجع (نص المسألة، الجواب). المستوى: easy / medium / hard."""
    r = rng.random()
    if level == 'easy':
        if r < 0.55:
            a, b = rng.randint(2, 20), rng.randint(2, 20)
            return f'{a} + {b}', a + b
        a = rng.randint(8, 30)
        b = rng.randint(1, a - 1)
        return f'{a} - {b}', a - b
    if level == 'medium':
        if r < 0.35:
            a, b = rng.randint(12, 89), rng.randint(11, 79)
            return f'{a} + {b}', a + b
        if r < 0.65:
            a = rng.randint(30, 99)
            b = rng.randint(11, a - 1)
            return f'{a} - {b}', a - b
        a, b = rng.randint(2, 9), rng.randint(3, 9)
        return f'{a} x {b}', a * b
    # hard
    if r < 0.30:
        a, b = rng.randint(6, 12), rng.randint(6, 12)
        return f'{a} x {b}', a * b
    if r < 0.50:
        a, b = rng.randint(12, 29), rng.randint(3, 9)
        return f'{a} x {b}', a * b
    if r < 0.75:
        a, b = rng.randint(120, 899), rng.randint(110, 699)
        return f'{a} + {b}', a + b
    a = rng.randint(300, 999)
    b = rng.randint(101, a - 1)
    return f'{a} - {b}', a - b


def make_options(rng, answer):
    """4 خيارات مختلفة (واحد صحيح) مرتبة عشوائيًا، كلها غير سالبة."""
    cands = [answer + d for d in (-10, -3, -2, -1, 1, 2, 3, 10)]
    cands = [c for c in cands if c >= 0 and c != answer]
    rng.shuffle(cands)
    opts = [answer] + cands[:3]
    extra = answer + 4
    while len(opts) < 4:                 # احتياط للأعداد الصغيرة جدًا
        if extra not in opts:
            opts.append(extra)
        extra += 1
    rng.shuffle(opts)
    return opts


def make_set(seed, level, n=80):
    """سلسلة مسائل ثابتة بحسب البذرة، ليحصل اللاعبان على المسائل نفسها."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        text, ans = make_question(rng, level)
        out.append((text, ans, make_options(rng, ans)))
    return out


class MathMixin:
    def ma_init(self):
        self.ma_names = ['', '']
        self.ma_level = 'easy'
        self.ma_rounds = 3
        self.ma_scores = [0, 0]
        self.ma_turn = 0
        self.ma_seed = 0
        self.ma_qs = []
        self.ma_qi = 0
        self.ma_c = 0
        self.ma_w = 0
        self.ma_end_t = 0.0
        self.ma_ev = None
        self._ma_counted = None
        self._ma_timer = None
        self._ma_q_lbl = None
        self._ma_score_lbl = None
        self._ma_btns = []

    def ma_stop(self):
        ev = getattr(self, 'ma_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.ma_ev = None

    # ---------- مساعدات ----------
    def mt(self, key, fs=16, pad=60, **fmt):
        en, ar = MT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def ma_player(self, i):
        name = (self.ma_names[i] or '').strip()
        if name:
            return self.disp_name(name)
        en, ar = MT['ph%d' % (i + 1)]
        return ar if self.is_ar() else en

    def ma_total_turns(self):
        return self.ma_rounds * 2

    def ma_cur(self):
        return self.ma_turn % 2

    def ma_round(self):
        return self.ma_turn // 2

    def ma_left(self):
        return max(0, int(math.ceil(self.ma_end_t - time.monotonic())))

    def ma_pts(self):
        return max(0, self.ma_c - self.ma_w)

    def ma_scoreboard(self, fs=17):
        return self.mt('scores', fs, 60, n1=self.ma_player(0), a=self.ma_scores[0],
                       n2=self.ma_player(1), b=self.ma_scores[1])

    # ---------- الإعداد ----------
    def show_ma_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.mt('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.mt('rules', 14), fs=14, color=app.muted_color))

        box.add_widget(self.label(self.mt('names_hint', 16), fs=16, bold=True))
        for i in (0, 1):
            en, ar = MT['ph%d' % (i + 1)]
            row, _ = self.entry(self.pair(en, ar, 15, 100), key='ma_p%d' % (i + 1))
            box.add_widget(row)

        box.add_widget(self.label(self.mt('level_head', 16), fs=16, bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(8))
        for lv in LEVELS:
            b = self.button(self.mt(lv, 15, 200), lambda lv=lv: self.ma_set_level(lv),
                            gray=(lv != self.ma_level))
            b.size_hint_y = 1
            row.add_widget(b)
        box.add_widget(row)

        box.add_widget(self.label(self.mt('rounds_head', 16), fs=16, bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(8))
        for n in ROUND_CHOICES:
            b = self.button(str(n), lambda n=n: self.ma_set_rounds(n), gray=(n != self.ma_rounds))
            b.size_hint_y = 1
            row.add_widget(b)
        box.add_widget(row)

        box.add_widget(self.button(self.mt('start', 17, 100), self.ma_start))
        box.add_widget(self.button(self.mt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ma_set_level(self, lv):
        self.ma_level = lv
        self.render()

    def ma_set_rounds(self, n):
        self.ma_rounds = n
        self.render()

    def ma_start(self):
        self.snapshot()
        self.ma_names = [(self.form.get('ma_p1', '') or '').strip()[:14],
                         (self.form.get('ma_p2', '') or '').strip()[:14]]
        self.ma_reset()
        self.go('ma_pass')

    def ma_reset(self):
        self.ma_scores = [0, 0]
        self.ma_turn = 0
        self._ma_counted = None
        self.ma_seed = random.randint(1, 10 ** 9)

    # ---------- تمرير الهاتف ----------
    def show_ma_pass(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.mt('round_of', 14, 60, i=self.ma_round() + 1,
                                          n=self.ma_rounds), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.mt('pass', 26, 60, name=self.ma_player(self.ma_cur())),
                                  fs=26, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.mt('pass_hint', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.ma_scoreboard(), fs=17))
        box.add_widget(self.button(self.mt('ready', 17, 100), self.ma_ready))
        box.add_widget(self.button(self.mt('change', 15, 100), lambda: self.go('ma_setup'),
                                   gray=True))

    def ma_ready(self):
        # البذرة تتغير كل جولة، ويتشاركها اللاعبان داخل الجولة الواحدة
        self.ma_qs = make_set(self.ma_seed + self.ma_round(), self.ma_level)
        self.ma_qi = 0
        self.ma_c = 0
        self.ma_w = 0
        self.ma_end_t = time.monotonic() + SECONDS
        self.go('ma_play')

    # ---------- الدور ----------
    def show_ma_play(self, box):
        app = App.get_running_app()
        left = self.ma_left()
        box.add_widget(self.label(self.ma_player(self.ma_cur()), fs=16,
                                  color=app.primary_color))
        timer = self.label(str(left), fs=48, bold=True,
                           color=RED if left <= 5 else app.text_color)
        box.add_widget(timer)
        self._ma_timer = timer

        card = Factory.GiftCard()
        q = self.label('', fs=40, bold=True)
        card.add_widget(q)
        box.add_widget(card)
        self._ma_q_lbl = q

        score = self.label(self.mt('turn_score', 15, 60, s=self.ma_pts()), fs=15,
                           color=app.muted_color)
        box.add_widget(score)
        self._ma_score_lbl = score

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(2 * 74 + 10))
        self._ma_btns = []
        for i in range(4):
            btn = Factory.StyledButton(text='')
            btn.font_size = sp(26) * app.font_scale
            btn.bold = True
            btn.bind(on_release=lambda b, k=i: self.ma_answer(k))
            self._ma_btns.append(btn)
            grid.add_widget(btn)
        box.add_widget(grid)
        self.ma_show_q()

        if left > 0:
            self.ma_ev = Clock.schedule_interval(self.ma_tick, 0.25)
        else:
            Clock.schedule_once(lambda dt: self.go('ma_turnend'), 0)

    def ma_show_q(self):
        text, ans, opts = self.ma_qs[self.ma_qi % len(self.ma_qs)]
        if self._ma_q_lbl is not None:
            self._ma_q_lbl.text = text
        for btn, val in zip(self._ma_btns, opts):
            btn.text = str(val)
            btn.custom_bg = []

    def ma_tick(self, dt):
        left = self.ma_left()
        if self._ma_timer is not None:
            self._ma_timer.text = str(left)
            if left <= 5:
                self._ma_timer.color = RED
        if left <= 0:
            self.ma_stop()
            fx_play('end')
            fx_buzz(300)
            self.go('ma_turnend')
            return False
        return True

    def ma_answer(self, k):
        if self.ma_left() <= 0:
            return
        text, ans, opts = self.ma_qs[self.ma_qi % len(self.ma_qs)]
        if opts[k] == ans:
            self.ma_c += 1
            fx_play('ok', 0.6)
        else:
            self.ma_w += 1
            fx_play('bad', 0.6)
            fx_buzz(60)
        self.ma_qi += 1
        if self._ma_score_lbl is not None:
            self._ma_score_lbl.text = self.mt('turn_score', 15, 60, s=self.ma_pts())
        self.ma_show_q()

    # ---------- نهاية الدور ----------
    def show_ma_turnend(self, box):
        app = App.get_running_app()
        if self._ma_counted != self.ma_turn:
            self.ma_scores[self.ma_cur()] += self.ma_pts()
            self._ma_counted = self.ma_turn
        box.add_widget(self.label(self.mt('times_up', 26), fs=26, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.mt('got', 17, 60, name=self.ma_player(self.ma_cur()),
                                          c=self.ma_c, w=self.ma_w, s=self.ma_pts()), fs=17))
        box.add_widget(self.label(self.ma_scoreboard(), fs=17, bold=True))
        last = self.ma_turn + 1 >= self.ma_total_turns()
        box.add_widget(self.button(self.mt('final' if last else 'next', 17, 100), self.ma_next))

    def ma_next(self):
        self.ma_turn += 1
        if self.ma_turn >= self.ma_total_turns():
            self.go('ma_end')
        else:
            self.go('ma_pass')

    # ---------- النهاية ----------
    def show_ma_end(self, box):
        app = App.get_running_app()
        a, b = self.ma_scores
        box.add_widget(self.label(self.mt('final', 16), fs=16, color=app.muted_color))
        if a == b:
            box.add_widget(self.label(self.mt('draw', 28), fs=28, bold=True,
                                      color=app.primary_color))
        else:
            box.add_widget(self.label(self.mt('win', 28, 60,
                                              name=self.ma_player(0 if a > b else 1)),
                                      fs=28, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.ma_scoreboard(20), fs=20, bold=True))
        fx_play('win')
        box.add_widget(self.button(self.mt('again', 16, 100), self.ma_again))
        box.add_widget(self.button(self.mt('change', 15, 100), lambda: self.go('ma_setup'),
                                   gray=True))
        box.add_widget(self.button(self.mt('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ma_again(self):
        self.ma_reset()
        self.go('ma_pass')
