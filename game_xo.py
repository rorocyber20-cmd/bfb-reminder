"""لعبة «إكس أو» (X-O): لاعبان على نفس الهاتف، أو ضد الهاتف بمستوى صعب.
لوحتان: 3x3 (كوّن 3 في صف؛ الهاتف لا يُهزم) و6x6 (كوّن 5 في صف؛ الهاتف قوي جدًا)."""
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

GREEN = [0.15, 0.62, 0.30, 1]
BLUE = [0.20, 0.55, 0.85, 1]
EMPTY = [0.30, 0.31, 0.38, 1]
WIN_LEN = {3: 3, 6: 5}                 # حجم اللوحة -> عدد العلامات المطلوب للفوز

XT = {
    'head': ('X-O', 'إكس أو'),
    'rules': ('Take turns placing X and O. The first to complete a line (row, column or '
              'diagonal) wins. Choose a mode, then the board size.',
              'تناوبوا على وضع X وO. أول من يكمّل خطًا (صفًا أو عمودًا أو قطرًا) يفوز. '
              'اختر الوضع ثم حجم اللوحة.'),
    'pick': ('Choose a mode', 'اختر الوضع'),
    'cpu': ('Vs phone (hard)', 'ضد الهاتف (صعب)'),
    'cpu_d': ('Play against the phone at hard level.', 'العب ضد الهاتف بمستوى صعب.'),
    'two': ('Two players', 'لاعبان'),
    'two_d': ('Two players on the same phone.', 'لاعبان على نفس الهاتف.'),
    'size_head': ('Choose the board size', 'اختر حجم اللوحة'),
    's3': ('3x3 board (classic)', 'لوحة 3x3 (كلاسيكية)'),
    's3_cpu': ('Get 3 in a row. The phone never loses. Can you force a draw?',
               'كوّن 3 في صف. الهاتف لا يخطئ. هل تستطيع التعادل معه؟'),
    's3_two': ('Get 3 in a row.', 'كوّن 3 في صف.'),
    's6': ('6x6 board (big)', 'لوحة 6x6 (كبيرة)'),
    's6_cpu': ('Get 5 in a row. The phone is very strong, but it can be beaten.',
               'كوّن 5 في صف. الهاتف قوي جدًا، لكن يمكن الفوز عليه.'),
    's6_two': ('Get 5 in a row.', 'كوّن 5 في صف.'),
    'back': ('Back', 'رجوع'),
    'info': ('{n}x{n} board: {k} in a row', 'لوحة {n}x{n}: {k} في صف'),
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

# ---------------------------------------------------------------
# منطق اللعبة (بدون واجهة، قابل للاختبار)
# ---------------------------------------------------------------
_LINES = {}


def lines_for(n, k):
    """كل الخطوط الممكنة للفوز: k خانات متتالية (صف/عمود/قطر) في لوحة n×n."""
    key = (n, k)
    if key not in _LINES:
        out = []
        for r in range(n):
            for c in range(n):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    er, ec = r + dr * (k - 1), c + dc * (k - 1)
                    if 0 <= er < n and 0 <= ec < n:
                        out.append(tuple((r + dr * i) * n + (c + dc * i) for i in range(k)))
        _LINES[key] = tuple(out)
    return _LINES[key]


def winner_line(board, n=3, k=3):
    """يرجع (العلامة الفائزة، الخط) أو (None, None)."""
    for ln in lines_for(n, k):
        first = board[ln[0]]
        if first and all(board[i] == first for i in ln):
            return first, ln
    return None, None


def is_full(board):
    return all(board)


def _minimax(board, turn, cpu, human, depth):
    """بحث كامل للوحة 3x3."""
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


def best_move_3(board, cpu='O', human='X'):
    """أفضل خانة في 3x3 (بحث كامل: لا يخسر أبدًا). عند تساوي الخيارات يختار عشوائيًا للتنويع."""
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


# ---- اللوحة الكبيرة 6x6 (5 في صف): بحث ألفا-بيتا محدود العمق مع تقييم للخطوط ----
_WEIGHTS = {3: [0, 1, 10], 4: [0, 1, 10, 120], 5: [0, 1, 8, 60, 500]}   # قيمة الخط بحسب عدد علاماتك فيه
_WIN = 1000000


def _static(board, lines, cpu, human):
    """يرجع (قيمة اللوحة للهاتف، من أكمل خطًا: cpu / human / None)."""
    score = 0
    weight = _WEIGHTS[len(lines[0])]
    for ln in lines:
        c = h = 0
        for i in ln:
            v = board[i]
            if v == cpu:
                c += 1
            elif v == human:
                h += 1
        if c and h:
            continue
        if c:
            if c == len(ln):
                return _WIN, 'cpu'
            score += weight[c]
        elif h:
            if h == len(ln):
                return -_WIN, 'human'
            score -= weight[h] * 1.15       # الدفاع أهم قليلًا
    return score, None


def _candidates(board, n):
    """الخانات الفارغة المجاورة لأي علامة (أو وسط اللوحة إن كانت فارغة)."""
    out = set()
    any_mark = False
    for i, v in enumerate(board):
        if not v:
            continue
        any_mark = True
        r, c = divmod(i, n)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < n and 0 <= cc < n and not board[rr * n + cc]:
                    out.add(rr * n + cc)
    if not any_mark:
        mid = n // 2
        return [(mid - 1) * n + mid - 1, (mid - 1) * n + mid, mid * n + mid - 1, mid * n + mid]
    return sorted(out)


def _search(board, n, lines, turn, cpu, human, depth, alpha, beta, width):
    sc, term = _static(board, lines, cpu, human)
    if term == 'cpu':
        return _WIN + depth
    if term == 'human':
        return -_WIN - depth
    cands = _candidates(board, n)
    if depth == 0 or not cands:
        return sc
    nxt = human if turn == cpu else cpu
    maximizing = turn == cpu
    # ترتيب النقلات بتقييم سريع واختيار أفضل width فقط
    scored = []
    for m in cands:
        board[m] = turn
        s, t = _static(board, lines, cpu, human)
        board[m] = ''
        scored.append((s if maximizing else -s, m))
    scored.sort(reverse=True)
    best = None
    for _, m in scored[:width]:
        board[m] = turn
        v = _search(board, n, lines, nxt, cpu, human, depth - 1, alpha, beta, width)
        board[m] = ''
        if best is None or (maximizing and v > best) or (not maximizing and v < best):
            best = v
        if maximizing:
            alpha = max(alpha, best)
        else:
            beta = min(beta, best)
        if alpha >= beta:
            break
    return best


def best_move_big(board, n, k, cpu='O', human='X', depth=4, width=6):
    b = list(board)
    lines = lines_for(n, k)
    empties = [i for i, v in enumerate(b) if not v]
    if not empties:
        return None
    if len(empties) == len(b):                         # أول نقلة: خانة من الوسط
        return random.choice(_candidates(b, n))
    # 1) فوز فوري، 2) منع فوز فوري للخصم
    for who in (cpu, human):
        for m in empties:
            b[m] = who
            w, _ = winner_line(b, n, k)
            b[m] = ''
            if w == who:
                return m
    # 3) بحث
    cands = _candidates(b, n)
    scored = []
    for m in cands:
        b[m] = cpu
        s, _ = _static(b, lines, cpu, human)
        b[m] = ''
        scored.append((s, m))
    scored.sort(reverse=True)
    top = scored[:max(width + 2, 8)]
    best_v, best_ms = None, []
    for _, m in top:
        b[m] = cpu
        v = _search(b, n, lines, human, cpu, human, depth - 1, -10 * _WIN, 10 * _WIN, width)
        b[m] = ''
        if best_v is None or v > best_v:
            best_v, best_ms = v, [m]
        elif v == best_v:
            best_ms.append(m)
    return random.choice(best_ms)


def best_move(board, cpu='O', human='X', n=3, k=3):
    if n == 3:
        return best_move_3(board, cpu, human)
    return best_move_big(board, n, k, cpu, human)


# ---------------------------------------------------------------
# الواجهة
# ---------------------------------------------------------------
class XOMixin:
    def xo_init(self):
        self.xo_mode = 'cpu'
        self.xo_n = 3
        self.xo_k = 3
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

    # ---------- الإعداد: الوضع ثم حجم اللوحة ----------
    def show_xo_setup(self, box):
        app = App.get_running_app()
        box.add_widget(self.label(self.xo_t('head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.xo_t('rules', 14), fs=14, color=app.muted_color))
        box.add_widget(self.label(self.xo_t('pick', 18), fs=18, bold=True))
        box.add_widget(self.button(self.xo_t('cpu', 17, 100), lambda: self.xo_pick_mode('cpu')))
        box.add_widget(self.label(self.xo_t('cpu_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('two', 17, 100), lambda: self.xo_pick_mode('two')))
        box.add_widget(self.label(self.xo_t('two_d', 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('menu', 15, 100), lambda: self.go('menu'),
                                   gray=True))

    def xo_pick_mode(self, mode):
        self.xo_mode = mode
        self.go('xo_size')

    def show_xo_size(self, box):
        app = App.get_running_app()
        sfx = 'cpu' if self.xo_mode == 'cpu' else 'two'
        box.add_widget(self.label(self.xo_t('head', 22), fs=22, bold=True,
                                  color=app.primary_color))
        box.add_widget(self.label(self.xo_t('size_head', 18), fs=18, bold=True))
        box.add_widget(self.button(self.xo_t('s3', 17, 100), lambda: self.xo_begin(3)))
        box.add_widget(self.label(self.xo_t('s3_' + sfx, 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('s6', 17, 100), lambda: self.xo_begin(6)))
        box.add_widget(self.label(self.xo_t('s6_' + sfx, 13), fs=13, color=app.muted_color))
        box.add_widget(self.button(self.xo_t('back', 15, 100), lambda: self.go('xo_setup'),
                                   gray=True))

    def xo_begin(self, size):
        self.xo_n = size
        self.xo_k = WIN_LEN[size]
        self.xo_score = [0, 0, 0]
        self.xo_first = 'X'
        self.xo_reset()

    def xo_reset(self):
        self.xo_board = [''] * (self.xo_n * self.xo_n)
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
        n = self.xo_n
        key = 'score_cpu' if self.xo_mode == 'cpu' else 'score_two'
        line = self.xo_t(key, 18, 60, a=self.xo_score[0], b=self.xo_score[1], c=self.xo_score[2])
        box.add_widget(self.label(line, fs=16, bold=True))
        box.add_widget(self.label(self.xo_t('info', 13, 60, n=n, k=self.xo_k), fs=13,
                                  color=app.muted_color))
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
        gap = dp(6) if n == 3 else dp(4)
        cap = dp(110) if n == 3 else dp(62)
        cell = min((Window.width - dp(48) - (n - 1) * gap) / n, cap)
        side = cell * n + gap * (n - 1)
        grid = GridLayout(cols=n, spacing=gap, size_hint=(None, None), size=(side, side),
                          row_default_height=cell, row_force_default=True,
                          col_default_width=cell, col_force_default=True)
        fsize = 46 if n == 3 else 26
        for i in range(n * n):
            mark = self.xo_board[i]
            btn = Factory.StyledButton(text=mark)
            btn.font_size = sp(fsize) * app.font_scale
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
        w, ln = winner_line(self.xo_board, self.xo_n, self.xo_k)
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
        i = best_move(self.xo_board, 'O', 'X', self.xo_n, self.xo_k)
        if i is not None:
            self.xo_place(i)
