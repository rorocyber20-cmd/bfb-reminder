"""وضع «المواجهة» 1 ضد 1 للثقافة العامة والألغاز: هاتف واحد، الشاشة نصفان، لكل لاعب زر.
من يضغط أولًا يجيب خلال 5 ثوانٍ. الجواب الصحيح نقطة له، والخطأ أو انتهاء الوقت نقطة للخصم.
أول من يصل إلى 3 أو 5 أو 7 نقاط يفوز."""
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import PopMatrix, PushMatrix, Rotate
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

import brain_data as bd

ANSWER_SECONDS = 5
READY_SECONDS = 3
LOCK_SECONDS = 0.5
TARGETS = (3, 5, 7)
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]
LOCKED = [0.45, 0.47, 0.52, 1]
HALF_BG = ([0.20, 0.45, 0.80, 1], [0.80, 0.35, 0.20, 1])

DL = {
    'head': ('Duel 1 vs 1', 'مواجهة 1 ضد 1'),
    'duel_btn': ('Duel 1 vs 1 (two players, split screen)', 'مواجهة 1 ضد 1 (لاعبان، شاشة نصفين)'),
    'rules_tv': ('Both players see the same question. Press your button first to answer within 5 seconds. '
                 'Right answer = a point for you. Wrong answer or no answer = a point for your opponent. '
                 'Pressing too early costs you a point!',
                 'يرى اللاعبان السؤال نفسه. اضغط زرّك أولًا لتجيب خلال 5 ثوانٍ. '
                 'الإجابة الصحيحة نقطة لك، والخاطئة أو عدم الإجابة نقطة لخصمك. '
                 'والضغط المبكر يكلّفك نقطة!'),
    'rules_rd': ('Both players see the same riddle. Press your button first, then say your answer out loud '
                 'within 5 seconds. Then the answer is shown and BOTH players judge: right or wrong. '
                 'If you disagree, no point. Pressing too early costs you a point!',
                 'يرى اللاعبان اللغز نفسه. اضغط زرّك أولًا ثم قل جوابك بصوت عالٍ خلال 5 ثوانٍ. '
                 'ثم تظهر الإجابة ويحكم اللاعبان معًا: صحيحة أو خاطئة. '
                 'وإذا اختلفتما فلا نقطة. والضغط المبكر يكلّفك نقطة!'),
    'names_hint': ('Player names (optional)', 'أسماء اللاعبين (اختياري)'),
    'n1': ('Player 1 (bottom)', 'اللاعب 1 (في الأسفل)'),
    'n2': ('Player 2 (top)', 'اللاعب 2 (في الأعلى)'),
    'p1': ('Player 1', 'اللاعب 1'),
    'p2': ('Player 2', 'اللاعب 2'),
    'target': ('First to {n} points wins', 'من يصل إلى {n} نقاط يفوز'),
    'face_on': ('Face to face (top half upside down)', 'وجهًا لوجه (النصف العلوي مقلوب)'),
    'face_off': ('Side by side (no flip)', 'جنبًا إلى جنب (بدون قلب)'),
    'start': ('Start', 'ابدأ'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'ready': ('Get ready...', 'استعدّا...'),
    'wait': ('...', '...'),
    'buzz': ('PRESS!', 'اضغط!'),
    'answering': ('{name} is answering...', '{name} يجيب...'),
    'say': ('Say your answer out loud!', 'قل جوابك بصوت عالٍ!'),
    'done': ('I answered', 'أجبت'),
    'judge_q': ("Was {name}'s answer correct?", 'هل كانت إجابة {name} صحيحة؟'),
    'answer_is': ('Answer: {a}', 'الجواب: {a}'),
    'yes': ('Correct', 'صحيحة'),
    'no': ('Wrong', 'خاطئة'),
    'waiting': ('Waiting for the other player...', 'بانتظار اللاعب الآخر...'),
    'o_right': ('{name} answered correctly! +1', '{name} أجاب صحيحًا! +1'),
    'o_wrong': ('{name} got it wrong. +1 for {opp}', '{name} أخطأ. +1 لـ {opp}'),
    'o_time': ("{name} ran out of time. +1 for {opp}", 'انتهى وقت {name}. +1 لـ {opp}'),
    'o_early': ('{name} pressed too early! +1 for {opp}', '{name} ضغط مبكرًا! +1 لـ {opp}'),
    'o_void': ('The judges disagreed. No point.', 'اختلف الحكمان. لا نقطة.'),
    'correct_is': ('Correct answer: {a}', 'الإجابة الصحيحة: {a}'),
    'next': ('Next', 'التالي'),
    'winner': ('{name} wins!', '{name} يفوز!'),
    'again': ('Play again', 'العب مجددًا'),
}


def flip(w):
    """يدوّر عنصرًا 180° حول مركزه (الرسم فقط). مساحة اللمس تبقى كما هي لأن العنصر متماثل حول مركزه."""
    with w.canvas.before:
        PushMatrix()
        rot = Rotate(angle=180, origin=w.center)
    with w.canvas.after:
        PopMatrix()
    w.bind(center=lambda inst, val: setattr(rot, 'origin', inst.center))
    return w


def flip_tree(w):
    """يدوّر العنصر وكل أبنائه (الأوراق) حتى يقرأ اللاعب المقابل النص مستقيمًا."""
    kids = list(getattr(w, 'children', None) or [])
    if kids:
        for k in kids:
            flip_tree(k)
    else:
        flip(w)
    return w


class DuelMixin:
    def dl_init(self):
        self.dl_kind = 'trivia'
        self.dl_target = 5
        self.dl_face = True
        self.dl_names = ['', '']
        self.dl_scores = [0, 0]
        self.dl_deck = []
        self.dl_item = None
        self.dl_order = []
        self.dl_phase = 'ready'
        self.dl_left = READY_SECONDS
        self.dl_lock = True
        self.dl_who = 0
        self.dl_votes = [None, None]
        self.dl_out = None
        self.dl_winner = None
        self.dl_ev = None
        self.dl_lock_ev = None
        self._dl_cds = []
        self._dl_buzz = []

    def dl_stop(self):
        for attr in ('dl_ev', 'dl_lock_ev'):
            ev = getattr(self, attr, None)
            if ev is not None:
                try:
                    ev.cancel()
                except Exception:
                    pass
            setattr(self, attr, None)

    def dt(self, key, fs=16, pad=60, **fmt):
        en, ar = DL[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def dl_name(self, p):
        n = (self.dl_names[p] or '').strip()
        if n:
            return n
        en, ar = DL['p1' if p == 0 else 'p2']
        return ar if self.is_ar() else en

    def dl_nm(self, p):
        return self.disp_name(self.dl_name(p))

    # ---------- الدخول والإعداد ----------
    def dl_open(self, kind):
        self.dl_kind = kind
        self.go('dl_setup')

    def show_dl_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.dt('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.dt('rules_tv' if self.dl_kind == 'trivia' else 'rules_rd', 14),
                                  fs=14, color=app.muted_color))
        box.add_widget(self.label(self.dt('names_hint', 14), fs=14, color=app.muted_color))
        r1, _ = self.entry(self.dt('n1', 15, 100), key='dl_n1')
        r2, _ = self.entry(self.dt('n2', 15, 100), key='dl_n2')
        box.add_widget(r1)
        box.add_widget(r2)
        box.add_widget(self.label(self.dt('target', 16, 60, n=self.dl_target), fs=16, bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        for n in TARGETS:
            b = Factory.StyledButton(text=str(n))
            if n != self.dl_target:
                b.custom_bg = LOCKED
            b.bind(on_release=lambda inst, n=n: self.dl_set_target(n))
            row.add_widget(b)
        box.add_widget(row)
        box.add_widget(self.button(self.dt('face_on' if self.dl_face else 'face_off', 15, 100),
                                   self.dl_toggle_face))
        box.add_widget(self.button(self.dt('start', 16, 100), self.dl_start))
        back = 'tv_mode' if self.dl_kind == 'trivia' else 'rd_mode'
        box.add_widget(self.button(self.dt('back', 15, 100), lambda: self.go(back), gray=True))

    def dl_set_target(self, n):
        self.snapshot()
        self.dl_target = n
        self.render()

    def dl_toggle_face(self):
        self.snapshot()
        self.dl_face = not self.dl_face
        self.render()

    def dl_start(self):
        self.snapshot()
        self.dl_names = [self.form.get('dl_n1', '').strip()[:14], self.form.get('dl_n2', '').strip()[:14]]
        self.dl_new_game()

    def dl_new_game(self):
        self.dl_scores = [0, 0]
        self.dl_deck = []
        self.dl_winner = None
        self.dl_next_round()

    # ---------- الجولات ----------
    def dl_draw(self):
        size = len(bd.TRIVIA) if self.dl_kind == 'trivia' else len(bd.RIDDLES)
        if not self.dl_deck:
            self.dl_deck = list(range(size))
            random.shuffle(self.dl_deck)
        idx = self.dl_deck.pop()
        if self.dl_kind == 'trivia':
            self.dl_item = bd.TRIVIA[idx]
            self.dl_order = list(range(len(self.dl_item[2])))
            random.shuffle(self.dl_order)
        else:
            self.dl_item = bd.RIDDLES[idx]

    def dl_next_round(self):
        self.dl_draw()
        self.dl_phase = 'ready'
        self.dl_left = READY_SECONDS
        self.dl_lock = True
        self.dl_votes = [None, None]
        self.dl_out = None
        self.go('dl_play')

    def dl_q_text(self, fs=15):
        it = self.dl_item
        return self.pair(it[0], it[1], fs, 40)

    def dl_answer_text(self):
        it = self.dl_item
        if self.dl_kind == 'trivia':
            a = it[2][it[3]]
            return a[1] if self.is_ar() else a[0]
        return it[5] if self.is_ar() else it[4]

    # ---------- الشاشة ----------
    def show_dl_play(self, box):
        scroll_h = 0
        try:
            scroll_h = self.ids.scroll.height
        except Exception:
            pass
        total = max(dp(460), (scroll_h or Window.height * 0.7) - dp(8))
        root = BoxLayout(orientation='vertical', size_hint_y=None, height=total, spacing=dp(4))
        self._dl_cds = []
        self._dl_buzz = []
        root.add_widget(self.dl_half(1))
        root.add_widget(self.dl_half(0))
        box.add_widget(root)
        self.dl_schedule()

    def dl_half(self, p):
        half = BoxLayout(orientation='vertical', size_hint_y=0.5, spacing=dp(5),
                         padding=[dp(8), dp(4)])
        items = self.dl_items(p)
        if self.dl_face and p == 1:
            items = items[::-1]
            for w in items:
                flip_tree(w)
        for w in items:
            half.add_widget(w)
        return half

    def dl_lbl(self, text, fs=15, bold=False, color=None):
        return self.label(text, fs=fs, bold=bold, color=color)

    def dl_head(self, p):
        return self.dl_lbl(self.wrap_user(f'{self.dl_name(p)}:  {self.dl_scores[p]}', 14, 60),
                           fs=14, bold=True, color=HALF_BG[p])

    def dl_buzzer(self, p, text, color, handler):
        b = Factory.StyledButton(text=text)
        b.custom_bg = color
        b.size_hint_y = 1
        b.bind(on_press=lambda *a: handler(p))
        return b

    def dl_cd(self, text, fs=34):
        lbl = self.dl_lbl(text, fs=fs, bold=True)
        self._dl_cds.append(lbl)
        return lbl

    def dl_items(self, p):
        ph = self.dl_phase
        opp = 1 - p
        if ph == 'ready':
            b = self.dl_buzzer(p, self.dt('wait', 18), LOCKED, self.dl_buzz)
            self._dl_buzz.append(b)
            return [self.dl_head(p), self.dl_cd(str(max(1, self.dl_left))), b]
        if ph == 'q':
            locked = self.dl_lock
            b = self.dl_buzzer(p, self.dt('wait' if locked else 'buzz', 20),
                               LOCKED if locked else GREEN, self.dl_buzz)
            self._dl_buzz.append(b)
            return [self.dl_head(p), self.dl_lbl(self.dl_q_text(15), fs=15, bold=True), b]
        if ph == 'answer':
            who = self.dl_who
            if p == who:
                items = [self.dl_cd(str(max(0, self.dl_left)), fs=26),
                         self.dl_lbl(self.dl_q_text(14), fs=14, bold=True)]
                if self.dl_kind == 'trivia':
                    for oi in self.dl_order:
                        o = self.dl_item[2][oi]
                        bt = Factory.StyledButton(text=self.pair(o[0], o[1], 14, 100))
                        bt.height = dp(38)
                        bt.bind(on_release=lambda inst, oi=oi: self.dl_pick(oi))
                        items.append(bt)
                else:
                    items.append(self.dl_lbl(self.dt('say', 16, 60), fs=16, bold=True,
                                             color=HALF_BG[p]))
                    bt = Factory.StyledButton(text=self.dt('done', 16, 100))
                    bt.size_hint_y = 1
                    bt.bind(on_release=lambda inst: self.dl_to_judge())
                    items.append(bt)
                return items
            return [self.dl_head(p),
                    self.dl_lbl(self.dt('answering', 18, 60, name=self.dl_nm(who)), fs=18, bold=True),
                    self.dl_cd(str(max(0, self.dl_left)), fs=34),
                    self.dl_lbl(self.dl_q_text(14), fs=14)]
        if ph == 'judge':
            who = self.dl_who
            items = [self.dl_lbl(self.dt('answer_is', 18, 60, a=self.dl_answer_text()), fs=18,
                                 bold=True, color=HALF_BG[p]),
                     self.dl_lbl(self.dt('judge_q', 15, 60, name=self.dl_nm(who)), fs=15)]
            if self.dl_votes[p] is None:
                row = BoxLayout(size_hint_y=1, spacing=dp(8))
                for val, key, col in ((True, 'yes', GREEN), (False, 'no', RED)):
                    bt = Factory.StyledButton(text=self.dt(key, 16, 100))
                    bt.custom_bg = col
                    bt.bind(on_release=lambda inst, val=val: self.dl_judge(p, val))
                    row.add_widget(bt)
                items.append(row)
            else:
                items.append(self.dl_lbl(self.dt('waiting', 14, 60), fs=14, color=LOCKED))
            return items
        if ph == 'result':
            items = [self.dl_head(p), self.dl_lbl(self.dl_out_text(), fs=16, bold=True)]
            if self.dl_out and self.dl_out[0] in ('wrong', 'time') and self.dl_kind == 'trivia':
                items.append(self.dl_lbl(self.dt('correct_is', 14, 60, a=self.dl_answer_text()),
                                         fs=14))
            if self.dl_out and self.dl_out[0] in ('right', 'wrong', 'time', 'void') \
                    and self.dl_kind == 'riddles':
                items.append(self.dl_lbl(self.dt('answer_is', 14, 60, a=self.dl_answer_text()),
                                         fs=14))
            bt = Factory.StyledButton(text=self.dt('next', 16, 100))
            bt.size_hint_y = 1
            bt.bind(on_release=lambda inst: self.dl_after_result())
            items.append(bt)
            return items
        # end
        items = [self.dl_lbl(self.dt('winner', 26, 60, name=self.dl_nm(self.dl_winner)), fs=26,
                             bold=True, color=GREEN),
                 self.dl_lbl(f'{self.dl_scores[0]} - {self.dl_scores[1]}', fs=22, bold=True)]
        bt = Factory.StyledButton(text=self.dt('again', 16, 100))
        bt.size_hint_y = 1
        bt.bind(on_release=lambda inst: self.dl_new_game())
        items.append(bt)
        if p == 0:
            bt2 = Factory.StyledButton(text=self.dt('menu', 15, 100))
            bt2.custom_bg = LOCKED
            bt2.height = dp(40)
            bt2.bind(on_release=lambda inst: self.go('menu'))
            items.append(bt2)
        return items

    def dl_out_text(self):
        if not self.dl_out:
            return ''
        kind, actor = self.dl_out
        if kind == 'void':
            return self.dt('o_void', 16, 60)
        return self.dt('o_' + kind, 16, 60, name=self.dl_nm(actor), opp=self.dl_nm(1 - actor))

    # ---------- المؤقتات ----------
    def dl_schedule(self):
        ph = self.dl_phase
        if ph == 'ready':
            self.dl_ev = Clock.schedule_interval(self.dl_tick_ready, 1.0)
        elif ph == 'q' and self.dl_lock:
            self.dl_lock_ev = Clock.schedule_once(self.dl_unlock, LOCK_SECONDS)
        elif ph == 'answer':
            self.dl_ev = Clock.schedule_interval(self.dl_tick_answer, 1.0)

    def dl_set_cds(self, text):
        for lbl in self._dl_cds:
            lbl.text = text

    def dl_tick_ready(self, dt):
        self.dl_left -= 1
        if self.dl_left <= 0:
            self.dl_stop()
            self.dl_phase = 'q'
            self.dl_lock = True
            self.go('dl_play')
            return False
        self.dl_set_cds(str(self.dl_left))
        return True

    def dl_unlock(self, dt):
        self.dl_lock = False
        self.dl_lock_ev = None
        for b in self._dl_buzz:
            b.text = self.dt('buzz', 20)
            b.custom_bg = GREEN

    def dl_tick_answer(self, dt):
        self.dl_left -= 1
        self.dl_set_cds(str(max(0, self.dl_left)))
        if self.dl_left <= 0:
            self.dl_stop()
            if self.dl_kind == 'trivia':
                self.dl_finish('time', self.dl_who)
            else:
                self.dl_to_judge()
            return False
        return True

    # ---------- الأحداث ----------
    def dl_buzz(self, p):
        if self.dl_phase == 'ready' or (self.dl_phase == 'q' and self.dl_lock):
            self.dl_stop()
            self.dl_finish('early', p)
        elif self.dl_phase == 'q':
            self.dl_stop()
            self.dl_who = p
            self.dl_phase = 'answer'
            self.dl_left = ANSWER_SECONDS
            self.go('dl_play')

    def dl_pick(self, oi):
        self.dl_stop()
        self.dl_finish('right' if oi == self.dl_item[3] else 'wrong', self.dl_who)

    def dl_to_judge(self):
        self.dl_stop()
        self.dl_phase = 'judge'
        self.dl_votes = [None, None]
        self.go('dl_play')

    def dl_judge(self, p, val):
        self.dl_votes[p] = val
        a, b = self.dl_votes
        if a is None or b is None:
            self.render()
            return
        if a == b:
            self.dl_finish('right' if a else 'wrong', self.dl_who)
        else:
            self.dl_finish('void', self.dl_who)

    def dl_finish(self, kind, actor):
        """actor: من أجاب (أو من ضغط مبكرًا). النقطة: صحيح → له، وغير ذلك → للخصم."""
        if kind == 'right':
            self.dl_scores[actor] += 1
        elif kind in ('wrong', 'time', 'early'):
            self.dl_scores[1 - actor] += 1
        self.dl_out = (kind, actor)
        self.dl_phase = 'result'
        self.go('dl_play')

    def dl_after_result(self):
        for p in (0, 1):
            if self.dl_scores[p] >= self.dl_target:
                self.dl_winner = p
                self.dl_phase = 'end'
                self.go('dl_play')
                return
        self.dl_next_round()
