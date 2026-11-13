#!/usr/bin/env python3
"""
Goldstone Explorer  -  for Pydroid 3 on Android (also runs on desktop Python)

Interactive companion to the explainer on Jeffrey Goldstone's physics:
  1 Overview        timeline of his career
  2 Mexican hat     spontaneous symmetry breaking, Higgs/Goldstone masses
  3 Dispersion      massive vs Goldstone vs magnon energy-momentum curves
  4 Counting        number of Goldstone bosons = dim G - dim H
  5 Higgs           gauge field "eats" the Goldstone boson
  6 QAOA on SK      real QAOA simulation on a Sherrington-Kirkpatrick spin glass
  7 Ring QAOA       checks the FGG ring-of-disagrees formula (2p+1)/(2p+2)

Only the standard library is used (tkinter, math, random, threading).
In Pydroid 3: open this file and press the yellow Run button.

Layout rules that prevent overlapping:
  * every legend is drawn in its own band above the plot, wrapping to new rows
  * axis margins are measured from the actual tick-label widths
  * the number of ticks is reduced until the labels fit
  * long labels are wrapped or shortened with "..." to the space available
  * explanations go in a separate scrollable text panel, never on the drawing
"""

import tkinter as tk
from tkinter import font as tkfont
import math
import random
import threading
import queue

PARISI = 0.763166

COL = dict(bg="#ffffff", fg="#1d1d1f", muted="#6b6b70", grid="#e6e4de",
           panel="#f1efe9", a="#2f6fdb", b="#d9572b", c="#2a9d6f",
           d="#8a5cd1", e="#b8860b")


# ----------------------------------------------------------------------------
# Small numeric helpers
# ----------------------------------------------------------------------------
def nice_ticks(lo, hi, maxn):
    if not hi > lo:
        hi = lo + 1.0
    raw = (hi - lo) / max(1, maxn)
    mag = 10 ** math.floor(math.log10(raw))
    step = 10 * mag
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw * (1 - 1e-9):
            step = m * mag
            break
    t = math.ceil(lo / step - 1e-9) * step
    out = []
    while t <= hi + step * 1e-9:
        out.append(t)
        t += step
    return out, step


def tick_fmt(t, step):
    d = max(0, -int(math.floor(math.log10(step) + 1e-9)))
    if abs(round(step * 10 ** d) - step * 10 ** d) > 1e-6:
        d += 1
    s = "%.*f" % (d, t)
    if s.startswith("-") and float(s) == 0:
        s = s[1:]
    return s


def linspace(a, b, n):
    if n == 1:
        return [a]
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ----------------------------------------------------------------------------
# QAOA state-vector simulator (pure Python)
# ----------------------------------------------------------------------------
def qaoa_run(cost, n, gammas, betas):
    """Return (<C>, (re, im)) for |g,b> = prod_k e^{-i b_k B} e^{-i g_k C} |+>^n."""
    N = len(cost)
    a = 1.0 / math.sqrt(N)
    re = [a] * N
    im = [0.0] * N
    for g, b in zip(gammas, betas):
        # phase separator: diagonal e^{-i g C(z)}
        for x in range(N):
            ph = -g * cost[x]
            c, s = math.cos(ph), math.sin(ph)
            r, i = re[x], im[x]
            re[x] = r * c - i * s
            im[x] = r * s + i * c
        # mixer: prod_j e^{-i b X_j} = prod_j (cos b - i sin b X_j)
        cb, sb = math.cos(b), math.sin(b)
        for q in range(n):
            m = 1 << q
            for x in range(N):
                if x & m:
                    continue
                y = x | m
                r0, i0, r1, i1 = re[x], im[x], re[y], im[y]
                re[x] = cb * r0 + sb * i1
                im[x] = cb * i0 - sb * r1
                re[y] = cb * r1 + sb * i0
                im[y] = cb * i1 - sb * r0
    e = 0.0
    for x in range(N):
        e += (re[x] * re[x] + im[x] * im[x]) * cost[x]
    return e, (re, im)


def coord_descent(f, x0, step=0.15, tol=2e-3, max_evals=260):
    x = list(x0)
    fx = f(x)
    ev = 1
    while step > tol and ev < max_evals:
        improved = False
        for i in range(len(x)):
            for d in (step, -step):
                y = x[:]
                y[i] += d
                fy = f(y)
                ev += 1
                if fy < fx - 1e-12:
                    x, fx = y, fy
                    improved = True
                    break
            if ev >= max_evals:
                break
        if not improved:
            step *= 0.5
    return x, fx


def interp(prev):
    """INTERP warm start: depth-q angles -> depth-(q+1) angles."""
    q = len(prev)
    out = []
    for i in range(q + 1):
        a = prev[i - 1] if i - 1 >= 0 else 0.0
        b = prev[i] if i < q else 0.0
        out.append((i / q) * a + ((q - i) / q) * b)
    return out


def spins(x, n):
    return [1 - 2 * ((x >> q) & 1) for q in range(n)]


def sk_costs(n, seed):
    rng = random.Random(seed)
    J = [(j, k, rng.gauss(0, 1)) for j in range(n) for k in range(j + 1, n)]
    s = 1.0 / math.sqrt(n)
    out = []
    for x in range(2 ** n):
        z = spins(x, n)
        out.append(s * sum(w * z[j] * z[k] for j, k, w in J))
    return out


def ring_cut(n):
    out = []
    for x in range(2 ** n):
        z = spins(x, n)
        out.append(sum(0.5 * (1 - z[j] * z[(j + 1) % n]) for j in range(n)))
    return out


def optimise_depths(cost, n, pmax, grid_g, grid_b, report, restarts=4, seed=0):
    """Optimise QAOA for p = 1..pmax (minimising <C>).
    Each depth tries warm starts from depth p-1 (INTERP and zero-padding, so the
    result can never get worse) plus a few random restarts, and keeps the best."""
    rng = random.Random(seed)
    gmax, bmax = max(grid_g), max(grid_b)
    gs = bs = None
    for p in range(1, pmax + 1):
        def f(x, p=p):
            return qaoa_run(cost, n, x[:p], x[p:])[0]
        starts = []
        if p == 1:
            best = None
            for g in grid_g:
                for b in grid_b:
                    v = f([g, b])
                    if best is None or v < best[0]:
                        best = (v, [g, b])
            starts.append(best[1])
        else:
            starts.append(interp(gs) + interp(bs))
            starts.append(gs + [0.0] + bs + [0.0])
        for _ in range(restarts if p > 1 else 0):
            starts.append([rng.uniform(0, gmax) for _ in range(p)] +
                          [rng.uniform(0, bmax) for _ in range(p)])
        best = None
        for x0 in starts:
            x, fx = coord_descent(f, x0)
            if best is None or fx < best[1] - 1e-12:
                best = (x, fx)
        x, fx = best
        gs, bs = x[:p], x[p:]
        _, (re, im) = qaoa_run(cost, n, gs, bs)
        report(p, fx, gs, bs, re, im)


