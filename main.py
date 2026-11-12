import os
import traceback

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.stencilview import StencilView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import platform
from datetime import date, datetime

IMPORT_ERROR = ''
try:
    import core
except Exception:
    core = None
    IMPORT_ERROR = traceback.format_exc()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = os.path.join(BASE_DIR, 'Cairo-Regular.ttf')

FONT_NAME = 'Roboto'
FONT_ERROR = ''
try:
    if os.path.exists(FONT_FILE):
        LabelBase.register(name='Cairo', fn_regular=FONT_FILE)
        FONT_NAME = 'Cairo'
except Exception:
    FONT_ERROR = traceback.format_exc()


def error_screen(text):
    """شاشة تعرض الخطأ بدل إغلاق التطبيق (للتشخيص)."""
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    label = Label(
        text="BFB Reminder - startup error\n\n" + text,
        size_hint_y=None,
        halign='left',
        valign='top',
        font_size='12sp',
        color=(1, 1, 1, 1),
    )
    label.bind(width=lambda inst, w: setattr(inst, 'text_size', (w - 20, None)))
    label.bind(texture_size=lambda inst, s: setattr(inst, 'height', s[1] + 20))
    sv = ScrollView()
    sv.add_widget(label)
    return sv

# تشكيل الحروف العربية وترتيبها (إن توفرت المكتبتان)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display

    # خط Cairo المرفق ينقصه الشكل المنفصل (isolated) للحروف، فنستعمل الحرف الأصلي بدله
    try:
        _reshape = arabic_reshaper.ArabicReshaper(
            configuration={'use_unshaped_instead_of_isolated': True}).reshape
    except Exception:
        _reshape = arabic_reshaper.reshape

    def fix_arabic(text):
        try:
            return get_display(_reshape(text))
        except Exception:
            return text
except Exception:
    def fix_arabic(text):
        return text


THEMES = {
    'light': {
        'bg': [0.94, 0.95, 0.97, 1],
        'card': [1, 1, 1, 1],
        'text': [0.2, 0.2, 0.2, 1],
        'muted': [0.5, 0.5, 0.55, 1],
    },
    'dark': {
        'bg': [0.08, 0.09, 0.11, 1],
        'card': [0.14, 0.15, 0.18, 1],
        'text': [0.92, 0.92, 0.95, 1],
        'muted': [0.55, 0.57, 0.62, 1],
    },
}

ACCENTS = {
    'blue': [0.10, 0.50, 0.80, 1],
    'green': [0.18, 0.62, 0.35, 1],
    'purple': [0.55, 0.35, 0.80, 1],
    'red': [0.85, 0.25, 0.30, 1],
    'teal': [0.10, 0.60, 0.60, 1],
    'pink': [0.91, 0.36, 0.62, 1],
}


# ---------------------------------------------------------------
# عناصر الواجهة (شكلها معرّف في ui.kv)
# ---------------------------------------------------------------
class StyledButton(Button):
    custom_bg = ListProperty([])


class NavButton(ToggleButton):
    pass


class CustomTextInput(TextInput):
    """حقل نص يعرض العربية مشكَّلة ومرتبة أثناء الكتابة (النص الحقيقي يبقى كما كتبه المستخدم)."""

    def _create_line_label(self, text, *args, **kwargs):
        hint = kwargs.get('hint', args[0] if args else False)
        try:
            if not hint and text and any('\u0600' <= c <= '\u06FF' for c in text):
                text = fix_arabic(text)
        except Exception:
            pass
        return super()._create_line_label(text, *args, **kwargs)


class LogoBox(StencilView, FloatLayout):
    """يقصّ ما يخرج عن حدوده، فيبدو اللوڨو طالعًا من وراء خانة الاسم."""


class BirthdayRow(BoxLayout):
    bname = StringProperty('')
    bdate = StringProperty('')
    name_text = StringProperty('')
    sub_text = StringProperty('')
    days_text = StringProperty('')
    days_color = ListProperty([0.18, 0.70, 0.40, 1])
    today = BooleanProperty(False)      # عيد ميلاده اليوم: بطاقة مميزة


DAYS_GREEN = [0.18, 0.70, 0.40, 1]
DAYS_ORANGE = [0.95, 0.60, 0.10, 1]
DAYS_RED = [0.90, 0.22, 0.25, 1]


def days_style(days):
    """نص ولون الأيام المتبقية: أخضر للبعيد، برتقالي خلال أسبوع، أحمر اليوم."""
    if days == 0:
        return 'Today!', DAYS_RED
    if days == 1:
        return 'Tomorrow', DAYS_ORANGE
    if days <= 7:
        return f'In {days} days', DAYS_ORANGE
    return f'In {days} days', DAYS_GREEN


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


