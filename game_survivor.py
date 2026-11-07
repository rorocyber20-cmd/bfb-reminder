"""نمط «آخر ناجٍ» لألعاب الثقافة العامة والألغاز: 3 لاعبين فأكثر على هاتف واحد.
كل لاعب يجيب بدوره عن سؤال خلال 15 ثانية؛ من يخطئ أو ينتهي وقته يُقصى حتى يبقى واحد."""
import random
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory

import brain_data as bd

SECONDS = 15
GREEN = [0.15, 0.62, 0.30, 1]
RED = [0.85, 0.22, 0.25, 1]

LS = {
    'tv_head': ('General Knowledge', 'ثقافة عامة'),
    'rd_head': ('Riddles', 'ألغاز'),
    'mode_hint': ('Choose how to play', 'اختر طريقة اللعب'),
    'solo': ('Solo mode', 'الوضع الفردي'),
    'survivor': ('Last Survivor (3+ players, one phone)', 'آخر ناجٍ (3 لاعبين فأكثر، هاتف واحد)'),
    'head': ('Last Survivor', 'آخر ناجٍ'),
    'rules': ('Pass the phone around. Each player gets a question and has 15 seconds. '
              'A wrong answer or running out of time puts you out. The last player standing wins!',
              'مرّروا الهاتف بينكم. يحصل كل لاعب على سؤال ولديه 15 ثانية. '
              'الإجابة الخاطئة أو انتهاء الوقت يُقصيك. آخر لاعب يبقى يفوز!'),
    'names_hint': ('Enter 3 to 8 player names, separated by commas.',
                   'أدخل من 3 إلى 8 أسماء لاعبين مفصولة بفواصل.'),
    'names_ph': ('Rayan, Mohamed, Bayan', 'ريان ، محمد ، بيان'),
    'need': ('At least 3 different players are needed.', 'يلزم 3 لاعبين مختلفين على الأقل.'),
    'start': ('Start', 'ابدأ'),
    'left': ('Players left: {n}', 'اللاعبون المتبقون: {n}'),
    'pass': ('Pass the phone to {name}', 'مرّر الهاتف إلى {name}'),
    'ready': ('I am ready', 'أنا جاهز'),
    'turn': ("{name}'s turn", 'دور {name}'),
    'reveal': ('Reveal the answer', 'اكشف الجواب'),
    'answer': ('Answer: {a}', 'الجواب: {a}'),
    'judge': ('Was the answer correct?', 'هل كانت الإجابة صحيحة؟'),
    'yes': ('Correct', 'صحيحة'),
    'no': ('Wrong', 'خاطئة'),
    'ok': ('Correct! You stay in.', 'صحيح! تبقى في اللعبة.'),
    'out': ('Wrong! {name} is out.', 'خطأ! {name} خرج من اللعبة.'),
    'time': ("Time's up! {name} is out.", 'انتهى الوقت! {name} خرج من اللعبة.'),
    'correct_is': ('Correct answer: {a}', 'الإجابة الصحيحة: {a}'),
    'next': ('Next', 'التالي'),
    'winner': ('{name} is the last survivor!', '{name} هو آخر ناجٍ!'),
    'again': ('Play again', 'العب مجددًا'),
    'back': ('Back', 'رجوع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
}


def parse_names(text, limit=8):
    out, seen = [], set()
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:14]
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:limit]