# ----------------------------------------------------------------------------
# Section base class
# ----------------------------------------------------------------------------
class Section:
    title = ""
    fields = []          # (key, label, default)

    def __init__(self, app):
        self.app = app
        self.vars = {k: tk.StringVar(value=str(d)) for k, _, d in self.fields}
        self.error = None
        try:
            self.calc()
        except ValueError:
            pass

    # ---- inputs -----------------------------------------------------------
    def num(self, k, lo=None, hi=None, integer=False):
        label = [l for kk, l, _ in self.fields if kk == k][0]
        s = self.vars[k].get().strip()
        try:
            x = int(s) if integer else float(s)
        except ValueError:
            raise ValueError("%s must be %s" % (label, "a whole number" if integer else "a number"))
        if (lo is not None and x < lo) or (hi is not None and x > hi):
            raise ValueError("%s must be between %s and %s" % (label, lo, hi))
        return x

    def build(self, fr):
        app = self.app
        cols = app.cols
        r = 0
        for i, (k, lab, _) in enumerate(self.fields):
            rr, cc = divmod(i, cols)
            cell = tk.Frame(fr, bg=COL["bg"])
            cell.grid(row=rr, column=cc, sticky="ew", padx=4, pady=2)
            tk.Label(cell, text=lab, bg=COL["bg"], fg=COL["muted"],
                     font=app.F(app.small), anchor="w").pack(fill="x")
            tk.Entry(cell, textvariable=self.vars[k], width=6, font=app.F(app.base),
                     relief="solid", bd=1).pack(fill="x")
            r = rr + 1
        for cc in range(cols):
            fr.columnconfigure(cc, weight=1)
        r = self.extra(fr, r)
        btns = self.buttons()
        if btns:
            bf = tk.Frame(fr, bg=COL["bg"])
            bf.grid(row=r, column=0, columnspan=cols, sticky="ew", pady=(4, 2))
            for j, (lab, cb) in enumerate(btns):
                tk.Button(bf, text=lab, command=cb, font=app.F(app.base, True),
                          bg=COL["a"], fg="white", activebackground=COL["a"],
                          activeforeground="white", relief="flat",
                          padx=6, pady=4).grid(row=0, column=j, sticky="ew", padx=3)
                bf.columnconfigure(j, weight=1)

    def radio_row(self, fr, r, var, options):
        app = self.app
        rf = tk.Frame(fr, bg=COL["bg"])
        rf.grid(row=r, column=0, columnspan=app.cols, sticky="ew", pady=2)
        for j, (val, lab) in enumerate(options):
            tk.Radiobutton(rf, text=lab, value=val, variable=var, indicatoron=0,
                           font=app.F(app.small), command=app.redraw, padx=6, pady=4,
                           selectcolor="#dfe8fb", bg=COL["panel"]).grid(
                row=0, column=j, sticky="ew", padx=2)
            rf.columnconfigure(j, weight=1)
        return r + 1

    def extra(self, fr, r):
        return r

    def buttons(self):
        return [("Compute", self.compute)] if self.fields else []

    def compute(self):
        try:
            self.calc()
            self.error = None
        except ValueError as e:
            self.error = str(e)
        self.app.redraw()
        self.app.show(self.text())

    def calc(self):
        pass

    def text(self):
        return []

    def draw(self, c, W, H):
        pass

    def err_seg(self):
        return [("Input error: " + self.error + "\n\n", "err")] if self.error else []


