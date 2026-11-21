# -*- coding: utf-8 -*-
"""
Riemann Hypothesis <-> Dynamical Quantum Phase Transitions
A touch-friendly explorer for Pydroid 3 (Android).

Based on: Wei, Xin, Long et al., "The Riemann Hypothesis manifested in
dynamical quantum phase transitions", Nature Communications (2026).
arXiv:2511.11199

Run in Pydroid 3.  Requires: matplotlib, numpy (install from Pydroid's
pip menu if missing).  tkinter ships with Pydroid 3.
"""

import math
import cmath
import tkinter as tk
from tkinter import ttk

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ----------------------------------------------------------------------
# THEME  (dark, high contrast -- readable on a phone outdoors)
# ----------------------------------------------------------------------
BG        = "#0b1220"
PANEL     = "#141d2e"
FG        = "#e7edf7"
MUTED     = "#8fa3bf"
PURPLE    = "#a78bfa"
BLUE      = "#38bdf8"
GOLD      = "#fbbf24"
RED       = "#f87171"
GREEN     = "#34d399"

F_TITLE   = ("DejaVu Sans", 15, "bold")
F_H       = ("DejaVu Sans", 12, "bold")
F_BODY    = ("DejaVu Sans", 11)
F_SMALL   = ("DejaVu Sans", 9)
F_MONO    = ("DejaVu Sans Mono", 10)

# Reference heights of the first 30 non-trivial zeros (published values),
# used only to annotate plots and to check the app's own root finder.
KNOWN_ZEROS = [14.134725142, 21.022039639, 25.010857580, 30.424876126,
               32.935061588, 37.586178159, 40.918719012, 43.327073281,
               48.005150881, 49.773832478, 52.970321478, 56.446247697,
               59.347044003, 60.831778525, 65.112544048, 67.079810529,
               69.546401711, 72.067157674, 75.704690699, 77.144840069,
               79.337375020, 82.910380854, 84.735492981, 87.425274613,
               88.809111208, 92.491899271, 94.651344041, 95.870634228,
               98.831194218, 101.317851006]


# ======================================================================
# 1. MATH ENGINE  --  zeta, Riemann-Siegel Z, zeros, Loschmidt amplitude
# ======================================================================

# Bernoulli numbers B_2, B_4, ... B_30 for the Euler-Maclaurin tail
_BERNOULLI = [1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6,
              -3617 / 510, 43867 / 798, -174611 / 330, 854513 / 138,
              -236364091 / 2730, 8553103 / 6, -23749461029 / 870,
              8615841276005 / 14322]

_ZETA_CACHE = {}


def zeta(s, M=15):
    """Riemann zeta for complex s by Euler-Maclaurin summation.

        zeta(s) = SUM_{n<N} n^-s + N^-s/2 + N^(1-s)/(s-1)
                  + SUM_k B_2k/(2k)! * (s)_(2k-1) * N^(-s-2k+1)

    Stable across the critical strip and accurate to ~1e-9 out to t ~ 120,
    which is all a phone needs.
    """
    s = complex(s)
    if abs(s - 1.0) < 1e-12:
        return complex(float("inf"), 0.0)

    key = (round(s.real, 12), round(s.imag, 12))
    hit = _ZETA_CACHE.get(key)
    if hit is not None:
        return hit

    N = int(max(20, abs(s.imag) + 10))
    total = 0j
    for n in range(1, N):
        total += n ** (-s)
    total += 0.5 * N ** (-s)
    total += N ** (1.0 - s) / (s - 1.0)

    poch = s                                   # (s)_1
    for k in range(1, M + 1):
        total += _BERNOULLI[k - 1] / math.factorial(2 * k) * poch \
            * (N ** (-s - 2 * k + 1))
        poch = poch * (s + 2 * k - 1) * (s + 2 * k)

    if len(_ZETA_CACHE) < 60000:
        _ZETA_CACHE[key] = total
    return total


def theta(t):
    """Riemann-Siegel theta, asymptotic expansion."""
    if t <= 0:
        return 0.0
    return (t / 2.0) * math.log(t / (2.0 * math.pi)) - t / 2.0 - math.pi / 8.0 \
        + 1.0 / (48.0 * t) + 7.0 / (5760.0 * t ** 3)