class DatePopup(Popup):
    """نافذة اختيار التاريخ (يوم/شهر/سنة)، ومعها خانة اسم عند التعديل."""
    show_name = BooleanProperty(False)
    name_text = StringProperty('')
    date_text = StringProperty('')
    save_cb = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        ids = self.ids
        ids.day_sp.values = [str(i) for i in range(1, 32)]
        ids.month_sp.values = MONTHS
        ids.year_sp.values = [str(y) for y in range(date.today().year, 1919, -1)]
        try:
            d = datetime.strptime(self.date_text, '%Y-%m-%d').date()
        except ValueError:
            d = date(2000, 1, 1)
        ids.day_sp.text = str(d.day)
        ids.month_sp.text = MONTHS[d.month - 1]
        ids.year_sp.text = str(d.year)
        if self.show_name:
            ids.name_in.text = self.name_text

    def confirm(self):
        ids = self.ids
        ids.err.text = ''
        name = ''
        if self.show_name:
            name = ids.name_in.text.strip()
            if not name:
                ids.err.text = 'Please enter a name'
                return
        try:
            y = int(ids.year_sp.text)
            m = MONTHS.index(ids.month_sp.text) + 1
            d = int(ids.day_sp.text)
            date_str = date(y, m, d).isoformat()
        except ValueError:
            ids.err.text = 'This date does not exist'
            return
        err = core.check_birth(date_str)
        if err:
            ids.err.text = err
            return
        cb = self.save_cb
        self.dismiss()
        if cb:
            cb(name, date_str)


class ConfirmPopup(Popup):
    """نافذة تأكيد (للحذف)."""
    msg = StringProperty('')
    sub = StringProperty('')
    yes_cb = ObjectProperty(None, allownone=True)

    def yes(self):
        cb = self.yes_cb
        self.dismiss()
        if cb:
            cb()