# ----------------------------------------------------------------------------
# 1  Overview
# ----------------------------------------------------------------------------
class Overview(Section):
    title = "1  Overview"
    events = [
        ("1933", "Born in Manchester, England"),
        ("1958", "PhD, Trinity College, Cambridge"),
        ("1961", "Paper introducing Goldstone bosons"),
        ("1962", "Goldstone theorem, with Salam and Weinberg"),
        ("1973", "Light-cone quantization of strings (GGRT)"),
        ("1977", "Joins the MIT physics faculty"),
        ("1983", "Green Professor; directs CTP until 1989"),
        ("1991", "Dirac Medal, shared with Mandelstam"),
        ("2000", "Quantum computation by adiabatic evolution"),
        ("2014", "Introduces QAOA with Farhi and Gutmann"),
        ("2019", "QAOA on the SK spin glass at infinite size"),
        ("2026", "Dies October 12, aged 93"),
    ]

    def text(self):
        return [
            ("Jeffrey Goldstone (1933-2026)\n", "h"),
            ("A theoretical physicist whose name is attached to the Goldstone boson "
             "and the Goldstone theorem: when a continuous symmetry of the laws of "
             "physics is spontaneously broken by the ground state, a massless spin-0 "
             "particle must appear. Late in his career he co-created adiabatic quantum "
             "computation and QAOA.\n\n", ""),
            ("How to use this app\n", "h"),
            ("Pick a section from the menu at the top (or use the arrow buttons). "
             "Change the numbers in the boxes and press Compute or Run. The picture "
             "updates above and the maths and results appear here. Drag this panel "
             "to scroll.\n\n", ""),
            ("Sections\n", "h"),
            ("2  Mexican hat: compute the vacuum and the particle masses.\n"
             "3  Dispersion: compare massive and massless energy curves.\n"
             "4  Counting: how many Goldstone bosons a symmetry breaking produces.\n"
             "5  Higgs: what happens when the symmetry is gauged.\n"
             "6  QAOA on SK: run a real quantum-algorithm simulation on a spin glass "
             "and compare with the Parisi value 0.7632.\n"
             "7  Ring QAOA: verify the conjecture (2p+1)/(2p+2) numerically.\n", ""),
        ]

    def draw(self, c, W, H):
        app = self.app
        pad = 10
        n = len(self.events)
        row_h = (H - 2 * pad) / n
        fs = int(max(9, min(app.small, row_h * 0.72)))
        f = app.F(fs)
        fb = app.F(fs, True)
        lh = f.metrics("linespace")
        yw = fb.measure("2026")
        xline = pad + yw + 14
        xt = xline + 16
        avail = W - xt - pad
        c.create_line(xline, pad + row_h / 2, xline, pad + row_h * (n - 0.5),
                      fill=COL["grid"], width=3)
        max_lines = max(1, int(row_h // lh))
        for i, (yr, ev) in enumerate(self.events):
            cy = pad + row_h * (i + 0.5)
            col = COL["b"] if yr in ("1961", "1962") else (COL["c"] if yr >= "2000" else COL["a"])
            r = max(4, fs * 0.28)
            c.create_oval(xline - r, cy - r, xline + r, cy + r, fill=col, outline=col)
            c.create_text(xline - 10, cy, text=yr, anchor="e", font=fb, fill=COL["fg"])
            lines = app.wrap(ev, f, avail)
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                lines[-1] = app.fit(lines[-1] + " ...", f, avail)
            y0 = cy - lh * len(lines) / 2
            for j, ln in enumerate(lines):
                c.create_text(xt, y0 + lh * (j + 0.5), text=ln, anchor="w", font=f, fill=COL["fg"])


# ----------------------------------------------------------------------------
# 2  Mexican hat
# ----------------------------------------------------------------------------
class Hat(Section):
    title = "2  Mexican hat"
    fields = [("mu2", "mu^2 (can be < 0)", 1.0), ("lam", "lambda (> 0)", 0.5)]

    def __init__(self, app):
        self.view = tk.StringVar(value="side")
        Section.__init__(self, app)

    def extra(self, fr, r):
        return self.radio_row(fr, r, self.view, [("side", "Side view"), ("top", "Top view")])

    def calc(self):
        mu2 = self.num("mu2", -100, 100)
        lam = self.num("lam", 1e-6, 100)
        self.mu2, self.lam = mu2, lam
        if mu2 > 0:
            self.v = math.sqrt(mu2 / lam)
            self.mh2, self.mpi2 = 2 * mu2, 0.0
            self.vmin = -mu2 * mu2 / (4 * lam)
        else:
            self.v = 0.0
            self.mh2 = self.mpi2 = -mu2
            self.vmin = 0.0

    def V(self, x):  # slice along x = sqrt(2) Re(phi)
        return -self.mu2 * x * x / 2 + self.lam * x ** 4 / 4

    def text(self):
        s = self.err_seg()
        s += [("Model\n", "h"),
              ("L = |d phi|^2 - V(phi),  V = -mu^2 |phi|^2 + lambda |phi|^4\n"
               "Symmetry: phi -> e^(i alpha) phi  (the group U(1), continuous).\n\n", "m"),
              ("Vacuum\n", "h"),
              ("For mu^2 > 0, phi = 0 is a maximum. Minimising V gives a whole circle of "
               "minima:\n", ""),
              ("  |phi|^2 = mu^2/(2 lambda) = v^2/2,  v = mu/sqrt(lambda)\n"
               "  V = lambda(|phi|^2 - v^2/2)^2 + const\n\n", "m"),
              ("Expanding around one vacuum\n", "h"),
              ("Write phi = (v + h + i pi)/sqrt(2). Then |phi|^2 - v^2/2 = (2vh + h^2 + pi^2)/2, "
               "so\n", ""),
              ("  V = lambda v^2 h^2 + lambda v h (h^2 + pi^2)\n"
               "      + (lambda/4)(h^2 + pi^2)^2 + const\n", "m"),
              ("There is an h^2 mass term but no pi^2 term:\n", ""),
              ("  m_h^2 = 2 lambda v^2 = 2 mu^2,   m_pi^2 = 0\n", "m"),
              ("pi is the Goldstone boson. In polar form phi = (v+rho)e^(i theta/v)/sqrt(2), "
               "theta only appears with derivatives, because shifting theta is the "
               "symmetry itself, so no mass term can ever be generated for it.\n\n", ""),
              ("Your numbers\n", "h")]
        if self.error is None:
            if self.mu2 > 0:
                s.append(("  v        = %.5f\n  V_min    = %.5f\n  m_h^2    = %.5f   (m_h = %.5f)\n"
                          "  m_pi^2   = 0       (Goldstone, massless)\n"
                          % (self.v, self.vmin, self.mh2, math.sqrt(self.mh2)), "m"))
                s.append(("\nBroken phase: the vacuum picks one point on the circle.\n", ""))
            else:
                s.append(("  v = 0\n  m_h^2 = m_pi^2 = -mu^2 = %.5f\n" % self.mh2, "m"))
                s.append(("\nmu^2 <= 0: symmetric phase. The single vacuum is phi = 0, "
                          "nothing is broken, and both modes have the same mass. "
                          "Try a positive mu^2 to break the symmetry.\n", ""))
        return s

    def draw(self, c, W, H):
        if self.error:
            return
        if self.view.get() == "side":
            R = 1.8 * self.v if self.v > 0 else 2.0 * max(1.0, math.sqrt(abs(self.mu2) / self.lam))
            xs = linspace(-R, R, 241)
            ys = [self.V(x) for x in xs]
            if self.v > 0:
                ytop = abs(self.vmin) * 2.2
                ylim = (self.vmin - 0.15 * (ytop - self.vmin), ytop)
            else:
                ytop = self.V(R * 0.8)
                ylim = (-0.08 * ytop - 1e-9, ytop)
            series = [dict(label="V along x = sqrt(2) Re phi", color=COL["a"], xs=xs, ys=ys, width=3)]
            if self.v > 0:
                series.append(dict(label="vacua x = +/- v", color=COL["b"],
                                   xs=[-self.v, self.v], ys=[self.vmin] * 2, line=False, marker=True))
            else:
                series.append(dict(label="single vacuum at 0", color=COL["b"],
                                   xs=[0], ys=[0], line=False, marker=True))
            self.app.plot_xy(c, W, H, series, "x = sqrt(2) Re phi", "V", ylim=ylim)
        else:
            self.draw_top(c, W, H)

    def draw_top(self, c, W, H):
        app = self.app
        broken = self.v > 0
        if broken:
            items = [("circle of vacua |phi| = v/sqrt(2)", COL["c"], "dash"),
                     ("chosen vacuum", COL["b"], "dot"),
                     ("h: radial, costs energy (massive)", COL["b"], "arrow"),
                     ("pi: along circle, free (massless)", COL["c"], "arrow"),
                     ("axes: Re phi (right), Im phi (up)", COL["muted"], "line")]
        else:
            items = [("single vacuum at phi = 0", COL["b"], "dot"),
                     ("mu^2 <= 0: nothing broken, no Goldstone", COL["muted"], "none"),
                     ("axes: Re phi (right), Im phi (up)", COL["muted"], "line")]
        top = app.legend(c, W, items) + 8
        pad = 10
        w, h = W - 2 * pad, H - top - pad
        S = min(w, h)
        if S < 40:
            return
        cx, cy = W / 2, top + h / 2
        half = S * 0.48
        for k in range(1, 6):
            rr = half * k / 5
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=COL["grid"])
        c.create_line(cx - half, cy, cx + half, cy, fill=COL["muted"], arrow="last")
        c.create_line(cx, cy + half, cx, cy - half, fill=COL["muted"], arrow="last")
        lw = max(2, int(S / 120))
        br = max(6, S * 0.035)
        if broken:
            R = S * 0.30
            c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=COL["c"], width=lw, dash=(8, 6))
            bx = cx + R
            c.create_line(bx + br + 3, cy - br * 1.6, cx + half * 0.97, cy - br * 1.6,
                          fill=COL["b"], width=lw, arrow="last", arrowshape=(12, 14, 5))
            Ra = R - br * 2.2
            pts = []
            for t in linspace(-0.12, -1.15, 24):
                pts += [cx + Ra * math.cos(t), cy + Ra * math.sin(t)]
            c.create_line(*pts, fill=COL["c"], width=lw, smooth=True, arrow="last", arrowshape=(12, 14, 5))
            c.create_oval(bx - br, cy - br, bx + br, cy + br, fill=COL["b"], outline=COL["b"])
        else:
            c.create_oval(cx - br, cy - br, cx + br, cy + br, fill=COL["b"], outline=COL["b"])