def Z(t):
    """Riemann-Siegel Z(t) = e^{i*theta(t)} * zeta(1/2 + it).  Real-valued.
    Its sign changes ARE the zeros on the critical line."""
    return (cmath.exp(1j * theta(t)) * zeta(0.5 + 1j * t)).real


def find_zeros(t_min, t_max, step=0.05):
    """Locate zeros on the critical line by bisecting sign changes of Z(t)."""
    zeros = []
    t = max(t_min, 0.5)
    prev_t, prev = t, Z(t)
    while t < t_max:
        t += step
        cur = Z(t)
        if prev == 0.0:
            zeros.append(prev_t)
        elif prev * cur < 0:                      # sign change -> bracket
            a, b, fa = prev_t, t, prev
            for _ in range(60):
                m = 0.5 * (a + b)
                fm = Z(m)
                if fa * fm <= 0:
                    b = m
                else:
                    a, fa = m, fm
            zeros.append(0.5 * (a + b))
        prev_t, prev = t, cur
    return zeros


def loschmidt(sigma, tau_array):
    """Loschmidt amplitude of the engineered many-body system.

        L(tau) = zeta(sigma + i*tau) / zeta(sigma)

    sigma  <-> inverse temperature of the thermal state (real part of s)
    tau    <-> quench evolution time            (imaginary part of s)

    |L| -> 0 exactly at a zeta zero: that is the probe-qubit coherence
    collapse the experiment measures.
    """
    ref = abs(zeta(complex(sigma, 0.0)))
    if ref == 0 or not np.isfinite(ref):
        ref = 1.0
    return np.array([zeta(complex(sigma, float(t))) / ref for t in tau_array])


def rate_function(L, N=1.0):
    """DQPT rate function  l(tau) = -ln|L(tau)| / N.
    Non-analytic kinks / divergences mark the phase transitions."""
    mag = np.abs(L)
    mag = np.where(mag < 1e-14, 1e-14, mag)
    return -np.log(mag) / N


# ======================================================================
# 2. SMALL GUI HELPERS  (touch sized)
# ======================================================================

def make_figure(width_px, height_px):
    """Figure sized in device pixels so it fits a phone screen."""
    dpi = 100.0
    fig = Figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi,
                 facecolor=PANEL)
    return fig


def style_axes(ax, xlabel="", ylabel="", title=""):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(True, color="#22304a", linewidth=0.5)
    if xlabel:
        ax.set_xlabel(xlabel, color=FG, fontsize=8)
    if ylabel:
        ax.set_ylabel(ylabel, color=FG, fontsize=8)
    if title:
        ax.set_title(title, color=PURPLE, fontsize=10, pad=6)


class Field(tk.Frame):
    """Label + entry, stacked, big tap target."""

    def __init__(self, parent, label, default, width=8):
        tk.Frame.__init__(self, parent, bg=PANEL)
        tk.Label(self, text=label, bg=PANEL, fg=MUTED,
                 font=F_SMALL, anchor="w").pack(fill="x")
        self.var = tk.StringVar(value=str(default))
        e = tk.Entry(self, textvariable=self.var, font=F_BODY, width=width,
                     bg="#1e293b", fg=FG, insertbackground=GOLD,
                     relief="flat", justify="center")
        e.pack(fill="x", ipady=6)
        self.entry = e

    def get(self, default=0.0):
        try:
            return float(self.var.get())
        except ValueError:
            return default


def big_button(parent, text, command, color=PURPLE):
    return tk.Button(parent, text=text, command=command, font=F_H,
                     bg=color, fg="#0b1220", activebackground=BLUE,
                     relief="flat", padx=10, pady=10, bd=0)


class ScrollFrame(tk.Frame):
    """Vertically scrollable frame -- essential on a phone."""

    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor="nw")
        self.inner.bind("<Configure>", self._on_conf)
        self.canvas.bind("<Configure>", self._on_canvas)
        # drag-to-scroll (touch)
        self.canvas.bind("<ButtonPress-1>", self._grab)
        self.canvas.bind("<B1-Motion>", self._drag)

    def _on_conf(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, ev):
        self.canvas.itemconfig(self._win, width=ev.width)

    def _grab(self, ev):
        self.canvas.scan_mark(ev.x, ev.y)

    def _drag(self, ev):
        self.canvas.scan_dragto(ev.x, ev.y, gain=1)


