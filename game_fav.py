"""المفضلة: نجمة بجانب كل لعبة. تُحفظ القائمة في ملف ويظهر قسم المفضلة أولًا."""
import math
import os

from kivy.app import App
from kivy.graphics import Color, Line, Mesh
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

import core

FAV_FILE = os.path.join(core.data_dir(), 'game_favs.json')
GOLD = (1.0, 0.78, 0.15, 1)


class StarButton(ButtonBehavior, Widget):
    on = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, on=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        cx, cy = self.center
        big = min(self.width, self.height) / 2 - dp(3)
        if big <= 0:
            return
        small = big * 0.45
        pts = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = big if i % 2 == 0 else small
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        with self.canvas:
            if self.on:
                Color(*GOLD)
                verts = [cx, cy, 0, 0]
                for x, y in pts + [pts[0]]:
                    verts += [x, y, 0, 0]
                Mesh(vertices=verts, indices=list(range(len(verts) // 4)), mode='triangle_fan')
            else:
                app = App.get_running_app()
                Color(*(app.muted_color if app else (0.5, 0.5, 0.55, 1)))
            flat = []
            for x, y in pts:
                flat += [x, y]
            Line(points=flat, close=True, width=dp(1.3))


class FavMixin:
    def fav_init(self):
        data = core._read(FAV_FILE, [])
        self.favs = [g for g in data if isinstance(g, str)] if isinstance(data, list) else []

    def fav_toggle(self, gid):
        favs = getattr(self, 'favs', [])
        if gid in favs:
            favs.remove(gid)
        else:
            favs.append(gid)
        self.favs = favs
        try:
            core._write(FAV_FILE, favs)
        except Exception as e:
            core.log(f'fav save: {e}')
        self.render()

    def fav_star(self, gid):
        star = StarButton(size_hint=(None, None), size=(dp(40), dp(40)),
                          pos_hint={'center_y': 0.5})
        star.on = gid in getattr(self, 'favs', [])
        star.bind(on_release=lambda *a: self.fav_toggle(gid))
        return star