# ----------------------------------------------------------------------------
# 3  Dispersion
# ----------------------------------------------------------------------------
class Dispersion(Section):
    title = "3  Dispersion"
    fields = [("m", "mass m", 1.2), ("D", "magnon stiffness D", 0.5), ("kmax", "max momentum", 3.0)]

    def calc(self):
        self.m = self.num("m", 0, 100)
        self.D = self.num("D", 0, 100)
        self.kmax = self.num("kmax", 0.1, 100)

    def text(self):
        s = self.err_seg()
        s += [("Energy versus momentum\n", "h"),
              ("A particle's dispersion relation says how much energy omega a "
               "wave of momentum k carries.\n\n", ""),
              ("  massive (h mode):     omega = sqrt(k^2 + m^2)\n"
               "  Goldstone (relativ.): omega = |k|\n"
               "  ferromagnet magnon:   omega = D k^2\n\n", "m"),
              ("Why Goldstone modes are gapless\n", "h"),
              ("Noether's theorem gives a conserved current d_mu j^mu = 0 and a charge Q "
               "with [Q, H] = 0. If the vacuum breaks the symmetry, Q|0> is not zero but "
               "has the same energy as |0>. Smearing the charge density with a long "
               "wavelength gives states Q_k|0> whose energy goes to 0 as k -> 0. With "
               "Lorentz invariance E^2 = k^2 + m^2, so m = 0.\n\n", ""),
              ("The massive mode has a gap: even at k = 0 it costs energy m. A ferromagnet "
               "has no Lorentz invariance, so its Goldstone mode is quadratic, "
               "omega ~ k^2, and two broken generators pair into a single mode.\n\n", "")]
        if self.error is None:
            rows = ["      k   massive  Goldstone   magnon"]
            for k in linspace(0, self.kmax, 6):
                rows.append("%7.3f  %8.4f  %9.4f  %7.4f" %
                            (k, math.sqrt(k * k + self.m ** 2), k, self.D * k * k))
            s += [("Table\n", "h"), ("\n".join(rows) + "\n", "m")]
        return s

    def draw(self, c, W, H):
        if self.error:
            return
        ks = linspace(0, self.kmax, 160)
        series = [
            dict(label="massive sqrt(k^2+m^2)", color=COL["b"], xs=ks, ys=[math.sqrt(k * k + self.m ** 2) for k in ks]),
            dict(label="Goldstone omega = k", color=COL["c"], xs=ks, ys=ks),
            dict(label="magnon D k^2", color=COL["d"], xs=ks, ys=[self.D * k * k for k in ks], dash=(8, 5)),
        ]
        ymax = max(math.sqrt(self.kmax ** 2 + self.m ** 2), self.kmax) * 1.05
        self.app.plot_xy(c, W, H, series, "momentum k", "energy omega", ylim=(0, ymax), xlim=(0, self.kmax))


# ----------------------------------------------------------------------------
# 4  Counting
# ----------------------------------------------------------------------------
class Counting(Section):
    title = "4  Counting"
    fields = [("N", "N (for O(N), SU(N))", 3)]
    patterns = [
        "U(1) -> nothing",
        "O(N) -> O(N-1)",
        "SU(N)xSU(N) -> SU(N)  (chiral)",
        "SO(3) -> SO(2)  antiferromagnet",
        "SO(3) -> SO(2)  ferromagnet",
        "SU(2)xU(1) -> U(1)  electroweak",
    ]

    def __init__(self, app):
        self.pat = tk.StringVar(value=self.patterns[1])
        Section.__init__(self, app)

    def extra(self, fr, r):
        app = self.app
        om = tk.OptionMenu(fr, self.pat, *self.patterns, command=lambda _: self.compute())
        om.config(font=app.F(app.small), bg=COL["panel"], highlightthickness=0)
        om["menu"].config(font=app.F(app.base))
        om.grid(row=r, column=0, columnspan=app.cols, sticky="ew", padx=4, pady=2)
        return r + 1

    def calc(self):
        N = self.num("N", 2, 12, integer=True)
        p = self.pat.get()
        note = ""
        if p.startswith("U(1)"):
            G, Hd = 1, 0
            note = "The phase rotation of a complex field is broken: one Goldstone (the pi field of section 2). In a superfluid this is the phonon."
        elif p.startswith("O(N)"):
            G, Hd = N * (N - 1) // 2, (N - 1) * (N - 2) // 2
            note = "An N-component vector picks a direction; rotations about it survive. N-1 Goldstones."
        elif p.startswith("SU(N)xSU(N)"):
            G, Hd = 2 * (N * N - 1), N * N - 1
            note = ("Chiral symmetry of QCD with N light quarks, broken by the quark condensate. "
                    "N=2 gives the 3 pions; N=3 gives 8 (pions, kaons, eta). Quark masses give them "
                    "small masses: m_pi^2 f_pi^2 = -(m_u+m_d)<qq>, so they are pseudo-Goldstones.")
        elif "anti" in p:
            G, Hd = 3, 1
            note = "Two linear (omega ~ k) spin-wave modes."
        elif "ferro" in p:
            G, Hd = 3, 1
            note = ("Non-relativistic exception: [S_x, S_y] = i S_z has a nonzero vacuum value (the "
                    "magnetisation), so the two broken generators pair into ONE quadratic magnon. "
                    "Rule: n_A + 2 n_B = dim G - dim H.")
        else:
            G, Hd = 4, 1
            note = ("The symmetry is gauged, so the 3 would-be Goldstones are eaten and become the "
                    "longitudinal polarisations of W+, W- and Z. No massless scalars remain.")
        broken = G - Hd
        if "ferro" in p:
            phys = 1
        elif "electroweak" in p:
            phys = 0
        else:
            phys = broken
        self.res = (p, N, G, Hd, broken, phys, note)

    def text(self):
        s = self.err_seg()
        s += [("Counting rule\n", "h"),
              ("If the Lagrangian's symmetry group G is broken by the vacuum down to a "
               "subgroup H, each broken generator is an independent flat direction in "
               "the space of vacua G/H. In a relativistic theory:\n", ""),
              ("  N_Goldstone = dim G - dim H\n", "m"),
              ("  dim O(N) = N(N-1)/2,   dim SU(N) = N^2 - 1\n\n", "m")]
        if self.error is None:
            p, N, G, Hd, br, ph, note = self.res
            s += [("Result\n", "h"),
                  ("  pattern : %s\n  N       : %d\n  dim G   : %d\n  dim H   : %d\n"
                   "  broken  : %d\n  massless Goldstone modes: %d\n\n" % (p, N, G, Hd, br, ph), "m"),
                  (note + "\n", "")]
        return s

    def draw(self, c, W, H):
        if self.error:
            return
        app = self.app
        p, N, G, Hd, br, ph, _ = self.res
        f = app.F(app.small)
        fb = app.F(app.small, True)
        lh = f.metrics("linespace")
        pad = 10
        title = app.fit(p, fb, W - 2 * pad)
        c.create_text(W / 2, pad + lh / 2, text=title, font=fb, fill=COL["fg"])
        vals = [("dim G", G, COL["a"]), ("dim H", Hd, COL["muted"]),
                ("broken", br, COL["b"]), ("massless", ph, COL["c"])]
        top = pad + lh * 2.4
        bottom = H - pad - lh * 1.4
        if bottom - top < lh * 2:
            return
        slot = (W - 2 * pad) / len(vals)
        bw = slot * 0.6
        vmax = max(1, max(v for _, v, _ in vals))
        c.create_line(pad, bottom, W - pad, bottom, fill=COL["muted"])
        for i, (lab, v, col) in enumerate(vals):
            x = pad + slot * (i + 0.5)
            hgt = (bottom - top) * v / vmax
            c.create_rectangle(x - bw / 2, bottom - hgt, x + bw / 2, bottom, fill=col, outline=col)
            c.create_text(x, bottom - hgt - 4, text=str(v), anchor="s", font=fb, fill=COL["fg"])
            c.create_text(x, bottom + 4, text=app.fit(lab, f, slot - 4), anchor="n", font=f, fill=COL["fg"])