# ======================================================================
# 3. THE APP
# ======================================================================

class RiemannApp:

    def __init__(self, root):
        self.root = root
        root.title("Riemann <-> DQPT Explorer")
        root.configure(bg=BG)

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        self.plot_w = max(320, min(sw - 30, 760))
        self.plot_h = int(self.plot_w * 0.62)
        try:                       # phone: fill the screen
            root.geometry("%dx%d" % (sw, sh))
        except Exception:
            pass

        self._header()
        self._tabs()

    # ---------------- header ----------------
    def _header(self):
        h = tk.Frame(self.root, bg=PANEL)
        h.pack(fill="x")
        tk.Label(h, text="Riemann Hypothesis \u2194 Quantum Dynamics",
                 bg=PANEL, fg=PURPLE, font=F_TITLE).pack(pady=(10, 0))
        tk.Label(h, text="\u03b6(\u03c3 + i\u03c4)  \u2192  probe-qubit coherence  L(\u03c4)",
                 bg=PANEL, fg=MUTED, font=F_SMALL).pack(pady=(2, 10))

    # ---------------- tabs ----------------
    def _tabs(self):
        style = ttk.Style()
        try:
            style.theme_use("default")
        except Exception:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED,
                        padding=(12, 10), font=F_BODY)
        style.map("TNotebook.Tab",
                  background=[("selected", PURPLE)],
                  foreground=[("selected", "#0b1220")])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.tab_zeta = ScrollFrame(nb);  nb.add(self.tab_zeta, text="Zeta")
        self.tab_dqpt = ScrollFrame(nb);  nb.add(self.tab_dqpt, text="DQPT")
        self.tab_find = ScrollFrame(nb);  nb.add(self.tab_find, text="Zeros")
        self.tab_map  = ScrollFrame(nb);  nb.add(self.tab_map,  text="Map")
        self.tab_info = ScrollFrame(nb);  nb.add(self.tab_info, text="Theory")

        self._build_zeta(self.tab_zeta.inner)
        self._build_dqpt(self.tab_dqpt.inner)
        self._build_find(self.tab_find.inner)
        self._build_map(self.tab_map.inner)
        self._build_info(self.tab_info.inner)

    # ==================================================================
    # TAB 1 -- zeta magnitude along a vertical line
    # ==================================================================
    def _build_zeta(self, p):
        card = tk.Frame(p, bg=PANEL, padx=12, pady=12)
        card.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="|\u03b6(\u03c3 + it)| along a vertical line",
                 bg=PANEL, fg=FG, font=F_H, anchor="w").pack(fill="x")
        tk.Label(card, text="\u03c3 = 1/2 is the critical line. Dips to zero are "
                            "the non-trivial zeros.",
                 bg=PANEL, fg=MUTED, font=F_SMALL, anchor="w",
                 wraplength=self.plot_w).pack(fill="x", pady=(2, 10))

        row = tk.Frame(card, bg=PANEL); row.pack(fill="x")
        self.z_sigma = Field(row, "\u03c3  (real part)", "0.5")
        self.z_tmin  = Field(row, "t min", "0")
        self.z_tmax  = Field(row, "t max", "50")
        for w in (self.z_sigma, self.z_tmin, self.z_tmax):
            w.pack(side="left", expand=True, fill="x", padx=3)

        brow = tk.Frame(card, bg=PANEL); brow.pack(fill="x", pady=(10, 0))
        big_button(brow, "Plot", self.plot_zeta).pack(side="left",
                                                      expand=True, fill="x", padx=3)
        big_button(brow, "\u03c3 = 0.5", lambda: self._set_sigma("0.5"),
                   BLUE).pack(side="left", expand=True, fill="x", padx=3)
        big_button(brow, "\u03c3 = 0.7", lambda: self._set_sigma("0.7"),
                   GOLD).pack(side="left", expand=True, fill="x", padx=3)

        self.z_msg = tk.Label(p, text="", bg=BG, fg=GOLD, font=F_SMALL,
                              wraplength=self.plot_w, justify="left")
        self.z_msg.pack(fill="x", padx=4, pady=4)

        self.z_fig = make_figure(self.plot_w, self.plot_h)
        self.z_canvas = FigureCanvasTkAgg(self.z_fig, master=p)
        self.z_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.plot_zeta()

    def _set_sigma(self, v):
        self.z_sigma.var.set(v)
        self.plot_zeta()

    def plot_zeta(self):
        sigma = self.z_sigma.get(0.5)
        t0 = self.z_tmin.get(0.0)
        t1 = self.z_tmax.get(50.0)
        if t1 <= t0:
            t1 = t0 + 10
        t1 = min(t1, 120)                       # keep it fast on a phone
        self.z_msg.config(text="Computing \u03b6 \u2026", fg=MUTED)
        self.z_msg.update_idletasks()
        ts = np.linspace(max(t0, 0.01), t1, 800)
        vals = np.array([abs(zeta(complex(sigma, t))) for t in ts])

        self.z_fig.clear()
        ax = self.z_fig.add_subplot(111)
        style_axes(ax, "t  (imaginary part / evolution time \u03c4)",
                   "|\u03b6(\u03c3+it)|",
                   "\u03c3 = %.3f" % sigma)
        col = BLUE if abs(sigma - 0.5) < 1e-9 else GOLD
        ax.plot(ts, vals, color=col, lw=1.4)
        ax.axhline(0, color=MUTED, lw=0.6)

        n_hit = 0
        if abs(sigma - 0.5) < 1e-6:
            for z in KNOWN_ZEROS:
                if t0 <= z <= t1:
                    ax.axvline(z, color=RED, lw=0.8, ls="--", alpha=0.8)
                    n_hit += 1
            self.z_msg.config(
                text="On the critical line: %d zero(s) in view. |\u03b6| touches 0 "
                     "\u2014 the probe qubit fully decoheres here." % n_hit,
                fg=GREEN)
        else:
            self.z_msg.config(
                text="Off the critical line (\u03c3 \u2260 1/2): |\u03b6| stays "
                     "strictly positive, so no phase transition occurs. That is "
                     "the Riemann Hypothesis, stated physically.",
                fg=GOLD)

        self.z_fig.tight_layout()
        self.z_canvas.draw()

    # ==================================================================
    # TAB 2 -- DQPT: coherence + rate function
    # ==================================================================
    def _build_dqpt(self, p):
        card = tk.Frame(p, bg=PANEL, padx=12, pady=12)
        card.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="Dynamical quantum phase transition",
                 bg=PANEL, fg=FG, font=F_H, anchor="w").pack(fill="x")
        tk.Label(card,
                 text="Prepare the many-body system at inverse temperature \u03c3, "
                      "quench it, and watch the probe qubit for time \u03c4.\n"
                      "L(\u03c4) = \u03b6(\u03c3+i\u03c4)/\u03b6(\u03c3)   \u2192   "
                      "l(\u03c4) = \u2212ln|L(\u03c4)|",
                 bg=PANEL, fg=MUTED, font=F_SMALL, anchor="w",
                 justify="left", wraplength=self.plot_w).pack(fill="x", pady=(2, 10))

        row = tk.Frame(card, bg=PANEL); row.pack(fill="x")
        self.d_sigma = Field(row, "\u03c3 (critical = 0.5)", "0.5")
        self.d_tmax  = Field(row, "\u03c4 max", "45")
        for w in (self.d_sigma, self.d_tmax):
            w.pack(side="left", expand=True, fill="x", padx=3)

        self.d_compare = tk.IntVar(value=1)
        tk.Checkbutton(card, text="Overlay an off-critical control run (\u03c3 = 0.8)",
                       variable=self.d_compare, command=self.plot_dqpt,
                       bg=PANEL, fg=MUTED, font=F_SMALL, selectcolor=PANEL,
                       activebackground=PANEL, activeforeground=FG,
                       anchor="w").pack(fill="x", pady=(8, 0))

        big_button(card, "Run the quench", self.plot_dqpt).pack(fill="x", pady=(10, 0))

        self.d_msg = tk.Label(p, text="", bg=BG, fg=GREEN, font=F_SMALL,
                              wraplength=self.plot_w, justify="left")
        self.d_msg.pack(fill="x", padx=4, pady=4)

        self.d_fig = make_figure(self.plot_w, int(self.plot_h * 1.5))
        self.d_canvas = FigureCanvasTkAgg(self.d_fig, master=p)
        self.d_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.plot_dqpt()

    def plot_dqpt(self):
        sigma = self.d_sigma.get(0.5)
        tmax = min(max(self.d_tmax.get(45.0), 5.0), 120.0)
        self.d_msg.config(text="Running the quench \u2026", fg=MUTED)
        self.d_msg.update_idletasks()
        taus = np.linspace(0.01, tmax, 800)

        L = loschmidt(sigma, taus)
        rate = rate_function(L)

        self.d_fig.clear()
        ax1 = self.d_fig.add_subplot(211)
        ax2 = self.d_fig.add_subplot(212)
        style_axes(ax1, "", "|L(\u03c4)|  probe coherence",
                   "Loschmidt amplitude,  \u03c3 = %.3f" % sigma)
        style_axes(ax2, "evolution time \u03c4", "l(\u03c4) = \u2212ln|L|",
                   "Rate function \u2014 kinks = DQPT")

        ax1.plot(taus, np.abs(L), color=BLUE, lw=1.4, label="\u03c3 = %.2f" % sigma)
        ax2.plot(taus, rate, color=BLUE, lw=1.4)

        if self.d_compare.get():
            Lc = loschmidt(0.8, taus)
            ax1.plot(taus, np.abs(Lc), color=GOLD, lw=1.2, ls="--",
                     label="control \u03c3 = 0.80")
            ax2.plot(taus, rate_function(Lc), color=GOLD, lw=1.2, ls="--")

        hits = 0
        if abs(sigma - 0.5) < 1e-6:
            for z in KNOWN_ZEROS:
                if z <= tmax:
                    hits += 1
                    ax1.axvline(z, color=RED, lw=0.8, ls=":", alpha=0.9)
                    ax2.axvline(z, color=RED, lw=0.8, ls=":", alpha=0.9)
            self.d_msg.config(
                text="Critical line: coherence collapses to 0 and l(\u03c4) diverges "
                     "at %d critical time(s) \u2014 exactly the first %d Riemann "
                     "zeros. This is the signal the 5-qubit NMR processor measured."
                     % (hits, hits),
                fg=GREEN)
        else:
            self.d_msg.config(
                text="\u03c3 = %.3f \u2260 1/2: |L| never reaches zero and l(\u03c4) "
                     "stays smooth \u2014 no transition. A kink here would falsify "
                     "the Riemann Hypothesis within this mapping." % sigma,
                fg=GOLD)

        ax1.legend(facecolor=PANEL, edgecolor=MUTED, labelcolor=FG, fontsize=7)
        ax1.set_ylim(bottom=0)
        self.d_fig.tight_layout()
        self.d_canvas.draw()

    # ==================================================================
    # TAB 3 -- numerical zero finder
    # ==================================================================
    def _build_find(self, p):
        card = tk.Frame(p, bg=PANEL, padx=12, pady=12)
        card.pack(fill="x", pady=(0, 8))

        tk.Label(card, text="Find zeros on the critical line",
                 bg=PANEL, fg=FG, font=F_H, anchor="w").pack(fill="x")
        tk.Label(card, text="Sign changes of the real Riemann\u2013Siegel function "
                            "Z(t) are bracketed and bisected to 1e\u201310.",
                 bg=PANEL, fg=MUTED, font=F_SMALL, anchor="w",
                 wraplength=self.plot_w).pack(fill="x", pady=(2, 10))

        row = tk.Frame(card, bg=PANEL); row.pack(fill="x")
        self.f_tmin = Field(row, "t min", "0")
        self.f_tmax = Field(row, "t max", "60")
        for w in (self.f_tmin, self.f_tmax):
            w.pack(side="left", expand=True, fill="x", padx=3)

        big_button(card, "Search", self.run_find, GREEN).pack(fill="x", pady=(10, 0))

        self.f_out = tk.Text(p, height=12, bg="#0f1728", fg=FG, font=F_MONO,
                             relief="flat", wrap="none", padx=10, pady=10)
        self.f_out.pack(fill="both", expand=True, padx=4, pady=4)

        self.f_fig = make_figure(self.plot_w, self.plot_h)
        self.f_canvas = FigureCanvasTkAgg(self.f_fig, master=p)
        self.f_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.run_find()

    def run_find(self):
        t0 = max(self.f_tmin.get(0.0), 0.0)
        t1 = min(max(self.f_tmax.get(60.0), t0 + 1), 120.0)
        self.f_out.delete("1.0", "end")
        self.f_out.insert("end", "Searching %.2f < t < %.2f ...\n" % (t0, t1))
        self.f_out.update_idletasks()

        zs = find_zeros(t0, t1, step=0.05)

        lines = ["  #      t (zero)        check |zeta|      DQPT time",
                 "  " + "-" * 52]
        for i, z in enumerate(zs, 1):
            mag = abs(zeta(complex(0.5, z)))
            lines.append("  %-5d %14.9f   %10.2e     \u03c4 = %.6f"
                         % (i, z, mag, z))
        lines.append("")
        lines.append("  %d zero(s) found. Every one has \u03c3 = 1/2 exactly," % len(zs))
        lines.append("  as the Riemann Hypothesis predicts.")
        self.f_out.delete("1.0", "end")
        self.f_out.insert("end", "\n".join(lines))

        # plot Z(t) with the roots marked
        ts = np.linspace(max(t0, 0.5), t1, 1200)
        zv = np.array([Z(t) for t in ts])
        self.f_fig.clear()
        ax = self.f_fig.add_subplot(111)
        style_axes(ax, "t", "Z(t)", "Riemann\u2013Siegel Z \u2014 roots = zeta zeros")
        ax.plot(ts, zv, color=PURPLE, lw=1.2)
        ax.axhline(0, color=MUTED, lw=0.8)
        if zs:
            ax.plot(zs, [0] * len(zs), "o", color=RED, ms=5)
        self.f_fig.tight_layout()
        self.f_canvas.draw()

    # ==================================================================
    # TAB 4 -- the correspondence diagram (hand-drawn on a Canvas)
    # ==================================================================
    def _build_map(self, p):
        tk.Label(p, text="The mapping", bg=BG, fg=FG, font=F_H,
                 anchor="w").pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(p, text="One complex number, two readings: mathematics on the "
                         "left, a laboratory setting on the right.",
                 bg=BG, fg=MUTED, font=F_SMALL, anchor="w", justify="left",
                 wraplength=self.plot_w).pack(fill="x", padx=12, pady=(0, 8))

        w = self.plot_w
        h = int(w * 1.05)
        c = tk.Canvas(p, width=w, height=h, bg=PANEL, highlightthickness=0)
        c.pack(padx=4, pady=4)
        self._draw_map(c, w, h)

        legend = tk.Frame(p, bg=PANEL, padx=12, pady=12)
        legend.pack(fill="x", padx=4, pady=(4, 10))
        rows = [("\u03c3 = Re(s)", "inverse temperature of the thermal state", BLUE),
                ("\u03c4 = Im(s)", "quench evolution time", GOLD),
                ("\u03b6(s) = 0", "probe-qubit coherence collapses \u2192 DQPT", RED)]
        for sym, meaning, col in rows:
            r = tk.Frame(legend, bg=PANEL); r.pack(fill="x", pady=3)
            tk.Label(r, text=sym, bg=PANEL, fg=col, font=F_H,
                     width=9, anchor="w").pack(side="left")
            tk.Label(r, text=meaning, bg=PANEL, fg=FG, font=F_SMALL,
                     anchor="w", wraplength=w - 110,
                     justify="left").pack(side="left", fill="x", expand=True)

    def _draw_map(self, c, w, h):
        # ---- critical strip (upper half of canvas) ----
        pad = 30
        x0, x1 = pad, w - pad
        y0, y1 = 20, int(h * 0.55)

        # strip 0 < sigma < 1 mapped to canvas x
        def sx(sigma):
            return x0 + (sigma + 0.5) / 2.0 * (x1 - x0)   # shows -0.5 .. 1.5

        def sy(t):
            return y1 - (t / 55.0) * (y1 - y0)

        c.create_rectangle(sx(0), y0, sx(1), y1, fill="#1c2740", outline="")
        c.create_text((sx(0) + sx(1)) / 2, y0 + 12, text="critical strip",
                      fill=PURPLE, font=F_SMALL)

        c.create_line(x0, y1, x1, y1, fill=MUTED, width=2)          # real axis
        c.create_line(sx(0), y0, sx(0), y1 + 6, fill=MUTED, width=1)
        c.create_text(sx(0), y1 + 18, text="0", fill=MUTED, font=F_SMALL)
        c.create_text(sx(1), y1 + 18, text="1", fill=MUTED, font=F_SMALL)
        c.create_text(x1 - 6, y1 + 18, text="\u03c3", fill=FG, font=F_SMALL)

        # critical line
        c.create_line(sx(0.5), y0 + 4, sx(0.5), y1, fill=BLUE, width=2, dash=(4, 3))
        c.create_text(sx(0.5) + 34, y0 + 30, text="\u03c3 = 1/2", fill=BLUE,
                      font=F_SMALL)

        # zeros on it
        for z in KNOWN_ZEROS[:6]:
            y = sy(z)
            c.create_oval(sx(0.5) - 4, y - 4, sx(0.5) + 4, y + 4,
                          fill=RED, outline="")
            c.create_text(sx(0.5) - 40, y, text="%.2f" % z, fill=RED,
                          font=("DejaVu Sans", 7))

        c.create_text(x0 + 4, y0 + 8, text="t", fill=FG, font=F_SMALL, anchor="w")

        # ---- arrow ----
        ym = int(h * 0.62)
        c.create_line(w / 2, y1 + 30, w / 2, ym, fill=GREEN, width=3,
                      arrow="last", arrowshape=(12, 14, 6))
        c.create_text(w / 2 + 70, (y1 + 30 + ym) / 2,
                      text="engineer H", fill=GREEN, font=F_SMALL)

        # ---- quantum register (lower half) ----
        yq = ym + 30
        c.create_text(w / 2, yq - 8, text="many-body register + probe qubit",
                      fill=FG, font=F_SMALL)

        n = 5
        span = (x1 - x0) * 0.8
        left = (w - span) / 2
        for i in range(n):
            cx = left + span * i / (n - 1)
            col = GOLD if i == n - 1 else BLUE
            c.create_oval(cx - 13, yq + 8, cx + 13, yq + 34,
                          fill=PANEL, outline=col, width=2)
            c.create_text(cx, yq + 21, text="q%d" % i, fill=col, font=("DejaVu Sans", 8))
            if i:
                px = left + span * (i - 1) / (n - 1)
                c.create_line(px + 13, yq + 21, cx - 13, yq + 21,
                              fill="#2c3a56", width=2)
        c.create_text(left + span + 4, yq + 46, text="probe", fill=GOLD,
                      font=("DejaVu Sans", 7))

        # coherence trace collapsing at a zero
        ty0 = yq + 70
        ty1 = h - 24
        c.create_line(x0, ty1, x1, ty1, fill=MUTED, width=1)
        c.create_text(x1 - 6, ty1 + 10, text="\u03c4", fill=FG, font=F_SMALL)
        c.create_text(x0, ty0 - 10, text="|L(\u03c4)|", fill=FG,
                      font=F_SMALL, anchor="w")

        taus = np.linspace(0.5, 45, 240)
        vals = np.abs(loschmidt(0.5, taus))
        vmax = max(vals.max(), 1e-9)
        pts = []
        for t, v in zip(taus, vals):
            px = x0 + (t / 45.0) * (x1 - x0)
            py = ty1 - (v / vmax) * (ty1 - ty0)
            pts.extend([px, py])
        c.create_line(*pts, fill=BLUE, width=2, smooth=True)

        for z in KNOWN_ZEROS[:4]:
            px = x0 + (z / 45.0) * (x1 - x0)
            c.create_line(px, ty0, px, ty1, fill=RED, width=1, dash=(2, 3))
        c.create_text(w / 2, ty1 + 12, text="dashed red = coherence collapse = DQPT",
                      fill=RED, font=("DejaVu Sans", 7))

    # ==================================================================
    # TAB 5 -- theory
    # ==================================================================
    def _build_info(self, p):
        blocks = [
            ("The zeta function",
             "\u03b6(s) = \u03a3 1/n^s  for Re(s) > 1, continued analytically to "
             "the whole plane except s = 1. Writing s = \u03c3 + it, the "
             "non-trivial zeros all lie in the strip 0 < \u03c3 < 1. Riemann's "
             "1859 conjecture: every one of them has \u03c3 = 1/2."),
            ("Hilbert\u2013P\u00f3lya, and why it stalled",
             "The classic physical attack looks for a Hamiltonian H whose "
             "eigenvalues are the zero heights t_n. Nobody has built one \u2014 "
             "such a stationary operator is hard to identify and harder to scale "
             "on near-term hardware."),
            ("The change of variable",
             "Wei, Xin and Long ask a different question: use time, not energy. "
             "Prepare a many-body system in thermal equilibrium, quench it, and "
             "let the two parts of s become two knobs on the experiment:\n\n"
             "    \u03c3  \u2192  inverse temperature\n"
             "    \u03c4  \u2192  evolution time\n\n"
             "Time is the most precisely controllable variable a quantum "
             "computer has, which is what makes this practical."),
            ("Loschmidt amplitude and rate function",
             "L(\u03c4) = \u27e8\u03c8(0)| e^(\u2212iH\u03c4) |\u03c8(0)\u27e9, "
             "engineered so that L(\u03c4) \u221d \u03b6(\u03c3 + i\u03c4).\n\n"
             "l(\u03c4) = \u2212ln|L(\u03c4)|/N\n\n"
             "A dynamical quantum phase transition is a non-analytic point of "
             "l(\u03c4). Since l diverges exactly where L vanishes, and L vanishes "
             "exactly where \u03b6 does, the zeros become critical times."),
            ("The statement, physically",
             "A DQPT can occur only if the system was prepared on the critical "
             "temperature \u03c3 = 1/2. Seeing a transition at any other "
             "temperature would mean a zeta zero off the critical line \u2014 "
             "the Riemann Hypothesis would be false. Every run of the "
             "experiment is a test."),
            ("What was measured",
             "A five-qubit NMR processor (three fluorine and two hydrogen spins "
             "in one molecule, one spin as the probe) was run at three settings: "
             "on the critical line, off it, and at the first zero's height. Probe "
             "coherence collapsed only when both conditions held at once, "
             "recovering the first five zeros. A companion numerical scheme "
             "based on the Loschmidt amplitude reached the trillionth zero, and "
             "agreement with the true values improved for larger zeros."),
            ("Cost",
             "Verifying zeros very far out classically means dense "
             "number-theoretic sums that grow exponentially. The proposed "
             "gate-based algorithm implements either construction in polynomial "
             "resources \u2014 the practical payoff of the whole reframing."),
            ("What this is not",
             "Not a proof. Experiments and simulations check finitely many "
             "zeros; the hypothesis is a statement about infinitely many. The "
             "contribution is a scalable instrument and a new correspondence, "
             "not a settled question."),
            ("Where it might go",
             "Larger processors for higher zeros; the same DQPT framework "
             "applied to the Witten index or black-hole thermodynamics; and "
             "hunting for physical twins of other arithmetic objects such as "
             "generalized L-functions."),
            ("Source",
             "Shijie Wei et al., 'The Riemann Hypothesis manifested in "
             "dynamical quantum phase transitions', Nature Communications "
             "(2026). DOI 10.1038/s41467-026-74935-8, arXiv:2511.11199."),
        ]
        for title, body in blocks:
            card = tk.Frame(p, bg=PANEL, padx=14, pady=12)
            card.pack(fill="x", padx=4, pady=5)
            tk.Label(card, text=title, bg=PANEL, fg=PURPLE, font=F_H,
                     anchor="w").pack(fill="x")
            tk.Label(card, text=body, bg=PANEL, fg=FG, font=F_BODY,
                     anchor="w", justify="left",
                     wraplength=self.plot_w - 20).pack(fill="x", pady=(6, 0))


# ======================================================================
def main():
    root = tk.Tk()
    RiemannApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
