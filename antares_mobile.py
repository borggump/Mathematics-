"""
Antares Explorer — a mobile GUI for the concepts behind Cisco's
Antares vulnerability-hunting models.

Runs on Android via Pydroid 3 (uses Kivy, which ships with Pydroid 3).
Also runs on desktop if Kivy is installed (pip install kivy).

Interactive: enter a repo size, bug count, model prices and scan
frequency; the app computes the base rate, F1 trade-off, guided-search
savings and total cost, and draws:
    - a "haystack" grid of files with vulnerable ones glowing red
    - a cost-vs-accuracy bar comparison
    - a precision/recall F1 curve

HOW TO RUN IN PYDROID 3
    1. Open Pydroid 3, tap the folder icon, open this file.
    2. Pydroid 3 already bundles Kivy. If it complains, open the
       "Pip" tab and install:  kivy
    3. Press the yellow ▶ play button.

Everything is pure-Python + Kivy graphics (no matplotlib needed),
so it stays light on a phone.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
import math
import random

# ---------------------------------------------------------------- palette
VOID   = (0.039, 0.055, 0.078, 1)   # #0a0e14
PANEL  = (0.066, 0.090, 0.125, 1)   # #111721
LINE   = (0.117, 0.156, 0.211, 1)   # #1e2836
INK    = (0.902, 0.925, 0.952, 1)   # #e6ecf3
MUTED  = (0.518, 0.580, 0.654, 1)   # #8494a7
SCAN   = (0.247, 0.878, 0.772, 1)   # #3fe0c5 teal
VULN   = (1.000, 0.368, 0.423, 1)   # #ff5e6c red
LEAD   = (1.000, 0.780, 0.302, 1)   # #ffc74d amber
SAFE   = (0.184, 0.250, 0.325, 1)   # #2f4053

Window.clearcolor = VOID


# ================================================================ helpers
def hexcol(*rgba):
    return rgba


def compute(N, k, price_small, price_big, rescans, tokens_k):
    """All the Antares math in one place. tokens_k is tokens/scan in thousands."""
    N = max(1, N)
    k = max(0, min(k, N))
    base_rate = k / N

    # guided-search pruning: keep fraction p per reasoning depth d
    p, d = 0.30, 3
    guided_files = N * (p ** d)
    guided_pct = guided_files / N

    # cost model  C = rescans * tokens * price_per_ktoken
    cost_small = rescans * tokens_k * price_small
    cost_big   = rescans * tokens_k * price_big
    cost_ratio = cost_big / cost_small if cost_small > 0 else float('inf')

    return {
        "base_rate": base_rate,
        "guided_files": guided_files,
        "guided_pct": guided_pct,
        "cost_small": cost_small,
        "cost_big": cost_big,
        "cost_ratio": cost_ratio,
    }


def f1(precision, recall):
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ================================================================ widgets
class HaystackCanvas(Widget):
    """Grid of files; vulnerable ones glow red."""
    def __init__(self, N=200, k=4, **kw):
        super().__init__(**kw)
        self.N, self.k = N, k
        self.bind(pos=self.redraw, size=self.redraw)

    def set_data(self, N, k):
        self.N = max(1, min(N, 1200))   # cap cells drawn for phone perf
        self.k = max(0, min(k, self.N))
        self.redraw()

    def redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=self.pos, size=self.size)

            cols = 20
            rows = max(1, math.ceil(self.N / cols))
            pad = dp(6)
            gap = dp(2)
            gw = (self.width - 2 * pad - (cols - 1) * gap) / cols
            gh = (self.height - 2 * pad - (rows - 1) * gap) / rows
            cell = max(dp(2), min(gw, gh))

            vuln_idx = set(random.sample(range(self.N), min(self.k, self.N)))
            for i in range(self.N):
                r = i // cols
                c = i % cols
                x = self.x + pad + c * (cell + gap)
                y = self.top - pad - (r + 1) * cell - r * gap
                if i in vuln_idx:
                    Color(*VULN)
                else:
                    Color(SAFE[0], SAFE[1], SAFE[2], 0.55)
                Rectangle(pos=(x, y), size=(cell, cell))


class BarCompare(Widget):
    """Two log-scaled cost bars: small model vs big model."""
    def __init__(self, cost_small=1, cost_big=100, **kw):
        super().__init__(**kw)
        self.cost_small = cost_small
        self.cost_big = cost_big
        self.bind(pos=self.redraw, size=self.redraw)

    def set_data(self, cost_small, cost_big):
        self.cost_small = max(1e-6, cost_small)
        self.cost_big = max(1e-6, cost_big)
        self.redraw()

    def redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=self.pos, size=self.size)

            pad = dp(14)
            base_y = self.y + pad + dp(18)
            top_y = self.top - pad - dp(14)
            usable_h = top_y - base_y

            # log scale so 1 vs 100 both visible
            def logh(v):
                lv = math.log10(max(v, 1e-3) + 1)
                lmax = math.log10(max(self.cost_big, self.cost_small) + 1)
                lmax = max(lmax, 0.3)
                return usable_h * (lv / lmax)

            bw = (self.width - 3 * pad) / 2
            # Antares bar (teal)
            h1 = logh(self.cost_small)
            Color(*SCAN)
            Rectangle(pos=(self.x + pad, base_y), size=(bw, h1))
            # GPT bar (red)
            h2 = logh(self.cost_big)
            Color(*VULN)
            Rectangle(pos=(self.x + 2 * pad + bw, base_y), size=(bw, h2))

            # baseline
            Color(*LINE)
            Line(points=[self.x + pad, base_y, self.right - pad, base_y], width=1)


class F1Curve(Widget):
    """Draws F1 as recall varies, at fixed precision — shows the harmonic squeeze."""
    def __init__(self, precision=0.6, **kw):
        super().__init__(**kw)
        self.precision = precision
        self.bind(pos=self.redraw, size=self.redraw)

    def set_data(self, precision):
        self.precision = max(0.001, min(1.0, precision))
        self.redraw()

    def redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=self.pos, size=self.size)

            pad = dp(20)
            ox, oy = self.x + pad, self.y + pad
            w = self.width - 2 * pad
            h = self.height - 2 * pad

            # axes
            Color(*LINE)
            Line(points=[ox, oy, ox, oy + h], width=1)
            Line(points=[ox, oy, ox + w, oy], width=1)

            # F1 curve
            pts = []
            for i in range(0, 101):
                recall = i / 100.0
                y = f1(self.precision, recall)
                px = ox + recall * w
                py = oy + y * h
                pts.extend([px, py])
            Color(*SCAN)
            Line(points=pts, width=1.6)

            # diagonal reference (precision == recall ideal)
            Color(LEAD[0], LEAD[1], LEAD[2], 0.4)
            Line(points=[ox, oy, ox + w, oy + h], width=1, dash_offset=4, dash_length=4)


# ================================================================ UI blocks
def styled_label(text, color=INK, size=15, bold=False, halign='left'):
    lbl = Label(text=text, color=color, font_size=sp_size(size),
                halign=halign, valign='middle', markup=True)
    lbl.bind(size=lambda w, *a: setattr(w, 'text_size', (w.width, None)))
    return lbl


def sp_size(n):
    from kivy.metrics import sp
    return sp(n)


def field(label_text, default):
    row = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(64),
                    spacing=dp(2))
    row.add_widget(styled_label(label_text, color=MUTED, size=12))
    ti = TextInput(text=str(default), multiline=False, input_filter='float',
                   background_color=PANEL, foreground_color=INK,
                   cursor_color=SCAN, font_size=sp_size(16),
                   size_hint_y=None, height=dp(40), padding=[dp(10), dp(8)])
    row.add_widget(ti)
    return row, ti


class Header(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', size_hint_y=None,
                         height=dp(96), padding=[dp(16), dp(14)], **kw)
        with self.canvas.before:
            Color(*PANEL)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        self.add_widget(styled_label("[b]ANTARES EXPLORER[/b]",
                                     color=SCAN, size=20))
        self.add_widget(styled_label(
            "Security needles in a million-line haystack",
            color=MUTED, size=13))

    def _upd(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================ app
class AntaresApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(Header())

        panel = TabbedPanel(do_default_tab=False, tab_height=dp(46),
                            background_color=VOID)

        # ---- TAB 1: Calculator ----
        tab_calc = TabbedPanelItem(text='Calculate')
        scroll = ScrollView()
        body = BoxLayout(orientation='vertical', size_hint_y=None,
                         padding=dp(16), spacing=dp(10))
        body.bind(minimum_height=body.setter('height'))

        body.add_widget(styled_label(
            "[b]Inputs[/b] — describe your repo & models", color=INK, size=16))

        f1r, self.in_N = field("Files in repository (N)", 800)
        f2r, self.in_k = field("Vulnerable files (k)", 4)
        f3r, self.in_ps = field("Small-model price ($ / 1k tokens)", 0.0002)
        f4r, self.in_pb = field("Big-model price ($ / 1k tokens)", 0.02)
        f5r, self.in_re = field("Rescans (commits/branches)", 500)
        f6r, self.in_tk = field("Tokens per scan (thousands)", 100)
        for r in (f1r, f2r, f3r, f4r, f5r, f6r):
            body.add_widget(r)

        btn = Button(text="Compute", size_hint_y=None, height=dp(50),
                     background_color=SCAN, color=VOID,
                     font_size=sp_size(17), bold=True)
        btn.bind(on_release=self.on_compute)
        body.add_widget(btn)

        self.out = styled_label("", color=INK, size=14)
        self.out.bind(texture_size=lambda w, *a:
                      setattr(w, 'height', w.texture_size[1] + dp(10)))
        self.out.size_hint_y = None
        body.add_widget(self.out)

        scroll.add_widget(body)
        tab_calc.add_widget(scroll)
        panel.add_widget(tab_calc)

        # ---- TAB 2: Haystack ----
        tab_hay = TabbedPanelItem(text='Haystack')
        hbox = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        hbox.add_widget(styled_label(
            "[b]The haystack[/b] — [color=ff5e6c]red[/color] cells are the "
            "vulnerable files hiding among the safe ones.",
            color=MUTED, size=13, ))
        self.hay = HaystackCanvas(N=200, k=4)
        hbox.add_widget(self.hay)
        self.hay_caption = styled_label("", color=SCAN, size=13,
                                        halign='center')
        self.hay_caption.size_hint_y = None
        self.hay_caption.height = dp(30)
        hbox.add_widget(self.hay_caption)
        tab_hay.add_widget(hbox)
        panel.add_widget(tab_hay)

        # ---- TAB 3: Cost ----
        tab_cost = TabbedPanelItem(text='Cost')
        cbox = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        cbox.add_widget(styled_label(
            "[b]Cost per scanning campaign[/b] (log scale)\n"
            "[color=3fe0c5]teal = Antares[/color]   "
            "[color=ff5e6c]red = frontier model[/color]",
            color=MUTED, size=13))
        self.bars = BarCompare()
        cbox.add_widget(self.bars)
        self.cost_caption = styled_label("", color=INK, size=14,
                                         halign='center')
        self.cost_caption.size_hint_y = None
        self.cost_caption.height = dp(46)
        cbox.add_widget(self.cost_caption)
        tab_cost.add_widget(cbox)
        panel.add_widget(tab_cost)

        # ---- TAB 4: F1 ----
        tab_f1 = TabbedPanelItem(text='F1')
        fbox = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        fbox.add_widget(styled_label(
            "[b]The harmonic squeeze[/b] — F1 vs recall at fixed precision.\n"
            "Accuracy alone is useless when bugs are rare; F1 rewards real "
            "discrimination.", color=MUTED, size=13))
        self.f1c = F1Curve(precision=0.6)
        fbox.add_widget(self.f1c)
        fbox.add_widget(styled_label(
            "x-axis: recall (0→1)   y-axis: F1 (0→1)\n"
            "dashed amber: the precision=recall ideal line",
            color=MUTED, size=12, halign='center'))
        tab_f1.add_widget(fbox)
        panel.add_widget(tab_f1)

        root.add_widget(panel)

        # first paint
        Clock.schedule_once(lambda dt: self.on_compute(None), 0.4)
        return root

    # ------------------------------------------------------ compute handler
    def _get(self, ti, default):
        try:
            return float(ti.text)
        except (ValueError, TypeError):
            return default

    def on_compute(self, *a):
        N = int(self._get(self.in_N, 800))
        k = int(self._get(self.in_k, 4))
        ps = self._get(self.in_ps, 0.0002)
        pb = self._get(self.in_pb, 0.02)
        re = int(self._get(self.in_re, 500))
        tk = self._get(self.in_tk, 100)

        r = compute(N, k, ps, pb, re, tk)

        self.out.text = (
            f"[b][color=3fe0c5]RESULTS[/color][/b]\n\n"
            f"Base rate  P(vuln) = k/N = [b]{r['base_rate']*100:.3f}%[/b]\n"
            f"  → guessing 'safe' everywhere scores "
            f"{(1-r['base_rate'])*100:.2f}% accuracy but catches 0 bugs.\n\n"
            f"Guided search reads only "
            f"[b]{r['guided_pct']*100:.2f}%[/b] of files "
            f"(~{r['guided_files']:.0f} of {N}) at depth 3, p=0.30.\n\n"
            f"[color=3fe0c5]Antares cost[/color]  = "
            f"[b]${r['cost_small']:.2f}[/b]\n"
            f"[color=ff5e6c]Frontier cost[/color] = "
            f"[b]${r['cost_big']:.2f}[/b]\n"
            f"Ratio = [b]{r['cost_ratio']:.0f}x[/b] cheaper for "
            f"comparable accuracy."
        )

        # update graphics tabs
        self.hay.set_data(N, k)
        self.hay_caption.text = (f"{N} files · {k} vulnerable "
                                 f"({r['base_rate']*100:.2f}% base rate)")
        self.bars.set_data(r['cost_small'], r['cost_big'])
        self.cost_caption.text = (
            f"Antares ${r['cost_small']:.2f}   vs   "
            f"Frontier ${r['cost_big']:.2f}\n"
            f"[b]{r['cost_ratio']:.0f}x[/b] cost gap, similar accuracy")
        # precision derived loosely from base rate for illustration
        prec = max(0.2, min(0.9, 0.6))
        self.f1c.set_data(prec)


if __name__ == '__main__':
    AntaresApp().run()