# ----------------------------------------------------------------------------
# 5  Higgs mechanism
# ----------------------------------------------------------------------------
class Higgs(Section):
    title = "5  Higgs"
    fields = [("e", "gauge coupling e", 0.65), ("v", "vacuum value v", 246.0), ("lam", "lambda", 0.13)]

    def calc(self):
        self.e = self.num("e", 0, 10)
        self.v = self.num("v", 0, 1e6)
        self.lam = self.num("lam", 0, 10)
        self.mA = self.e * self.v
        self.mh = math.sqrt(2 * self.lam) * self.v

    def text(self):
        s = self.err_seg()
        s += [("Gauging the symmetry\n", "h"),
              ("Let alpha depend on position. Invariance needs a gauge field A_mu and the "
               "covariant derivative D_mu = d_mu - i e A_mu:\n", ""),
              ("  L = |D phi|^2 - V(phi) - F_mn F^mn / 4\n\n", "m"),
              ("Write phi = (v + rho) e^(i theta/v) / sqrt(2). A gauge transformation with "
               "alpha = -theta/v removes theta completely (unitary gauge). Left behind is\n", ""),
              ("  |D phi|^2  contains  (1/2) e^2 v^2 A_mu A^mu\n"
               "  => m_A = e v,   m_h = sqrt(2 lambda) v\n\n", "m"),
              ("The Goldstone boson has become the photon's third (longitudinal) "
               "polarisation. This loophole in Goldstone's theorem (it assumes a global "
               "symmetry) is the Higgs mechanism of 1964. In the Standard Model the three "
               "would-be Goldstones become parts of W+, W- and Z.\n\n", ""),
              ("Degrees of freedom are conserved\n", "h"),
              ("  before: photon 2 + complex scalar 2 = 4\n"
               "  after : massive vector 3 + Higgs 1  = 4\n\n", "m")]
        if self.error is None:
            s += [("Your numbers\n", "h"),
                  ("  m_A = e v            = %.4f\n  m_h = sqrt(2 lam) v  = %.4f\n" % (self.mA, self.mh), "m"),
                  ("\n(With v = 246 and lambda = 0.13, m_h comes out near the measured Higgs mass "
                   "of about 125 GeV.)\n", "")]
        return s

    def draw(self, c, W, H):
        if self.error:
            return
        app = self.app
        pad = 10
        fs = int(max(9, min(app.small, (H - 2 * pad) / 12.5 / 1.2)))
        f = app.F(fs)
        fb = app.F(fs, True)
        lh = f.metrics("linespace")
        y = pad
        gap = 12
        bw = (W - 2 * pad - gap) / 2
        bh = lh * 2.9

        def header(txt, yy):
            c.create_text(pad, yy + lh / 2, text=app.fit(txt, fb, W - 2 * pad), anchor="w", font=fb, fill=COL["fg"])
            return yy + lh * 1.3

        def box(x, yy, col, l1, l2):
            c.create_rectangle(x, yy, x + bw, yy + bh, outline=col, width=2, fill="#fafafa")
            c.create_text(x + bw / 2, yy + bh / 2 - lh * 0.56, text=app.fit(l1, fb, bw - 10), font=fb, fill=col)
            c.create_text(x + bw / 2, yy + bh / 2 + lh * 0.56, text=app.fit(l2, f, bw - 10), font=f, fill=COL["fg"])

        y = header("Before breaking (4 degrees of freedom)", y)
        box(pad, y, COL["a"], "photon A", "massless: 2 pol.")
        box(pad + bw + gap, y, COL["c"], "complex phi", "h + pi: 2 fields")
        y += bh + lh * 0.4
        ax = pad + bw + gap + bw * 0.75
        c.create_line(ax, y, ax, y + lh * 1.2, fill=COL["c"], width=3, arrow="last")
        c.create_line(ax, y + lh * 0.6, pad + bw * 0.5, y + lh * 1.2, fill=COL["c"], width=2, arrow="last", dash=(6, 4))
        y += lh * 1.4
        c.create_text(W / 2, y + lh / 2, text=app.fit("pi is eaten by the photon", f, W - 2 * pad),
                      font=f, fill=COL["muted"])
        y += lh * 1.4
        y = header("After breaking (still 4)", y)
        box(pad, y, COL["a"], "massive A", "3 pol., m_A = %.3g" % self.mA)
        box(pad + bw + gap, y, COL["b"], "Higgs h", "1 field, m_h = %.3g" % self.mh)


