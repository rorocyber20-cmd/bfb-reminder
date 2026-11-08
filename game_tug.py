"""لعبة «شد الحبل»: هاتف واحد موضوع بين فريقين متقابلين (1 ضد 1 أو 2 ضد 2).
الشاشة نصفان: الفريق 2 في النصف الأعلى (النص مقلوب 180°) والفريق 1 في الأسفل.
كل اللمس يُعالَج داخل لوحة واحدة (TugArena) فتتحمل عدة أصابع في وقت واحد.
الحبل يتحرك نحو الفريق الذي يضغط أكثر، ومن يوصله إلى طرفه يفوز."""
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, PopMatrix, PushMatrix, Rectangle, Rotate,
                           RoundedRectangle)
from kivy.metrics import dp, sp
from kivy.uix.label import Label
from kivy.uix.widget import Widget

# عدد الضغطات الصافية (الفارق) اللازم للفوز: كلما قلّ كان الحبل أسرع وكل ضغطة أوضح
NEED = {'1v1': 15, '2v2': 24}
ZONE = 0.30          # ارتفاع منطقة كل فريق من ارتفاع اللوحة

TG = {
    'head': ('Tug of War', 'شد الحبل'),
    'rules': ('Two sides face each other on one phone. Tap your side as fast as you can to pull '
              'the rope towards you. Whoever brings the rope to their end wins!',
              'جانبان يتقابلان على هاتف واحد. اضغط على جهتك بأسرع ما تستطيع لتشدّ الحبل نحوك. '
              'من يوصل الحبل إلى طرفه يفوز!'),
    'tip': ('Put the phone flat on a table between you. Team 2 sits at the top of the screen.',
            'ضعوا الهاتف مسطحًا على طاولة بينكم. الفريق 2 يجلس في أعلى الشاشة.'),
    'pick': ('Choose a mode', 'اختر الوضع'),
    'm11': ('1 vs 1', '1 ضد 1'),
    'm11_d': ('One big button per player.', 'زر كبير واحد لكل لاعب.'),
    'm22': ('2 vs 2', '2 ضد 2'),
    'm22_d': ('Two players per team: each one takes one half of the team zone.',
              'لاعبان في كل فريق: كل واحد يأخذ نصف منطقة فريقه.'),
    'ready': ('Get ready...', 'استعدوا...'),
    'place': ('Put your fingers on your side now.', 'ضعوا أصابعكم على جهتكم الآن.'),
    'tap': ('TAP!', 'اضغط!'),
    'p1': ('Player 1', 'اللاعب 1'),
    'p2': ('Player 2', 'اللاعب 2'),
    't1': ('Team 1', 'الفريق 1'),
    't2': ('Team 2', 'الفريق 2'),
    'winner': ('{name} wins!', 'فاز {name}!'),
    'score': ('{n1}: {a}   |   {n2}: {b}', '{n1}: {a}   |   {n2}: {b}'),
    'again': ('Play again', 'العب مجددًا'),
    'change': ('Change mode', 'تغيير الوضع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'exit': ('Quit game', 'إنهاء اللعبة'),
    'exit_sure': ('Tap again to quit', 'اضغط مرة أخرى للإنهاء'),
}


class TugArena(Widget):
    """لوحة اللعب: منطقتا فريقين + الحبل. تستدعي on_tap(team) عند كل ضغطة (team: 0 أسفل، 1 أعلى)."""

    def __init__(self, mode, texts, on_tap, **kwargs):
        super().__init__(**kwargs)
        app = App.get_running_app()
        self.mode = mode
        self.on_tap = on_tap
        self.active = False
        self.knot = 0.0                  # -1 = طرف الفريق 1 (أسفل)، +1 = طرف الفريق 2 (أعلى)
        slots = 1 if mode == '1v1' else 2
        self._n = slots * 2              # الترتيب: [خانة 0 فريق 0، خانة 0 فريق 1، خانة 1 ...]
        self._cols, self._rects, self._labels = [], [], []
        with self.canvas:
            for _ in range(self._n):
                self._cols.append(Color(*app.primary_color))
                self._rects.append(RoundedRectangle(radius=[dp(app.radius)]))
            Color(*app.muted_color)
            self._fin_top = Rectangle()
            self._fin_bot = Rectangle()
            Color(*app.text_color)
            self._rope = Rectangle()
            self._knot = Ellipse()
        for i in range(self._n):
            team = i % 2
            lbl = Label(text=texts[team], font_name=app.font,
                        font_size=sp(20) * app.font_scale, bold=True, color=[1, 1, 1, 1],
                        halign='center', valign='middle', size_hint=(None, None))
            lbl.bind(size=lambda inst, v: setattr(inst, 'text_size', v))
            if team == 1:                # الفريق العلوي: النص مقلوب 180° ليقرأه من يجلس قبالتنا
                with lbl.canvas.before:
                    PushMatrix()
                    rot = Rotate(angle=180, origin=lbl.center)
                with lbl.canvas.after:
                    PopMatrix()
                lbl.bind(center=lambda inst, v, r=rot: setattr(r, 'origin', inst.center))
            self._labels.append(lbl)
            self.add_widget(lbl)
        self.bind(pos=self._layout, size=self._layout)
        self._layout()

    # ---------- الهندسة ----------
    def _zones(self):
        """قائمة (فريق، x، y، عرض، ارتفاع) بنفس ترتيب العناصر الرسومية."""
        m, gap = dp(4), dp(8)
        zh = self.height * ZONE
        slots = self._n // 2
        sw = (self.width - gap * (slots - 1)) / slots
        out = []
        for s in range(slots):
            sx = self.x + s * (sw + gap)
            out.append((0, sx, self.y + m, sw, zh - m))
            out.append((1, sx, self.y + self.height - zh, sw, zh - m))
        return out

    def _layout(self, *args):
        for i, (team, zx, zy, zw, zh) in enumerate(self._zones()):
            self._rects[i].pos = (zx, zy)
            self._rects[i].size = (zw, zh)
            self._labels[i].pos = (zx, zy)
            self._labels[i].size = (zw, zh)
        self._place_rope()

    def _place_rope(self):
        cy = self.y + self.height / 2
        half = self.height * (0.5 - ZONE)
        ky = cy + self.knot * half
        self._fin_top.pos = (self.x, cy + half - dp(1))
        self._fin_top.size = (self.width, dp(2))
        self._fin_bot.pos = (self.x, cy - half - dp(1))
        self._fin_bot.size = (self.width, dp(2))
        self._rope.pos = (self.x, ky - dp(3))
        self._rope.size = (self.width, dp(6))
        self._knot.pos = (self.center_x - dp(15), ky - dp(15))
        self._knot.size = (dp(30), dp(30))

    def set_knot(self, value):
        self.knot = value
        self._place_rope()

    # ---------- اللمس ----------
    def hit(self, x, y):
        """يرجع (الفريق، فهرس المنطقة) أو None إن كانت اللمسة في شريط الحبل الأوسط."""
        zh = self.height * ZONE
        if y < self.y + zh:
            team = 0
        elif y > self.y + self.height - zh:
            team = 1
        else:
            return None
        slot = 0 if (self._n == 2 or x < self.center_x) else 1
        return team, slot * 2 + team

    def on_touch_down(self, touch):
        if not self.active or not self.collide_point(*touch.pos):
            return False
        res = self.hit(touch.x, touch.y)
        if res is None:
            return True
        team, idx = res
        self._cols[idx].a = 0.6
        Clock.schedule_once(lambda dt, i=idx: setattr(self._cols[i], 'a', 1), 0.07)
        self.on_tap(team)
        return True


class TugMixin:
    def tug_init(self):
        self.tug_mode = '1v1'
        self.tug_pos = 0.0
        self.tug_n = 0
        self.tug_score = [0, 0]
        self.tug_winner = 0
        self.tug_cd = 3
        self.tug_live = False
        self.tug_ev = None
        self._tug_fin_ev = None
        self._tug_exit_ev = None
        self._tug_armed = False
        self._tug_cd_lbl = None
        self._tug_back = None
        self.tug_arena = None

    def tug_stop(self):
        for name in ('tug_ev', '_tug_fin_ev', '_tug_exit_ev'):
            ev = getattr(self, name, None)
            if ev is not None:
                try:
                    ev.cancel()
                except Exception:
                    pass
            setattr(self, name, None)
        self.tug_live = False
        self._tug_armed = False
        arena = getattr(self, 'tug_arena', None)
        if arena is not None:
            arena.active = False

    # ---------- مساعدات ----------
    def tug_t(self, key, fs=16, pad=60, **fmt):
        en, ar = TG[key]
        return self.pair(en, ar, fs, pad, **fmt)

    def tug_raw(self, team):
        """اسم الفريق/اللاعب غير مُشكَّل (يُشكَّل لاحقًا داخل الجملة)."""
        en, ar = TG[('p' if self.tug_mode == '1v1' else 't') + str(team + 1)]
        return ar if self.is_ar() else en

    def tug_scoreline(self, fs=18):
        return self.tug_t('score', fs, 60, n1=self.tug_raw(0), a=self.tug_score[0],
                          n2=self.tug_raw(1), b=self.tug_score[1])

    # ---------- الإعداد ----------
    def show_tug_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tug_t('head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.tug_t('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.tug_t('tip', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.tug_t('pick', 18), fs=18, bold=True))
        box.add_widget(self.button(self.tug_t('m11', 17, 100), lambda: self.tug_begin('1v1')))
        box.add_widget(self.label(self.tug_t('m11_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.tug_t('m22', 17, 100), lambda: self.tug_begin('2v2')))
        box.add_widget(self.label(self.tug_t('m22_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.tug_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))

    def tug_begin(self, mode):
        self.tug_mode = mode
        self.tug_score = [0, 0]
        self.tug_again()

    def tug_again(self):
        self.tug_pos = 0.0
        self.tug_n = 0
        self.tug_cd = 3
        self.go('tug_count')

    # ---------- العد التنازلي ----------
    def show_tug_count(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tug_t('ready', 20), fs=20, bold=True,
                                  color=app.primary_color))
        lbl = self.label(str(self.tug_cd), fs=72, bold=True)
        box.add_widget(lbl)
        self._tug_cd_lbl = lbl
        box.add_widget(self.label(self.tug_t('place', 14), fs=14, color=app.muted_color))
        self.tug_ev = Clock.schedule_interval(self.tug_count_tick, 1.0)

    def tug_count_tick(self, dt):
        self.tug_cd -= 1
        if self.tug_cd <= 0:
            self.tug_stop()
            self.go('tug_play')
            return False
        if self._tug_cd_lbl is not None:
            self._tug_cd_lbl.text = str(self.tug_cd)
        return True

    # ---------- اللعب ----------
    def _tug_height(self):
        app = App.get_running_app()
        try:
            sh = self.ids.scroll.height
        except Exception:
            sh = 0
        if sh < dp(300):
            sh = Window.height - dp(190)
        back_h = max(dp(app.btn_height), dp(48))
        return max(dp(300), sh - dp(8) - dp(10) - back_h - dp(6))

    def show_tug_play(self, box):
        texts = {}
        for team in (0, 1):
            texts[team] = (self.shape(self.tug_raw(team), 20, 60) + '\n'
                           + self.tug_t('tap', 22, 60))
        arena = TugArena(self.tug_mode, texts, self.tug_tap, size_hint_y=None,
                         height=self._tug_height())
        arena.set_knot(self.tug_pos)
        arena.active = True
        self.tug_arena = arena
        self.tug_live = True
        box.add_widget(arena)
        back = self.button(self.tug_t('exit', 15, 100), self.tug_exit, gray=True)
        self._tug_back = back
        box.add_widget(back)

    def tug_tap(self, team):
        if not self.tug_live:
            return
        need = NEED.get(self.tug_mode, 30)
        self.tug_n += 1 if team == 1 else -1          # عدّاد صحيح لتفادي أخطاء الأعداد العشرية
        self.tug_n = max(-need, min(need, self.tug_n))
        self.tug_pos = self.tug_n / need
        if self.tug_arena is not None:
            self.tug_arena.set_knot(self.tug_pos)
        if abs(self.tug_n) >= need:
            self.tug_live = False
            if self.tug_arena is not None:
                self.tug_arena.active = False
            winner = 1 if self.tug_pos > 0 else 0
            self._tug_fin_ev = Clock.schedule_once(lambda dt: self.tug_finish(winner), 0.4)

    def tug_finish(self, winner):
        self.tug_score[winner] += 1
        self.tug_winner = winner
        self.go('tug_end')

    def tug_exit(self):
        """ضغطتان للخروج، كي لا يحدث بالخطأ أثناء الضغط السريع."""
        if self._tug_armed:
            self.tug_stop()
            self.go('tug_setup')
            return
        self._tug_armed = True
        if self._tug_back is not None:
            self._tug_back.text = self.tug_t('exit_sure', 15, 100)
        self._tug_exit_ev = Clock.schedule_once(self._tug_disarm, 2.0)

    def _tug_disarm(self, dt):
        self._tug_armed = False
        self._tug_exit_ev = None
        if self._tug_back is not None:
            self._tug_back.text = self.tug_t('exit', 15, 100)

    # ---------- النتيجة ----------
    def show_tug_end(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.tug_t('winner', 28, 60, name=self.tug_raw(self.tug_winner)),
                                  fs=28, bold=True, color=app.primary_color))
        box.add_widget(self.label(self.tug_scoreline(20), fs=20, bold=True))
        box.add_widget(self.button(self.tug_t('again', 16, 100), self.tug_again))
        box.add_widget(self.button(self.tug_t('change', 15, 100), lambda: self.go('tug_setup'),
                                   gray=True))
        box.add_widget(self.button(self.tug_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))
