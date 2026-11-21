"""
TRANSMON QUBIT EXPLORER  -  for Pydroid 3 (Android)
====================================================
An interactive, touch-friendly app that lets you dial in the two
defining energies of a transmon (E_J and E_C) and instantly see:

  * the qubit frequency          w01 = sqrt(8 Ej Ec) - Ec
  * the anharmonicity            alpha ~ -Ec
  * the E_J / E_C ratio          (the single knob that defines the device)
  * the cosine potential well with its unevenly-spaced energy levels
  * the charge-dispersion curves (why big C beats charge noise)

Physics after Koch et al., Phys. Rev. A 76, 042319 (2007).

------------------------------------------------------------------
HOW TO RUN IN PYDROID 3
------------------------------------------------------------------
1. Install Pydroid 3 from the Play Store.
2. Open Pydroid 3 -> menu -> "Pip" tab and install:  kivy   matplotlib   numpy
   (Pydroid usually ships numpy/matplotlib; you mainly need kivy.)
3. Open this file in Pydroid 3 and press the yellow "Run" (play) button.

If Kivy is unavailable, a Tkinter fallback (see transmon_tk.py) works too.
------------------------------------------------------------------
"""

import numpy as np

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex as HEX

# --- matplotlib embedded in Kivy (rendered to PNG, shown as an Image) -----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
import io

# ---- palette (matches the HTML explainer) -------------------------------
BG      = "#0c1830"
PANEL   = "#0a1428"
INK     = "#dbe4f0"
SUPER   = "#5fb7e0"   # superconductor blue
GOLD    = "#d8a24a"
COPPER  = "#c77b3a"
VIOLET  = "#6a4fb0"
MUTED   = "#8b9cb4"

Window.clearcolor = HEX(BG)


# =========================================================================
#  PHYSICS
# =========================================================================
def transmon_levels(Ej, Ec, n_levels=5):
    """Diagonalise the transmon Hamiltonian in the charge basis.
    Returns eigen-energies (GHz-like units, whatever Ej/Ec carry)."""
    N = 40                                   # charge cutoff (-N..N)
    n = np.arange(-N, N + 1)
    dim = len(n)
    # 4 Ec (n - ng)^2 on the diagonal, ng = 0
    H = np.diag(4.0 * Ec * n**2).astype(float)
    # -Ej/2 on the off-diagonals (cos phi couples |n> <-> |n+-1>)
    off = -0.5 * Ej * np.ones(dim - 1)
    H += np.diag(off, 1) + np.diag(off, -1)
    evals = np.linalg.eigvalsh(H)
    return evals[:n_levels]


def transmon_summary(Ej, Ec):
    """Key spectroscopic numbers."""
    E = transmon_levels(Ej, Ec, 4)
    w01 = E[1] - E[0]
    w12 = E[2] - E[1]
    alpha = w12 - w01
    ratio = Ej / Ec
    return dict(w01=w01, w12=w12, alpha=alpha, ratio=ratio, levels=E)


# =========================================================================
#  PLOTTING  ->  returns a Kivy texture
# =========================================================================
def make_figure(Ej, Ec):
    s = transmon_summary(Ej, Ec)
    E = s["levels"]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(4.6, 6.4), dpi=110,
        gridspec_kw={"height_ratios": [1.15, 1]}
    )
    fig.patch.set_facecolor(BG)

    # ---- (A) cosine potential well + energy levels ----------------------
    ax1.set_facecolor(PANEL)
    phi = np.linspace(-np.pi, np.pi, 400)
    U = -Ej * np.cos(phi)
    ax1.plot(phi, U, color=SUPER, lw=2.4)
    # harmonic reference parabola near the bottom
    ax1.plot(phi, -Ej + 0.5 * Ej * phi**2, color=MUTED,
             lw=1.2, ls="--", alpha=0.55)

    labels = ["|0>", "|1>", "|2>", "|3>", "|4>"]
    for i, e in enumerate(E):
        # draw each level only across the classically-allowed width
        w = np.sqrt(max(2.0 * (e + Ej) / Ej, 1e-6))
        w = min(w, np.pi)
        ax1.hlines(e, -w, w, color=GOLD, lw=2.0)
        ax1.text(w + 0.08, e, labels[i], color=GOLD, fontsize=9, va="center")

    ax1.set_title("Cosine well  &  anharmonic levels",
                  color=INK, fontsize=11, pad=8)
    ax1.set_xlabel("phase  phi", color=MUTED, fontsize=9)
    ax1.set_ylabel("energy", color=MUTED, fontsize=9)
    ax1.tick_params(colors=MUTED, labelsize=7)
    for sp in ax1.spines.values():
        sp.set_color(MUTED)

    # ---- (B) charge dispersion: E vs offset charge ng -------------------
    ax2.set_facecolor(PANEL)
    ng = np.linspace(-1, 1, 60)
    band0, band1 = [], []
    N = 40
    n = np.arange(-N, N + 1)
    for g in ng:
        H = np.diag(4.0 * Ec * (n - g) ** 2).astype(float)
        off = -0.5 * Ej * np.ones(len(n) - 1)
        H += np.diag(off, 1) + np.diag(off, -1)
        ev = np.linalg.eigvalsh(H)
        band0.append(ev[0]); band1.append(ev[1])
    band0 = np.array(band0); band1 = np.array(band1)
    # reference to level bottom for clarity
    ax2.plot(ng, band0 - band0.mean(), color=SUPER, lw=2.2, label="|0>")
    ax2.plot(ng, band1 - band1.mean(), color=VIOLET, lw=2.2, label="|1>")
    ax2.set_title("Charge dispersion (flat = noise-immune)",
                  color=INK, fontsize=11, pad=8)
    ax2.set_xlabel("offset charge  ng", color=MUTED, fontsize=9)
    ax2.set_ylabel("energy (centred)", color=MUTED, fontsize=9)
    ax2.tick_params(colors=MUTED, labelsize=7)
    ax2.legend(fontsize=8, facecolor=PANEL, edgecolor=MUTED,
               labelcolor=INK, loc="upper right")
    for sp in ax2.spines.values():
        sp.set_color(MUTED)

    fig.tight_layout(pad=1.2)

    # ---- render to a Kivy texture ---------------------------------------
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return CoreImage(buf, ext="png").texture