# ---------------------------------------------------------------
# نافذة المساعدة (زر i): شرح الألعاب والإعدادات ونصائح، بالعربية والإنجليزية
# ---------------------------------------------------------------
HELP_TEXT = {
    'en': {
        'title': 'Help',
        'intro': 'Tap a title to open or close it.',
        'close': 'Close',
        'skip': 'Skip',
        'footer': 'Reopen this window any time with the (i) button.',
        'sections': [
            ('games', 'Games', [
                'No account needed. Pick a category, then a game. Tap the star '
                'on a game to keep it in Favorites at the top.',
                'There are two kinds of games: games played with a CODE (each '
                'friend plays on their own phone) and games played on ONE phone '
                '(everyone plays together on the same device). Each game '
                'explains its own rules on its first screen.',
                'Code games: you send a code to a friend (WhatsApp, SMS...) '
                'and they enter it on their phone. Codes: BFB- is Who knows me '
                'best, BFBR- is its result, BFBL- is Two Truths and a Lie.',
                'A received code works only once, so it cannot be pasted '
                'again to cheat.',
                'One-phone games: pass the phone around or play face to face, '
                'taking turns.',
                'Results of Who knows me best are kept in the Results section.',
            ]),
            ('settings', 'Settings', [
                'Theme and Accent color change how the whole app looks.',
                'Corner roundness, Button height and Text size: adjust them '
                'to your taste.',
                'Export backup copies all your birthdays and settings as one '
                'message (it starts with BFBK-) and opens Share. Send it to '
                'yourself to keep it safe.',
                'Import backup: copy that message first, then press Import. '
                'Birthdays are merged and nothing is deleted.',
                'Test Notification checks that notifications work on your phone.',
                'Reset to defaults restores the look settings only. Your '
                'birthdays stay as they are.',
            ]),
            ('notif', 'Make sure reminders arrive', [
                'Allow notifications: Phone Settings, then Apps, then BFB, then '
                'Notifications. Use Test Notification in Settings to check.',
                'Autostart: turn it ON for BFB (Xiaomi / Redmi / Poco: Settings, '
                'Apps, Manage apps, BFB, Autostart). Without it, reminders stop '
                'after the phone restarts.',
                'Battery: set BFB to No restrictions. On Xiaomi phones also open '
                'Recent apps and lock BFB (pull its card down and tap the lock).',
                'Keep the small permanent notification. It keeps reminders alive. '
                'Do not use Force stop; if you do, open BFB once again.',
                'The reminder arrives at the hour you chose, or up to about 10 '
                'minutes later. Open the app once after installing or updating.',
            ]),
            ('tips', 'Tips', [
                'Reminders arrive 7 days and 1 day before each birthday. In Settings '
                'you can turn each one on or off and choose the time.',
                'On Xiaomi / Redmi phones: allow Autostart for BFB and set '
                'Battery to No restrictions, or reminders may not arrive.',
                'No notifications? Phone Settings, then Apps, then BFB, then '
                'Notifications.',
                'New phone? Export a backup before, and import it after.',
            ]),
        ],
    },
    'ar': {
        'title': 'مساعدة',
        'intro': 'اضغط على العنوان لفتحه أو إغلاقه.',
        'close': 'إغلاق',
        'skip': 'تخطي',
        'footer': 'يمكنك فتح هذه النافذة في أي وقت من زر (i).',
        'sections': [
            ('games', 'الألعاب', [
                'بدون حساب. اختر صنفًا ثم لعبة. اضغط النجمة على اللعبة '
                'لتبقى في المفضلة أعلى القائمة.',
                'الألعاب نوعان: ألعاب تُلعب بالكود (كل صديق على هاتفه) '
                'وألعاب تُلعب على هاتف واحد (الجميع يلعبون معًا على الجهاز '
                'نفسه). كل لعبة تشرح قواعدها في شاشتها الأولى.',
                'ألعاب الكود: ترسل كودًا لصديقك (واتساب، رسائل...) وهو يدخله '
                'في هاتفه. الأكواد: BFB- لعبة من يعرفني أكثر، وBFBR- نتيجتها، '
                'وBFBL- الكذبة والحقيقة.',
                'الكود المستلم يُستعمل مرة واحدة فقط، فلا يمكن لصقه مجددًا '
                'للغش.',
                'ألعاب الهاتف الواحد: مرّروا الهاتف بينكم أو العبوا وجهًا '
                'لوجه بالتناوب.',
                'نتائج من يعرفني أكثر تجدها في قسم النتائج.',
            ]),
            ('settings', 'الإعدادات', [
                'الثيم واللون يغيّران شكل التطبيق كله.',
                'استدارة الزوايا وارتفاع الأزرار وحجم الخط: اضبطها كما '
                'يريحك.',
                'تصدير النسخة الاحتياطية ينسخ كل أعياد الميلاد والإعدادات '
                'في رسالة واحدة تبدأ بـ BFBK- ويفتح المشاركة. أرسلها '
                'لنفسك لتحفظها.',
                'استيراد النسخة: انسخ الرسالة أولًا ثم اضغط استيراد. '
                'تُدمج الأعياد ولا يُحذف شيء.',
                'اختبار الإشعارات يتأكد أن الإشعارات تعمل في هاتفك.',
                'إعادة الضبط تعيد إعدادات المظهر فقط، وأعياد الميلاد '
                'تبقى كما هي.',
            ]),
            ('notif', 'ضمان وصول التذكيرات', [
                'اسمح بالإشعارات: إعدادات الهاتف ثم التطبيقات ثم BFB ثم '
                'الإشعارات. وجرّب زر Test Notification في الإعدادات.',
                'التشغيل التلقائي (Autostart): فعّله للتطبيق (في Xiaomi وRedmi '
                'وPoco: الإعدادات، التطبيقات، إدارة التطبيقات، BFB، التشغيل '
                'التلقائي). بدونه تتوقف التذكيرات بعد إعادة تشغيل الهاتف.',
                'البطارية: اجعل التطبيق على "بدون قيود". وفي هواتف Xiaomi افتح '
                'التطبيقات الأخيرة وثبّت BFB (اسحب بطاقته للأسفل واضغط القفل).',
                'أبقِ الإشعار الدائم الصغير، فهو الذي يُبقي التذكير شغّالًا. '
                'لا تستعمل "إيقاف إجباري"، وإذا فعلت فافتح BFB مرة أخرى.',
                'يصل التذكير في الساعة التي اخترتها أو بعدها بنحو 10 دقائق '
                'كحد أقصى. افتح التطبيق مرة واحدة بعد التثبيت أو التحديث.',
            ]),
            ('tips', 'نصائح', [
                'تصلك التذكيرات قبل أسبوع وقبل يوم من كل عيد ميلاد. ومن الإعدادات '
                'يمكنك تشغيل أو إيقاف كل واحد واختيار الساعة.',
                'في هواتف Xiaomi وRedmi: فعّل التشغيل التلقائي (Autostart) '
                'للتطبيق واجعل البطارية بدون قيود، وإلا قد لا تصل '
                'التذكيرات.',
                'لا تظهر الإشعارات؟ إعدادات الهاتف ثم التطبيقات ثم BFB '
                'ثم الإشعارات.',
                'هاتف جديد؟ صدّر نسخة احتياطية قبل التغيير واستوردها بعده.',
            ]),
        ],
    },
}


