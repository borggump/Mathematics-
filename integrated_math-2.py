"""
Integrated Math Explorer
========================
Pydroid3 / Android — uses Kivy (pre-installed in Pydroid3)
Run: python integrated_math.py

If Kivy is missing in Pydroid3:
  pip install kivy
"""

import math

# ── Suppress Kivy startup log ──────────────────────────────────
import os
os.environ["KIVY_NO_ENV_CONFIG"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.config import Config
Config.set("graphics", "width",  "400")
Config.set("graphics", "height", "700")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Line, Ellipse, Rectangle,
                            RoundedRectangle, Triangle)
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock

# ── Palette ────────────────────────────────────────────────────
BG      = (0.055, 0.059, 0.102, 1)
SURFACE = (0.086, 0.090, 0.141, 1)
BORDER  = (0.145, 0.149, 0.251, 1)
ALG     = (0.310, 0.557, 0.969, 1)   # blue
GEO     = (0.969, 0.635, 0.310, 1)   # amber
TRIG    = (0.635, 0.310, 0.969, 1)   # violet
STAT    = (0.310, 0.969, 0.635, 1)   # green
TEXT    = (0.910, 0.914, 0.957, 1)
MUTED   = (0.482, 0.490, 0.620, 1)
WHITE   = (1, 1, 1, 1)

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4))

Window.clearcolor = BG

# ── Helpers ────────────────────────────────────────────────────
def rgba(*c):
    """Accept 4-tuple float rgba and return it."""
    return c[0] if len(c)==1 else c

def color_str(c):
    return "#{:02x}{:02x}{:02x}".format(
        int(c[0]*255), int(c[1]*255), int(c[2]*255))

def lbl(text, color=None, size=14, bold=False, halign="left", padding=(16,4)):
    color = color or TEXT
    l = Label(
        text=text,
        color=color,
        font_size=dp(size),
        bold=bold,
        halign=halign,
        valign="top",
        size_hint_y=None,
        padding=padding,
    )
    l.bind(width=lambda inst, w: setattr(inst, "text_size", (w - dp(padding[0]*2), None)))
    l.bind(texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + dp(padding[1]*2)))
    return l

def divider():
    w = Widget(size_hint_y=None, height=dp(1))
    with w.canvas:
        Color(*BORDER)
        w.rect = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda i,v: setattr(i.rect,"pos",v),
           size=lambda i,v: setattr(i.rect,"size",v))
    return w

def card_bg(widget):
    with widget.canvas.before:
        Color(*SURFACE)
        widget._bg = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(8)])
        Color(*BORDER)
        widget._bd = RoundedRectangle(pos=widget.pos, size=widget.size,
                                       radius=[dp(8)], width=1)  # kivy draws filled; use Line instead
    widget.bind(pos=lambda i,v: (setattr(i._bg,"pos",v), setattr(i._bd,"pos",v)),
                size=lambda i,v: (setattr(i._bg,"size",v), setattr(i._bd,"size",v)))

def make_input(default="", color=ALG):
    cs = color_str(color)
    ti = TextInput(
        text=default,
        multiline=False,
        background_color=SURFACE,
        foreground_color=color,
        cursor_color=color,
        font_size=dp(14),
        size_hint=(None, None),
        width=dp(90),
        height=dp(36),
        padding=[dp(8), dp(8)],
    )
    return ti

def action_btn(text, color=ALG):
    bg = list(color[:3]) + [1]
    btn = Button(
        text=text,
        font_size=dp(13),
        bold=True,
        color=BG,
        background_color=bg,
        background_normal="",
        size_hint_y=None,
        height=dp(44),
    )
    return btn

def mono_card(text, color=TEXT):
    box = BoxLayout(orientation="vertical",
                    size_hint_y=None, padding=dp(12), spacing=dp(2))
    with box.canvas.before:
        Color(*SURFACE)
        box._bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
    box.bind(pos=lambda i,v: setattr(i._bg,"pos",v),
             size=lambda i,v: (setattr(i._bg,"size",v), setattr(i,"height",i.minimum_height)))
    box.bind(minimum_height=box.setter("height"))
    l = Label(text=text, color=color, font_size=dp(12),
               halign="left", valign="top", size_hint_y=None,
               font_name="RobotoMono")
    l.bind(width=lambda inst,w: setattr(inst,"text_size",(w,None)))
    l.bind(texture_size=lambda inst,ts: setattr(inst,"height",ts[1]+dp(8)))
    box.add_widget(l)
    return box

