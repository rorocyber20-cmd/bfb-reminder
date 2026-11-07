"""لعبة «من المصاب؟»: هاتف واحد، 4 لاعبين فأكثر (حتى 12).
مصاب واحد (أو اثنان عند 8 لاعبين فأكثر) ينتحلون صفة السليمين. كل جولة: نقاش ثم تصويت سري.
السليمون يصوّتون على من يشكّون به، والمصاب يختار من يريد إقصاءه. (اختياري) طبيب ينقذ شخصًا كل جولتين."""
import random
import re

from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

MIN_PLAYERS = 4
MAX_PLAYERS = 12
DOCTOR_MIN = 6
HEALTHY_GAP = 2      # عدد السليمين يجب أن يزيد على عدد المصابين بهذا القدر على الأقل
TALK_SECONDS = 60
RED = [0.85, 0.22, 0.25, 1]
GREEN = [0.15, 0.62, 0.30, 1]

OB = {
    'head': ('Who is infected?', 'من المصاب؟'),
    'rules': ('Pass the phone around. Some players are secretly INFECTED (you choose how many). '
              'Each round you talk, then everyone votes in secret. Healthy players vote for who they '
              'think is infected. The infected player chooses who to eliminate. '
              'If most healthy players pick the infected, they win. If they fail, the infected '
              "player's choice is eliminated. The infected win when they are as many as the healthy.",
              'مرّروا الهاتف بينكم. يوجد مصابون سرًّا (أنتم تختارون عددهم). '
              'في كل جولة تتناقشون ثم يصوّت الجميع سرًّا. السليمون يصوّتون على من يشكّون أنه المصاب، '
              'والمصاب يختار من يريد إقصاءه. إن اتفقت أغلبية السليمين على المصاب يفوزون. '
              'وإن أخطأوا يُقصى من اختاره المصاب. ويفوز المصابون عندما يتساوى عددهم مع عدد السليمين.'),
    'names_hint': ('Enter 4 to 12 player names, separated by commas.',
                   'أدخل من 4 إلى 12 اسمًا مفصولة بفواصل.'),
    'names_ph': ('Rayan, Mohamed, Bayan, Sara', 'ريان ، محمد ، بيان ، سارة'),
    'need': ('At least 4 different players are needed.', 'يلزم 4 لاعبين مختلفين على الأقل.'),
    'doc_on': ('Doctor: ON (needs 6+ players)', 'الطبيب: مفعّل (يلزم 6 لاعبين فأكثر)'),
    'doc_off': ('Doctor: OFF', 'الطبيب: متوقف'),
    'inf_n': ('Infected players: {k}', 'عدد المصابين: {k}'),
    'inf_hint': ('The healthy players must outnumber the infected by at least 2.',
                 'يجب أن يزيد عدد السليمين على المصابين بـ 2 على الأقل.'),
    'inf_max': ('With {n} players you can have at most {m} infected.',
                'مع {n} لاعبين أقصى عدد للمصابين هو {m}.'),
    'start': ('Start', 'ابدأ'),
    'pass_role': ('Pass the phone to {name}', 'مرّر الهاتف إلى {name}'),
    'pass_hint': ('Only {name} should look at the screen.', 'يجب أن ينظر {name} وحده إلى الشاشة.'),
    'got': ('I got the phone', 'استلمت الهاتف'),
    'hold': ('Hold to see your role', 'اضغط مطوّلًا لترى دورك'),
    'hidden': ('Role hidden', 'الدور مخفي'),
    'done': ('Done', 'تم'),
    'r_inf': ('You are INFECTED! Act healthy and eliminate one player each round.',
              'أنت المصاب! تظاهر بأنك سليم وأقصِ لاعبًا في كل جولة.'),
    'r_partner': ('Your infected partner: {name}', 'شريكك المصاب: {name}'),
    'r_ok': ('You are HEALTHY. Find the infected!', 'أنت سليم. اكتشف المصاب!'),
    'r_doc': ('You are the DOCTOR (healthy). In rounds 1, 3, 5... you can protect one player '
              'from the infection. You may protect yourself.',
              'أنت الطبيب (سليم). في الجولات 1 و3 و5... يمكنك حماية لاعب من العدوى. '
              'ويمكنك أن تحمي نفسك.'),
    'round': ('Round {r}', 'الجولة {r}'),
    'alive': ('Players left: {n}', 'اللاعبون المتبقون: {n}'),
    'inf_left': ('Infected left: {n}', 'المصابون المتبقون: {n}'),
    'prot_yes': ('Doctor protection: available this round', 'حماية الطبيب: متاحة في هذه الجولة'),
    'prot_no': ('Doctor protection: resting this round', 'حماية الطبيب: مستريحة في هذه الجولة'),
    'talk': ('Discuss! Who looks infected?', 'ناقشوا! من يبدو مصابًا؟'),
    'talk_up': ("Time's up!", 'انتهى الوقت!'),
    'to_vote': ('Go to voting', 'انتقل إلى التصويت'),
    'pass_vote': ('Pass the phone to {name} to vote', 'مرّر الهاتف إلى {name} للتصويت'),
    'pick': ('{name}: choose a player', '{name}: اختر لاعبًا'),
    'pick_hint': ('Healthy: vote for who you think is infected. Infected: choose who to eliminate.',
                  'السليم: صوّت على من تشك أنه المصاب. المصاب: اختر من تريد إقصاءه.'),
    'prot': ('{name}: choose a player to protect', '{name}: اختر لاعبًا لحمايته'),
    'prot_hint': ("Only the Doctor's choice counts, and only on rounds 1, 3, 5... Everyone must choose.",
                  'يُحسب اختيار الطبيب فقط وفي الجولات 1 و3 و5... فقط. على الجميع أن يختاروا.'),
    'confirm': ('Confirm', 'تأكيد'),
    'choose_first': ('Choose a player first.', 'اختر لاعبًا أولًا.'),
    'tally': ('Votes of the healthy players:', 'أصوات السليمين:'),
    'no_votes': ('No votes.', 'لا أصوات.'),
    'caught': ('{name} was the infected and is out!', '{name} كان المصاب وخرج من اللعبة!'),
    'wrong': ('The vote failed.', 'فشل التصويت.'),
    'saved': ('{name} was attacked, but the Doctor saved them!', 'تعرّض {name} للهجوم لكن الطبيب أنقذه!'),
    'out': ('{name} was eliminated.', 'تم إقصاء {name}.'),
    'next_round': ('Next round', 'الجولة التالية'),
    'win_ok': ('The healthy players win!', 'السليمون يفوزون!'),
    'win_inf': ('The infected win!', 'المصابون يفوزون!'),
    'roles': ('Roles:', 'الأدوار:'),
    'role_inf': ('infected', 'مصاب'),
    'role_doc': ('doctor', 'طبيب'),
    'role_ok': ('healthy', 'سليم'),
    'again': ('Play again', 'العب مجددًا'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'back': ('Back', 'رجوع'),
}


def parse_names(text, limit=MAX_PLAYERS):
    out, seen = [], set()
    for p in re.split(r'[,،\n]+', text or ''):
        p = p.strip()[:14]
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:limit]


