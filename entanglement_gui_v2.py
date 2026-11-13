# entanglement_gui_v2.py
# Quantum Entanglement Explorer - GUI for Pydroid 3 (Android), with an
# SPDC source diagram drawn in code (no image file needed).
# Requires Kivy (install from Pydroid 3: Pip -> kivy).

import math

from kivy.app import App
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

SQ = 1 / math.sqrt(2)
CUSTOM = "Custom (enter below)"
PRESETS = {
    "Phi+ : (|00>+|11>)/sqrt2": [SQ, 0, 0, SQ],
    "Phi- : (|00>-|11>)/sqrt2": [SQ, 0, 0, -SQ],
    "Psi+ : (|01>+|10>)/sqrt2": [0, SQ, SQ, 0],
    "Psi- : (|01>-|10>)/sqrt2": [0, SQ, -SQ, 0],
    "Product |00>": [1, 0, 0, 0],
    CUSTOM: None,
}

THEORY = """THEORY

Physical source (SPDC):
  A laser pumps a nonlinear crystal. Now and then one photon splits into
  two lower-energy photons. In a type-II crystal the two photons leave on
  two cones with perpendicular polarizations: one horizontal (H), one
  vertical (V). Because we cannot tell which cone a pair came from, the
  pair is in the state (|HV> + |VH>)/sqrt2 = Psi+ (with H=0, V=1).

Two-qubit state:
  |psi> = c00|00> + c01|01> + c10|10> + c11|11>,  sum |cij|^2 = 1

Separability:
  Product state  <=>  det C = c00*c11 - c01*c10 = 0
  Concurrence    C = 2|det C|   (0 = product, 1 = maximally entangled)

Measurement basis at angle t (deg):
  t+ = (cos t/2,  sin t/2)     t- = (-sin t/2,  cos t/2)

Correlation for |Phi+> at angles t (Alice) and p (Bob):
  P(same) = cos^2((t-p)/2),  E = cos(t-p)

Bell/CHSH:
  S = E(a,b) - E(a,b') + E(a',b) + E(a',b')
  Local hidden variables: |S| <= 2
  Quantum maximum:        |S| = 2*sqrt(2) = 2.828  (Tsirelson bound)

No signaling: Bob's local statistics do not depend on Alice's choice,
so entanglement correlates results but cannot send a message.
"""


def normalize(c):
    n = math.sqrt(sum(x * x for x in c))
    if n == 0:
        raise ValueError("state vector cannot be all zeros")
    return [x / n for x in c]


def basis(angle_deg, sign):
    t = math.radians(angle_deg) / 2
    if sign > 0:
        return [math.cos(t), math.sin(t)]
    return [-math.sin(t), math.cos(t)]


def joint_prob(c, va, vb):
    amp = sum(va[i] * vb[j] * c[2 * i + j] for i in range(2) for j in range(2))
    return amp * amp


def outcome_probs(c, a_deg, b_deg):
    out = {}
    for sa in (1, -1):
        for sb in (1, -1):
            out[(sa, sb)] = joint_prob(c, basis(a_deg, sa), basis(b_deg, sb))
    return out


def correlation(c, a_deg, b_deg):
    probs = outcome_probs(c, a_deg, b_deg)
    E = sum(sa * sb * p for (sa, sb), p in probs.items())
    p_same = probs[(1, 1)] + probs[(-1, -1)]
    return E, p_same


def fmt(x):
    return f"{x:+.3f}"