# ----------------------------------------------------------------------------
# 6  QAOA on SK
# ----------------------------------------------------------------------------
class QaoaSK(Section):
    title = "6  QAOA on SK"
    fields = [("n", "spins n (4-10)", 8), ("p", "max depth p (1-5)", 4), ("seed", "random seed", 1)]

    def __init__(self, app):
        self.view = tk.StringVar(value="energy")
        self.results = []
        self.running = False
        self.status = "Press Run QAOA to start."
        self.emin = None
        Section.__init__(self, app)

    def extra(self, fr, r):
        return self.radio_row(fr, r, self.view, [("energy", "Energy vs p"), ("angles", "Best angles")])

    def buttons(self):
        return [("Run QAOA", self.run)]

    def run(self):
        if self.running:
            return
        try:
            n = self.num("n", 4, 10, integer=True)
            p = self.num("p", 1, 5, integer=True)
            seed = self.num("seed", 0, 10 ** 9, integer=True)
            self.error = None
        except ValueError as e:
            self.error = str(e)
            self.app.show(self.text())
            return
        self.n, self.pmax = n, p
        self.results, self.emin, self.running = [], None, True
        self.status = "Building the instance..."
        self.app.redraw()
        self.app.show(self.text())
        threading.Thread(target=self.worker, args=(n, p, seed), daemon=True).start()

    def worker(self, n, pmax, seed):
        q = self.app.q
        try:
            cost = sk_costs(n, seed)
            emin = min(cost)
            q.put((self, ("inst", emin / n)))

            def report(p, fx, gs, bs, re, im):
                pg = sum(re[x] ** 2 + im[x] ** 2 for x in range(len(cost)) if cost[x] <= emin + 1e-9)
                q.put((self, ("step", p, fx / n, gs, bs, pg)))

            optimise_depths(cost, n, pmax, linspace(0.1, 1.2, 9), linspace(0.1, 1.4, 8), report, restarts=3, seed=seed)
            q.put((self, ("done",)))
        except Exception as e:  # report instead of crashing the GUI
            q.put((self, ("error", str(e))))

    def on_msg(self, msg):
        if msg[0] == "inst":
            self.emin = msg[1]
            self.status = "Optimising p = 1..."
        elif msg[0] == "step":
            self.results.append(msg[1:])
            if msg[1] < self.pmax:
                self.status = "Optimising p = %d..." % (msg[1] + 1)
        elif msg[0] == "done":
            self.running = False
            self.status = "Finished."
        else:
            self.running = False
            self.status = "Error: " + msg[1]

    def text(self):
        s = self.err_seg()
        s += [("Status: " + self.status + "\n\n", "h")]
        if self.emin is not None:
            rows = ["  exact ground state  -E/n = %.4f" % (-self.emin),
                    "  Parisi value (n->inf)     = %.4f" % PARISI, "",
                    "  p   -<C>/n   ratio   P(ground)"]
            for p, e, gs, bs, pg in self.results:
                rows.append("  %d   %.4f   %.3f   %.3f" % (p, -e, e / self.emin, pg))
            s += [("Results\n", "h"), ("\n".join(rows) + "\n\n", "m")]
        s += [("The SK spin glass\n", "h"),
              ("  C(z) = (1/sqrt n) sum_{j<k} J_jk z_j z_k,  J_jk ~ N(0,1),  z = +/-1\n\n", "m"),
              ("Every spin talks to every other with a random sign. Finding the minimum "
               "is hard in general, but as n -> infinity the typical ground-state energy "
               "per spin is known exactly: min C / n -> -0.763166..., the Parisi value. "
               "For small n the exact minimum fluctuates from instance to instance; change "
               "the seed to see it.\n\n", ""),
              ("QAOA\n", "h"),
              ("  |g,b> = e^(-i b_p B) e^(-i g_p C) ... e^(-i b_1 B) e^(-i g_1 C) |+>^n\n"
               "  B = sum_j X_j,   minimise <g,b| C |g,b> over 2p angles\n\n", "m"),
              ("This app simulates the full quantum state (2^n complex amplitudes) and tunes "
               "the angles by coordinate descent. Depth p is warm-started from depth p-1 "
               "(INTERP), so the energy can only improve as p grows. 'ratio' is <C>/C_min "
               "and P(ground) is the chance a measurement returns an optimal string.\n\n", ""),
              ("The conjecture\n", "h"),
              ("Basso, Farhi, Marwaha, Villalonga and Zhou (2021) conjectured\n", ""),
              ("  lim_{p->inf} lim_{n->inf} min <C>/n = -Parisi\n", "m"),
              ("i.e. QAOA is asymptotically optimal on typical SK instances. The order of "
               "limits matters: at fixed p, as n grows QAOA is a local algorithm. In the MIT "
               "obituary, Edward Farhi says an AI recently proved this conjecture.\n\n", ""),
              ("Speed: n = 10 and p = 5 can take a minute or more on a phone.\n", "")]
        return s

    def draw(self, c, W, H):
        app = self.app
        if not self.results:
            f = app.F(app.small)
            msg = self.status if self.running else "Press Run QAOA to simulate."
            for j, ln in enumerate(app.wrap(msg, f, W - 20)):
                c.create_text(W / 2, H / 2 + j * f.metrics("linespace"), text=ln, font=f, fill=COL["muted"])
            return
        P = len(self.results)
        if self.view.get() == "energy":
            xs = [r[0] for r in self.results]
            ys = [-r[1] for r in self.results]
            series = [dict(label="QAOA -<C>/n", color=COL["a"], xs=xs, ys=ys, marker=True),
                      dict(label="exact (this n) %.3f" % (-self.emin), color=COL["c"],
                           xs=[0.5, self.pmax + 0.5], ys=[-self.emin] * 2, dash=(8, 5)),
                      dict(label="Parisi 0.763", color=COL["b"], xs=[0.5, self.pmax + 0.5], ys=[PARISI] * 2)]
            lo = min(ys + [-self.emin, PARISI])
            hi = max(ys + [-self.emin, PARISI])
            app.plot_xy(c, W, H, series, "depth p", "energy per spin  -<C>/n",
                        xlim=(0.5, self.pmax + 0.5), ylim=(min(0, lo), hi * 1.08), int_x=True)
        else:
            p, e, gs, bs, pg = self.results[-1]
            idx = list(range(1, p + 1))
            series = [dict(label="gamma_i (phase)", color=COL["a"], xs=idx, ys=gs, marker=True),
                      dict(label="beta_i (mixer)", color=COL["c"], xs=idx, ys=bs, marker=True)]
            allv = gs + bs
            app.plot_xy(c, W, H, series, "layer i  (depth p = %d)" % p, "angle (radians)",
                        xlim=(0.5, p + 0.5), ylim=(min(0, min(allv)) - 0.05, max(allv) * 1.15 + 0.05), int_x=True)