# =========================================================================
#  UI
# =========================================================================
class Readout(Label):
    pass


class TransmonApp(App):
    def build(self):
        self.title = "Transmon Qubit Explorer"

        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        # ---- header ------------------------------------------------------
        header = Label(
            text="[b]TRANSMON QUBIT EXPLORER[/b]\n"
                 "[size=12sp][color=8b9cb4]a Josephson junction "
                 "+ a big capacitor[/color][/size]",
            markup=True, halign="center", size_hint_y=None, height=64,
            color=HEX(SUPER),
        )
        root.add_widget(header)

        # ---- sliders -----------------------------------------------------
        controls = GridLayout(cols=1, size_hint_y=None, height=180, spacing=4)

        self.ej = 15.0     # Josephson energy
        self.ec = 0.3      # charging energy

        controls.add_widget(self._slider_row(
            "E_J  (Josephson energy)", 1.0, 40.0, self.ej, self._set_ej))
        controls.add_widget(self._slider_row(
            "E_C  (charging energy)", 0.05, 2.0, self.ec, self._set_ec))
        root.add_widget(controls)

        # ---- numeric readout --------------------------------------------
        self.readout = Label(
            markup=True, halign="center", size_hint_y=None, height=96,
            color=HEX(INK),
        )
        root.add_widget(self.readout)

        # ---- graphics (scrollable so tall figures fit small screens) ----
        scroll = ScrollView(size_hint=(1, 1))
        self.plot = KivyImage(allow_stretch=True, keep_ratio=True,
                              size_hint_y=None)
        self.plot.height = 720
        scroll.add_widget(self.plot)
        root.add_widget(scroll)

        self._refresh()
        return root

    # ---- slider factory --------------------------------------------------
    def _slider_row(self, caption, mn, mx, val, cb):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=64)
        lab = Label(text=caption, color=HEX(GOLD), font_size="13sp",
                    size_hint_y=None, height=22, halign="left")
        lab.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        sld = Slider(min=mn, max=mx, value=val, step=(mx - mn) / 100.0)
        sld.bind(value=cb)
        box.add_widget(lab)
        box.add_widget(sld)
        return box

    def _set_ej(self, _s, v):
        self.ej = float(v); self._refresh()

    def _set_ec(self, _s, v):
        self.ec = float(v); self._refresh()

    # ---- recompute + redraw ---------------------------------------------
    def _refresh(self):
        s = transmon_summary(self.ej, self.ec)
        regime = ("[color=5fb7e0]TRANSMON regime[/color]"
                  if s["ratio"] >= 20 else
                  "[color=c77b3a]charge-qubit regime[/color]")
        self.readout.text = (
            "[b]E_J/E_C = %5.1f[/b]   %s\n"
            "[color=d8a24a]w01[/color] = %6.3f   "
            "[color=d8a24a]w12[/color] = %6.3f\n"
            "[color=6a4fb0]anharmonicity alpha[/color] = %+6.3f  (~ -E_C)"
        ) % (s["ratio"], regime, s["w01"], s["w12"], s["alpha"])

        self.plot.texture = make_figure(self.ej, self.ec)


if __name__ == "__main__":
    TransmonApp().run()