class SPDCDiagram(Widget):
    """Draws the SPDC source: laser, crystal, two photon cones, entangled pair.

    Coordinates u, v are fractions of the widget (0..1), v=1 is the top.
    """

    S = (0.32, 0.77)      # where the pump splits inside the crystal
    H = (0.48, 0.22)      # horizontally polarized photon endpoint
    V = (0.91, 0.28)      # vertically polarized photon endpoint

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.labels = {}
        specs = [
            ("laser", "Laser beam"),
            ("crystal", "Crystal"),
            ("vert", "Vertically-\npolarized photons"),
            ("horiz", "Horizontally-\npolarized photons"),
            ("ent", "Entangled photons"),
        ]
        for key, text in specs:
            lbl = Label(text=text, font_size="12sp", halign="left",
                        size_hint=(None, None), color=(0.92, 0.92, 0.92, 1))
            self.labels[key] = lbl
            self.add_widget(lbl)
        self.bind(pos=self.redraw, size=self.redraw)

    def P(self, u, v):
        return (self.x + u * self.width, self.y + v * self.height)

    def _place(self, key, u, v):
        lbl = self.labels[key]
        lbl.texture_update()
        lbl.size = lbl.texture_size
        x, y = self.P(u, v)
        x = min(x, self.right - lbl.width)
        lbl.pos = (x, y)

    def redraw(self, *args):
        self.canvas.clear()
        S, H, V = self.S, self.H, self.V
        with self.canvas:
            # Translucent cones
            Color(0.3, 0.8, 0.3, 0.22)
            Triangle(points=[*self.P(*S), *self.P(0.93, 0.34), *self.P(0.70, 0.60)])
            Triangle(points=[*self.P(*S), *self.P(0.40, 0.10), *self.P(0.56, 0.40)])
            Ellipse(pos=self.P(0.42, 0.09), size=(0.44 * self.width, 0.30 * self.height))
            Ellipse(pos=self.P(0.45, 0.31), size=(0.42 * self.width, 0.30 * self.height))

            # Crystal
            Color(0.55, 0.80, 0.95, 0.75)
            Rectangle(pos=self.P(0.18, 0.66), size=(0.27 * self.width, 0.18 * self.height))

            # Dashed cone axes
            Color(0.65, 0.65, 0.65, 1)
            Line(points=[*self.P(*S), *self.P(0.66, 0.32)],
                 dash_length=6, dash_offset=4, width=1)
            Line(points=[*self.P(*S), *self.P(0.60, 0.12)],
                 dash_length=6, dash_offset=4, width=1)

            # Entangled photon paths
            Color(0.2, 1.0, 0.2, 1)
            Line(points=[*self.P(*S), *self.P(*H)], width=1.5)
            Line(points=[*self.P(*S), *self.P(*V)], width=1.5)

            # Polarization marks: horizontal arrow for H, vertical arrow for V
            hx, hy = self.P(*H)
            Line(points=[hx - dp(7), hy, hx + dp(7), hy], width=1.2)
            vx, vy = self.P(*V)
            Line(points=[vx, vy - dp(7), vx, vy + dp(7)], width=1.2)

            # Laser beam through the crystal
            Color(0.9, 0.1, 0.1, 1)
            Line(points=[*self.P(0.25, 0.98), *self.P(*S), *self.P(0.71, 0.25)],
                 width=dp(2.5))
            lx, ly = self.P(0.71, 0.25)
            Ellipse(pos=(lx - dp(4), ly - dp(4)), size=(dp(8), dp(8)))

        self._place("laser", 0.00, 0.93)
        self._place("crystal", 0.47, 0.74)
        self._place("vert", 0.62, 0.86)
        self._place("horiz", 0.00, 0.40)
        self._place("ent", 0.45, 0.00)


