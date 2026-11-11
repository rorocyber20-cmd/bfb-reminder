"""لعبة «إكس أو» (X-O): لاعبان على نفس الهاتف، أو ضد الهاتف بمستوى صعب لا يُهزم (أفضل ما تحققه ضده التعادل).
أول من يضع 3 علامات في صف أو عمود أو قطر يفوز."""
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout

try:
    from fx import play as fx_play, buzz as fx_buzz
except Exception:                      # الصوت اختياري: لا يجب أن يكسر اللعبة
    def fx_play(*a, **k):
        pass

    def fx_buzz(*a, **k):
        pass

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
GREEN = [0.15, 0.62, 0.30, 1]
BLUE = [0.20, 0.55, 0.85, 1]
EMPTY = [0.30, 0.31, 0.38, 1]

XT = {
    'head': ('X-O', 'إكس أو'),
    'rules': ('Take turns placing X and O. The first to get 3 in a row, column or diagonal wins.',
              'تناوبوا على وضع X وO. أول من يكمّل 3 في صف أو عمود أو قطر يفوز.'),
    'pick': ('Choose a mode', 'اختر الوضع'),
    'cpu': ('Vs phone (hard)', 'ضد الهاتف (صعب)'),
    'cpu_d': ('The phone never loses. Can you force a draw?',
              'الهاتف لا يخطئ. هل تستطيع التعادل معه؟'),
    'two': ('Two players', 'لاعبان'),
    'two_d': ('Two players on the same phone.', 'لاعبان على نفس الهاتف.'),
    'your': ('Your turn (X)', 'دورك (X)'),
    'think': ('The phone is thinking...', 'الهاتف يفكّر...'),
    'turn': ('Turn: {m}', 'الدور: {m}'),
    'you_win': ('You win!', 'فزت!'),
    'cpu_win': ('The phone wins!', 'فاز الهاتف!'),
    'win': ('{m} wins!', 'فاز {m}!'),
    'draw': ("It's a draw!", 'تعادل!'),
    'score_cpu': ('You: {a}   |   Phone: {b}   |   Draws: {c}',
                  'أنت: {a}   |   الهاتف: {b}   |   تعادل: {c}'),
    'score_two': ('X: {a}   |   O: {b}   |   Draws: {c}', 'X: {a}   |   O: {b}   |   تعادل: {c}'),
    'again': ('Play again', 'العب مجددًا'),
    'change': ('Change mode', 'تغيير الوضع'),
    'menu': ('Back to games', 'العودة إلى الألعاب'),
    'quit': ('Quit game', 'إنهاء اللعبة'),
}


def winner_line(board):
    """يرجع (العلامة الفائزة، الخط) أو (None, None)."""
    for ln in LINES:
        a, b, c = ln
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], ln
    return None, None


def is_full(board):
    return all(board)


def _minimax(board, turn, cpu, human, depth):
    w, _ = winner_line(board)
    if w == cpu:
        return 10 - depth
    if w == human:
        return depth - 10
    if is_full(board):
        return 0
    nxt = human if turn == cpu else cpu
    best = None
    for i in range(9):
        if board[i]:
            continue
        board[i] = turn
        sc = _minimax(board, nxt, cpu, human, depth + 1)
        board[i] = ''
        if best is None or (turn == cpu and sc > best) or (turn == human and sc < best):
            best = sc
    return best


def best_move(board, cpu='O', human='X'):
    """أفضل خانة للهاتف (بحث كامل: لا يخسر أبدًا). عند تساوي الخيارات يختار عشوائيًا للتنويع."""
    b = list(board)
    if not any(b):                       # أول نقلة على لوحة فارغة: كلها متساوية، نتجنّب الحساب الطويل
        return random.choice([0, 2, 4, 6, 8])
    scores = {}
    for i in range(9):
        if b[i]:
            continue
        b[i] = cpu
        scores[i] = _minimax(b, human, cpu, human, 1)
        b[i] = ''
    if not scores:
        return None
    top = max(scores.values())
    return random.choice([i for i, v in scores.items() if v == top])