# ----------------------------------------------------------------------------
# 7  Ring of disagrees
# ----------------------------------------------------------------------------
class Ring(Section):
    title = "7  Ring QAOA"
    fields = [("n", "ring size n (6, 8, 10)", 10), ("p", "max depth p", 3)]

    def __init__(self, app):
        self.results = []
        self.running = False
        self.status = "Press Run QAOA to start."
        Section.__init__(self, app)

    def buttons(self):
        return [("Run QAOA", self.run)]

    def run(self):
        if self.running:
            return
        try:
            n = self.num("n", 6, 10, integer=True)
            if n % 2:
                raise ValueError("ring size n must be even (6, 8 or 10)")
            pmax_ok = (n - 4) // 2
            p = self.num("p", 1, pmax_ok, integer=True)
            self.error = None
        except ValueError as e:
            self.error = str(e)
            self.app.show(self.text())
            return
        self.n, self.pmax = n, p
        self.results, self.running = [], True
        self.status = "Optimising p = 1..."
        self.app.redraw()
        self.app.show(self.text())
        threading.Thread(target=self.worker, args=(n, p), daemon=True).start()

    def worker(self, n, pmax):
        q = self.app.q
        try:
            neg = [-v for v in ring_cut(n)]

            def report(p, fx, gs, bs, re, im):
                q.put((self, ("step", p, -fx / n)))

            optimise_depths(neg, n, pmax, linspace(0.1, 3.0, 10), linspace(0.1, 1.5, 8), report, restarts=5)
            q.put((self, ("done",)))
        except Exception as e:
            q.put((self, ("error", str(e))))

    def on_msg(self, msg):
        if msg[0] == "step":
            self.results.append((msg[1], msg[2]))
            if msg[1] < self.pmax:
                self.status = "Optimising p = %d..." % (msg[1] + 1)
        elif msg[0] == "done":
            self.running = False
            self.status = "Finished."
        else:
            self.running = False
            self.status = "Error: " + msg[1]

    def text(self):
        s = self.err_seg()
        s += [("Status: " + self.status + "\n\n", "h")]
        if self.results:
            rows = ["  p   QAOA ratio   (2p+1)/(2p+2)   difference"]
            for p, r in self.results:
                fr = (2 * p + 1) / (2 * p + 2)
                rows.append("  %d    %.6f      %.6f       %.1e" % (p, r, fr, abs(r - fr)))
            s += [("Results\n", "h"), ("\n".join(rows) + "\n\n", "m")]
        s += [("MaxCut on a ring\n", "h"),
              ("  C = sum_j (1 - Z_j Z_{j+1}) / 2   on a ring of n vertices\n\n", "m"),
              ("For even n the best cut uses all n edges, so the approximation ratio is "
               "<C>/n.\n\n", ""),
              ("Farhi-Goldstone-Gutmann conjecture (2014)\n", "h"),
              ("Depth-p QAOA on the ring achieves exactly\n", ""),
              ("  ratio = (2p+1)/(2p+2)   ->  3/4, 5/6, 7/8, ...\n\n", "m"),
              ("Why ring size matters: QAOA is local. After p layers, each edge term only "
               "involves qubits within distance p, a path of 2p+2 vertices. If n is at "
               "least 2p+4, that neighbourhood never wraps around the ring, so a small "
               "ring gives the same answer as an infinite one. That's why the app limits p "
               "to (n-4)/2.\n\n", ""),
              ("A June 2026 MIT paper reports a Lean-verified proof of this conjecture "
               "for all p, found with the AI model Claude Fable 5.\n", "")]
        return s

    def draw(self, c, W, H):
        app = self.app
        pm = max(3, self.pmax if self.results else 3)
        ps = linspace(1, pm, 60)
        series = [dict(label="(2p+1)/(2p+2)", color=COL["b"], xs=ps, ys=[(2 * p + 1) / (2 * p + 2) for p in ps])]
        if self.results:
            series.append(dict(label="QAOA simulation", color=COL["a"],
                               xs=[r[0] for r in self.results], ys=[r[1] for r in self.results],
                               line=False, marker=True))
        app.plot_xy(c, W, H, series, "depth p", "approximation ratio",
                    xlim=(0.5, pm + 0.5), ylim=(0.7, 0.92), int_x=True)