class EntanglementApp(App):

    def build(self):
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        root.add_widget(Label(
            text="[b]Quantum Entanglement Explorer[/b]", markup=True,
            font_size="20sp", size_hint_y=None, height=44))

        root.add_widget(SPDCDiagram(size_hint_y=None, height=dp(280)))

        form = GridLayout(cols=2, spacing=6, size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.state_spin = Spinner(
            text=list(PRESETS)[0], values=list(PRESETS),
            size_hint_y=None, height=44)
        self.custom = self._field("1,0,0,1")
        self.theta = self._field("0")
        self.phi = self._field("45")
        self.chsh = self._field("0,90,45,135")

        rows = [
            ("State", self.state_spin),
            ("Custom c00,c01,c10,c11", self.custom),
            ("Alice angle (deg)", self.theta),
            ("Bob angle (deg)", self.phi),
            ("CHSH a,a',b,b' (deg)", self.chsh),
        ]
        for text, widget in rows:
            form.add_widget(Label(text=text, size_hint_y=None, height=44))
            form.add_widget(widget)
        root.add_widget(form)

        buttons = BoxLayout(size_hint_y=None, height=50, spacing=6)
        for text, callback in [
            ("Compute", self.compute),
            ("CHSH max", self.chsh_max),
            ("Theory", self.show_theory),
        ]:
            b = Button(text=text)
            b.bind(on_press=callback)
            buttons.add_widget(b)
        root.add_widget(buttons)

        self.out = Label(
            text="", font_size="15sp", halign="left", valign="top",
            size_hint_y=None)
        self.out.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
        self.out.bind(texture_size=lambda w, v: setattr(w, "height", v[1]))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.out)
        root.add_widget(scroll)

        self.compute()
        return root

    def _field(self, text):
        return TextInput(text=text, multiline=False,
                         size_hint_y=None, height=44)

    def compute(self, instance=None):
        try:
            preset = PRESETS[self.state_spin.text]
            if preset is None:
                raw = [float(x) for x in self.custom.text.split(",")]
                if len(raw) != 4:
                    raise ValueError("custom state needs exactly 4 numbers")
                c = normalize(raw)
            else:
                c = normalize(preset)

            th = float(self.theta.text)
            ph = float(self.phi.text)

            parts = [float(x) for x in self.chsh.text.split(",")]
            if len(parts) != 4:
                raise ValueError("CHSH needs exactly 4 angles")
            a, a2, b, b2 = parts
        except ValueError as e:
            self.out.text = f"[Input error] {e}"
            return

        det = c[0] * c[3] - c[1] * c[2]
        entangled = abs(det) > 1e-9
        lines = ["STATE",
                 f"|psi> = {c[0]:.3f}|00> + {c[1]:.3f}|01> + "
                 f"{c[2]:.3f}|10> + {c[3]:.3f}|11>",
                 f"det C = {det:+.4f}",
                 f"Concurrence = {2 * abs(det):.4f}",
                 "=> ENTANGLED" if entangled else "=> PRODUCT (separable)",
                 ""]

        probs = outcome_probs(c, th, ph)
        E, p_same = correlation(c, th, ph)
        lines.append(f"MEASUREMENT  Alice {th:g} deg, Bob {ph:g} deg")
        for (sa, sb), p in probs.items():
            lines.append(f"  A={sa:+d}, B={sb:+d}:  P = {p:.4f}")
        lines.append(f"E = {E:+.4f}   P(same) = {p_same:.4f}   "
                     f"P(diff) = {1 - p_same:.4f}")
        lines.append("")

        e1 = correlation(c, a, b)[0]
        e2 = correlation(c, a, b2)[0]
        e3 = correlation(c, a2, b)[0]
        e4 = correlation(c, a2, b2)[0]
        S = e1 - e2 + e3 + e4
        lines.append("CHSH TEST")
        lines.append(f"E(a,b)={e1:+.4f}  E(a,b')={e2:+.4f}")
        lines.append(f"E(a',b)={e3:+.4f}  E(a',b')={e4:+.4f}")
        lines.append(f"S = {S:+.4f}   (local limit |S| <= 2)")
        if abs(S) > 2 + 1e-9:
            lines.append("=> Violates local hidden variables")
        else:
            lines.append("=> Within the local hidden-variable bound")
        lines.append("|S| bar: " + "#" * int(abs(S) * 20))

        self.out.text = "\n".join(lines)

    def chsh_max(self, instance=None):
        self.chsh.text = "0,90,45,135"
        self.compute()

    def show_theory(self, instance=None):
        self.out.text = THEORY


if __name__ == "__main__":
    EntanglementApp().run()