class XOMixin:
    def xo_init(self):
        self.xo_mode = 'cpu'
        self.xo_board = [''] * 9
        self.xo_turn = 'X'
        self.xo_first = 'X'
        self.xo_over = False
        self.xo_res = None            # 'X' أو 'O' أو 'D'
        self.xo_win = ()
        self.xo_score = [0, 0, 0]     # X، O، تعادل
        self._xo_ev = None

    def xo_stop(self):
        ev = getattr(self, '_xo_ev', None)
        if ev is not None:
            try:
                ev.cancel()
            except Exception:
                pass
        self._xo_ev = None

    def xo_t(self, key, fs=16, pad=60, **fmt):
        en, ar = XT[key]
        return self.pair(en, ar, fs, pad, **fmt)

    # ---------- الإعداد ----------
    def show_xo_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.xo_t('head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.xo_t('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.xo_t('pick', 18), fs=18, bold=True))
        box.add_widget(self.button(self.xo_t('cpu', 17, 100), lambda: self.xo_begin('cpu')))
        box.add_widget(self.label(self.xo_t('cpu_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('two', 17, 100), lambda: self.xo_begin('two')))
        box.add_widget(self.label(self.xo_t('two_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))

    def xo_begin(self, mode):
        self.xo_mode = mode
        self.xo_score = [0, 0, 0]
        self.xo_first = 'X'
        self.xo_reset()

    def xo_reset(self):
        self.xo_board = [''] * 9
        self.xo_turn = self.xo_first
        self.xo_over = False
        self.xo_res = None
        self.xo_win = ()
        self.go('xo_play')

    def xo_again(self):
        self.xo_first = 'O' if self.xo_first == 'X' else 'X'      # يتناوب من يبدأ
        self.xo_reset()

    # ---------- اللعب ----------
    def _xo_cpu_turn(self):
        return self.xo_mode == 'cpu' and self.xo_turn == 'O' and not self.xo_over

    def show_xo_play(self, box):
        app = App.get_running_app()
        if self.xo_mode == 'cpu':
            line = self.xo_t('score_cpu', 18, 60, a=self.xo_score[0], b=self.xo_score[1],
                             c=self.xo_score[2])
        else:
            line = self.xo_t('score_two', 18, 60, a=self.xo_score[0], b=self.xo_score[1],
                             c=self.xo_score[2])
        box.add_widget(self.label(line, fs=16, bold=True))
        # سطر الحالة
        if self.xo_over:
            if self.xo_res == 'D':
                txt, col = self.xo_t('draw', 24, 60), app.primary_color
            elif self.xo_mode == 'cpu':
                human = self.xo_res == 'X'
                txt = self.xo_t('you_win' if human else 'cpu_win', 24, 60)
                col = GREEN if human else app.primary_color
            else:
                txt, col = self.xo_t('win', 24, 60, m=self.xo_res), GREEN
            box.add_widget(self.label(txt, fs=24, bold=True, color=col))
        else:
            if self.xo_mode == 'cpu':
                txt = self.xo_t('think' if self.xo_turn == 'O' else 'your', 18, 60)
            else:
                txt = self.xo_t('turn', 18, 60, m=self.xo_turn)
            box.add_widget(self.label(txt, fs=18, bold=True, color=app.muted_color))
        # اللوحة
        gap = dp(6)
        cell = min((Window.width - dp(48) - 2 * gap) / 3, dp(110))
        side = cell * 3 + gap * 2
        grid = GridLayout(cols=3, spacing=gap, size_hint=(None, None), size=(side, side),
                          row_default_height=cell, row_force_default=True,
                          col_default_width=cell, col_force_default=True)
        for i in range(9):
            mark = self.xo_board[i]
            btn = Factory.StyledButton(text=mark)
            btn.font_size = sp(46) * app.font_scale
            btn.bold = True
            if i in self.xo_win:
                btn.custom_bg = GREEN
            elif mark == 'X':
                btn.custom_bg = app.primary_color
            elif mark == 'O':
                btn.custom_bg = BLUE
            else:
                btn.custom_bg = EMPTY
            btn.bind(on_release=lambda b, k=i: self.xo_tap(k))
            grid.add_widget(btn)
        holder = AnchorLayout(size_hint_y=None, height=side + dp(8))
        holder.add_widget(grid)
        box.add_widget(holder)
        if self.xo_over:
            box.add_widget(self.button(self.xo_t('again', 16, 100), self.xo_again))
            box.add_widget(self.button(self.xo_t('change', 15, 100),
                                       lambda: self.go('xo_setup'), gray=True))
            box.add_widget(self.button(self.xo_t('menu', 15, 100), lambda: self.go('menu'),
                                       gray=True))
        else:
            box.add_widget(self.button(self.xo_t('quit', 15, 100), lambda: self.go('xo_setup'),
                                       gray=True))
        # دور الهاتف: يُجدَّد هنا لأن كل إعادة رسم تلغي المؤقتات
        if self._xo_cpu_turn():
            self._xo_ev = Clock.schedule_once(self.xo_cpu_move, 0.6)

    def xo_tap(self, i):
        if self.xo_over or self.xo_board[i] or self._xo_cpu_turn() or self._xo_ev is not None:
            return
        self.xo_place(i)

    def xo_place(self, i):
        mark = self.xo_turn
        self.xo_board[i] = mark
        w, ln = winner_line(self.xo_board)
        if w:
            self.xo_over, self.xo_res, self.xo_win = True, w, ln
            self.xo_score[0 if w == 'X' else 1] += 1
            if self.xo_mode == 'cpu' and w == 'O':
                fx_play('end')
                fx_buzz(250)
            else:
                fx_play('win')
                fx_buzz(150)
        elif is_full(self.xo_board):
            self.xo_over, self.xo_res = True, 'D'
            self.xo_score[2] += 1
            fx_play('skip')
        else:
            self.xo_turn = 'O' if mark == 'X' else 'X'
            fx_play('tap', 0.6)
        self.render()

    def xo_cpu_move(self, dt):
        self._xo_ev = None
        if not self._xo_cpu_turn():
            return
        i = best_move(self.xo_board, 'O', 'X')
        if i is not None:
            self.xo_place(i)
