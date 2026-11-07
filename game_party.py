"""ألعاب الأصدقاء (هاتف واحد يمر بين اللاعبين): صراحة وتحدي، من الأقرب إليك."""
import random
import re

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App

import party_data as pd

try:
    from game_tools import WheelWidget, WHEEL_COLORS
except Exception:
    WheelWidget = None
    WHEEL_COLORS = [(0.25, 0.55, 0.90, 1)]

GRAY = [0.45, 0.47, 0.52, 1]

PT = {
    'td_head': ('Truth or Dare', 'صراحة وتحدي'),
    'level': ('Choose a level', 'اختر المستوى'),
    'fun': ('Fun', 'خفيف'),
    'bold': ('Bold', 'جريء'),
    'names_hint': ("Players' names, separated by commas (optional)",
                   'أسماء اللاعبين مفصولة بفواصل (اختياري)'),
    'names_ph': ('Rayan, Mohamed, Bayan', 'ريان ، محمد ، بيان'),
    'start': ('Start', 'ابدأ'),
    'turn': ("{name}'s turn", 'دور {name}'),
    'pick': ('Truth or Dare?', 'صراحة أم تحدي؟'),
    'truth': ('Truth', 'صراحة'),
    'dare': ('Dare', 'تحدي'),
    'another': ('Another one', 'واحد آخر'),
    'next_p': ('Next player', 'اللاعب التالي'),
    'next_t': ('Next turn', 'الدور التالي'),
    'mode_head': ('How do you want to play?', 'كيف تريدون اللعب؟'),
    'mode_app': ('App picks the questions and dares', 'التطبيق يختار الأسئلة والتحديات'),
    'mode_wheel': ('Who asks whom? (wheel picks the pair)', 'من يسأل من؟ (العجلة تختار الزوج)'),
    'tw_hint': ('Enter 3 to 12 player names, separated by commas. The wheel picks who asks and who is asked. '
                'You make up the questions and dares yourselves!',
                'أدخل من 3 إلى 12 اسمًا مفصولة بفواصل. العجلة تختار من يسأل ومن يُسأل، '
                'وأنتم من يبتكر الأسئلة والتحديات!'),
    'tw_need': ('At least 3 different players are needed.', 'يلزم 3 لاعبين مختلفين على الأقل.'),
    'tw_round': ('Round {r}', 'الجولة {r}'),
    'tw_spin1': ('Spin: who asks?', 'أدر العجلة: من يسأل؟'),
    'tw_spin2': ('Spin: who is asked?', 'أدر العجلة: من يُسأل؟'),
    'tw_asker': ('{name} asks!', '{name} هو من يسأل!'),
    'tw_pair': ('{a} asks {b}!', '{a} يسأل {b}!'),
    'tw_pair_hint': ('Ask a question or give a dare. {b} chooses: truth or dare?',
                     'اسأل سؤالًا أو اطلب تحديًا. و{b} يختار: صراحة أم تحدي؟'),
    'tw_next': ('Next round', 'الجولة التالية'),
    'ml_head': ('Who is most likely to...', 'من الأكثر احتمالًا أن ...'),
    'ml_names': ('Enter 3 to 8 player names, separated by commas.',
                 'أدخل من 3 إلى 8 أسماء لاعبين مفصولة بفواصل.'),
    'ml_need': ('At least 3 players are needed. Please enter 3 different names or more.',
                 'يلزم 3 لاعبين على الأقل. الرجاء إدخال 3 أسماء مختلفة أو أكثر.'),
    'ml_pass': ('Pass the phone to {name}', 'مرّر الهاتف إلى {name}'),
    'ml_vote': ('Vote for the person you think fits best:', 'صوّت لمن تظنه الأنسب:'),
    'ml_winner': ('Most votes: {names}', 'الأكثر أصواتًا: {names}'),
    'ml_next': ('Next question', 'السؤال التالي'),
    'ml_finish': ('Final results', 'النتائج النهائية'),
    'ml_final': ('Final ranking', 'الترتيب النهائي'),
    'ml_line': ('{name}: {n}', '{name}: {n}'),
    'progress': ('Question {i} of {n}', 'السؤال {i} من {n}'),
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


class PartyMixin:
    def party_init(self):
        self.td_level = 'fun'
        self.td_mode = 'app'
        self.tw_players = []
        self.tw_round = 1
        self.tw_phase = 0
        self.tw_opts = []
        self.tw_angle = 0.0
        self.tw_asker = ''
        self.tw_target = ''
        self.td_players = []
        self.td_turn = 0
        self.td_card = None
        self.td_kind = ''
        self.td_decks = {}
        self.ml_players = []
        self.ml_qs = []
        self.ml_i = 0
        self.ml_votes = {}
        self.ml_voter = 0
        self.ml_totals = {}

    def tt(self, table, key, fs=16, pad=60, **fmt):
        en, ar = table[key]
        return self.pair(en, ar, fs, pad, **fmt)

    # ---------- صراحة وتحدي ----------
    def draw_card(self, kind):
        src = (pd.TRUTHS if kind == 'truth' else pd.DARES)[self.td_level]
        key = (kind, self.td_level)
        deck = self.td_decks.get(key)
        if not deck:
            deck = list(range(len(src)))
            random.shuffle(deck)
            self.td_decks[key] = deck
        return src[deck.pop()]

    def show_td_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tt(PT, 'td_head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tt(PT, 'mode_head', 16), fs=16, bold=True))
        for md in ('app', 'wheel'):
            box.add_widget(self.button(self.tt(PT, 'mode_' + md, 15, 100),
                                       lambda md=md: self.td_set_mode(md),
                                       gray=(md != self.td_mode)))
        if self.td_mode == 'app':
            box.add_widget(self.label(self.tt(PT, 'level', 16), fs=16, bold=True))
            row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
            for lv in ('fun', 'bold'):
                b = Factory.StyledButton(text=self.tt(PT, lv, 16, 100))
                if lv != self.td_level:
                    b.custom_bg = GRAY
                b.bind(on_release=lambda inst, lv=lv: self.td_set_level(lv))
                row.add_widget(b)
            box.add_widget(row)
            box.add_widget(self.label(self.tt(PT, 'names_hint', 14), fs=14, color=app.muted_color))
        else:
            box.add_widget(self.label(self.tt(PT, 'tw_hint', 14), fs=14, color=app.muted_color))
        er, _ = self.entry(self.tt(PT, 'names_ph', 15, 100), multiline=False, key='td_names')
        box.add_widget(er)
        box.add_widget(self.button(self.tt(PT, 'start', 16, 100), self.td_start))
        box.add_widget(self.button(self.tt(PT, 'menu', 15, 100), lambda: self.go('menu'), gray=True))

    def td_set_mode(self, md):
        self.snapshot()
        self.td_mode = md
        self.render()

    def td_set_level(self, lv):
        self.td_level = lv
        self.render()

    def td_start(self):
        self.snapshot()
        if self.td_mode == 'wheel':
            names = parse_names(self.form.get('td_names', ''), limit=12)
            if len(names) < 3:
                self.set_status(self.tt(PT, 'tw_need', 13))
                return
            self.tw_players = names
            self.tw_reset()
            self.go('tw_play')
            return
        self.td_players = parse_names(self.form.get('td_names', ''))
        self.td_turn = 0
        self.td_card = None
        self.go('td_play')

    def show_td_play(self, box):
        app = App.get_running_app()
        if self.td_players:
            name = self.disp_name(self.td_players[self.td_turn % len(self.td_players)])
            box.add_widget(self.label(self.tt(PT, 'turn', 22, 60, name=name), fs=22, bold=True,
                                      color=app.primary_color))
        if self.td_card is None:
            box.add_widget(self.label(self.tt(PT, 'pick', 18), fs=18, bold=True))
            box.add_widget(self.button(self.tt(PT, 'truth', 18, 100),
                                       lambda: self.td_draw('truth')))
            box.add_widget(self.button(self.tt(PT, 'dare', 18, 100),
                                       lambda: self.td_draw('dare')))
        else:
            card = Factory.GiftCard()
            card.add_widget(self.label(self.tt(PT, self.td_kind, 16), fs=16, bold=True,
                                       color=app.primary_color))
            card.add_widget(self.label(self.pair(self.td_card[0], self.td_card[1], 20, 90),
                                       fs=20, bold=True))
            box.add_widget(card)
            box.add_widget(self.button(self.tt(PT, 'another', 15, 100),
                                       lambda: self.td_draw(self.td_kind), gray=True))
            box.add_widget(self.button(
                self.tt(PT, 'next_p' if self.td_players else 'next_t', 16, 100), self.td_next))
        box.add_widget(self.button(self.tt(PT, 'back', 15, 100),
                                   lambda: self.go('td_setup'), gray=True))

    # ---------- صراحة وتحدي: العجلة تختار الزوج ----------
    def tw_reset(self):
        self.tw_round = 1
        self.tw_phase = 0
        self.tw_opts = []
        self.tw_angle = 0.0
        self.tw_asker = ''
        self.tw_target = ''

    def show_tw_play(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tt(PT, 'tw_round', 22, 60, r=self.tw_round), fs=22,
                                  bold=True, color=app.primary_color))
        if self.tw_opts and WheelWidget is not None:
            wheel = WheelWidget(size_hint_y=None, height=dp(280))
            wheel.n = max(2, len(self.tw_opts))
            wheel.angle = self.tw_angle
            self._wheel = wheel
            box.add_widget(wheel)
        if self.tw_phase == 0:
            if self.tw_opts:
                self.tw_legend(box)
            box.add_widget(self.button(self.tt(PT, 'tw_spin1', 17, 100), self.tw_spin_asker))
        elif self.tw_phase == 1:
            box.add_widget(self.label(self.tt(PT, 'tw_asker', 22, 60,
                                              name=self.disp_name(self.tw_asker)),
                                      fs=22, bold=True, color=app.primary_color))
            self.tw_legend(box)
            box.add_widget(self.button(self.tt(PT, 'tw_spin2', 17, 100), self.tw_spin_target))
        else:
            box.add_widget(self.label(
                self.tt(PT, 'tw_pair', 24, 60, a=self.disp_name(self.tw_asker),
                        b=self.disp_name(self.tw_target)),
                fs=24, bold=True, color=app.primary_color))
            box.add_widget(self.label(
                self.tt(PT, 'tw_pair_hint', 15, 60, b=self.disp_name(self.tw_target)),
                fs=15, color=app.muted_color))
            self.tw_legend(box)
            box.add_widget(self.button(self.tt(PT, 'tw_next', 16, 100), self.tw_next))
        box.add_widget(self.button(self.tt(PT, 'back', 15, 100),
                                   lambda: self.go('td_setup'), gray=True))

    def tw_legend(self, box):
        for i, opt in enumerate(self.tw_opts):
            col = list(WHEEL_COLORS[i % len(WHEEL_COLORS)])
            box.add_widget(self.label(self.wrap_user(opt, 15, 100), fs=15, bold=True, color=col))

    def tw_spin(self, opts, done):
        if getattr(self, 'wheel_anim', None) is not None:
            return
        self.tw_opts = list(opts)
        self.tw_angle = 0.0
        self.render()                       # يبني العجلة الجديدة
        wheel = self._wheel
        idx = random.randrange(len(opts))
        if wheel is None:                   # لو تعذّر تحميل العجلة نكتفي بالنتيجة
            done(opts[idx])
            return
        seg = 360.0 / len(opts)
        theta = (idx + random.uniform(0.15, 0.85)) * seg
        final = 360 * 5 + theta
        anim = Animation(angle=final, duration=3.5, t='out_cubic')

        def finished(*a):
            self.tw_angle = final % 360
            self.wheel_anim = None
            done(opts[idx])

        anim.bind(on_complete=finished)
        self.wheel_anim = anim
        anim.start(wheel)

    def tw_spin_asker(self):
        def done(name):
            self.tw_asker = name
            self.tw_phase = 1
            self.render()
        self.tw_spin(self.tw_players, done)

    def tw_spin_target(self):
        def done(name):
            self.tw_target = name
            self.tw_phase = 2
            self.render()
        self.tw_spin([p for p in self.tw_players if p != self.tw_asker], done)

    def tw_next(self):
        self.tw_round += 1
        self.tw_phase = 0
        self.tw_opts = []
        self.tw_angle = 0.0
        self.render()

    def td_draw(self, kind):
        self.td_kind = kind
        self.td_card = self.draw_card(kind)
        self.render()

    def td_next(self):
        self.td_turn += 1
        self.td_card = None
        self.render()

    # ---------- من الأقرب إليك ----------
    def show_ml_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tt(PT, 'ml_head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tt(PT, 'ml_names', 15), fs=15, color=app.muted_color))
        er, _ = self.entry(self.tt(PT, 'names_ph', 15, 100), key='ml_names')
        box.add_widget(er)
        box.add_widget(self.button(self.tt(PT, 'start', 16, 100), self.ml_start))
        box.add_widget(self.button(self.tt(PT, 'menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ml_start(self):
        self.snapshot()
        names = parse_names(self.form.get('ml_names', ''))
        if len(names) < 3:
            self.set_status(self.tt(PT, 'ml_need', 13))
            return
        self.ml_players = names
        self.ml_qs = random.sample(range(len(pd.LIKELY)), min(8, len(pd.LIKELY)))
        self.ml_i = 0
        self.ml_totals = {n: 0 for n in names}
        self.ml_new_round()
        self.go('ml_vote')

    def ml_new_round(self):
        self.ml_votes = {n: 0 for n in self.ml_players}
        self.ml_voter = 0

    def show_ml_vote(self, box):
        app = App.get_running_app()
        n = len(self.ml_qs)
        en, ar = pd.LIKELY[self.ml_qs[self.ml_i]]
        voter = self.ml_players[self.ml_voter]
        box.add_widget(self.label(self.tt(PT, 'progress', 13, 60, i=self.ml_i + 1, n=n),
                                  fs=13, color=app.muted_color))
        card = Factory.GiftCard()
        card.add_widget(self.label(self.pair(en, ar, 20, 90), fs=20, bold=True))
        box.add_widget(card)
        box.add_widget(self.label(self.tt(PT, 'ml_pass', 18, 60, name=self.disp_name(voter)),
                                  fs=18, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.tt(PT, 'ml_vote', 14), fs=14, color=app.muted_color))
        for name in self.ml_players:
            if name == voter:
                continue
            box.add_widget(self.button(self.shape(name, 16, 100) if self.is_ar()
                                       else self.disp_name(name),
                                       lambda nm=name: self.ml_cast(nm)))

    def ml_cast(self, name):
        self.ml_votes[name] += 1
        self.ml_voter += 1
        if self.ml_voter >= len(self.ml_players):
            top = max(self.ml_votes.values())
            for nm, v in self.ml_votes.items():
                if v == top:
                    self.ml_totals[nm] += 1
            self.go('ml_result')
        else:
            self.render()

    def show_ml_result(self, box):
        app = App.get_running_app()
        en, ar = pd.LIKELY[self.ml_qs[self.ml_i]]
        top = max(self.ml_votes.values())
        winners = [self.disp_name(n) for n, v in self.ml_votes.items() if v == top]
        card = Factory.GiftCard()
        card.add_widget(self.label(self.pair(en, ar, 17, 90), fs=17, bold=True))
        box.add_widget(card)
        box.add_widget(self.label(self.tt(PT, 'ml_winner', 22, 60, names=' + '.join(winners)),
                                  fs=22, bold=True, color=app.primary_color))
        for nm, v in sorted(self.ml_votes.items(), key=lambda kv: -kv[1]):
            box.add_widget(self.label(self.tt(PT, 'ml_line', 15, 60, name=self.disp_name(nm), n=v),
                                      fs=15, color=app.muted_color))
        last = self.ml_i + 1 >= len(self.ml_qs)
        box.add_widget(self.button(self.tt(PT, 'ml_finish' if last else 'ml_next', 16, 100),
                                   self.ml_next))

    def ml_next(self):
        self.ml_i += 1
        if self.ml_i >= len(self.ml_qs):
            self.go('ml_final')
        else:
            self.ml_new_round()
            self.go('ml_vote')

    def show_ml_final(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tt(PT, 'ml_final', 22), fs=22, bold=True,
                                  color=app.primary_color))
        for nm, v in sorted(self.ml_totals.items(), key=lambda kv: -kv[1]):
            box.add_widget(self.label(self.tt(PT, 'ml_line', 18, 60, name=self.disp_name(nm), n=v),
                                      fs=18, bold=True))
        box.add_widget(self.button(self.tt(PT, 'again', 16, 100), lambda: self.go('ml_setup')))
        box.add_widget(self.button(self.tt(PT, 'menu', 15, 100), lambda: self.go('menu'), gray=True))