# ----------------------------------------------------------------------------
# Application shell
# ----------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Goldstone Explorer")
        root.configure(bg=COL["bg"])
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        short = min(sw, sh)
        self.base = max(13, min(40, int(short / 30)))
        self.small = max(11, int(self.base * 0.8))
        self.cols = max(1, min(3, sw // (self.base * 11)))
        self.fonts = {}
        root.option_add("*Font", self.F(self.base))
        self.q = queue.Queue()

        self.sections = [Overview(self), Hat(self), Dispersion(self), Counting(self),
                         Higgs(self), QaoaSK(self), Ring(self)]
        self.cur = self.sections[0]

        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=5)
        root.rowconfigure(3, weight=4)

        # top bar: section picker + prev/next
        top = tk.Frame(root, bg=COL["panel"])
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        bfont = self.F(self.base, True)
        tk.Button(top, text=" < ", font=bfont, command=lambda: self.step(-1),
                  relief="flat", bg=COL["panel"]).grid(row=0, column=0, padx=4, pady=4)
        self.sec_var = tk.StringVar(value=self.cur.title)
        om = tk.OptionMenu(top, self.sec_var, *[s.title for s in self.sections], command=self.pick)
        om.config(font=bfont, bg=COL["panel"], highlightthickness=0, relief="flat")
        om["menu"].config(font=self.F(self.base))
        om.grid(row=0, column=1, sticky="ew", pady=4)
        tk.Button(top, text=" > ", font=bfont, command=lambda: self.step(1),
                  relief="flat", bg=COL["panel"]).grid(row=0, column=2, padx=4, pady=4)

        self.inp = None

        self.canvas = tk.Canvas(root, bg=COL["bg"], highlightthickness=0, height=10)
        self.canvas.grid(row=2, column=0, sticky="nsew", padx=4, pady=(2, 2))
        self.canvas.bind("<Configure>", lambda e: self.schedule_redraw())
        self._pending = None

        tf = tk.Frame(root, bg=COL["bg"])
        tf.grid(row=3, column=0, sticky="nsew")
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        self.txt = tk.Text(tf, wrap="word", height=4, bg=COL["panel"], fg=COL["fg"],
                           relief="flat", padx=10, pady=8, font=self.F(self.small))
        self.txt.grid(row=0, column=0, sticky="nsew")
        sb = tk.Scrollbar(tf, command=self.txt.yview, width=max(16, self.base))
        sb.grid(row=0, column=1, sticky="ns")
        self.txt.config(yscrollcommand=sb.set)
        self.txt.tag_config("h", font=self.F(self.small, True), foreground=COL["a"], spacing1=4)
        self.txt.tag_config("m", font=tkfont.Font(root=root, family="Courier", size=-int(self.small * 0.92)),
                            foreground="#333")
        self.txt.tag_config("err", foreground=COL["b"], font=self.F(self.small, True))
        # touch-drag scrolling for phones
        self.txt.bind("<Button-1>", lambda e: self.txt.scan_mark(e.x, e.y))
        self.txt.bind("<B1-Motion>", lambda e: (self.txt.scan_dragto(e.x, e.y, gain=1), "break")[1])

        self.activate(self.cur)
        root.after(150, self.poll)

    # ---- fonts and text fitting --------------------------------------------
    def F(self, px, bold=False):
        key = (int(px), bold)
        if key not in self.fonts:
            self.fonts[key] = tkfont.Font(root=self.root, family="Helvetica", size=-int(px),
                                          weight="bold" if bold else "normal")
        return self.fonts[key]

    @staticmethod
    def fit(text, f, maxw):
        if maxw <= 0:
            return ""
        if f.measure(text) <= maxw:
            return text
        s = text
        while s and f.measure(s + "...") > maxw:
            s = s[:-1]
        return s.rstrip() + "..." if s else ""

    @staticmethod
    def wrap(text, f, maxw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.measure(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return [App.fit(l, f, maxw) for l in lines]

    # ---- navigation ----------------------------------------------------------
    def pick(self, title):
        for s in self.sections:
            if s.title == title:
                self.activate(s)

    def step(self, d):
        i = (self.sections.index(self.cur) + d) % len(self.sections)
        self.activate(self.sections[i])

    def activate(self, sec):
        self.cur = sec
        self.sec_var.set(sec.title)
        if self.inp is not None:
            self.inp.destroy()
        self.inp = tk.Frame(self.root, bg=COL["bg"])
        self.inp.grid(row=1, column=0, sticky="ew", padx=4)
        sec.build(self.inp)
        self.show(sec.text())
        self.schedule_redraw()

    def show(self, segs):
        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        for t, tag in segs:
            self.txt.insert("end", t, tag)
        self.txt.config(state="disabled")
        self.txt.yview_moveto(0)

    def schedule_redraw(self):
        if self._pending:
            self.root.after_cancel(self._pending)
        self._pending = self.root.after(40, self.redraw)

    def redraw(self):
        self._pending = None
        c = self.canvas
        c.delete("all")
        W, H = c.winfo_width(), c.winfo_height()
        if W > 40 and H > 40:
            self.cur.draw(c, W, H)

    def poll(self):
        try:
            while True:
                sec, msg = self.q.get_nowait()
                sec.on_msg(msg)
                if sec is self.cur:
                    self.redraw()
                    self.show(sec.text())
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    # ---- drawing helpers ----------------------------------------------------
    def legend(self, c, W, items, y0=8):
        """items: (label, colour, kind) with kind in line/dash/dot/arrow/marker/none.
        Lays out left-to-right and wraps; returns the y below the legend."""
        f = self.F(self.small)
        lh = f.metrics("linespace")
        pad = 10
        sw = lh * 1.6
        x, y = pad, y0
        for lab, col, kind in items:
            room = W - 2 * pad - (sw + 8 if kind != "none" else 0)
            lab = self.fit(lab, f, room)
            w = (sw + 8 if kind != "none" else 0) + f.measure(lab) + lh
            if x + w > W - pad and x > pad:
                x, y = pad, y + lh * 1.25
            cy = y + lh / 2
            if kind in ("line", "dash", "arrow"):
                c.create_line(x, cy, x + sw, cy, fill=col, width=3,
                              dash=(6, 4) if kind == "dash" else (),
                              arrow="last" if kind == "arrow" else "none")
            if kind in ("dot", "marker"):
                r = lh * 0.24
                c.create_oval(x + sw / 2 - r, cy - r, x + sw / 2 + r, cy + r, fill=col, outline=col)
            tx = x + (sw + 8 if kind != "none" else 0)
            c.create_text(tx, cy, text=lab, anchor="w", font=f, fill=COL["fg"])
            x += w
        return y + lh * 1.25 if items else y0

    def plot_xy(self, c, W, H, series, xlabel, ylabel, xlim=None, ylim=None, int_x=False):
        f = self.F(self.small)
        lh = f.metrics("linespace")
        pad = 10
        items = []
        for s in series:
            line, mk = s.get("line", True), s.get("marker", False)
            kind = ("dash" if s.get("dash") else "line") if line else "marker"
            items.append((s["label"], s["color"], kind))
        y = self.legend(c, W, items)
        c.create_text(pad, y + lh / 2, text=self.fit(ylabel, f, W - 2 * pad), anchor="w", font=f, fill=COL["muted"])
        top = y + lh * 1.5
        bottom = H - (lh * 2.5 + pad + 8)
        ph = bottom - top
        if ph < lh * 2:
            return

        allx = [v for s in series for v in s["xs"]]
        ally = [v for s in series for v in s["ys"]]
        x0, x1 = xlim if xlim else (min(allx), max(allx))
        if ylim:
            y0, y1 = ylim
        else:
            y0, y1 = min(ally), max(ally)
            m = (y1 - y0) * 0.06 or 1
            y0, y1 = y0 - m, y1 + m
        if x1 - x0 < 1e-12:
            x1 = x0 + 1
        if y1 - y0 < 1e-12:
            y1 = y0 + 1

        yt, ystep = nice_ticks(y0, y1, max(2, int(ph / (lh * 1.8))))
        yt = [t for t in yt if y0 - 1e-9 <= t <= y1 + 1e-9]
        ylabs = [tick_fmt(t, ystep) for t in yt]
        left = pad + (max(f.measure(s) for s in ylabs) if ylabs else 0) + 8
        right = W - pad - 4
        pw = right - left
        if pw < 40:
            return

        if int_x:
            ints = list(range(int(math.ceil(x0)), int(math.floor(x1)) + 1))
            wl = max([f.measure(str(i)) for i in ints] + [1])
            k = 1
            while ints and len(ints[::k]) * (wl + lh) > pw:
                k += 1
            xt = ints[::k]
            xlabs = [str(i) for i in xt]
        else:
            nx = 8
            while True:
                xt, xstep = nice_ticks(x0, x1, nx)
                xt = [t for t in xt if x0 - 1e-9 <= t <= x1 + 1e-9]
                xlabs = [tick_fmt(t, xstep) for t in xt]
                need = sum(f.measure(s) + lh for s in xlabs)
                if need <= pw or nx <= 2:
                    break
                nx -= 1

        X = lambda v: left + (v - x0) / (x1 - x0) * pw
        Y = lambda v: bottom - (v - y0) / (y1 - y0) * ph

        for t, s in zip(yt, ylabs):
            c.create_line(left, Y(t), right, Y(t), fill=COL["grid"])
            c.create_text(left - 6, Y(t), text=s, anchor="e", font=f, fill=COL["muted"])
        xly = bottom + lh / 2 + 4      # below the lowest y-tick label, so corners never collide
        for t, s in zip(xt, xlabs):
            c.create_line(X(t), top, X(t), bottom, fill=COL["grid"])
            half = f.measure(s) / 2
            cx = min(max(X(t), half + 2), W - 2 - half)   # keep the label on screen
            c.create_text(cx, xly, text=s, anchor="n", font=f, fill=COL["muted"])
        c.create_rectangle(left, top, right, bottom, outline=COL["muted"])
        c.create_text((left + right) / 2, xly + lh + 4, text=self.fit(xlabel, f, pw),
                      anchor="n", font=f, fill=COL["fg"])

        def inside(xv, yv):
            return x0 - 1e-9 <= xv <= x1 + 1e-9 and y0 - 1e-9 <= yv <= y1 + 1e-9

        for s in series:
            col = s["color"]
            if s.get("line", True):
                run = []
                for xv, yv in zip(s["xs"], s["ys"]):
                    if inside(xv, yv):
                        run += [X(xv), Y(yv)]
                    else:
                        if len(run) >= 4:
                            c.create_line(*run, fill=col, width=s.get("width", 3), dash=s.get("dash") or ())
                        run = []
                if len(run) >= 4:
                    c.create_line(*run, fill=col, width=s.get("width", 3), dash=s.get("dash") or ())
            if s.get("marker"):
                r = max(4, lh * 0.22)
                for xv, yv in zip(s["xs"], s["ys"]):
                    if inside(xv, yv):
                        c.create_oval(X(xv) - r, Y(yv) - r, X(xv) + r, Y(yv) + r,
                                      fill=col, outline="white", width=1.5)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