# ── Scrollable screen base ─────────────────────────────────────
class ScrollScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical")
        self.add_widget(root)

        sv = ScrollView(do_scroll_x=False, bar_width=dp(4),
                        bar_color=list(MUTED[:3])+[0.5],
                        bar_inactive_color=list(MUTED[:3])+[0.2])
        root.add_widget(sv)

        self.content = BoxLayout(orientation="vertical",
                                  size_hint_y=None, spacing=dp(4),
                                  padding=[dp(8), dp(12), dp(8), dp(24)])
        self.content.bind(minimum_height=self.content.setter("height"))
        sv.add_widget(self.content)

    def add(self, widget):
        self.content.add_widget(widget)


# ══════════════════════════════════════════════════════════════
# CANVAS WIDGETS
# ══════════════════════════════════════════════════════════════

class LineCanvas(Widget):
    """Draws two lines and their intersection."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.m1 = 2.0; self.b1 = 1.0
        self.m2 = -1.0; self.b2 = 7.0
        self.ix = 2.0; self.iy = 5.0
        self.bind(size=self._draw, pos=self._draw)

    def update(self, m1, b1, m2, b2, ix, iy):
        self.m1=m1; self.b1=b1; self.m2=m2; self.b2=b2
        self.ix=ix; self.iy=iy
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        W, H = self.width, self.height
        if W < 10: return
        ox, oy = W/2, H/2
        sc = min(W, H) / 14

        with self.canvas:
            # Background
            Color(*SURFACE)
            Rectangle(pos=self.pos, size=self.size)

            # Grid
            Color(*BORDER)
            for i in range(-7, 8):
                x = ox + i*sc + self.x
                Line(points=[x, self.y, x, self.y+H], width=dp(0.5))
            for j in range(-4, 5):
                y = oy + j*sc + self.y
                Line(points=[self.x, y, self.x+W, y], width=dp(0.5))

            # Axes
            Color(0.23, 0.24, 0.38, 1)
            Line(points=[self.x, oy+self.y, self.x+W, oy+self.y], width=dp(1.5))
            Line(points=[ox+self.x, self.y, ox+self.x, self.y+H], width=dp(1.5))

            # Axis tick labels drawn via Label widgets — skip in canvas, use text below

            # Line 1: y = m1*x + b1
            Color(*ALG)
            pts1 = []
            for xi in range(-8, 9):
                yi = self.m1*xi + self.b1
                if -5 < yi < 5:
                    pts1 += [ox + xi*sc + self.x, oy + yi*sc + self.y]
            if len(pts1) >= 4:
                Line(points=pts1, width=dp(2))

            # Line 2
            Color(*GEO)
            pts2 = []
            for xi in range(-8, 9):
                yi = self.m2*xi + self.b2
                if -5 < yi < 5:
                    pts2 += [ox + xi*sc + self.x, oy + yi*sc + self.y]
            if len(pts2) >= 4:
                Line(points=pts2, width=dp(2))

            # Intersection
            if self.ix is not None:
                ipx = ox + self.ix*sc + self.x
                ipy = oy + self.iy*sc + self.y
                if self.x < ipx < self.x+W and self.y < ipy < self.y+H:
                    Color(*TRIG, 0.6)
                    Line(points=[ipx, self.y+oy, ipx, ipy], dash_length=dp(4), dash_offset=dp(3), width=dp(1))
                    Line(points=[self.x+ox, ipy, ipx, ipy], dash_length=dp(4), dash_offset=dp(3), width=dp(1))
                    Color(*WHITE)
                    Ellipse(pos=(ipx-dp(5), ipy-dp(5)), size=(dp(10), dp(10)))
                    Color(*TRIG)
                    Line(ellipse=(ipx-dp(6), ipy-dp(6), dp(12), dp(12)), width=dp(2))


class TriangleCanvas(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.a = 3.0; self.b = 4.0; self.c = 5.0
        self.A = 53.1; self.B = 36.9
        self.bind(size=self._draw, pos=self._draw)

    def update(self, a, b, c, A, B):
        self.a=a; self.b=b; self.c=c; self.A=A; self.B=B
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        W, H = self.width, self.height
        if W < 10: return
        margin = dp(44)
        sc = min((W - 2*margin) / max(self.b, 0.1),
                 (H - 2*margin) / max(self.a, 0.1))
        sc = min(sc, dp(28))

        x0 = self.x + margin
        y0 = self.y + margin
        x1 = x0 + self.b * sc
        y1 = y0
        x2 = x0
        y2 = y0 + self.a * sc

        with self.canvas:
            Color(*SURFACE)
            Rectangle(pos=self.pos, size=self.size)

            # Triangle fill
            Color(0.086, 0.090, 0.18, 1)
            Triangle(points=[x0,y0, x1,y1, x2,y2])

            # Triangle outline
            Color(*GEO)
            Line(points=[x0,y0, x1,y1, x2,y2, x0,y0], width=dp(2))

            # Right angle square
            sq = dp(10)
            Color(*GEO, 0.4)
            Rectangle(pos=(x0, y0), size=(sq, sq))
            Color(*GEO)
            Line(points=[x0,y0+sq, x0+sq,y0+sq, x0+sq,y0], width=dp(1.5))

            # Angle arc at x1 (angle B)
            Color(*ALG)
            Line(ellipse=(x1-dp(20), y1-dp(20), dp(40), dp(40),
                          90, 90+int(self.B)), width=dp(1.5))

            # Angle arc at x2 (angle A)
            Color(*TRIG)
            Line(ellipse=(x2-dp(16), y2-dp(16), dp(32), dp(32),
                          270, 270+int(self.A)), width=dp(1.5))


class UnitCircleCanvas(Widget):
    angle = NumericProperty(50.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._draw, pos=self._draw, angle=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        W, H = self.width, self.height
        if W < 10: return
        ox, oy = W/2 + self.x, H/2 + self.y
        R = min(W, H)/2 - dp(36)

        rad = math.radians(self.angle)
        s = math.sin(rad); c = math.cos(rad)
        px = ox + c*R; py = oy + s*R

        with self.canvas:
            # Background
            Color(*SURFACE)
            Rectangle(pos=self.pos, size=self.size)

            # Grid
            Color(*BORDER)
            for i in range(-4, 5):
                xg = ox + i*R/2
                Line(points=[xg, self.y, xg, self.y+H], width=dp(0.5))
            for j in range(-3, 4):
                yg = oy + j*R/2
                Line(points=[self.x, yg, self.x+W, yg], width=dp(0.5))

            # Axes
            Color(0.23, 0.24, 0.38, 1)
            Line(points=[self.x, oy, self.x+W, oy], width=dp(1.5))
            Line(points=[ox, self.y, ox, self.y+H], width=dp(1.5))

            # Unit circle
            Color(*ALG, 0.35)
            Line(ellipse=(ox-R, oy-R, R*2, R*2), width=dp(1.5))

            # Angle arc
            extent = self.angle if self.angle >= 0 else 360+self.angle
            Color(*STAT)
            Line(ellipse=(ox-dp(28), oy-dp(28), dp(56), dp(56), 0, extent), width=dp(2))

            # cos line (horizontal)
            Color(*ALG)
            Line(points=[ox, oy, px, oy], width=dp(2), dash_length=dp(5), dash_offset=dp(4))

            # sin line (vertical)
            Color(*TRIG)
            Line(points=[px, oy, px, py], width=dp(2), dash_length=dp(5), dash_offset=dp(4))

            # Radius
            Color(*WHITE, 0.8)
            Line(points=[ox, oy, px, py], width=dp(2))

            # Point
            Color(*WHITE)
            Ellipse(pos=(px-dp(6), py-dp(6)), size=(dp(12), dp(12)))
            Color(*TRIG)
            Line(ellipse=(px-dp(7), py-dp(7), dp(14), dp(14)), width=dp(2))

            # -1, 1 tick marks
            Color(*MUTED)
            for v, lx, ly in [(-1, ox-R-dp(2), oy), (1, ox+R-dp(2), oy)]:
                Line(points=[lx, oy-dp(4), lx, oy+dp(4)], width=dp(1))


# ══════════════════════════════════════════════════════════════
# SCREENS
# ══════════════════════════════════════════════════════════════

class PathwaysScreen(ScrollScreen):
    def __init__(self, **kw):
        super().__init__(name="pathways", **kw)
        c = self.content

        c.add_widget(lbl("PART 1 · STRUCTURE", MUTED, 10))
        c.add_widget(lbl("Two Pathways Through High School Math",
                         WHITE, 17, bold=True))
        c.add_widget(lbl(
            "Traditional math teaches one subject per year. "
            "Integrated math blends algebra, geometry & trig every year.",
            MUTED, 12))
        c.add_widget(divider())

        # Traditional
        c.add_widget(lbl("Traditional  AGA  Sequence", MUTED, 11, bold=True))
        trad = [
            ("9th",  "Algebra I",          ALG,
             "Solve equations, graph lines, inequalities.\n"
             "Core formula: y = mx + b\n"
             "Quadratic: ax² + bx + c = 0"),
            ("10th", "Geometry",            GEO,
             "Angles, proofs, triangles, circles.\n"
             "Pythagorean theorem: a² + b² = c²\n"
             "⚠  Full year with NO algebra practice!"),
            ("11th", "Algebra II",          ALG,
             "Polynomials, logs, complex numbers.\n"
             "Quadratic formula: x = (−b ± √(b²−4ac)) / 2a\n"
             "log(ab) = log a + log b"),
            ("12th", "Pre-Calc / Calculus", TRIG,
             "Limits, derivatives, integrals.\n"
             "f'(x) = lim[h→0] (f(x+h)−f(x)) / h\n"
             "Only path available in traditional sequence."),
        ]
        for yr, name, col, detail in trad:
            self._year_row(c, yr, name, col, detail)

        c.add_widget(divider())
        c.add_widget(lbl("Integrated Math Sequence", MUTED, 11, bold=True))

        int_courses = [
            ("9th",  "Integrated Math I",  [ALG, GEO, TRIG],
             "Algebra + Geometry + Trig woven together.\n"
             "Linear equations, triangle geometry, intro sin/cos.\n"
             "sin θ = opp/hyp   cos θ = adj/hyp"),
            ("10th", "Integrated Math II", [ALG, GEO, TRIG],
             "Deeper quadratics, circle geometry, unit circle.\n"
             "x² + y² = 1   (cos θ, sin θ) on unit circle\n"
             "Foundational math COMPLETE by end of 10th grade."),
        ]
        for yr, name, cols, detail in int_courses:
            self._blend_row(c, yr, name, cols, detail)

        c.add_widget(lbl("── foundational math complete ──", MUTED, 10, halign="center"))
        self._year_row(c, "11th", "Statistics / Data Science", STAT,
                       "Mean, std dev, regression, probability.\n"
                       "x̄ = Σxᵢ/n    σ = √(Σ(xᵢ−x̄)²/n)\n"
                       "Opens non-calculus STEM and business paths.")
        self._year_row(c, "12th", "Calculus  OR  AP Statistics", TRIG,
                       "Students CHOOSE their 12th-grade math path.\n"
                       "Not everyone needs calculus — data science,\n"
                       "nursing, business → statistics is equally rigorous.")

        c.add_widget(divider())
        c.add_widget(lbl(
            "KEY INSIGHT: In the traditional path a 10th grader spends "
            "an entire year in geometry with NO algebra practice — yet state "
            "exams in 10th grade test algebra heavily. Integrated math "
            "eliminates this gap.", MUTED, 11))

    def _year_row(self, container, yr, name, col, detail):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
                        spacing=dp(6), padding=[dp(8), dp(6)])
        with box.canvas.before:
            Color(*col, 0.12)
            box._bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
            Color(*col, 0.9)
            box._ln = Line(rounded_rectangle=[*box.pos, *box.size, dp(8)], width=dp(1))
        box.bind(pos=lambda i,v: (setattr(i._bg,"pos",v),
                                   setattr(i._ln,"rounded_rectangle",[*v,*i.size,dp(8)])),
                 size=lambda i,v: (setattr(i._bg,"size",v),
                                    setattr(i._ln,"rounded_rectangle",[*i.pos,*v,dp(8)])))

        box.add_widget(Label(text=yr, color=MUTED, font_size=dp(10),
                              size_hint=(None,1), width=dp(34), halign="left"))
        box.add_widget(Label(text=name, color=col, font_size=dp(13), bold=True,
                              halign="left", text_size=(dp(170),None), valign="middle"))

        def show(dt, d=detail, n=name, color=col):
            self._popup(n, d, color)
        btn = Button(text="▸ info", font_size=dp(11), color=col,
                     background_color=(0,0,0,0), background_normal="",
                     size_hint=(None,1), width=dp(60))
        btn.bind(on_press=lambda *a: Clock.schedule_once(show, 0))
        box.add_widget(btn)
        container.add_widget(box)

    def _blend_row(self, container, yr, name, cols, detail):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(52),
                        spacing=dp(6), padding=[dp(8), dp(6)])
        with box.canvas.before:
            Color(*SURFACE)
            box._bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
            # triple-colour left bar
            for i, col in enumerate(cols):
                Color(*col, 0.8)
                bar_h = box.height / len(cols) if hasattr(box, "height") else dp(14)

        box.add_widget(Label(text=yr, color=MUTED, font_size=dp(10),
                              size_hint=(None,1), width=dp(34)))
        box.add_widget(Label(text=name, color=WHITE, font_size=dp(13), bold=True,
                              halign="left", text_size=(dp(170),None), valign="middle"))

        # colour dots
        dots = BoxLayout(size_hint=(None,1), width=dp(36), spacing=dp(3),
                          padding=[0, dp(18)])
        for col in cols:
            dot = Widget(size_hint=(None,None), size=(dp(8),dp(8)))
            with dot.canvas:
                Color(*col)
                Ellipse(pos=dot.pos, size=dot.size)
            dot.bind(pos=lambda i,v: i.canvas.clear() or
                     (i.canvas.add(Color(*col)) or i.canvas.add(Ellipse(pos=v,size=i.size))))
            dots.add_widget(dot)
        box.add_widget(dots)

        def show(dt, d=detail, n=name):
            self._popup(n, d, WHITE)
        btn = Button(text="▸ info", font_size=dp(11), color=WHITE,
                     background_color=(0,0,0,0), background_normal="",
                     size_hint=(None,1), width=dp(60))
        btn.bind(on_press=lambda *a: Clock.schedule_once(show, 0))
        box.add_widget(btn)
        container.add_widget(box)

    def _popup(self, title, text, color):
        from kivy.uix.popup import Popup
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(16))
        content.add_widget(Label(text=title, color=color, font_size=dp(15),
                                  bold=True, size_hint_y=None, height=dp(36),
                                  halign="left", text_size=(dp(300),None)))
        l = Label(text=text, color=TEXT, font_size=dp(12),
                   halign="left", valign="top", size_hint_y=None)
        l.bind(width=lambda i,w: setattr(i,"text_size",(w,None)))
        l.bind(texture_size=lambda i,ts: setattr(i,"height",ts[1]+dp(8)))
        content.add_widget(l)
        btn = Button(text="Close", font_size=dp(13), size_hint_y=None, height=dp(40),
                     background_color=list(SURFACE), background_normal="")
        popup = Popup(title="", content=content, size_hint=(0.88,0.55),
                      background_color=BG, separator_height=0)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


class AlgebraScreen(ScrollScreen):
    def __init__(self, **kw):
        super().__init__(name="algebra", **kw)
        c = self.content

        c.add_widget(lbl("PART 2 · ALGEBRA", MUTED, 10))
        c.add_widget(lbl("Find Where Two Lines Cross", WHITE, 17, bold=True))
        c.add_widget(lbl("y = m₁x + b₁  and  y = m₂x + b₂\n"
                         "Enter values → tap Solve", MUTED, 12))

        # Input grid
        grid = GridLayout(cols=4, size_hint_y=None, height=dp(100),
                           spacing=dp(6), padding=[dp(4), dp(4)])
        grid.add_widget(lbl("m₁", ALG, 12)); self.m1 = make_input("2", ALG);    grid.add_widget(self.m1)
        grid.add_widget(lbl("b₁", ALG, 12)); self.b1 = make_input("1", ALG);    grid.add_widget(self.b1)
        grid.add_widget(lbl("m₂", GEO, 12)); self.m2 = make_input("-1", GEO);   grid.add_widget(self.m2)
        grid.add_widget(lbl("b₂", GEO, 12)); self.b2 = make_input("7", GEO);    grid.add_widget(self.b2)
        c.add_widget(grid)

        btn = action_btn("Solve & Draw", ALG)
        btn.bind(on_press=self._solve)
        c.add_widget(btn)

        self.result_lbl = lbl("", WHITE, 14, bold=True)
        c.add_widget(self.result_lbl)

        self.line_cv = LineCanvas(size_hint_y=None, height=dp(200))
        c.add_widget(self.line_cv)

        self.steps_lbl = lbl("", TEXT, 11)
        c.add_widget(self.steps_lbl)

        Clock.schedule_once(lambda dt: self._solve(None), 0.5)

    def _solve(self, *_):
        try:
            m1 = float(self.m1.text); b1 = float(self.b1.text)
            m2 = float(self.m2.text); b2 = float(self.b2.text)
        except ValueError:
            self.result_lbl.text = "⚠  Enter valid numbers"; return

        if m1 == m2:
            msg = "Parallel — no intersection" if b1 != b2 else "Identical lines — infinite solutions"
            self.result_lbl.text = msg
            self.line_cv.update(m1,b1,m2,b2,None,None)
            return

        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1
        denom = 1 + m1*m2
        angle = 90.0 if abs(denom)<1e-9 else math.degrees(math.atan(abs((m1-m2)/denom)))
        r = math.sqrt(x**2 + y**2)
        theta_p = math.degrees(math.atan2(y, x))

        self.result_lbl.text = f"Intersection: ({x:.3f}, {y:.3f})"
        self.steps_lbl.text = (
            f"[b][color=4f8ef7]Algebra[/color][/b]\n"
            f"  {m1:+.2f}x + {b1:+.2f} = {m2:+.2f}x + {b2:+.2f}\n"
            f"  ({m1-m2:.2f})x = {b2-b1:.2f}   →   x = {x:.4f}\n"
            f"  y = {m1}({x:.4f}) + {b1} = {y:.4f}\n\n"
            f"[b][color=f7a24f]Geometry[/color][/b]\n"
            f"  Angle between lines:\n"
            f"  tan θ = |m₁−m₂|/|1+m₁m₂| = {abs(m1-m2):.3f}/{abs(denom):.3f}\n"
            f"  θ ≈ {angle:.1f}°\n\n"
            f"[b][color=a24ff7]Trigonometry[/color][/b]\n"
            f"  Polar form of ({x:.2f}, {y:.2f}):\n"
            f"  r = √(x²+y²) = {r:.3f}\n"
            f"  φ = arctan(y/x) ≈ {theta_p:.1f}°"
        )
        self.steps_lbl.markup = True
        self.line_cv.update(m1, b1, m2, b2, x, y)


class GeometryScreen(ScrollScreen):
    def __init__(self, **kw):
        super().__init__(name="geometry", **kw)
        c = self.content

        c.add_widget(lbl("PART 3 · GEOMETRY", MUTED, 10))
        c.add_widget(lbl("Pythagorean Theorem", WHITE, 17, bold=True))
        c.add_widget(lbl("Enter any 2 sides — leave the third blank.\n"
                         "a² + b² = c²", MUTED, 12))

        grid = GridLayout(cols=4, size_hint_y=None, height=dp(100),
                           spacing=dp(6), padding=[dp(4), dp(4)])
        grid.add_widget(lbl("a", ALG, 12)); self.a_in = make_input("3", ALG); grid.add_widget(self.a_in)
        grid.add_widget(lbl("b", GEO, 12)); self.b_in = make_input("4", GEO); grid.add_widget(self.b_in)
        grid.add_widget(lbl("c", TRIG, 12)); self.c_in = make_input("",  TRIG); grid.add_widget(self.c_in)

        c.add_widget(grid)

        btn = action_btn("Calculate & Draw", GEO)
        btn.bind(on_press=self._calc)
        c.add_widget(btn)

        self.result_lbl = lbl("", WHITE, 14, bold=True)
        c.add_widget(self.result_lbl)

        self.tri_cv = TriangleCanvas(size_hint_y=None, height=dp(200))
        c.add_widget(self.tri_cv)

        self.steps_lbl = lbl("", TEXT, 11)
        c.add_widget(self.steps_lbl)

        Clock.schedule_once(lambda dt: self._calc(None), 0.5)

    def _calc(self, *_):
        def val(ti):
            t = ti.text.strip()
            return float(t) if t else None
        try:
            a, b, c = val(self.a_in), val(self.b_in), val(self.c_in)
        except ValueError:
            self.result_lbl.text = "⚠  Enter valid numbers"; return

        try:
            if a and b and not c:   c = math.sqrt(a**2 + b**2)
            elif a and c and not b: b = math.sqrt(c**2 - a**2)
            elif b and c and not a: a = math.sqrt(c**2 - b**2)
            elif a and b and c:     pass
            else: self.result_lbl.text = "⚠  Enter at least 2 sides"; return
            if a <= 0 or b <= 0 or c <= 0: raise ValueError
        except (ValueError, TypeError):
            self.result_lbl.text = "⚠  Invalid triangle sides"; return

        A = math.degrees(math.atan2(a, b))
        B = 90.0 - A
        area = 0.5 * a * b
        perim = a + b + c

        self.result_lbl.text = f"a={a:.3f}  b={b:.3f}  c={c:.3f}"
        self.steps_lbl.text = (
            f"a² + b² = c²\n"
            f"{a:.3f}² + {b:.3f}² = {a**2:.3f} + {b**2:.3f} = {c**2:.3f}\n"
            f"c = √{c**2:.3f} = {c:.4f}\n\n"
            f"Angle α (opp b) = arctan(b/a) = {A:.1f}°\n"
            f"Angle β (opp a) = {B:.1f}°\n"
            f"α + β + 90° = 180° ✓\n\n"
            f"Area      = ½ · a · b = {area:.3f}\n"
            f"Perimeter = a+b+c = {perim:.3f}\n\n"
            f"Trig ratios (angle α):\n"
            f"  sin α = {math.sin(math.radians(A)):.4f}\n"
            f"  cos α = {math.cos(math.radians(A)):.4f}\n"
            f"  tan α = {math.tan(math.radians(A)):.4f}"
        )
        self.tri_cv.update(a, b, c, A, B)


class TrigScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="trig", **kw)
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        self.add_widget(root)

        root.add_widget(lbl("PART 4 · TRIGONOMETRY", MUTED, 10))
        root.add_widget(lbl("Unit Circle Explorer", WHITE, 17, bold=True))
        root.add_widget(lbl("Drag the slider to rotate θ", MUTED, 12))

        self.circle = UnitCircleCanvas(size_hint=(1, 1))
        root.add_widget(self.circle)

        self.slider = Slider(min=0, max=360, value=50, size_hint_y=None, height=dp(44),
                              cursor_size=(dp(24),dp(24)), value_track=True,
                              value_track_color=list(TRIG))
        self.slider.bind(value=self._update)
        root.add_widget(self.slider)

        # Value readout
        grid = GridLayout(cols=2, size_hint_y=None, height=dp(100),
                           spacing=dp(4), padding=[dp(8), dp(4)])
        self.sin_lbl  = Label(text="sin θ = 0.766",  color=TRIG, font_size=dp(13), halign="left")
        self.cos_lbl  = Label(text="cos θ = 0.643",  color=ALG,  font_size=dp(13), halign="left")
        self.tan_lbl  = Label(text="tan θ = 1.192",  color=GEO,  font_size=dp(13), halign="left")
        self.quad_lbl = Label(text="Quadrant: I",    color=STAT, font_size=dp(13), halign="left")
        for w in [self.sin_lbl, self.cos_lbl, self.tan_lbl, self.quad_lbl]:
            w.bind(size=lambda i,v: setattr(i,"text_size",v))
            grid.add_widget(w)
        root.add_widget(grid)

        root.add_widget(lbl("sin²θ + cos²θ = 1   (Pythagorean identity)",
                            MUTED, 11))

        self._update(None, 50)

    def _update(self, inst, val):
        deg = float(val)
        rad = math.radians(deg)
        s = math.sin(rad); co = math.cos(rad)
        t = math.tan(rad)
        self.circle.angle = deg
        self.sin_lbl.text  = f"sin {deg:.0f}° = {s:+.4f}"
        self.cos_lbl.text  = f"cos {deg:.0f}° = {co:+.4f}"
        self.tan_lbl.text  = f"tan {deg:.0f}° = {'undef' if abs(co)<0.01 else f'{t:+.4f}'}"
        q = (1 if deg<90 else 2 if deg<180 else 3 if deg<270 else 4)
        signs = {1:"sin+, cos+", 2:"sin+, cos−", 3:"sin−, cos−", 4:"sin−, cos+"}
        self.quad_lbl.text = f"Q{q}: {signs[q]}"


class CompareScreen(ScrollScreen):
    def __init__(self, **kw):
        super().__init__(name="compare", **kw)
        c = self.content

        c.add_widget(lbl("PART 5 · EVIDENCE & TRADEOFFS", MUTED, 10))
        c.add_widget(lbl("Key Statistics", WHITE, 17, bold=True))

        stats = [
            ("16%",    "US districts offer integrated math (2023)", ALG),
            ("11→67%", "Chapman KS proficiency 2015 → 2025",        GEO),
            ("37%",    "California proficiency after 10+ yrs",      TRIG),
            ("~3 mo",  "Extra learning from integrated math",       STAT),
            ("2027",   "Maryland mandates statewide rollout",       ALG),
            ("27",     "States reworking math transitions",         GEO),
        ]
        for num, desc, col in stats:
            box = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=dp(58), spacing=dp(8), padding=[dp(10),dp(6)])
            with box.canvas.before:
                Color(*SURFACE)
                box._bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
            box.bind(pos=lambda i,v: setattr(i._bg,"pos",v),
                     size=lambda i,v: setattr(i._bg,"size",v))
            box.add_widget(Label(text=num, color=col, font_size=dp(18), bold=True,
                                  size_hint=(None,1), width=dp(80), halign="center"))
            box.add_widget(Label(text=desc, color=TEXT, font_size=dp(12),
                                  halign="left", valign="middle", text_size=(dp(220),None)))
            c.add_widget(box)

        c.add_widget(divider())
        c.add_widget(lbl("Tradeoffs at a Glance", WHITE, 15, bold=True))

        rows = [
            ("Retention",       "Topics revisited yearly →\nfewer gaps",       "Year-long gaps possible",          ALG, GEO),
            ("10th exam",       "Sees algebra + geometry\nby 10th grade",      "Algebra gap in geometry year",     GEO, TRIG),
            ("STEM depth",      "Trig/calc may be\nshallower",                 "Strong calculus foundation",       TRIG, ALG),
            ("Flexibility",     "Stats/data path opens\nin 11th grade",        "Race to calculus is default",      STAT, MUTED),
            ("Credit xfer",     "Messy: Int II ≠ Alg I\nat new school",        "Clear & universal everywhere",     TRIG, GEO),
            ("Teacher load",    "Must teach algebra\nAND geometry",            "Can specialise in one area",       TRIG, GEO),
        ]

        header = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4),
                            padding=[dp(8), 0])
        for txt, col, w in [("Topic", MUTED, dp(90)), ("Integrated", ALG, dp(130)),
                              ("Traditional", GEO, dp(130))]:
            header.add_widget(Label(text=txt, color=col, font_size=dp(10),
                                     bold=True, size_hint=(None,1), width=w, halign="left",
                                     text_size=(w, None)))
        c.add_widget(header)
        c.add_widget(divider())

        for topic, int_t, trad_t, ic, tc in rows:
            row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(4),
                             padding=[dp(8), dp(4)])
            row.add_widget(Label(text=topic, color=MUTED, font_size=dp(10),
                                  size_hint=(None,1), width=dp(90), halign="left",
                                  text_size=(dp(90),None), valign="top"))
            row.add_widget(Label(text=int_t, color=ic, font_size=dp(10),
                                  size_hint=(None,1), width=dp(130), halign="left",
                                  text_size=(dp(128),None), valign="top"))
            row.add_widget(Label(text=trad_t, color=tc, font_size=dp(10),
                                  size_hint=(None,1), width=dp(130), halign="left",
                                  text_size=(dp(128),None), valign="top"))
            c.add_widget(row)
            c.add_widget(divider())

        c.add_widget(divider())
        c.add_widget(lbl(
            "Bottom line: Integrated math shows real but modest gains "
            "(~2–3 months of extra learning). Its bigger value is structural — "
            "opening multiple math pathways instead of one race to calculus.",
            MUTED, 11))


# ══════════════════════════════════════════════════════════════
# NAVIGATION BAR
# ══════════════════════════════════════════════════════════════
class NavBar(BoxLayout):
    def __init__(self, sm, **kw):
        super().__init__(size_hint_y=None, height=dp(52),
                          orientation="horizontal", spacing=0, **kw)
        self.sm = sm
        with self.canvas.before:
            Color(*SURFACE)
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*BORDER)
            self._top = Line(points=[self.x, self.top, self.right, self.top], width=dp(1))
        self.bind(pos=self._redraw, size=self._redraw)

        tabs = [("Path",     "pathways",  ALG),
                ("Algebra",  "algebra",   ALG),
                ("Geometry", "geometry",  GEO),
                ("Trig",     "trig",      TRIG),
                ("Compare",  "compare",   STAT)]
        self.btns = {}
        for label, name, col in tabs:
            btn = Button(text=label, font_size=dp(11), bold=True,
                          color=MUTED,
                          background_color=(0,0,0,0), background_normal="",
                          on_press=lambda b, n=name, c=col: self._go(n, c))
            self.btns[name] = (btn, col)
            self.add_widget(btn)

        self._highlight("pathways", ALG)

    def _redraw(self, *_):
        self._bg.pos = self.pos; self._bg.size = self.size
        self._top.points = [self.x, self.top, self.right, self.top]

    def _go(self, name, col):
        self.sm.current = name
        self._highlight(name, col)

    def _highlight(self, active, col):
        for name, (btn, c) in self.btns.items():
            btn.color = c if name == active else MUTED
            btn.bold = (name == active)


# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════
class IntegratedMathApp(App):
    def build(self):
        self.title = "Integrated Math Explorer"
        root = BoxLayout(orientation="vertical")

        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(PathwaysScreen())
        sm.add_widget(AlgebraScreen())
        sm.add_widget(GeometryScreen())
        sm.add_widget(TrigScreen())
        sm.add_widget(CompareScreen())

        root.add_widget(sm)
        root.add_widget(NavBar(sm))
        return root


if __name__ == "__main__":
    IntegratedMathApp().run()