def max_infected(n):
    """أكبر عدد مصابين مسموح: السليمون يزيدون عليهم بـ HEALTHY_GAP على الأقل."""
    return max(1, (n - HEALTHY_GAP) // 2)


def assign_roles(names, use_doctor, k=1):
    """يرجع قاموس {اسم: 'inf' | 'doc' | 'ok'}."""
    order = list(names)
    random.shuffle(order)
    roles = {n: 'ok' for n in names}
    k = max(1, min(int(k), max_infected(len(names))))
    for n in order[:k]:
        roles[n] = 'inf'
    if use_doctor and len(names) >= DOCTOR_MIN:
        roles[order[k]] = 'doc'
    return roles


def protection_available(round_no):
    """الطبيب يحمي في الجولات 1 و3 و5... (يستريح في الجولة التي بعد كل حماية)."""
    return round_no % 2 == 1


def resolve_round(alive, roles, votes, prots, round_no, rnd=random):
    """يحسب نتيجة الجولة.
    votes: {لاعب: هدف} لكل لاعب حي. prots: اختيارات الحماية.
    يرجع قاموسًا: kind (caught|saved|out)، target، tally {هدف: عدد أصوات السليمين}."""
    healthy = [p for p in alive if roles[p] != 'inf']
    infected = [p for p in alive if roles[p] == 'inf']
    tally = {}
    for p in healthy:
        t = votes.get(p)
        if t in alive:
            tally[t] = tally.get(t, 0) + 1
    need = len(healthy) / 2.0
    top = [t for t, c in tally.items() if c > need]
    if top and roles[top[0]] == 'inf':
        return {'kind': 'caught', 'target': top[0], 'tally': tally}
    picks = [votes[p] for p in infected if votes.get(p) in alive]
    victim = rnd.choice(picks) if picks else rnd.choice(alive)
    doc = next((p for p in alive if roles[p] == 'doc'), None)
    if doc and protection_available(round_no) and prots.get(doc) == victim:
        return {'kind': 'saved', 'target': victim, 'tally': tally}
    return {'kind': 'out', 'target': victim, 'tally': tally}


def check_win(alive, roles):
    inf = sum(1 for p in alive if roles[p] == 'inf')
    ok = len(alive) - inf
    if inf == 0:
        return 'ok'
    if inf >= ok:
        return 'inf'
    return None


class OutbreakMixin:
    def ob_init(self):
        self.ob_players = []
        self.ob_roles = {}
        self.ob_doc = True
        self.ob_k = 1
        self.ob_alive = []
        self.ob_round = 1
        self.ob_ri = 0            # دور عرض الأدوار
        self.ob_voters = []
        self.ob_vi = 0
        self.ob_votes = {}
        self.ob_prots = {}
        self.ob_sel = None
        self.ob_result = None
        self.ob_winner = None
        self.ob_use_doc = False
        self.ob_left = TALK_SECONDS
        self.ob_ev = None
        self._ob_lbl = None

    def ob_stop(self):
        ev = getattr(self, 'ob_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self.ob_ev = None

    def ob(self, key, fs=16, pad=60, **fmt):
        en, ar = OB[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def ob_nm(self, name):
        return self.disp_name(name)

    # ---------- الإعداد ----------
    def show_ob_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.ob('head', 24), fs=24, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.ob('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.ob('names_hint', 14), fs=14, color=app.muted_color))
        row, _ = self.entry(self.ob('names_ph', 15, 100), key='ob_names')
        box.add_widget(row)
        box.add_widget(self.label(self.ob('inf_n', 18, 60, k=self.ob_k), fs=18, bold=True))
        row = BoxLayout(size_hint_y=None, height=dp(app.btn_height), spacing=dp(10))
        row.add_widget(self.button('-', lambda: self.ob_change_k(-1)))
        row.add_widget(self.button('+', lambda: self.ob_change_k(1)))
        box.add_widget(row)
        box.add_widget(self.label(self.ob('inf_hint', 12, 60), fs=12, color=app.muted_color))
        box.add_widget(self.button(self.ob('doc_on' if self.ob_doc else 'doc_off', 15, 100),
                                   self.ob_toggle_doc, gray=not self.ob_doc))
        box.add_widget(self.button(self.ob('start', 16, 100), self.ob_start))
        box.add_widget(self.button(self.ob('menu', 15, 100), lambda: self.go('menu'), gray=True))

    def ob_change_k(self, delta):
        self.snapshot()
        self.ob_k = max(1, min(MAX_PLAYERS, self.ob_k + delta))
        self.render()

    def ob_toggle_doc(self):
        self.snapshot()
        self.ob_doc = not self.ob_doc
        self.render()

    def ob_start(self):
        self.snapshot()
        names = parse_names(self.form.get('ob_names', ''))
        if len(names) < MIN_PLAYERS:
            self.set_status(self.ob('need', 13))
            return
        m = max_infected(len(names))
        if self.ob_k > m:
            self.set_status(self.ob('inf_max', 13, 60, n=len(names), m=m))
            return
        self.ob_players = names
        self.ob_new_game()

    def ob_new_game(self):
        self.ob_use_doc = bool(self.ob_doc and len(self.ob_players) >= DOCTOR_MIN)
        self.ob_roles = assign_roles(self.ob_players, self.ob_use_doc, self.ob_k)
        self.ob_alive = list(self.ob_players)
        self.ob_round = 1
        self.ob_ri = 0
        self.ob_winner = None
        self.go('ob_rpass')

    # ---------- كشف الأدوار ----------
    def show_ob_rpass(self, box):
        app = App.get_running_app()
        name = self.ob_nm(self.ob_players[self.ob_ri])
        box.add_widget(self.label(self.ob('pass_role', 24, 60, name=name), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.ob('pass_hint', 14, 60, name=name), fs=14,
                                  color=app.muted_color))
        box.add_widget(self.button(self.ob('got', 17, 100), lambda: self.go('ob_rshow')))

    def ob_role_text(self, player):
        role = self.ob_roles[player]
        if role == 'inf':
            text = self.ob('r_inf', 20, 60)
            partners = [p for p in self.ob_players if p != player and self.ob_roles[p] == 'inf']
            for p in partners:
                text += '\n\n' + self.ob('r_partner', 18, 60, name=self.ob_nm(p))
            return text, RED
        if role == 'doc':
            return self.ob('r_doc', 18, 60), GREEN
        return self.ob('r_ok', 20, 60), GREEN

    def show_ob_rshow(self, box):
        app = App.get_running_app()
        player = self.ob_players[self.ob_ri]
        box.add_widget(self.label(self.ob_nm(player), fs=22, bold=True, color=app.primary_color))
        hidden = self.ob('hidden', 16)
        info = self.label(hidden, fs=20, bold=True, color=app.muted_color)
        box.add_widget(info)
        text, color = self.ob_role_text(player)

        def show(*a):
            info.text = text
            info.color = color

        def hide(*a):
            info.text = hidden
            info.color = app.muted_color

        btn = Factory.StyledButton(text=self.ob('hold', 17, 100))
        btn.height = dp(90)
        btn.bind(on_press=show, on_release=hide)
        box.add_widget(btn)
        box.add_widget(self.button(self.ob('done', 16, 100), self.ob_role_done))

    def ob_role_done(self):
        self.ob_ri += 1
        if self.ob_ri >= len(self.ob_players):
            self.ob_left = TALK_SECONDS
            self.go('ob_talk')
        else:
            self.go('ob_rpass')

    # ---------- النقاش ----------
    def ob_counts(self):
        inf = sum(1 for p in self.ob_alive if self.ob_roles[p] == 'inf')
        return inf

    def show_ob_talk(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.ob('round', 24, 60, r=self.ob_round), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.ob('alive', 15, 60, n=len(self.ob_alive)), fs=15,
                                  color=app.muted_color))
        box.add_widget(self.label(self.ob('inf_left', 15, 60, n=self.ob_counts()), fs=15,
                                  color=app.muted_color))
        if self.ob_use_doc:
            key = 'prot_yes' if protection_available(self.ob_round) else 'prot_no'
            box.add_widget(self.label(self.ob(key, 14, 60), fs=14, color=app.muted_color))
        for p in self.ob_alive:
            box.add_widget(self.label(self.wrap_user(p, 16, 100), fs=16))
        box.add_widget(self.label(self.ob('talk', 18, 60), fs=18, bold=True))
        timer = self.label(str(max(0, self.ob_left)), fs=40, bold=True,
                           color=RED if self.ob_left <= 10 else app.text_color)
        box.add_widget(timer)
        self._ob_lbl = timer
        box.add_widget(self.button(self.ob('to_vote', 16, 100), self.ob_begin_vote))
        if self.ob_left > 0:
            self.ob_ev = Clock.schedule_interval(self.ob_tick, 1.0)

    def ob_tick(self, dt):
        self.ob_left -= 1
        if self._ob_lbl is not None:
            self._ob_lbl.text = str(max(0, self.ob_left)) if self.ob_left > 0 \
                else self.ob('talk_up', 20)
            if self.ob_left <= 10:
                self._ob_lbl.color = RED
        if self.ob_left <= 0:
            self.ob_stop()
            return False
        return True

    # ---------- التصويت ----------
    def ob_begin_vote(self):
        self.ob_stop()
        self.ob_voters = list(self.ob_alive)
        self.ob_vi = 0
        self.ob_votes = {}
        self.ob_prots = {}
        self.ob_sel = None
        self.go('ob_vpass')

    def ob_voter(self):
        return self.ob_voters[self.ob_vi]

    def show_ob_vpass(self, box):
        app = App.get_running_app()
        name = self.ob_nm(self.ob_voter())
        box.add_widget(self.label(self.ob('pass_vote', 24, 60, name=name), fs=24, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.button(self.ob('got', 17, 100), lambda: self.go('ob_vpick')))

    def ob_choices(self, include_self):
        me = self.ob_voter()
        return [p for p in self.ob_alive if include_self or p != me]

    def ob_pick_list(self, box, include_self):
        for p in self.ob_choices(include_self):
            b = self.button(self.wrap_user(p, 16, 100), lambda p=p: self.ob_select(p),
                            gray=(p != self.ob_sel))
            box.add_widget(b)

    def ob_select(self, p):
        self.ob_sel = p
        self.render()

    def show_ob_vpick(self, box):
        app = App.get_running_app()
        name = self.ob_nm(self.ob_voter())
        box.add_widget(self.label(self.ob('pick', 20, 60, name=name), fs=20, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.ob('pick_hint', 13, 60), fs=13, color=app.muted_color))
        self.ob_pick_list(box, False)
        box.add_widget(self.button(self.ob('confirm', 16, 100), self.ob_vote_ok))

    def ob_vote_ok(self):
        if self.ob_sel is None:
            self.set_status(self.ob('choose_first', 13))
            return
        self.ob_votes[self.ob_voter()] = self.ob_sel
        self.ob_sel = None
        if self.ob_use_doc:
            self.go('ob_ppick')
        else:
            self.ob_next_voter()

    def show_ob_ppick(self, box):
        app = App.get_running_app()
        name = self.ob_nm(self.ob_voter())
        box.add_widget(self.label(self.ob('prot', 20, 60, name=name), fs=20, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.ob('prot_hint', 13, 60), fs=13, color=app.muted_color))
        self.ob_pick_list(box, True)
        box.add_widget(self.button(self.ob('confirm', 16, 100), self.ob_prot_ok))

    def ob_prot_ok(self):
        if self.ob_sel is None:
            self.set_status(self.ob('choose_first', 13))
            return
        self.ob_prots[self.ob_voter()] = self.ob_sel
        self.ob_sel = None
        self.ob_next_voter()

    def ob_next_voter(self):
        self.ob_vi += 1
        if self.ob_vi >= len(self.ob_voters):
            self.ob_finish_round()
        else:
            self.go('ob_vpass')

    # ---------- النتيجة ----------
    def ob_finish_round(self):
        res = resolve_round(self.ob_alive, self.ob_roles, self.ob_votes, self.ob_prots,
                            self.ob_round)
        self.ob_result = res
        if res['kind'] in ('caught', 'out'):
            self.ob_alive.remove(res['target'])
        self.ob_winner = check_win(self.ob_alive, self.ob_roles)
        self.go('ob_res')

    def show_ob_res(self, box):
        app = App.get_running_app()
        res = self.ob_result
        box.add_widget(self.label(self.ob('tally', 15), fs=15, color=app.muted_color))
        if res['tally']:
            for p, c in sorted(res['tally'].items(), key=lambda x: -x[1]):
                box.add_widget(self.label(self.wrap_user(f'{p}: {c}', 16, 100), fs=16))
        else:
            box.add_widget(self.label(self.ob('no_votes', 15), fs=15))
        name = self.ob_nm(res['target'])
        if res['kind'] == 'caught':
            box.add_widget(self.label(self.ob('caught', 24, 60, name=name), fs=24, bold=True,
                                      color=GREEN))
        else:
            box.add_widget(self.label(self.ob('wrong', 20), fs=20, bold=True, color=RED))
            key = 'saved' if res['kind'] == 'saved' else 'out'
            box.add_widget(self.label(self.ob(key, 20, 60, name=name), fs=20, bold=True))
        if self.ob_winner:
            box.add_widget(self.button(self.ob('next_round', 16, 100), lambda: self.go('ob_end')))
        else:
            box.add_widget(self.button(self.ob('next_round', 16, 100), self.ob_next_round))

    def ob_next_round(self):
        self.ob_round += 1
        self.ob_left = TALK_SECONDS
        self.go('ob_talk')

    def show_ob_end(self, box):
        app = App.get_running_app()
        key = 'win_ok' if self.ob_winner == 'ok' else 'win_inf'
        box.add_widget(self.label(self.ob(key, 26), fs=26, bold=True,
                                  color=GREEN if self.ob_winner == 'ok' else RED))
        box.add_widget(self.label(self.ob('roles', 15), fs=15, color=app.muted_color))
        for p in self.ob_players:
            role = self.ob_roles[p]
            rk = {'inf': 'role_inf', 'doc': 'role_doc'}.get(role, 'role_ok')
            en, ar = OB[rk]
            word = ar if self.is_ar() else en
            box.add_widget(self.label(self.wrap_user(f'{p}: {word}', 16, 100), fs=16,
                                      color=RED if role == 'inf' else app.text_color))
        box.add_widget(self.button(self.ob('again', 16, 100), self.ob_new_game))
        box.add_widget(self.button(self.ob('menu', 15, 100), lambda: self.go('menu'), gray=True))
