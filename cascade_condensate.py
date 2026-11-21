"""
Cascade & Condensate
Twisted Trilayer Graphene explorer for Pydroid 3 (Android)

Requires: kivy  (Pydroid 3 -> Pip -> install "kivy")
Run:      Pydroid 3 -> open this file -> Run

Schematic curves based on standard magic-angle phenomenology.
Not digitized from Hoke et al., Nat. Nanotechnol. 21, 772-778 (2026).
"""

import math

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

# ----------------------------------------------------------------- palette
INK      = (0.051, 0.106, 0.118, 1)
PAPER    = (0.910, 0.894, 0.855, 1)
PANEL    = (0.957, 0.945, 0.914, 1)
GRAPHITE = (0.227, 0.271, 0.282, 1)
COPPER   = (0.710, 0.396, 0.114, 1)
CYAN     = (0.122, 0.478, 0.549, 1)
VIOLET   = (0.357, 0.294, 0.541, 1)

Window.clearcolor = PAPER

# ----------------------------------------------------------------- physics
A_GRAPHENE = 0.246          # nm
W_TUNNEL   = 110.0          # meV
HVF_KD     = 9800.0         # meV, hbar*vF*k_D  (vF ~ 1e6 m/s)

INTS = [-3, -2, -1, 0, 1, 2, 3]
NU_MIN, NU_MAX = -3.6, 3.6


def moire_period(theta_deg):
    """lambda_m = a / (2 sin(theta/2))  [nm]"""
    t = math.radians(theta_deg)
    return A_GRAPHENE / (2.0 * math.sin(t / 2.0))


def cell_area(theta_deg):
    """A_m = (sqrt3/2) lambda_m^2  [nm^2]"""
    return (math.sqrt(3) / 2.0) * moire_period(theta_deg) ** 2


def full_filling_density(theta_deg):
    """n_s = 4/A_m  ->  cm^-2"""
    return 4.0 / cell_area(theta_deg) * 1e14      # nm^-2 -> cm^-2


def alpha_param(theta_deg, layers=3):
    """alpha = w / (hbar vF k_theta); trilayer boosts w by sqrt(2)."""
    t = math.radians(theta_deg)
    k_theta = 2.0 * math.sin(t / 2.0)             # in units of k_D
    w = W_TUNNEL * (math.sqrt(2) if layers == 3 else 1.0)
    return w / (HVF_KD * k_theta)


def coulomb_U(theta_deg, eps_r=4.0):
    """U ~ e^2 / (4 pi eps lambda_m)  [meV]; e^2/(4 pi eps0) = 1440 meV*nm"""
    return 1440.0 / (eps_r * moire_period(theta_deg))


def _gauss(x, mu, s):
    return math.exp(-((x - mu) ** 2) / (2.0 * s * s))


def rho(v):
    """Resistivity: peaks at integer nu, largest at 0 and +-2."""
    r = 0.06
    for i in INTS:
        amp = 0.95 if i == 0 else (0.80 if abs(i) == 2 else 0.42)
        r += amp * _gauss(v, i, 0.13)
    return r


def dmudn(v):
    """Inverse compressibility: spike at integer, negative-kappa flanks."""
    s = 0.0
    for i in INTS:
        s += 1.00 * _gauss(v, i, 0.10)
        s -= 0.55 * _gauss(v, i + 0.42, 0.24)
        s -= 0.55 * _gauss(v, i - 0.42, 0.24)
    return s


def tc(v):
    """Superconducting domes: on the flanks, never on the integers."""
    domes = ((-2.55, 0.62), (-1.55, 0.42), (1.55, 0.42),
             (2.55, 0.62), (-2.45, 0.30), (2.45, 0.30))
    return max(a * _gauss(v, c, 0.30) for c, a in domes)


def phase_at(v):
    if tc(v) > 0.18:
        return "superconducting", COPPER
    if dmudn(v) > 0.45:
        return "incompressible / insulator", VIOLET
    if dmudn(v) < -0.20:
        return "kappa < 0 / cascade flank", CYAN
    return "metallic", GRAPHITE