def wrap_shaped(text, max_w, measure):
    """يقسّم نصًا عربيًا إلى أسطر تتّسع للعرض، ثم يشكّل كل سطر وحده،
    لأن تشكيل الفقرة كلها ثم تركها تلتفّ يقلب ترتيب الأسطر. يرجع قائمة أسطر."""
    lines, cur = [], ''
    for word in text.split():
        trial = (cur + ' ' + word).strip()
        if cur and measure(fix_arabic(trial)) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return [fix_arabic(line) for line in lines]


class HelpPopup(Popup):
    first_run = BooleanProperty(False)
    lang = StringProperty('ar')
    lang_btn_text = StringProperty('EN')
    close_text = StringProperty('Close')
    dismiss_cb = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.open_keys = set()
        self.bind(on_dismiss=self._dismissed)
        self.rebuild()

    def _dismissed(self, *args):
        cb = self.dismiss_cb
        if cb:
            cb()

    def toggle_lang(self):
        self.lang = 'en' if self.lang == 'ar' else 'ar'
        self.rebuild()

    def toggle_section(self, key):
        if key in self.open_keys:
            self.open_keys.discard(key)
        else:
            self.open_keys.add(key)
        self.rebuild()

    @staticmethod
    def _measurer(font_name, font_px):
        try:
            core_label = CoreLabel(font_name=font_name, font_size=font_px)
            core_label.get_extents('test')
            return lambda s: core_label.get_extents(s)[0]
        except Exception:
            return lambda s: len(s) * font_px * 0.6

    def _label(self, app, text, halign, color, size):
        lbl = Label(
            text=text,
            font_name=app.font,
            font_size=sp(size) * app.font_scale,
            color=list(color),
            size_hint_y=None,
            halign=halign,
            valign='top',
        )
        lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
        lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + dp(6)))
        return lbl

    def _header(self, app, key, title, opened, ar, halign):
        mark = '-' if opened else '+'
        text = (fix_arabic(title) + '   ' + mark) if ar else (mark + '   ' + title)
        btn = StyledButton(
            text=text,
            custom_bg=list(app.card_color),
            color=list(app.text_color),
            size_hint_y=None,
            height=dp(46),
            halign=halign,
            valign='middle',
            padding_x=dp(14),
        )
        btn.bind(size=lambda i, s: setattr(i, 'text_size', (s[0] - dp(28), s[1])))
        btn.bind(on_release=lambda *a: self.toggle_section(key))
        return btn

    def rebuild(self):
        app = App.get_running_app()
        ar = self.lang == 'ar'
        data = HELP_TEXT[self.lang]
        halign = 'right' if ar else 'left'

        def shape(s):
            return fix_arabic(s) if ar else s

        self.title = shape(data['title'])
        self.lang_btn_text = 'EN' if ar else 'AR'
        self.close_text = shape(data['skip'] if self.first_run else data['close'])

        font_px = sp(14) * app.font_scale
        max_w = Window.width * 0.94 - dp(36)
        measure = self._measurer(app.font, font_px)

        def plain(text):
            if not ar:
                return text
            return '\n'.join(wrap_shaped(text, max_w, measure))

        def bullets(items):
            out = []
            for item in items:
                if ar:
                    lines = wrap_shaped(item, max_w - dp(16), measure)
                    lines[0] = lines[0] + '  -'
                    out.append('\n'.join(lines))
                else:
                    out.append('- ' + item)
            return '\n\n'.join(out)

        box = self.ids.content
        box.clear_widgets()
        box.add_widget(self._label(app, plain(data['intro']), halign, app.muted_color, 13))
        for key, title, items in data['sections']:
            opened = key in self.open_keys
            box.add_widget(self._header(app, key, title, opened, ar, halign))
            if opened:
                box.add_widget(self._label(app, bullets(items), halign, app.text_color, 14))
        box.add_widget(self._label(app, plain(data['footer']), halign, app.muted_color, 12))


try:
    from gift_ui import GiftScreen, GiftCard