class SurvivorMixin:
    def ls_init(self):
        self.ls_kind = 'trivia'
        self.ls_players = []
        self.ls_alive = []
        self.ls_pos = 0
        self.ls_deck = []
        self.ls_item = None
        self.ls_order = []
        self.ls_left = SECONDS
        self.ls_ev = None
        self.ls_res = 'ok'
        self.ls_revealed = False
        self._ls_lbl = None

    def ls_stop(self):
        ev = getattr(self, 'ls_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.ls_ev = None

    def ls(self, key, fs=16, pad=60, **fmt):
        en, ar = LS[key]
        return self.pair(en, ar, fs, pad, **fmt)

    # ---------- اختيار الوضع ----------
    def show_tv_mode(self, box):
        self.show_mode(box, 'tv_head', 'tv_home', 'trivia')

    def show_rd_mode(self, box):
        self.show_mode(box, 'rd_head', 'rd_home', 'riddles')

    def show_mode(self, box, head, solo_stage, kind):
        app = App.get_running_app()
        box.add_widget(self.label(self.ls(head, 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.ls('mode_hint', 15), fs=15, color=app.muted_color))
        box.add_widget(self.button(self.ls('solo', 16, 100), lambda: self.go(solo_stage)))
        box.add_widget(self.button(self.ls('survivor', 16, 100), lambda: self.ls_open(kind)))
        if getattr(self, 'dl_open', None) is not None:
            from game_duel import DL
            en, ar = DL['duel_btn']
            box.add_widget(self.button(self.pair(en, ar, 16, 100), lambda: self.dl_open(kind)))
        box.add_widget(self.button(self.ls('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ls_open(self, kind):
        self.ls_kind = kind
        self.deck_reset()
        self.go('ls_setup')

    def deck_reset(self):
        self.ls_deck = []

    # ---------- الإعداد ----------
    def show_ls_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.ls('head', 22), fs=22, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.ls('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.ls('names_hint', 14), fs=14, color=app.muted_color))
        row, _ = self.entry(self.ls('names_ph', 15, 100), key='ls_names')
        box.add_widget(row)
        box.add_widget(self.button(self.ls('start', 16, 100), self.ls_start))
        back = 'tv_mode' if self.ls_kind == 'trivia' else 'rd_mode'
        box.add_widget(self.button(self.ls('back', 15, 100), lambda: self.go(back), gray=True))

    def ls_start(self):
        self.snapshot()
        names = parse_names(self.form.get('ls_names', ''))
        if len(names) < 3:
            self.set_status(self.ls('need', 13))
            return
        self.ls_players = names
        self.ls_reset()
        self.go('ls_pass')

    def ls_reset(self):
        self.ls_alive = list(self.ls_players)
        self.ls_pos = 0
        self.deck_reset()

    # ---------- الأدوار ----------
    def cur_name(self):
        return self.disp_name(self.ls_alive[self.ls_pos])

    def show_ls_pass(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.ls('left', 14, 60, n=len(self.ls_alive)), fs=14,
                                  color=app.muted_color))
        box.add_widget(self.label(self.ls('pass', 24, 60, name=self.cur_name()), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.ls('ready', 17, 100), self.ls_ready))

    def ls_ready(self):
        size = len(bd.TRIVIA) if self.ls_kind == 'trivia' else len(bd.RIDDLES)
        if not self.ls_deck:
            self.ls_deck = list(range(size))
            random.shuffle(self.ls_deck)
        idx = self.ls_deck.pop()
        if self.ls_kind == 'trivia':
            self.ls_item = bd.TRIVIA[idx]
            self.ls_order = list(range(len(self.ls_item[2])))
            random.shuffle(self.ls_order)
        else:
            self.ls_item = bd.RIDDLES[idx]
        self.ls_left = SECONDS
        self.ls_revealed = False
        self.ls_res = 'ok'
        self.go('ls_q')

    def show_ls_q(self, box):
        app = App.get_running_app()
        it = self.ls_item
        box.add_widget(self.label(self.ls('turn', 18, 60, name=self.cur_name()), fs=18, bold=True,
                                  color=app.primary_color))
        timer = self.label(str(self.ls_left), fs=40, bold=True,
                           color=RED if self.ls_left <= 5 else app.text_color)
        box.add_widget(timer)
        self._ls_lbl = timer
        if self.ls_kind == 'trivia':
            box.add_widget(self.label(self.pair(it[0], it[1], 20, 50), fs=20, bold=True))
            for oi in self.ls_order:
                o = it[2][oi]
                box.add_widget(self.button(self.pair(o[0], o[1], 16, 110),
                                           lambda oi=oi: self.ls_pick(oi)))
            running = True
        else:
            card = Factory.GiftCard()
            card.add_widget(self.label(self.pair(it[0], it[1], 20, 90), fs=20, bold=True))
            box.add_widget(card)
            if not self.ls_revealed:
                box.add_widget(self.button(self.ls('reveal', 16, 100), self.ls_reveal))
                running = True
            else:
                box.add_widget(self.label(self.ls('answer', 22, 60, a=self.raw_pair(it[4], it[5])),
                                          fs=22, bold=True, color=app.primary_color))
                box.add_widget(self.label(self.ls('judge', 15), fs=15, color=app.muted_color))
                box.add_widget(self.button(self.ls('yes', 16, 100), lambda: self.ls_judge(True)))
                box.add_widget(self.button(self.ls('no', 16, 100), lambda: self.ls_judge(False),
                                           gray=True))
                running = False
        if running and self.ls_left > 0:
            self.ls_ev = Clock.schedule_interval(self.ls_tick, 1.0)

    def raw_pair(self, en, ar):
        return ar if self.is_ar() else en

    def ls_tick(self, dt):
        self.ls_left -= 1
        if self._ls_lbl is not None:
            self._ls_lbl.text = str(max(0, self.ls_left))
            if self.ls_left <= 5:
                self._ls_lbl.color = RED
        if self.ls_left <= 0:
            self.ls_stop()
            self.ls_finish('time')
            return False
        return True

    def ls_pick(self, oi):
        self.ls_finish('ok' if oi == self.ls_item[3] else 'out')

    def ls_reveal(self):
        self.ls_stop()
        self.ls_revealed = True
        self.render()

    def ls_judge(self, correct):
        self.ls_finish('ok' if correct else 'out')

    def ls_finish(self, res):
        self.ls_stop()
        self.ls_res = res
        self.go('ls_fb')

    def show_ls_fb(self, box):
        app = App.get_running_app()
        res = self.ls_res
        name = self.cur_name()
        if res == 'ok':
            box.add_widget(self.label(self.ls('ok', 22), fs=22, bold=True, color=GREEN))
        else:
            box.add_widget(self.label(self.ls('time' if res == 'time' else 'out', 22, 60, name=name),
                                      fs=22, bold=True, color=RED))
            it = self.ls_item
            if self.ls_kind == 'trivia':
                a = it[2][it[3]]
                ans = self.raw_pair(a[0], a[1])
            else:
                ans = self.raw_pair(it[4], it[5])
            box.add_widget(self.label(self.ls('correct_is', 18, 60, a=ans), fs=18))
        box.add_widget(self.button(self.ls('next', 16, 100), self.ls_next))

    def ls_next(self):
        if self.ls_res == 'ok':
            self.ls_pos = (self.ls_pos + 1) % len(self.ls_alive)
        else:
            self.ls_alive.pop(self.ls_pos)
            if self.ls_pos >= len(self.ls_alive):
                self.ls_pos = 0
        if len(self.ls_alive) <= 1:
            self.go('ls_end')
        else:
            self.go('ls_pass')

    def show_ls_end(self, box):
        app = App.get_running_app()
        name = self.disp_name(self.ls_alive[0]) if self.ls_alive else ''
        box.add_widget(self.label(self.ls('winner', 24, 60, name=name), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.ls('again', 16, 100), self.ls_again))
        box.add_widget(self.button(self.ls('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ls_again(self):
        self.ls_reset()
        self.go('ls_pass')