# ------------------------------------------------------- moire canvas
class MoireView(Widget):
    """Live interference of three triangular lattices."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.theta = 1.55
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(self._redraw, 0)

    def set_theta(self, t):
        self.theta = t
        self._redraw()

    def _lines(self, ang, a, alpha):
        """One triangular lattice = three line families at 0/60/120 deg."""
        cx, cy = self.center
        R = math.hypot(self.width, self.height) * 0.6
        Color(INK[0], INK[1], INK[2], alpha)
        for k in range(3):
            phi = ang + k * math.pi / 3.0
            c, s = math.cos(phi), math.sin(phi)
            n = int(R / a) + 1
            for j in range(-n, n + 1):
                off = j * a
                # line through (cx - s*off, cy + c*off) along (c, s)
                px, py = cx - s * off, cy + c * off
                Line(points=[px - c * R, py - s * R,
                             px + c * R, py + s * R], width=0.9)

    def _redraw(self, *_):
        self.canvas.clear()
        if self.width < 2:
            return
        a = dp(15)
        rad = math.radians(self.theta)
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=self.pos, size=self.size)
            self._lines(0.0, a, 0.20)     # layer 1
            self._lines(rad, a, 0.20)     # layer 2, twisted
            self._lines(0.0, a, 0.06)     # layer 3, aligned with 1


# ------------------------------------------------------- stacked panel
class StackView(Widget):
    """Three lanes on one shared nu axis. Touch to probe."""

    def __init__(self, readout, **kw):
        super().__init__(**kw)
        self.readout = readout
        self.hover = None
        self.bind(pos=self._redraw, size=self._redraw)
        Clock.schedule_once(self._redraw, 0)

    # -- geometry
    def _x(self, v):
        L, R = self.x + dp(30), self.right - dp(10)
        return L + (v - NU_MIN) / (NU_MAX - NU_MIN) * (R - L)

    def _v(self, px):
        L, R = self.x + dp(30), self.right - dp(10)
        return NU_MIN + (px - L) / (R - L) * (NU_MAX - NU_MIN)

    # -- touch
    def on_touch_down(self, t):
        if self.collide_point(*t.pos):
            self._probe(t.x)
            return True
        return super().on_touch_down(t)

    def on_touch_move(self, t):
        if self.collide_point(*t.pos):
            self._probe(t.x)
            return True
        return super().on_touch_move(t)

    def _probe(self, px):
        v = max(NU_MIN, min(NU_MAX, self._v(px)))
        self.hover = v
        name, col = phase_at(v)
        sign = "+" if v >= 0 else ""
        self.readout.text = f"[b]nu = {sign}{v:.2f}[/b]   {name}"
        self.readout.color = col
        self._redraw()

    # -- curve plotting
    def _curve(self, fn, y0, y1, scale, rgb, signed=False):
        L, R = self.x + dp(30), self.right - dp(10)
        n = 240
        pts = []
        if signed:
            mid = (y0 + y1) / 2.0
            half = (y1 - y0) / 2.0 * 0.92
            for i in range(n + 1):
                px = L + (R - L) * i / n
                y = mid + fn(self._v(px)) / scale * half
                pts += [px, y]
            Color(0.05, 0.11, 0.12, 0.22)
            Line(points=[L, mid, R, mid], width=0.8)
        else:
            h = (y1 - y0) * 0.90
            for i in range(n + 1):
                px = L + (R - L) * i / n
                y = y0 + fn(self._v(px)) / scale * h
                pts += [px, y]
        Color(rgb[0], rgb[1], rgb[2], 1)
        Line(points=pts, width=dp(1.1))

    def _redraw(self, *_):
        self.canvas.clear()
        if self.width < 2:
            return
        H = self.height
        # lane boundaries, bottom-up (Kivy y grows upward)
        lanes = [
            (self.y + H * 0.68, self.y + H * 0.99),   # rho
            (self.y + H * 0.36, self.y + H * 0.64),   # dmu/dn
            (self.y + H * 0.07, self.y + H * 0.31),   # Tc
        ]
        with self.canvas:
            Color(*PANEL)
            Rectangle(pos=self.pos, size=self.size)

            # integer guide lines
            for i in INTS:
                Color(VIOLET[0], VIOLET[1], VIOLET[2], 0.45 if i == 0 else 0.25)
                Line(points=[self._x(i), self.y + dp(16),
                             self._x(i), self.top - dp(2)], width=0.8)

            # touch crosshair
            if self.hover is not None:
                Color(COPPER[0], COPPER[1], COPPER[2], 0.85)
                Line(points=[self._x(self.hover), self.y + dp(16),
                             self._x(self.hover), self.top - dp(2)],
                     width=dp(1.3))

            self._curve(rho,   lanes[0][0], lanes[0][1], 1.05, GRAPHITE)
            self._curve(dmudn, lanes[1][0], lanes[1][1], 1.15, CYAN, signed=True)
            self._curve(tc,    lanes[2][0], lanes[2][1], 0.70, COPPER)


# ------------------------------------------------------- helpers
def head(text, size=17, color=INK, bold=True):
    return Label(text=text, markup=True, font_size=sp(size), bold=bold,
                 color=color, size_hint_y=None, halign="left",
                 valign="middle", height=dp(28),
                 text_size=(Window.width - dp(28), None))


def para(text, size=13, color=GRAPHITE):
    lbl = Label(text=text, markup=True, font_size=sp(size), color=color,
                size_hint_y=None, halign="left", valign="top")
    lbl.bind(width=lambda s, w: setattr(s, "text_size", (w, None)))
    lbl.bind(texture_size=lambda s, ts: setattr(s, "height", ts[1] + dp(6)))
    return lbl


def eyebrow(text):
    return Label(text=f"[b]{text}[/b]", markup=True, font_size=sp(10),
                 color=COPPER, size_hint_y=None, height=dp(20),
                 halign="left", valign="middle",
                 text_size=(Window.width - dp(28), None))


# ------------------------------------------------------- tab 1: lattice
class LatticeTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(8), **kw)

        self.add_widget(eyebrow("TWIST THE MIDDLE LAYER"))
        self.moire = MoireView(size_hint_y=0.52)
        self.add_widget(self.moire)

        self.theta_lbl = Label(text="", markup=True, font_size=sp(13),
                               color=INK, size_hint_y=None, height=dp(26))
        self.add_widget(self.theta_lbl)

        sl = Slider(min=0.40, max=4.00, value=1.55, step=0.01,
                    size_hint_y=None, height=dp(44),
                    cursor_size=(dp(28), dp(28)))
        sl.bind(value=self._on_theta)
        self.add_widget(sl)

        self.derived = Label(text="", markup=True, font_size=sp(12),
                             color=GRAPHITE, size_hint_y=None, height=dp(150),
                             halign="left", valign="top")
        self.derived.bind(width=lambda s, w:
                          setattr(s, "text_size", (w - dp(8), None)))
        self.add_widget(self.derived)

        self._on_theta(None, 1.55)

    def _on_theta(self, _, t):
        self.moire.set_theta(t)
        lam = moire_period(t)
        ns = full_filling_density(t)
        al = alpha_param(t, layers=3)
        U = coulomb_U(t)
        W = max(2.0, 60.0 * abs(al - 0.605) + 4.0)   # crude bandwidth proxy
        flat = "FLAT BAND -- interactions dominate" if abs(al - 0.605) < 0.06 \
               else "dispersive"
        col = "b5651d" if abs(al - 0.605) < 0.06 else "3a4548"

        self.theta_lbl.text = f"[b]theta = {t:.2f} deg[/b]"
        self.derived.text = (
            f"[b]lambda_m[/b] = a / 2 sin(theta/2)   = [b]{lam:.2f} nm[/b]\n"
            f"[b]A_m[/b]      = (sqrt3/2) lambda_m^2 = {cell_area(t):.1f} nm^2\n"
            f"[b]n_s[/b]      = 4 / A_m              = {ns:.2e} cm^-2\n\n"
            f"[b]alpha[/b] = sqrt2 w / (hbar vF k_theta) = "
            f"[color=#{col}][b]{al:.3f}[/b][/color]\n"
            f"     magic angle at alpha ~ 0.605\n\n"
            f"[b]U[/b] ~ e^2 / 4 pi eps lambda_m = {U:.1f} meV\n"
            f"[b]W[/b] ~ {W:.1f} meV   ->   U/W = {U/W:.2f}\n\n"
            f"[color=#{col}][b]{flat}[/b][/color]"
        )


# ------------------------------------------------------- tab 2: panel
class PanelTab(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(6), **kw)

        self.add_widget(eyebrow("DRAG ACROSS THE PANEL"))

        self.readout = Label(text="[b]nu = --[/b]   touch to probe",
                             markup=True, font_size=sp(12), color=GRAPHITE,
                             size_hint_y=None, height=dp(26))
        self.add_widget(self.readout)

        self.add_widget(StackView(self.readout, size_hint_y=0.60))

        axis = Label(text="  ".join(f"{i:+d}" if i else " 0" for i in INTS),
                     font_size=sp(10), color=GRAPHITE,
                     size_hint_y=None, height=dp(18))
        self.add_widget(axis)

        legend = Label(
            markup=True, font_size=sp(11), size_hint_y=None, height=dp(78),
            halign="left", valign="top", color=INK,
            text=("[color=#3a4548]---[/color] rho  resistivity\n"
                  "[color=#1f7a8c]---[/color] d(mu)/dn  inverse compressibility\n"
                  "[color=#b5651d]---[/color] T_c  superconducting domes\n"
                  "[color=#5b4b8a]---[/color] integer nu  flavor reset"))
        legend.bind(width=lambda s, w:
                    setattr(s, "text_size", (w - dp(8), None)))
        self.add_widget(legend)


# ------------------------------------------------------- tab 3: theory
class TheoryTab(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw)
        box = BoxLayout(orientation="vertical", padding=dp(14),
                        spacing=dp(10), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        box.add_widget(head("Trilayer decomposes exactly"))
        box.add_widget(para(
            "Mirror symmetry rotates the outer layers into parity eigenstates,\n"
            "    psi_pm = (psi_1 +- psi_3) / sqrt2\n\n"
            "Only psi_+ couples to the middle layer, with strength sqrt2 w:\n\n"
            "    H = H_TBG(sqrt2 w)  (+)  H_Dirac\n\n"
            "Two consequences. The magic angle shifts up by sqrt2, to ~1.5 deg. "
            "And the spectator Dirac cone screens, weakening the correlated "
            "insulators while leaving superconductivity robust and tunable by "
            "displacement field D."))

        box.add_widget(head("The claim"))
        box.add_widget(para(
            "Let nu_SC be where T_c > 0, nu_CI the integer fillings with a gap, "
            "and nu_osc the domain of compressibility oscillations. Then:\n\n"
            "    nu_SC  is a subset of  nu_osc\n"
            "    nu_SC  intersect  nu_CI  =  empty\n\n"
            "Superconductivity tracks the cascade -- flavor symmetry breaking "
            "and Fermi-surface reconstruction -- not the insulator. Screen the "
            "insulators away and the superconductor survives untouched."))

        box.add_widget(head("Why the flanks"))
        box.add_widget(para(
            "[b]Density of states.[/b] On the flank the reconstructed Fermi "
            "surface sweeps a van Hove singularity. In BCS,\n\n"
            "    T_c ~ Theta exp[ -1 / N(0) V ]\n\n"
            "so a peak in N(0) enhances T_c exponentially.\n\n"
            "[b]Fluctuations.[/b] The cascade is a symmetry-breaking "
            "transition, so soft flavor and valley modes live near it. The RPA "
            "pairing vertex\n\n"
            "    Gamma(q,w) ~ g^2 chi_0 / (1 - g chi_0)\n\n"
            "diverges as g chi_0 -> 1, the Stoner condition, met exactly where "
            "the compressibility goes anomalous. Both mechanisms predict the "
            "same thing: superconductivity lives adjacent to the ordered "
            "state, never on top of it."))

        box.add_widget(head("Verdict", color=COPPER))
        box.add_widget(para(
            "[b]This is not a doped Mott insulator.[/b] It is a Fermi-liquid "
            "instability on the surfaces left behind by the cascade. The "
            "insulator and the superconductor are siblings, not parent and "
            "child.", size=14, color=INK))

        box.add_widget(para(
            "\nSummary of: Hoke, J. C. et al. Link between thermodynamic "
            "correlation signatures and superconductivity in twisted trilayer "
            "graphene. Nat. Nanotechnol. 21, 772-778 (2026).\n"
            "Curves are schematic, from standard magic-angle phenomenology -- "
            "not digitized from the paper.\n"
            "Lineage: Cao 2018 / Saito 2020 / Stepanov 2020 / Xiao 2026.",
            size=10))

        self.add_widget(box)


# ------------------------------------------------------- app
class CascadeApp(App):
    title = "Cascade & Condensate"

    def build(self):
        root = BoxLayout(orientation="vertical")

        bar = Label(
            text="[b]Cascade & Condensate[/b]   twisted trilayer graphene",
            markup=True, font_size=sp(13), color=INK,
            size_hint_y=None, height=dp(38))
        root.add_widget(bar)

        tabs = TabbedPanel(do_default_tab=False, tab_pos="bottom_mid",
                           tab_height=dp(44), background_color=PAPER)

        for name, widget in (("lattice", LatticeTab()),
                             ("panel", PanelTab()),
                             ("theory", TheoryTab())):
            item = TabbedPanelItem(text=name, font_size=sp(12))
            item.add_widget(widget)
            tabs.add_widget(item)

        root.add_widget(tabs)
        return root


if __name__ == "__main__":
    CascadeApp().run()