except Exception:
    GIFT_ERROR = traceback.format_exc()
    if core is not None:
        core.log(GIFT_ERROR)
    from kivy.uix.label import Label as _Label

    class GiftCard(BoxLayout):
        pass

    class GiftScreen(Screen):
        title_text = StringProperty('Gift tab failed to load')
        lang_label = StringProperty('')

        def toggle_lang(self):
            pass

        def on_kv_post(self, base_widget):
            Clock.schedule_once(self._show_error, 0.3)

        def _show_error(self, dt):
            lbl = _Label(text=GIFT_ERROR, font_size='11sp', size_hint_y=None,
                         halign='left', valign='top')
            lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
            lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + 20))
            self.ids.content.add_widget(lbl)


try:
    from games_ui import GamesScreen
except Exception:
    GAMES_ERROR = traceback.format_exc()
    if core is not None:
        core.log(GAMES_ERROR)
    from kivy.uix.label import Label as _GLabel

    class GamesScreen(Screen):
        title_text = StringProperty('Games tab failed to load')
        lang_label = StringProperty('')

        def toggle_lang(self):
            pass

        def on_kv_post(self, base_widget):
            Clock.schedule_once(self._show_error, 0.3)

        def _show_error(self, dt):
            lbl = _GLabel(text=GAMES_ERROR, font_size='11sp', size_hint_y=None,
                          halign='left', valign='top')
            lbl.bind(width=lambda i, w: setattr(i, 'text_size', (w, None)))
            lbl.bind(texture_size=lambda i, s: setattr(i, 'height', s[1] + 20))
            self.ids.content.add_widget(lbl)


class SettingsScreen(Screen):
    pass


class BirthdaysScreen(Screen):
    birth_str = StringProperty('')
    rise = NumericProperty(0)  # 0 = اللوڨو مخبّأ، 1 = ظاهر
    _confetti_shown = False    # يظهر التأثير الاحتفالي مرة واحدة في كل تشغيل للتطبيق
    _confetti_ev = None
    _confetti_group = None

    def on_kv_post(self, base_widget):
        Clock.schedule_once(self.refresh_list, 0.2)
        self.queue_intro()

    def on_pre_enter(self, *args):
        self.refresh_list()
        self.queue_intro()

    def on_leave(self, *args):
        self.stop_confetti()

    def queue_intro(self):
        Clock.unschedule(self.play_intro)
        self.rise = 0
        Clock.schedule_once(self.play_intro, 0.15)

    def play_intro(self, *args):
        Animation.cancel_all(self, 'rise')
        self.rise = 0
        Animation(rise=1, duration=0.9, t='out_back').start(self)

    def refresh_list(self, *args):
        # قد يُستدعى أثناء بناء الشاشة قبل أن تكتمل عناصرها
        if 'list_layout' not in self.ids:
            Clock.schedule_once(self.refresh_list, 0.2)
            return
        layout = self.ids.list_layout
        layout.clear_widgets()

        rows = []
        for item in core.load_birthdays():
            try:
                rows.append((core.days_until(item['date']),
                             core.next_age(item['date']),
                             item['name'], item['date']))
            except Exception:
                continue

        rows.sort(key=lambda r: r[0])
        today_names = [r[2] for r in rows if r[0] == 0]
        if today_names:
            try:
                names = ', '.join(fix_arabic(n) for n in today_names)
                layout.add_widget(Factory.TodayBanner(text='Happy birthday!  ' + names))
            except Exception as e:
                if core:
                    core.log(f"today banner: {e}")
            if not BirthdaysScreen._confetti_shown:
                BirthdaysScreen._confetti_shown = True
                Clock.schedule_once(self.play_confetti, 0.6)
        for days_left, age, name, date_str in rows:
            days_text, days_color = days_style(days_left)
            layout.add_widget(BirthdayRow(
                bname=name,
                bdate=date_str,
                name_text=fix_arabic(name),
                sub_text=f"Turns {age}  |  {date_str}",
                days_text=days_text,
                days_color=days_color,
                today=(days_left == 0),
            ))

    def stop_confetti(self):
        if self._confetti_ev is not None:
            try:
                self._confetti_ev.cancel()
            except Exception:
                pass
            self._confetti_ev = None
        if self._confetti_group is not None:
            try:
                self.canvas.after.remove(self._confetti_group)
            except Exception:
                pass
            self._confetti_group = None

    def play_confetti(self, *args):
        """قصاصات ملونة تتساقط ثلاث ثوانٍ فوق الشاشة ثم تختفي (لا تعترض اللمس)."""
        try:
            import random
            from kivy.graphics import Color, InstructionGroup, Rectangle
            self.stop_confetti()
            w, h = self.width, self.height
            if w < 50 or h < 50:
                return
            group = InstructionGroup()
            parts = []
            for _ in range(48):
                group.add(Color(random.uniform(0.45, 1), random.uniform(0.3, 1),
                                random.uniform(0.3, 1), 1))
                size = dp(random.randint(6, 10))
                x = random.uniform(0, w)
                y = h + random.uniform(0, h * 0.4)
                rect = Rectangle(pos=(self.x + x, self.y + y), size=(size, size * 0.6))
                group.add(rect)
                parts.append([rect, x, y, random.uniform(0.5, 1.1) * h * 0.55,
                              random.uniform(0, 6.28), random.uniform(1.5, 3.5)])
            self.canvas.after.add(group)
            self._confetti_group = group
            state = {'t': 0.0}

            def step(dt):
                import math
                state['t'] += dt
                t = state['t']
                for rect, x, y, speed, ph, freq in parts:
                    rect.pos = (self.x + x + math.sin(t * freq + ph) * dp(18),
                                self.y + y - speed * t)
                if t >= 3.2:
                    self.stop_confetti()
                    return False
                return True

            self._confetti_ev = Clock.schedule_interval(step, 1 / 30.)
        except Exception as e:
            if core:
                core.log(f"confetti: {e}")
            self.stop_confetti()

    def open_date_picker(self):
        DatePopup(
            show_name=False,
            date_text=self.birth_str,
            save_cb=lambda n, d: setattr(self, 'birth_str', d),
        ).open()

    def edit_birthday(self, name, date_str):
        def save(new_name, new_date):
            app = App.get_running_app()
            items = core.load_birthdays()
            for b in items:
                if b['name'] == name and b['date'] == date_str:
                    b['name'] = new_name
                    b['date'] = new_date
                    break
            try:
                core.save_birthdays(items)
            except Exception as e:
                app.show_status(f"Save error: {e}")
                return
            self.refresh_list()
            app.show_status(core.check_and_notify())

        DatePopup(show_name=True, name_text=name, date_text=date_str,
                  save_cb=save).open()

    def add_birthday(self):
        app = App.get_running_app()
        name = self.ids.name_input.text.strip()
        date_str = self.birth_str.strip()

        if not name or not date_str:
            app.show_status("Please enter a name and pick a date")
            return

        err = core.check_birth(date_str)
        if err:
            app.show_status(err)
            return

        items = core.load_birthdays()
        items.append({'name': name, 'date': date_str})
        try:
            core.save_birthdays(items)
        except Exception as e:
            app.show_status(f"Save error: {e}")
            return

        self.ids.name_input.text = ""
        self.birth_str = ""
        self.refresh_list()
        # فحص فوري (مثلًا لو كان الموعد بعد 7 أيام أو يوم)
        app.show_status(core.check_and_notify())


