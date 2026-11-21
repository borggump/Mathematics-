"""
TRANSMON QUBIT EXPLORER  -  Tkinter edition  (for Pydroid 3)
============================================================
Zero-install version: Tkinter + matplotlib both ship with Pydroid 3,
so this usually runs with no pip step at all.

Dial E_J and E_C with the sliders and watch:
  * the qubit frequency        w01 = sqrt(8 Ej Ec) - Ec
  * the anharmonicity          alpha ~ -Ec
  * the E_J/E_C ratio          (transmon regime when >= ~20)
  * the cosine potential well with its uneven energy levels
  * the charge-dispersion bands (flat bands = charge-noise immunity)

Physics after Koch et al., Phys. Rev. A 76, 042319 (2007).

RUN:  open in Pydroid 3, press the yellow play button.
      In Pydroid, Settings -> "Use matplotlib backend" can be left default;
      this script forces the Tk backend itself.
"""

import numpy as np
import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---- palette (matches the HTML explainer) -------------------------------
BG     = "#0c1830"
PANEL  = "#0a1428"
INK    = "#dbe4f0"
SUPER  = "#5fb7e0"
GOLD   = "#d8a24a"
COPPER = "#c77b3a"
VIOLET = "#6a4fb0"
MUTED  = "#8b9cb4"

N_CHARGE = 40   # charge-basis cutoff (-N..N)


# =========================================================================
#  PHYSICS
# =========================================================================
def hamiltonian(Ej, Ec, ng=0.0):
    n = np.arange(-N_CHARGE, N_CHARGE + 1)
    H = np.diag(4.0 * Ec * (n - ng) ** 2).astype(float)
    off = -0.5 * Ej * np.ones(len(n) - 1)
    return H + np.diag(off, 1) + np.diag(off, -1)


def levels(Ej, Ec, k=5, ng=0.0):
    return np.linalg.eigvalsh(hamiltonian(Ej, Ec, ng))[:k]


def summary(Ej, Ec):
    E = levels(Ej, Ec, 4)
    w01 = E[1] - E[0]
    w12 = E[2] - E[1]
    return dict(w01=w01, w12=w12, alpha=w12 - w01,
                ratio=Ej / Ec, levels=E)


# =========================================================================
#  APP
# =========================================================================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Transmon Qubit Explorer")
        root.configure(bg=BG)

        self.ej = tk.DoubleVar(value=15.0)
        self.ec = tk.DoubleVar(value=0.30)

        # ---- header -----------------------------------------------------
        tk.Label(root, text="TRANSMON QUBIT EXPLORER",
                 bg=BG, fg=SUPER, font=("Helvetica", 15, "bold")
                 ).pack(pady=(8, 0))
        tk.Label(root, text="a Josephson junction  +  a big capacitor",
                 bg=BG, fg=MUTED, font=("Helvetica", 10)).pack()

        # ---- sliders ----------------------------------------------------
        self._slider("E_J  (Josephson energy)", self.ej, 1.0, 40.0)
        self._slider("E_C  (charging energy)", self.ec, 0.05, 2.0)

        # ---- numeric readout --------------------------------------------
        self.readout = tk.Label(root, bg=PANEL, fg=INK, justify="center",
                                font=("Courier", 11), padx=8, pady=8)
        self.readout.pack(fill="x", padx=10, pady=6)

        # ---- figure -----------------------------------------------------
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2, 1, figsize=(4.4, 6.0), dpi=100,
            gridspec_kw={"height_ratios": [1.15, 1]})
        self.fig.patch.set_facecolor(BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True,
                                         padx=6, pady=6)

        self.refresh()

    # ---- widgets --------------------------------------------------------
    def _slider(self, caption, var, lo, hi):
        tk.Label(self.root, text=caption, bg=BG, fg=GOLD,
                 font=("Helvetica", 11), anchor="w"
                 ).pack(fill="x", padx=12, pady=(6, 0))
        s = tk.Scale(self.root, variable=var, from_=lo, to=hi,
                     resolution=(hi - lo) / 100.0, orient="horizontal",
                     bg=BG, fg=INK, troughcolor=PANEL,
                     highlightthickness=0, showvalue=True,
                     command=lambda *_: self.refresh())
        s.pack(fill="x", padx=12)

    # ---- recompute + redraw --------------------------------------------
    def refresh(self):
        Ej, Ec = self.ej.get(), self.ec.get()
        s = summary(Ej, Ec)
        regime = "TRANSMON regime" if s["ratio"] >= 20 else "charge-qubit regime"
        self.readout.config(
            text=("E_J/E_C = %5.1f      %s\n"
                  "w01 = %6.3f     w12 = %6.3f\n"
                  "anharmonicity alpha = %+6.3f   (~ -E_C = %+6.3f)")
            % (s["ratio"], regime, s["w01"], s["w12"], s["alpha"], -Ec))

        self._draw_well(Ej, Ec, s["levels"])
        self._draw_dispersion(Ej, Ec)
        self.fig.tight_layout(pad=1.1)
        self.canvas.draw()

    def _draw_well(self, Ej, Ec, E):
        ax = self.ax1
        ax.clear(); ax.set_facecolor(PANEL)
        phi = np.linspace(-np.pi, np.pi, 400)
        ax.plot(phi, -Ej * np.cos(phi), color=SUPER, lw=2.2)
        ax.plot(phi, -Ej + 0.5 * Ej * phi**2, color=MUTED,
                lw=1.1, ls="--", alpha=0.5)
        for i, e in enumerate(E):
            w = min(np.sqrt(max(2.0 * (e + Ej) / Ej, 1e-6)), np.pi)
            ax.hlines(e, -w, w, color=GOLD, lw=1.8)
            ax.text(w + 0.08, e, "|%d>" % i, color=GOLD, fontsize=8,
                    va="center")
        ax.set_title("Cosine well & anharmonic levels",
                     color=INK, fontsize=10)
        ax.set_xlabel("phase  phi", color=MUTED, fontsize=8)
        self._style(ax)

    def _draw_dispersion(self, Ej, Ec):
        ax = self.ax2
        ax.clear(); ax.set_facecolor(PANEL)
        ng = np.linspace(-1, 1, 50)
        b0, b1 = [], []
        for g in ng:
            ev = np.linalg.eigvalsh(hamiltonian(Ej, Ec, g))
            b0.append(ev[0]); b1.append(ev[1])
        b0 = np.array(b0); b1 = np.array(b1)
        ax.plot(ng, b0 - b0.mean(), color=SUPER, lw=2.0, label="|0>")
        ax.plot(ng, b1 - b1.mean(), color=VIOLET, lw=2.0, label="|1>")
        ax.set_title("Charge dispersion (flat = noise-immune)",
                     color=INK, fontsize=10)
        ax.set_xlabel("offset charge  ng", color=MUTED, fontsize=8)
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=MUTED,
                  labelcolor=INK)
        self._style(ax)

    def _style(self, ax):
        ax.tick_params(colors=MUTED, labelsize=7)
        for sp in ax.spines.values():
            sp.set_color(MUTED)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