# ---------------------------------------------------------------
# التطبيق
# ---------------------------------------------------------------
class BFBApp(App):
    ACCENTS = ACCENTS

    font = StringProperty(FONT_NAME)
    bg_color = ListProperty(THEMES['light']['bg'])
    card_color = ListProperty(THEMES['light']['card'])
    text_color = ListProperty(THEMES['light']['text'])
    muted_color = ListProperty(THEMES['light']['muted'])
    primary_color = ListProperty(ACCENTS['blue'])
    radius = NumericProperty(10)
    btn_height = NumericProperty(50)
    font_scale = NumericProperty(1.0)
    notify_week = NumericProperty(1)
    notify_day = NumericProperty(1)
    notify_hour = NumericProperty(9)
    status = StringProperty('')
    status_color = ListProperty([0.85, 0.2, 0.2, 1])
    sound_on = BooleanProperty(True)
    vibrate_on = BooleanProperty(True)

    def build(self):
        self.build_failed = False
        if core is None:
            self.build_failed = True
            return error_screen(IMPORT_ERROR)
        try:
            Window.softinput_mode = 'below_target'
            self.prefs = core.load_settings()
            self.apply_prefs()
            self._sync_fx()
            kv_path = os.path.join(BASE_DIR, 'ui.kv')
            if not os.path.exists(kv_path):
                files = ', '.join(sorted(os.listdir(BASE_DIR)))
                raise FileNotFoundError(f"ui.kv not found in {BASE_DIR}\nFiles: {files}")
            return Builder.load_file(kv_path)
        except Exception:
            self.build_failed = True
            tb = traceback.format_exc()
            try:
                core.log(tb)
            except Exception:
                pass
            return error_screen(tb + ("\nFONT: " + FONT_ERROR if FONT_ERROR else ""))

    # ---------- الإعدادات ----------
    def apply_prefs(self):
        theme = THEMES.get(self.prefs.get('theme'), THEMES['light'])
        self.bg_color = theme['bg']
        self.card_color = theme['card']
        self.text_color = theme['text']
        self.muted_color = theme['muted']
        self.primary_color = ACCENTS.get(self.prefs.get('accent'), ACCENTS['blue'])
        self.radius = float(self.prefs.get('radius', 10))
        self.btn_height = float(self.prefs.get('btn_height', 50))
        self.font_scale = float(self.prefs.get('font_scale', 1.0))
        self.notify_week = 1 if self.prefs.get('notify_week', 1) else 0
        self.notify_day = 1 if self.prefs.get('notify_day', 1) else 0
        try:
            self.notify_hour = max(0, min(23, int(self.prefs.get('notify_hour', 9))))
        except Exception:
            self.notify_hour = 9

    def _save_later(self):
        Clock.unschedule(self._save_prefs)
        Clock.schedule_once(self._save_prefs, 0.6)

    def _save_prefs(self, *args):
        try:
            core.save_settings(self.prefs)
        except Exception as e:
            core.log(f"save settings: {e}")

    def set_theme(self, name):
        self.prefs['theme'] = name
        self.apply_prefs()
        self._save_later()

    def set_accent(self, name):
        self.prefs['accent'] = name
        self.apply_prefs()
        self._save_later()

    def set_radius(self, value):
        if abs(self.radius - value) < 0.001:
            return
        self.prefs['radius'] = float(value)
        self.radius = float(value)
        self._save_later()

    def set_btn_height(self, value):
        if abs(self.btn_height - value) < 0.001:
            return
        self.prefs['btn_height'] = float(value)
        self.btn_height = float(value)
        self._save_later()

    def set_font_scale(self, value):
        if abs(self.font_scale - value) < 0.001:
            return
        self.prefs['font_scale'] = round(float(value), 2)
        self.font_scale = round(float(value), 2)
        self._save_later()

    # ---------- الصوت والاهتزاز ----------
    def _sync_fx(self):
        try:
            import fx
            self.sound_on = fx.is_on('sound')
            self.vibrate_on = fx.is_on('vibrate')
            fx.init()
        except Exception:
            pass

    def toggle_fx(self, which):
        try:
            import fx
            fx.set_on(which, not fx.is_on(which))
            self._sync_fx()
            if which == 'sound':
                fx.play('ok')
            else:
                fx.buzz(80)
        except Exception as e:
            if core:
                core.log(f"toggle fx: {e}")

    def open_app_settings(self):
        """يفتح صفحة إعدادات التطبيق في الهاتف (منها: الإشعارات، البطارية، التشغيل التلقائي)."""
        try:
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Settings = autoclass('android.provider.Settings')
                Uri = autoclass('android.net.Uri')
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                intent.setData(Uri.parse('package:' + activity.getPackageName()))
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                activity.startActivity(intent)
        except Exception as e:
            if core:
                core.log(f"open app settings: {e}")
            self.show_status("Open Phone Settings, then Apps, then BFB.")

    def toggle_notify(self, which):
        key = 'notify_week' if which == 'week' else 'notify_day'
        self.prefs[key] = 0 if self.prefs.get(key, 1) else 1
        self.apply_prefs()
        self._save_later()

    def change_hour(self, delta):
        self.prefs['notify_hour'] = (int(self.notify_hour) + int(delta)) % 24
        self.apply_prefs()
        self._save_later()

    def reset_settings(self):
        seen = self.prefs.get('help_seen', False)
        self.prefs = dict(core.DEFAULT_SETTINGS)
        self.prefs['help_seen'] = seen
        self.apply_prefs()
        self._save_later()

    # ---------- المساعدة ----------
    def show_help(self, first_run=False):
        HelpPopup(first_run=first_run, dismiss_cb=self._help_done).open()

    def _help_done(self):
        if not self.prefs.get('help_seen'):
            self.prefs['help_seen'] = True
            self._save_later()

    def _maybe_show_help(self, dt):
        if not self.prefs.get('help_seen'):
            self.show_help(first_run=True)

    # ---------- رابط تيليغرام ----------
    TELEGRAM_URL = 'https://t.me/bfbreminder'

    def open_telegram(self):
        """يفتح الرابط عبر تطبيق تيليغرام أو المتصفح (لا يحتاج صلاحية الإنترنت)."""
        try:
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(self.TELEGRAM_URL))
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                activity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open(self.TELEGRAM_URL)
        except Exception as e:
            if core:
                core.log(f"open telegram: {e}")
            self.show_status("Could not open the link. Search for @bfbreminder in Telegram.")

    # ---------- التنقل ----------
    def go(self, screen_name):
        self.root.ids.sm.current = screen_name

    # ---------- الحالة والإشعارات ----------
    def show_status(self, errors, ok=False):
        if not errors:
            self.status = ''
            return
        if isinstance(errors, str):
            msg = errors
        else:
            msg = "Notification error: " + str(errors[0])
        self.status = msg
        self.status_color = [0.1, 0.6, 0.2, 1] if ok else [0.85, 0.2, 0.2, 1]

    def test_notification(self):
        ok, err = core.test_notification()
        if ok:
            self.show_status(
                "Notification sent. If you see nothing, check phone settings.",
                ok=True)
        else:
            self.show_status("Error: " + err)

    # ---------- نسخة احتياطية ----------
    def export_backup(self):
        try:
            code = core.export_backup()
            text = "BFB backup - keep this message safe:\n" + code
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(text)
            if platform == 'android':
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                JString = autoclass('java.lang.String')
                intent = Intent(Intent.ACTION_SEND)
                intent.setType('text/plain')
                intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', JString(text)))
                chooser = Intent.createChooser(intent, cast('java.lang.CharSequence', JString('BFB')))
                PythonActivity.mActivity.startActivity(chooser)
            self.show_status("Backup copied. Save it somewhere safe (e.g. send it to yourself).",
                             ok=True)
        except Exception as e:
            self.show_status(f"Backup error: {e}")

    def import_backup(self):
        try:
            from kivy.core.clipboard import Clipboard
            added, skipped = core.import_backup(Clipboard.paste() or '')
        except ValueError:
            self.show_status("No valid backup found in the clipboard. Copy the backup message first.")
            return
        except Exception as e:
            self.show_status(f"Import error: {e}")
            return
        self.prefs = core.load_settings()
        self.apply_prefs()
        try:
            self.root.ids.sm.get_screen('birthdays').refresh_list()
        except Exception:
            pass
        self.show_status(f"Backup restored: {added} added, {skipped} already existed.", ok=True)

    # ---------- بيانات ----------
    def edit_birthday(self, name, date_str):
        self.root.ids.sm.get_screen('birthdays').edit_birthday(name, date_str)

    def ask_delete(self, name, date_str):
        ConfirmPopup(
            msg='Delete this birthday?',
            sub=fix_arabic(name),
            yes_cb=lambda: self.delete_birthday(name, date_str),
        ).open()

    def delete_birthday(self, name, date_str):
        items = [
            b for b in core.load_birthdays()
            if not (b['name'] == name and b['date'] == date_str)
        ]
        try:
            core.save_birthdays(items)
        except Exception as e:
            self.show_status(f"Delete error: {e}")
        self.root.ids.sm.get_screen('birthdays').refresh_list()

    # ---------- التشغيل ----------
    def on_start(self):
        if getattr(self, 'build_failed', False):
            return
        Clock.schedule_once(self._maybe_show_help, 1.5)
        if platform == 'android':
            try:
                from android.permissions import request_permissions
                request_permissions(
                    ['android.permission.POST_NOTIFICATIONS'],
                    lambda perms, grants: self.start_background()
                )
            except Exception as e:
                core.log(f"permission error: {e}")
                self.start_background()
        else:
            Clock.schedule_once(lambda dt: self.show_status(core.check_and_notify()), 1)

    def start_background(self, *args):
        try:
            self.show_status(core.check_and_notify())
        except Exception as e:
            core.log(f"start check: {e}")
        started = False
        # الطريقة الأولى: نفس استدعاء Java الذي نجح عند الإقلاع (يبدأ الخدمة ويُظهر الإشعار الدائم)
        try:
            from jnius import autoclass
            core.log("service: app asks to start the service (direct)")
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            autoclass('org.bfb.bfbreminder.ServiceReminder').start(activity, 'app')
            core.log("service: direct start call returned")
            started = True
        except Exception as e:
            core.log(f"service error (direct): {e}")
        if not started:
            try:
                from android import AndroidService
                core.log("service: app asks to start the service (AndroidService)")
                svc = AndroidService('BFB Reminder', 'تذكير أعياد الميلاد يعمل')
                svc.start('service started')
                core.log("service: AndroidService start call returned")
            except Exception as e:
                core.log(f"service error: {e}")


if __name__ == '__main__':
    BFBApp().run()
