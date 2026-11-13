#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yang-Mills Explorer
===================
An interactive, illustrated explanation of the Yang-Mills existence result
(the AI-generated proof affirmed by David Gross's panel, November 2026) and
of the mathematics behind it.

* Runs in Pydroid 3 on Android and in ordinary desktop Python.
* Uses only the standard library: tkinter + math. Nothing to install.
* Every piece of text and graphics is placed by a flow-layout engine that
  measures what it has just drawn before placing the next item, so text
  and graphics never overlap, whatever the screen size or font.

How to use
----------
Tap the arrow buttons or the menu in the top bar to change section. Sections
marked "[calc]" have input boxes: edit the numbers, then tap "Compute" to see
the results and graphs. Drag the page up and down with a finger to scroll.

Notation in formulas: _ means subscript, ^ means superscript,
e.g. A_mu^a is A with subscript mu and superscript a.
"""

import math
import os
import sys
import tkinter as tk
import tkinter.font as tkfont

IS_ANDROID = ("ANDROID_ROOT" in os.environ) or hasattr(sys, "getandroidapilevel")

HBARC = 0.1973269804          # hbar*c in GeV*fm
GEV_PER_FM_IN_N = 160217.6634  # 1 GeV/fm expressed in newtons
G_STD = 9.80665                # standard gravity, m/s^2

# ---------------------------------------------------------------- colours --
BG = "#15171a"
CARD = "#23262b"
FIELD = "#30343a"
FG = "#ecebe6"
MUTED = "#a5a9b0"
LINE = "#4a4e55"
GRID = "#2b2e34"
ACCENT = "#7fb0e0"
GOOD = "#6cc596"
WARN = "#ef9a73"
PURPLE = "#c39be8"
SOFT_ACC = "#1e2b38"
SOFT_GOOD = "#1c2f25"
SOFT_WARN = "#38261e"


# =========================================================== physics core ==
def b0_coeff(n_colours, n_flavours=0):
    """One-loop beta-function coefficient for SU(N) with nf quark flavours."""
    return 11.0 * n_colours / 3.0 - 2.0 * n_flavours / 3.0


def alpha_one_loop(mu_over_lambda, n_colours, n_flavours=0):
    """alpha = g^2/(4 pi) = 4 pi / (b0 ln(mu^2/Lambda^2))."""
    b0 = b0_coeff(n_colours, n_flavours)
    log_term = math.log(mu_over_lambda ** 2)
    return 4.0 * math.pi / (b0 * log_term)


def plaquette_terms(f, eps):
    """SU(2) plaquette U_p = exp(i theta sigma3/2), theta = eps^2 f.
    Returns theta, exact Re tr(1-U_p), continuum approximation, rel. error."""
    theta = eps * eps * f
    exact = 2.0 - 2.0 * math.cos(theta / 2.0)
    approx = theta * theta / 4.0
    rel = (approx - exact) / exact if exact != 0 else 0.0
    return theta, exact, approx, rel


def rg_flow(n_colours, g2_start, block, max_steps, g2_strong=4.0 * math.pi):
    """Toward coarser scales: 1/g^2_(k+1) = 1/g^2_k - (b0/8 pi^2) ln L.
    Returns the list of couplings and the first step k* where g^2 >= g2_strong
    (or None if never reached)."""
    b0 = b0_coeff(n_colours)
    dec = b0 * math.log(block) / (8.0 * math.pi ** 2)
    inv = 1.0 / g2_start
    values = [g2_start]
    k_star = None
    for k in range(1, max_steps + 1):
        inv -= dec
        if inv <= 1.0 / g2_strong:
            values.append(float("inf"))
            k_star = k
            break
        values.append(1.0 / inv)
    return values, k_star


def cornell_potential(r_fm, sigma_gev2, coulomb_c):
    """V(R) = sigma R / (hbar c) - c (hbar c) / R, in GeV (R in fm)."""
    return sigma_gev2 * r_fm / HBARC - coulomb_c * HBARC / r_fm


# =========================================================== small helpers ==
def nice_step(span, n):
    if span <= 0:
        return 1.0
    raw = span / max(n, 1)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw - 1e-15:
            return m * mag
    return 10 * mag


def fmt(v, sig=3):
    if v == 0:
        return "0"
    if not math.isfinite(v):
        return "inf"
    a = abs(v)
    if a >= 1e5 or a < 1e-3:
        s = "%.*e" % (max(sig - 1, 0), v)
        mant, ex = s.split("e")
        if "." in mant:
            mant = mant.rstrip("0").rstrip(".")
        return "%se%d" % (mant, int(ex))
    s = "%.*g" % (sig, v)
    if "e" in s:
        s = ("%f" % v).rstrip("0").rstrip(".")
    return s


def linear_ticks(lo, hi, n):
    step = nice_step(hi - lo, n)
    ticks = []
    v = math.ceil(lo / step - 1e-9) * step
    while v <= hi + 1e-9 * max(abs(step), 1e-300):
        ticks.append(round(v / step) * step)
        v += step
    return ticks


# =========================================================== layout engine ==
class Page:
    """Flow layout on a Canvas. Every call draws, measures the real
    bounding box, and moves the cursor below it, so nothing overlaps."""

    def __init__(self, app):
        self.app = app
        self.c = app.canvas
        self.W = app.W
        self.F = app.fonts
        self.pad = max(10, int(self.W * 0.045))
        self.inner = self.W - 2 * self.pad
        self.lh = self.F["body"].metrics("linespace")
        self.slh = self.F["small"].metrics("linespace")
        self.y = self.pad
        self.marks = {}

    # ---- primitives
    def _text_at(self, x, y, s, font, color, width, anchor="nw", justify="left"):
        item = self.c.create_text(x, y, text=s, anchor=anchor, width=max(width, 20),
                                  font=self.F[font], fill=color, justify=justify)
        b = self.c.bbox(item)
        if b is None:
            b = (x, y, x, y)
        return b

    def text(self, s, font="body", color=FG, indent=0, gap=None, center=False):
        width = self.inner - indent
        if center:
            b = self._text_at(self.pad + self.inner / 2.0, self.y, s, font, color,
                              width, anchor="n", justify="center")
        else:
            b = self._text_at(self.pad + indent, self.y, s, font, color, width)
        self.y = b[3] + (int(self.lh * 0.45) if gap is None else gap)
        return b

    def space(self, factor=0.5):
        self.y += int(self.lh * factor)

    def mark(self, name):
        self.marks[name] = max(self.y - self.pad, 0)

    def h1(self, s):
        b = self.text(s, "h1", FG, gap=int(self.lh * 0.25))
        self.c.create_rectangle(self.pad, self.y, self.pad + int(self.inner * 0.25),
                                self.y + max(3, int(self.lh * 0.12)), fill=ACCENT, outline="")
        self.y += int(self.lh * 0.7)
        return b

    def h2(self, s):
        self.space(0.4)
        self.c.create_line(self.pad, self.y, self.pad + self.inner, self.y, fill=LINE)
        self.y += int(self.lh * 0.45)
        return self.text(s, "h2", FG, gap=int(self.lh * 0.3))

    def bullets(self, items, color=FG, font="body"):
        bw = self.F[font].measure("•  ")
        for s in items:
            top = self.y
            self.c.create_text(self.pad, top, text="•", anchor="nw", font=self.F[font], fill=ACCENT)
            b = self._text_at(self.pad + bw, top, s, font, color, self.inner - bw)
            self.y = b[3] + int(self.lh * 0.3)
        self.y += int(self.lh * 0.2)

    def card(self, parts, fill=CARD, outline=LINE, x=None, width=None, advance=True):
        """parts: list of (text, font, colour). Draws text, then a box behind."""
        x = self.pad if x is None else x
        width = self.inner if width is None else width
        p = int(self.lh * 0.55)
        top = self.y
        y = top + p
        for i, (s, font, color) in enumerate(parts):
            b = self._text_at(x + p, y, s, font, color, width - 2 * p)
            y = b[3] + (int(self.lh * 0.3) if i < len(parts) - 1 else 0)
        bottom = y + p
        r = self.c.create_rectangle(x, top, x + width, bottom, fill=fill, outline=outline, width=2)
        self.c.tag_lower(r)
        if advance:
            self.y = bottom + int(self.lh * 0.6)
        return top, bottom, r

    def formula(self, lines, note=None):
        parts = [(s, "math", ACCENT) for s in lines]
        if note:
            parts.append((note, "small", MUTED))
        self.card(parts, fill=SOFT_ACC, outline=ACCENT)

    def callout(self, label, body, kind="def"):
        fill, outline, col = {"def": (SOFT_ACC, ACCENT, ACCENT),
                              "ok": (SOFT_GOOD, GOOD, GOOD),
                              "open": (SOFT_WARN, WARN, WARN)}[kind]
        self.card([(label.upper(), "tag", col), (body, "body", FG)], fill=fill, outline=outline)

    def two_cards(self, left, right, styles):
        gap = int(self.lh * 0.5)
        w = (self.inner - gap) / 2.0
        top = self.y
        bottoms = []
        rects = []
        for i, parts in enumerate((left, right)):
            self.y = top
            t, b, r = self.card(parts, fill=styles[i][0], outline=styles[i][1],
                                x=self.pad + i * (w + gap), width=w, advance=False)
            bottoms.append(b)
            rects.append(r)
        bottom = max(bottoms)
        for i, r in enumerate(rects):
            x0 = self.pad + i * (w + gap)
            self.c.coords(r, x0, top, x0 + w, bottom)
        self.y = bottom + int(self.lh * 0.6)
        return top, bottom

    def arrow_down(self, x=None, color=MUTED):
        x = self.pad + self.inner / 2.0 if x is None else x
        h = int(self.lh * 1.1)
        top = self.y - int(self.lh * 0.45)
        self.c.create_line(x, top, x, top + h, fill=color, width=max(2, self.lh // 14),
                           arrow="last", arrowshape=self._arrowshape())
        self.y = top + h + int(self.lh * 0.25)

    def _arrowshape(self):
        a = max(8, int(self.lh * 0.35))
        return (a, int(a * 1.2), int(a * 0.45))

    def swatch_text(self, color, s, dashed=False):
        sw = int(self.slh * 0.75)
        top = self.y
        cy = top + self.slh / 2.0
        if dashed:
            self.c.create_line(self.pad, cy, self.pad + sw, cy, fill=color, width=3, dash=(4, 3))
        else:
            self.c.create_rectangle(self.pad, cy - sw / 2.0, self.pad + sw, cy + sw / 2.0,
                                    fill=color, outline="")
        b = self._text_at(self.pad + sw + int(self.slh * 0.5), top, s, "small", FG,
                          self.inner - sw - int(self.slh * 0.5))
        self.y = max(b[3], top + self.slh) + int(self.slh * 0.25)

    def widget(self, w):
        self.c.update_idletasks()
        item = self.c.create_window(self.pad, self.y, window=w, anchor="nw", width=self.inner)
        self.c.update_idletasks()
        h = max(w.winfo_reqheight(), w.winfo_height())
        self.app.widgets.append(w)
        self.y += h + int(self.lh * 0.6)
        return item

    def table(self, header, rows):
        """Aligned monospace table if it fits; otherwise one card per row."""
        cols = len(header)
        cells = [header] + rows
        widths = [max(len(r[i]) for r in cells) for i in range(cols)]
        lines = ["  ".join(r[i].rjust(widths[i]) for i in range(cols)) for r in cells]
        if self.F["mono"].measure(max(lines, key=len)) + int(self.lh * 1.2) <= self.inner:
            parts = [(lines[0], "mono", MUTED)] + [(ln, "mono", FG) for ln in lines[1:]]
            self.card(parts)
        else:
            for r in rows:
                parts = [("%s: %s" % (header[i], r[i]), "small", FG if i else ACCENT)
                         for i in range(cols)]
                self.card(parts)


# =========================================================== chart drawing ==
def line_chart(pg, series, title, xlabel, xlog=False, xr=None, yr=None,
               hlines=(), vlines=(), legend=()):
    """series: list of dicts {x:[], y:[], color, width, points:[(x,y)]}.
    Labels are never drawn inside the plot; legend goes below."""
    c = pg.c
    F = pg.F["small"]
    lh = F.metrics("linespace")
    pg.text(title, "bold", gap=int(lh * 0.35))

    xs = [x for s in series for x in s["x"]]
    ys = [y for s in series for y in s["y"] if y is not None and math.isfinite(y)]
    xmin, xmax = xr if xr else (min(xs), max(xs))
    ymin, ymax = yr if yr else (min(ys), max(ys))
    if ymax - ymin < 1e-12:
        ymax = ymin + 1.0
    tx = (lambda v: math.log10(v)) if xlog else (lambda v: v)
    txmin, txmax = tx(xmin), tx(xmax)
    if txmax - txmin < 1e-12:
        txmax = txmin + 1.0

    H = max(int(lh * 7), int(pg.inner * 0.62))
    yt = linear_ticks(ymin, ymax, max(2, int(H / (lh * 2.2))))
    ylabs = [fmt(v) for v in yt]
    left = max([F.measure(s) for s in ylabs] + [0]) + int(lh * 0.6)

    if xlog:
        xt = [10.0 ** d for d in range(int(math.floor(txmin)), int(math.ceil(txmax)) + 1)
              if txmin - 1e-9 <= d <= txmax + 1e-9]
        if len(xt) < 2:
            xt = [xmin, xmax]
    else:
        guess_w = max(F.measure(fmt(xmin)), F.measure(fmt(xmax))) + lh
        nx = max(2, int((pg.inner - left) / (guess_w * 1.6)))
        xt = linear_ticks(xmin, xmax, nx)
    xlabs = [fmt(v) for v in xt]
    rightpad = (F.measure(xlabs[-1]) // 2 + 4) if xlabs else 4

    X0 = pg.pad + left
    X1 = pg.pad + pg.inner - rightpad
    Y0 = pg.y + lh // 2 + 2
    Y1 = Y0 + H

    def px(x):
        return X0 + (tx(x) - txmin) / (txmax - txmin) * (X1 - X0)

    def py(y):
        return Y1 - (y - ymin) / (ymax - ymin) * (Y1 - Y0)

    # grid + y labels
    last = None
    for v, s in zip(yt, ylabs):
        Y = py(v)
        c.create_line(X0, Y, X1, Y, fill=GRID)
        if last is None or abs(Y - last) >= lh * 1.05:
            c.create_text(X0 - int(lh * 0.3), Y, text=s, anchor="e", font=F, fill=MUTED)
            last = Y
    c.create_rectangle(X0, Y0, X1, Y1, outline=LINE, width=2)

    # x labels (start below the half-height of the lowest y label)
    xl_top = Y1 + lh // 2 + 4
    last_right = -1e9
    for v, s in zip(xt, xlabs):
        if v < xmin - 1e-12 or v > xmax + 1e-12:
            continue
        X = px(v)
        w = F.measure(s)
        c.create_line(X, Y1, X, Y1 + 5, fill=LINE)
        if X - w / 2.0 >= last_right + lh * 0.5 and X + w / 2.0 <= pg.pad + pg.inner:
            c.create_text(X, xl_top, text=s, anchor="n", font=F, fill=MUTED)
            last_right = X + w / 2.0

    # reference lines
    for (yv, col) in hlines:
        if ymin <= yv <= ymax:
            c.create_line(X0, py(yv), X1, py(yv), fill=col, width=2, dash=(6, 4))
    for (xv, col) in vlines:
        if xmin <= xv <= xmax:
            c.create_line(px(xv), Y0, px(xv), Y1, fill=col, width=2, dash=(6, 4))

    # data, broken into segments where a point leaves the window
    for s in series:
        seg = []
        for x, y in zip(s["x"], s["y"]):
            ok = (y is not None and math.isfinite(y) and ymin <= y <= ymax
                  and xmin <= x <= xmax)
            if ok:
                seg += [px(x), py(y)]
            else:
                if len(seg) >= 4:
                    c.create_line(*seg, fill=s["color"], width=s.get("width", 3))
                seg = []
        if len(seg) >= 4:
            c.create_line(*seg, fill=s["color"], width=s.get("width", 3))
        for (x, y) in s.get("points", []):
            if ymin <= y <= ymax and xmin <= x <= xmax:
                r = max(5, lh // 4)
                c.create_oval(px(x) - r, py(y) - r, px(x) + r, py(y) + r,
                              fill=s["color"], outline=FG, width=2)

    pg.y = xl_top + lh + int(lh * 0.25)
    pg.text(xlabel, "small", MUTED, center=True, gap=int(lh * 0.4))
    for item in legend:
        pg.swatch_text(*item)
    pg.space(0.5)


def bar_chart(pg, values, title, xlabel, threshold=None, cap=None):
    c = pg.c
    F = pg.F["small"]
    lh = F.metrics("linespace")
    pg.text(title, "bold", gap=int(lh * 0.35))
    finite = [v for v in values if math.isfinite(v)]
    top_v = cap if cap is not None else max(finite + [threshold or 0])
    yt = linear_ticks(0, top_v, 5)
    ylabs = [fmt(v) for v in yt]
    left = max(F.measure(s) for s in ylabs) + int(lh * 0.6)
    H = max(int(lh * 7), int(pg.inner * 0.6))
    X0 = pg.pad + left
    X1 = pg.pad + pg.inner - 4
    Y0 = pg.y + lh // 2 + 2
    Y1 = Y0 + H
    ymax = max(yt[-1], top_v)

    def py(v):
        return Y1 - min(v, ymax) / ymax * (Y1 - Y0)

    last = None
    for v, s in zip(yt, ylabs):
        Y = py(v)
        c.create_line(X0, Y, X1, Y, fill=GRID)
        if last is None or abs(Y - last) >= lh * 1.05:
            c.create_text(X0 - int(lh * 0.3), Y, text=s, anchor="e", font=F, fill=MUTED)
            last = Y
    n = len(values)
    pitch = (X1 - X0) / float(n)
    bw = max(1.0, pitch * 0.7)
    for i, v in enumerate(values):
        cx = X0 + pitch * (i + 0.5)
        vv = ymax if not math.isfinite(v) else v
        col = WARN if (threshold is not None and (not math.isfinite(v) or v >= threshold)) else ACCENT
        c.create_rectangle(cx - bw / 2, py(vv), cx + bw / 2, Y1, fill=col, outline="")
    c.create_rectangle(X0, Y0, X1, Y1, outline=LINE, width=2)
    if threshold is not None and threshold <= ymax:
        c.create_line(X0, py(threshold), X1, py(threshold), fill=WARN, width=2, dash=(6, 4))
    # x labels with automatic thinning
    xl_top = Y1 + lh // 2 + 4
    labw = F.measure(str(n - 1)) + lh * 0.6
    step = max(1, int(math.ceil(labw / pitch)))
    last_right = -1e9
    for i in range(0, n, step):
        cx = X0 + pitch * (i + 0.5)
        s = str(i)
        w = F.measure(s)
        if cx - w / 2.0 >= last_right + lh * 0.3 and cx + w / 2.0 <= pg.pad + pg.inner:
            c.create_text(cx, xl_top, text=s, anchor="n", font=F, fill=MUTED)
            last_right = cx + w / 2.0
    pg.y = xl_top + lh + int(lh * 0.25)
    pg.text(xlabel, "small", MUTED, center=True, gap=int(lh * 0.4))


# ======================================================== special diagrams ==
def spectrum_diagram(pg, gapped):
    """Energy axis: 0, Delta, 2 Delta at fixed fractions so labels never touch."""
    c = pg.c
    F = pg.F["small"]
    lh = F.metrics("linespace")
    xa = pg.pad + pg.F["small"].measure("0") + 6
    xb = pg.pad + pg.inner - F.measure("E") - 12
    top = pg.y
    yl = top + int(lh * 1.0)
    w = max(2, lh // 10)
    c.create_line(xa, yl, xb, yl, fill=FG, width=w, arrow="last", arrowshape=pg._arrowshape())
    c.create_text(xb + 6, yl, text="E", anchor="w", font=F, fill=FG)
    band_h = max(6, int(lh * 0.35))
    if gapped:
        xd = xa + (xb - xa) * 0.40
        x2 = xa + (xb - xa) * 0.80
        c.create_rectangle(xd, yl - band_h, xb - 4, yl + band_h, fill=WARN, outline="")
        c.create_line(x2, yl - band_h * 1.6, x2, yl + band_h * 1.6, fill=FG, width=2)
        c.create_line(xd, yl - band_h * 1.6, xd, yl + band_h * 1.6, fill=FG, width=2)
        c.create_text(xd, yl + band_h * 1.6 + 2, text="Δ", anchor="n", font=F, fill=WARN)
        c.create_text(x2, yl + band_h * 1.6 + 2, text="2Δ", anchor="n", font=F, fill=FG)
        c.create_line(xa + 8, yl - band_h * 2.4, xd - 8, yl - band_h * 2.4, fill=MUTED,
                      width=2, arrow="both", arrowshape=pg._arrowshape())
    else:
        c.create_rectangle(xa, yl - band_h, xb - 4, yl + band_h, fill=ACCENT, outline="")
    r = max(5, lh // 4)
    c.create_oval(xa - r, yl - r, xa + r, yl + r, fill=GOOD, outline=FG, width=2)
    c.create_text(xa, yl + band_h * 1.6 + 2, text="0", anchor="n", font=F, fill=FG)
    pg.y = yl + band_h * 1.6 + 2 + lh + int(lh * 0.4)


def plaquette_diagram(pg):
    c = pg.c
    F = pg.F["small"]
    lh = F.metrics("linespace")
    labels = ("U₁", "U₂", "U₃⁻¹", "U₄⁻¹")
    lw = max(F.measure(s) for s in labels) + int(lh * 0.6)
    side = int(min(pg.inner - 2 * lw - 2 * lh, pg.inner * 0.55))
    side = max(side, int(lh * 4))
    cx = pg.pad + pg.inner / 2.0
    x0, x1 = cx - side / 2.0, cx + side / 2.0
    y0 = pg.y + lh + 6
    y1 = y0 + side
    # background lattice
    n = 3
    for i in range(-1, n + 2):
        gx = x0 + i * side
        if pg.pad <= gx <= pg.pad + pg.inner:
            c.create_line(gx, y0 - lh * 0.5, gx, y1 + lh * 0.5, fill=GRID, width=2)
    for gy in (y0, y1):
        c.create_line(pg.pad, gy, pg.pad + pg.inner, gy, fill=GRID, width=2)
    c.create_rectangle(x0, y0, x1, y1, fill=SOFT_ACC, outline="")
    wdt = max(3, lh // 7)
    sh = pg._arrowshape()
    inset = side * 0.06
    c.create_line(x0, y1, x1 - inset, y1, fill=ACCENT, width=wdt, arrow="last", arrowshape=sh)
    c.create_line(x1, y1, x1, y0 + inset, fill=ACCENT, width=wdt, arrow="last", arrowshape=sh)
    c.create_line(x1, y0, x0 + inset, y0, fill=ACCENT, width=wdt, arrow="last", arrowshape=sh)
    c.create_line(x0, y0, x0, y1 - inset, fill=ACCENT, width=wdt, arrow="last", arrowshape=sh)
    r = max(4, lh // 5)
    for (px_, py_) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        c.create_oval(px_ - r, py_ - r, px_ + r, py_ + r, fill=FG, outline="")
    gap = int(lh * 0.35)
    c.create_text(cx, y1 + gap, text=labels[0], anchor="n", font=F, fill=FG)
    c.create_text(x1 + gap, (y0 + y1) / 2, text=labels[1], anchor="w", font=F, fill=FG)
    c.create_text(cx, y0 - gap, text=labels[2], anchor="s", font=F, fill=FG)
    c.create_text(x0 - gap, (y0 + y1) / 2, text=labels[3], anchor="e", font=F, fill=FG)
    inner_label = "plaquette p"
    if F.measure(inner_label) < side * 0.8:
        c.create_text(cx, (y0 + y1) / 2, text=inner_label, anchor="center", font=F, fill=ACCENT)
    c.create_text(x0 - r - 2, y1 + gap, text="x", anchor="ne", font=F, fill=MUTED)
    pg.y = y1 + gap + lh + int(lh * 0.5)


def blocking_diagram(pg):
    c = pg.c
    F = pg.F["small"]
    lh = F.metrics("linespace")
    agap = int(lh * 1.6)
    cell = (pg.inner - 2 * agap) / 3.0
    top = pg.y
    caps = ("spacing ε\n8×8 sites\naction S₀",
            "spacing 2ε\n4×4 blocks\naction S₁",
            "spacing 4ε\n2×2 blocks\naction S₂")
    bottoms = []
    for k, n in enumerate((8, 4, 2)):
        x0 = pg.pad + k * (cell + agap)
        c.create_rectangle(x0, top, x0 + cell, top + cell, fill=CARD, outline=LINE, width=2)
        for i in range(1, n):
            g = x0 + cell * i / n
            c.create_line(g, top, g, top + cell, fill=MUTED if n < 8 else LINE)
            gy = top + cell * i / n
            c.create_line(x0, gy, x0 + cell, gy, fill=MUTED if n < 8 else LINE)
        b = pg._text_at(x0 + cell / 2.0, top + cell + int(lh * 0.3), caps[k], "small", FG,
                        cell, anchor="n", justify="center")
        bottoms.append(b[3])
        if k < 2:
            ax0 = x0 + cell + 4
            ax1 = x0 + cell + agap - 4
            c.create_line(ax0, top + cell / 2, ax1, top + cell / 2, fill=ACCENT, width=3,
                          arrow="last", arrowshape=pg._arrowshape())
    pg.y = max(bottoms) + int(lh * 0.6)


# ================================================================= sections ==
def sec_overview(app, pg):
    pg.h1("Yang–Mills existence, explained")
    pg.text("On 26 Oct 2026 OpenAI said an unreleased model had produced a proof that "
            "quantum Yang–Mills theory exists as a rigorous mathematical object. On 10 Nov "
            "2026 a five-member panel chaired by Nobel laureate David Gross reported that the "
            "proof establishes existence of pure Yang–Mills theory under the standard "
            "definitions used in physics and mathematics.")
    pg.text("The Clay Millennium Prize problem has two parts:", "bold")
    pg.card([("Clay Millennium Problem", "bold", FG),
             ("“Yang–Mills existence and mass gap”", "small", MUTED)],
            fill=SOFT_ACC, outline=ACCENT)
    pg.arrow_down()
    pg.two_cards(
        [("Part 1 · Existence", "bold", FG),
         ("A quantum Yang–Mills theory on ℝ⁴ satisfying the axioms of quantum field "
          "theory, for every compact simple group G.", "small", FG),
         ("✓ AI proof, affirmed by the review panel", "small", GOOD)],
        [("Part 2 · Mass gap", "bold", FG),
         ("The energy spectrum has a gap: spec H ⊂ {0} ∪ [Δ, ∞) with Δ > 0. "
          "The lightest particle has positive mass.", "small", FG),
         ("✗ Open, not claimed, so the $1M prize stands", "small", WARN)],
        [(SOFT_GOOD, GOOD), (SOFT_WARN, WARN)])
    pg.text("According to reports, the construction is built on two older human-made tools: "
            "Kenneth Wilson's lattice gauge theory (1974) and Tadeusz Balaban's "
            "renormalisation-group programme (1980s). That's probably why the Economist says "
            "the key insights came from human physicists.")
    pg.h2("How to use this app")
    pg.bullets(["Use ◀ ▶ or the menu at the top to move between sections.",
                "Sections marked [calc] have input boxes. Edit the numbers, then tap "
                "Compute to update the results and graphs.",
                "Drag the page with your finger to scroll.",
                "In formulas, _ means subscript and ^ means superscript, "
                "e.g. A_μ^a."])


def sec_classical(app, pg):
    pg.h1("Classical Yang–Mills theory")
    pg.text("Fix a compact simple Lie group G, e.g. SU(2) or SU(3) (quantum chromodynamics "
            "uses SU(3)), with Lie algebra g and generators T^a. The basic field is a "
            "connection, a g-valued 1-form:")
    pg.formula(["A = A_μ(x) dx^μ = Σ_a A_μ^a(x) T^a dx^μ"],
               "Electromagnetism is the special case G = U(1).")
    pg.text("Covariant derivative and curvature (field strength):")
    pg.formula(["D_μ = ∂_μ + A_μ",
                "F_μν = [D_μ, D_ν] = ∂_μA_ν − ∂_νA_μ + [A_μ, A_ν]",
                "F = dA + A∧A"])
    pg.text("The commutator [A_μ, A_ν] is the whole story. It vanishes for U(1), so photons don't "
            "interact with each other, but not for non-abelian G, so gluons do.")
    pg.h2("Gauge symmetry")
    pg.formula(["A ↦ U A U⁻¹ + U d(U⁻¹)", "F ↦ U F U⁻¹"],
               "for any map U: ℝ⁴ → G. Physics may depend only on gauge-invariant quantities.")
    pg.text("Gauge-invariant observables include tr(F_μν F^μν) and the Wilson loop, "
            "the holonomy around a closed curve C:")
    pg.formula(["W_C(A) = tr P exp( ∮_C A )"])
    pg.h2("Action and field equations")
    pg.text("In Euclidean (imaginary-time) signature, the setting used for rigorous work:")
    pg.formula(["S(A) = (1 / 4g²) ∫ Σ_μν |F_μν(x)|² d⁴x",
                "Field equations:  D^μ F_μν = 0"],
               "g is the coupling constant. The equations are nonlinear.")
    pg.text("Expanding |F|² gives (∂A)² plus cubic terms ~ g·∂A·A·A and quartic terms "
            "~ g²·A⁴. These are the three- and four-gluon self-interactions.")
    pg.h2("Why quantising it is hard")
    pg.formula(["<O> = (1/Z) ∫ O(A) e^(−S(A)) DA",
                "Z = ∫ e^(−S(A)) DA"])
    pg.bullets(["No Lebesgue measure exists in infinite dimensions, so “DA” is meaningless. "
                "A probability measure on very rough (distributional) fields must be "
                "constructed directly.",
                "Gauge redundancy: each physical configuration is counted infinitely often, "
                "so one must work on the quotient space A/G.",
                "Ultraviolet divergences: in 4D the coupling g is dimensionless, which makes "
                "this the critical, hardest case for renormalisation."])
    pg.h2("Dimension counting")
    for title, body, kind in (
            ("φ⁴ theory in 2D and 3D", "Constructed rigorously (Glimm, Jaffe and others, 1970s).", "ok"),
            ("φ⁴ theory in 4D", "Proved trivial: the interaction vanishes in the continuum "
                                "limit (Aizenman & Duminil-Copin, 2021).", "open"),
            ("Yang–Mills in 2D and 3D", "2D is exactly solvable; 3D is partly controlled.", "ok"),
            ("Yang–Mills in 4D", "Expected to be non-trivial because of asymptotic freedom. "
                                 "Existence is now claimed by the AI proof.", "def")):
        pg.callout(title, body, kind)


def sec_running(app, pg):
    pg.h1("Running coupling  [calc]")
    pg.text("Under renormalisation the coupling changes with the energy scale μ. "
            "To leading (one-loop) order:")
    pg.formula(["μ dg/dμ = β(g) = −(b₀ / 16π²) g³ + O(g⁵)",
                "b₀ = 11N/3 − 2n_f/3      (SU(N), n_f quark flavours)",
                "α(μ) = g²/4π = 4π / ( b₀ ln(μ²/Λ²) )"],
               "The minus sign is asymptotic freedom (Gross, Wilczek, Politzer, 1973).")
    fields = [("rc_N", "Number of colours N (SU(N))", 3),
              ("rc_nf", "Quark flavours n_f (0 = pure Yang–Mills)", 0),
              ("rc_mu", "Energy ratio μ/Λ (must be > 1)", 100)]
    app.form(pg, fields)
    pg.mark("out")
    pg.h2("Results")
    try:
        N = app.num("rc_N", int, 2, 20, "N")
        nf = app.num("rc_nf", int, 0, 40, "n_f")
        mu = app.num("rc_mu", float, 1.0001, 1e12, "μ/Λ")
    except ValueError as e:
        pg.callout("Input error", str(e), "open")
        return
    b0 = b0_coeff(N, nf)
    if b0 <= 0:
        pg.callout("Not asymptotically free",
                   "b₀ = %s ≤ 0. With this many quark flavours the coupling grows at high "
                   "energy, so the one-loop formula has no UV-free limit. Reduce n_f." % fmt(b0, 4),
                   "open")
        return
    a = alpha_one_loop(mu, N, nf)
    pg.card([("b₀ = %s" % fmt(b0, 5), "math", FG),
             ("α(μ) = %s" % fmt(a, 4), "math", FG),
             ("g²(μ) = 4πα = %s" % fmt(4 * math.pi * a, 4), "math", FG),
             ("At μ/Λ = %s the theory is %s." % (
                 fmt(mu, 4), "weakly coupled (perturbation theory OK)" if a < 0.3
                 else "strongly coupled (perturbation theory unreliable)"), "small",
              GOOD if a < 0.3 else WARN)])
    hi = max(mu * 10.0, 1000.0)
    lo = 1.5
    xs = [lo * (hi / lo) ** (i / 200.0) for i in range(201)]
    series = [{"x": xs, "y": [alpha_one_loop(x, N, nf) for x in xs], "color": ACCENT,
               "points": [(mu, a)] if lo <= mu <= hi else []}]
    legend = [(ACCENT, "SU(%d), n_f = %d (dot = your input)" % (N, nf))]
    if nf > 0:
        series.append({"x": xs, "y": [alpha_one_loop(x, N, 0) for x in xs], "color": PURPLE})
        legend.append((PURPLE, "pure Yang–Mills, n_f = 0"))
    legend.append((WARN, "α = 0.3: rough edge of perturbation theory"))
    ytop = min(3.0, max(alpha_one_loop(lo, N, nf), 0.5))
    line_chart(pg, series, "α(μ) versus energy", "μ / Λ  (log scale)", xlog=True,
               xr=(lo, hi), yr=(0.0, ytop), hlines=[(0.3, WARN)], legend=legend)
    pg.text("Weak at high energy (short distances), so the continuum limit is controllable "
            "and existence can be proved. Strong at low energy, where the mass gap and "
            "confinement live. That regime is still out of reach.", "small", MUTED)


def sec_massgap(app, pg):
    pg.h1("The mass gap  [calc]")
    pg.text("A quantum field theory has a Hilbert space, a vacuum Ω and a Hamiltonian H ≥ 0 "
            "with HΩ = 0. It has a mass gap Δ > 0 if")
    pg.formula(["spec(H) ⊂ {0} ∪ [Δ, ∞)"],
               "Equivalently, connected correlations decay exponentially:")
    pg.formula(["|<O(x)O(0)> − <O>²| ≤ C e^(−Δ|x|)"])
    pg.text("No gap, e.g. free photons:", "bold")
    spectrum_diagram(pg, gapped=False)
    pg.text("Mass gap, expected for Yang–Mills:", "bold")
    spectrum_diagram(pg, gapped=True)
    pg.text("Classically, Yang–Mills waves are massless. The quantum theory is expected to "
            "generate a mass scale out of nothing (Δ ∝ Λ, “dimensional transmutation”). That "
            "would explain why the strong force is short-ranged.", "small", MUTED)
    fields = [("mg_D", "Mass gap Δ in GeV (lattice SU(3) glueball ≈ 1.7)", 1.7),
              ("mg_x", "Max distance to plot, in fm (1 fm = 10⁻¹⁵ m)", 2.0)]
    app.form(pg, fields)
    pg.mark("out")
    pg.h2("Results")
    try:
        D = app.num("mg_D", float, 1e-4, 100.0, "Δ")
        xm = app.num("mg_x", float, 0.05, 100.0, "distance")
    except ValueError as e:
        pg.callout("Input error", str(e), "open")
        return
    xi = HBARC / D
    pg.card([("Δ = %s MeV" % fmt(D * 1000, 4), "math", FG),
             ("Correlation length ξ = ħc/Δ = %s fm" % fmt(xi, 4), "math", FG),
             ("Correlation at 1 fm: e^(−1/ξ) = %s" % fmt(math.exp(-1.0 / xi), 3), "math", FG),
             ("Beyond a few ξ the field “forgets” what happened elsewhere: the force is "
              "short-ranged.", "small", MUTED)])
    x0 = xm / 40.0
    xs = [x0 + (xm - x0) * i / 200.0 for i in range(201)]
    gapped = [math.exp(-(x - x0) / xi) for x in xs]
    gapless = [(x0 / x) ** 2 for x in xs]
    line_chart(pg, [{"x": xs, "y": gapped, "color": WARN},
                    {"x": xs, "y": gapless, "color": ACCENT}],
               "Correlation versus distance (normalised)", "distance |x| in fm",
               xr=(x0, xm), yr=(0.0, 1.0), vlines=[(xi, MUTED)] if xi <= xm else [],
               legend=[(WARN, "with gap: e^(−|x|/ξ), exponential decay"),
                       (ACCENT, "no gap: ~1/|x|², power-law decay"),
                       (MUTED, "ξ = ħc/Δ (dashed line)")])
    pg.callout("Status", "The existence proof says nothing either way about Δ > 0. Lattice "
                         "computer simulations strongly suggest a gap, but simulations are not "
                         "proofs.", "open")


def sec_lattice(app, pg):
    pg.h1("Step 1: the lattice  [calc]")
    pg.text("Wilson (1974): replace ℝ⁴ by a lattice of spacing ε. Put a group element on each "
            "link instead of the potential A:")
    pg.formula(["U_(x,μ) ≈ exp( ε A_μ(x) ) ∈ G"])
    plaquette_diagram(pg)
    pg.text("Going around an elementary square (a plaquette p) gives the curvature:")
    pg.formula(["U_p = U₁ U₂ U₃⁻¹ U₄⁻¹ ≈ exp( ε² F_μν(x) + O(ε³) )"])
    pg.text("Wilson action and probability measure (dU = Haar measure on G):")
    pg.formula(["S_ε(U) = (1/g²) Σ_p Re tr(1 − U_p)",
                "dμ_ε = (1/Z_ε) e^(−S_ε(U)) Π_links dU"],
               "A finite product of compact groups, so this is a perfectly well-defined "
               "probability measure.")
    pg.bullets(["Gauge symmetry is exact: U_(x,μ) → V_x U_(x,μ) V_(x+μ)⁻¹.",
                "Reflection positivity holds (Osterwalder–Seiler, 1978).",
                "Cost: only 90° rotations survive. Full rotation symmetry must re-emerge as "
                "ε → 0."])
    pg.h2("Check the continuum limit yourself")
    pg.text("Take an SU(2) plaquette U_p = exp(iθσ₃/2) with θ = ε²f. The exact lattice term "
            "is Re tr(1−U_p) = 2 − 2cos(θ/2). The continuum formula −½ tr X² gives θ²/4. "
            "Their relative difference is ≈ θ²/48, so halving ε should cut the error 16×.",
            "small", MUTED)
    fields = [("lt_f", "Field strength f (arbitrary units)", 1.0),
              ("lt_e", "Starting lattice spacing ε", 1.0)]
    app.form(pg, fields)
    pg.mark("out")
    pg.h2("Results")
    try:
        f = app.num("lt_f", float, -1e3, 1e3, "f")
        e = app.num("lt_e", float, 1e-4, 10.0, "ε")
    except ValueError as ex:
        pg.callout("Input error", str(ex), "open")
        return
    if f == 0:
        pg.callout("Zero field", "With f = 0 every plaquette is the identity and both sides are "
                                 "exactly 0. Try f ≠ 0.", "open")
        return
    rows = []
    prev = None
    for k in range(5):
        eps = e / 2 ** k
        th, ex_, ap, rel = plaquette_terms(f, eps)
        ratio = "" if prev in (None, 0) or rel == 0 else fmt(prev / rel, 3)
        rows.append([fmt(eps, 4), fmt(ex_, 4), fmt(ap, 4), fmt(rel, 3), ratio or "—"])
        prev = rel
    pg.table(["ε", "exact", "θ²/4", "rel.err", "drop"], rows)
    pg.text("“drop” is the factor by which the error shrank after halving ε. It approaches 16, "
            "confirming S_ε → (1/4g²)∫|F|² as ε → 0. Making the same limit work for the "
            "probability measures, not just the actions, is the hard part.", "small", MUTED)


def sec_rg(app, pg):
    pg.h1("Step 2: renormalisation group  [calc]")
    pg.text("As ε → 0 the number of variables explodes. Following Wilson, and made rigorous by "
            "Balaban, integrate out fluctuations one length scale at a time:")
    blocking_diagram(pg)
    pg.formula(["e^(−S_(k+1)(V)) = ∫ δ(V − B(U)) e^(−S_k(U)) dU",
                "1/g²_(k+1) ≈ 1/g²_k − (b₀/8π²) ln L"],
               "B averages over blocks of side L. Going to coarser scales, the coupling grows.")
    pg.text("Balaban's key ideas (1982–1989):", "bold")
    pg.bullets(["Small-field / large-field split: expand perturbatively where the curvature is "
                "small; large-field regions are exponentially suppressed.",
                "Gauge fixing inside blocks, which avoids global Gribov problems.",
                "Cluster (polymer) expansions keep corrections local, so errors don't pile up.",
                "Main theorem: bounds on the partition function, uniform in ε, on a finite torus."])
    pg.callout("The gap Balaban left",
               "He controlled the partition function in a finite box, but not the "
               "gauge-invariant correlation functions, the infinite-volume limit or all the "
               "axioms. Reports say the AI proof builds on this programme and carries it "
               "through.", "open")
    fields = [("rg_N", "Number of colours N (SU(N))", 3),
              ("rg_g", "Starting coupling g² at the finest scale", 1.0),
              ("rg_L", "Block factor L (integer ≥ 2)", 2),
              ("rg_k", "Maximum number of RG steps", 30)]
    app.form(pg, fields)
    pg.mark("out")
    pg.h2("Results")
    try:
        N = app.num("rg_N", int, 2, 20, "N")
        g2 = app.num("rg_g", float, 0.01, 12.0, "g²")
        L = app.num("rg_L", int, 2, 10, "L")
        K = app.num("rg_k", int, 1, 200, "steps")
    except ValueError as e:
        pg.callout("Input error", str(e), "open")
        return
    strong = 4.0 * math.pi
    vals, kstar = rg_flow(N, g2, L, K, strong)
    b0 = b0_coeff(N)
    lam_eps = math.exp(-8.0 * math.pi ** 2 / (b0 * g2))
    parts = [("b₀ = %s, decrease of 1/g² per step = %s" % (
        fmt(b0, 4), fmt(b0 * math.log(L) / (8 * math.pi ** 2), 3)), "math", FG)]
    if kstar is not None:
        parts.append(("Strong coupling (g² ≥ 4π) reached at step k* = %d" % kstar, "math", WARN))
        parts.append(("That is a length L^k* = %s × the lattice spacing." % fmt(float(L) ** kstar, 4),
                      "math", FG))
    else:
        parts.append(("Still weakly coupled after %d steps: increase the steps or g²." % K,
                      "math", GOOD))
    parts.append(("One-loop estimate: Λ·ε ≈ exp(−8π²/(b₀g²)) = %s, i.e. the strong scale is ≈ %s "
                  "lattice spacings." % (fmt(lam_eps, 3), fmt(1.0 / lam_eps, 3)), "small", MUTED))
    pg.card(parts)
    bar_chart(pg, vals, "Coupling g² after each RG step", "RG step k (coarser →)",
              threshold=strong, cap=strong * 1.25)
    pg.swatch_text(ACCENT, "weak coupling: Balaban-type expansions work")
    pg.swatch_text(WARN, "g² ≥ 4π (dashed line): perturbative control lost")
    pg.space(0.4)
    pg.text("Existence needs control as ε → 0 (to the left: g → 0, fine). The mass gap needs "
            "control to the right, past k*, where no small parameter exists.", "small", MUTED)


def sec_confinement(app, pg):
    pg.h1("Confinement  [calc]")
    pg.text("Closely tied to the mass gap is confinement. Large Wilson loops are expected to "
            "follow an area law instead of a perimeter law:")
    pg.formula(["area law:       <W_C> ~ e^(−σ · Area(C))",
                "perimeter law:  <W_C> ~ e^(−m · Perimeter(C))"],
               "σ > 0 is the string tension. An area law means a quark and antiquark feel a "
               "constant pulling force, so they can never be separated.")
    pg.text("A popular model of the quark–antiquark potential (the Cornell potential):")
    pg.formula(["V(R) = σR/ħc − c·ħc/R"],
               "Linear confinement at long range plus a Coulomb-like term at short range "
               "(asymptotic freedom).")
    fields = [("cf_s", "String tension σ in GeV² (typical 0.18)", 0.18),
              ("cf_c", "Coulomb coefficient c (typical 0.3)", 0.3),
              ("cf_R", "Max separation R in fm", 2.0)]
    app.form(pg, fields)
    pg.mark("out")
    pg.h2("Results")
    try:
        s = app.num("cf_s", float, 0.0, 10.0, "σ")
        cc = app.num("cf_c", float, 0.0, 5.0, "c")
        R = app.num("cf_R", float, 0.3, 20.0, "R")
    except ValueError as e:
        pg.callout("Input error", str(e), "open")
        return
    force_gev_fm = s / HBARC
    newtons = force_gev_fm * GEV_PER_FM_IN_N
    pg.card([("Force = σ/ħc = %s GeV/fm" % fmt(force_gev_fm, 4), "math", FG),
             ("= %s N ≈ %s tonnes-force" % (fmt(newtons, 4), fmt(newtons / G_STD / 1000.0, 3)),
              "math", FG),
             ("V(%s fm) = %s GeV" % (fmt(R, 3), fmt(cornell_potential(R, s, cc), 4)), "math", FG),
             ("A constant force of over ten tonnes between two quarks, at any distance, "
              "until it becomes cheaper to create a new quark pair (string breaking).",
              "small", MUTED)])
    r0 = 0.1
    xs = [r0 + (R - r0) * i / 200.0 for i in range(201)]
    full = [cornell_potential(x, s, cc) for x in xs]
    coul = [cornell_potential(x, 0.0, cc) for x in xs]
    lo = min(full + coul)
    hi = max(full + coul)
    padv = 0.08 * (hi - lo if hi > lo else 1.0)
    line_chart(pg, [{"x": xs, "y": full, "color": WARN},
                    {"x": xs, "y": coul, "color": ACCENT}],
               "Potential V(R) in GeV", "separation R in fm", xr=(r0, R),
               yr=(lo - padv, hi + padv),
               legend=[(WARN, "confining: Coulomb + σR (grows forever)"),
                       (ACCENT, "Coulomb only: flattens out, no confinement")])
    pg.callout("Status", "Confinement (σ > 0) in continuum 4D Yang–Mills is unproved. It is "
                         "provable at very strong lattice coupling, but connecting that regime to "
                         "the weak-coupling continuum limit is the open problem.", "open")


def sec_proof(app, pg):
    pg.h1("Step 3: building the theory")
    pg.text("“Exists” means constructing correlation functions S_n(x₁,…,x_n) = <O₁(x₁)…O_n(x_n)> "
            "of gauge-invariant observables that satisfy the Osterwalder–Schrader axioms:")
    for name, body in (("OS0 Regularity", "S_n are tempered distributions with growth bounds."),
                       ("OS1 Euclidean invariance", "Invariant under rotations and translations of ℝ⁴."),
                       ("OS2 Reflection positivity", "<Θ(F)* F> ≥ 0 for time reflection Θ. "
                                                     "This gives a positive inner product."),
                       ("OS3 Symmetry", "S_n is symmetric in its arguments."),
                       ("OS4 Clustering", "Correlations factorise at large separation "
                                          "(a unique vacuum).")):
        pg.card([(name, "bold", ACCENT), (body, "small", FG)])
    pg.callout("OS reconstruction theorem (1973–75)",
               "If OS0–OS4 hold, there is a Hilbert space, a vacuum, a Hamiltonian H ≥ 0 and a "
               "Poincaré symmetry: a genuine relativistic quantum theory (Wightman axioms). "
               "Also required: the theory must be non-trivial (not free).", "def")
    pg.h2("The construction pipeline")
    steps = [("Lattice measure μ_(ε,L)", "Wilson action on a finite torus; well-defined.", CARD, LINE),
             ("Uniform bounds (Balaban RG)", "Estimates on correlations that don't depend on ε.",
              SOFT_ACC, ACCENT),
             ("Continuum limit ε → 0", "Compactness gives a convergent subsequence.", SOFT_ACC, ACCENT),
             ("Infinite volume L → ∞", "Limit along subsequences; uniqueness not shown.",
              SOFT_ACC, ACCENT),
             ("Verify OS axioms + non-triviality", "Then OS reconstruction gives a quantum theory "
                                                   "on ℝ⁴.", SOFT_GOOD, GOOD)]
    for i, (t, b, fill, out) in enumerate(steps):
        pg.card([(t, "bold", FG), (b, "small", MUTED)], fill=fill, outline=out)
        if i < len(steps) - 1:
            pg.arrow_down()
    pg.two_cards(
        [("Human-built tools", "bold", FG),
         ("Wilson lattice (1974)\nOS axioms (1973–75)\nBalaban RG (1982–89)\n"
          "Asymptotic freedom (1973)", "small", FG)],
        [("Hard points", "bold", WARN),
         ("Rotation invariance must re-emerge\nOnly gauge-invariant observables\n"
          "Strong coupling at long range", "small", FG)],
        [(CARD, LINE), (SOFT_WARN, WARN)])
    pg.text("Compactness in one sentence: if S_n^(ε,L) obey bounds uniform in ε and L, some "
            "subsequence converges. Properties preserved by limits, like reflection positivity, "
            "pass to the limit for free. Rotation invariance and non-triviality need separate "
            "proofs. Different subsequences could in principle give different limits.", "small", MUTED)
    pg.text("This is the standard blueprint described in reports. The full 1,147-page proof "
            "hasn't been read here, so this isn't a line-by-line summary.", "small", MUTED)


def sec_lean(app, pg):
    pg.h1("The Lean check & scorecard")
    pg.text("Lean is a proof assistant: each logical step is checked by a small trusted kernel. "
            "A successful check establishes")
    pg.formula(["⊢ FormalStatement"])
    pg.text("with essentially no hidden logical gap. What it cannot establish is that "
            "FormalStatement means what humans mean by “quantum Yang–Mills theory exists.” "
            "The definitions of the measures, observables, axioms and non-triviality all had to "
            "be written in Lean. Checking those definitions was the review panel's main job.")
    pg.callout("Caveats on the review",
               "• OpenAI chose the chair (Gross), and he chose the other four members.\n"
               "• Reviewers said they used OpenAI's own model to help digest the code and do "
               "not yet fully understand the proof.\n"
               "• Independent human understanding and journal refereeing are still to come.",
               "open")
    pg.h2("Scorecard (12 Nov 2026)")
    for claim, status, col in (
            ("Lattice YM well-defined, gauge-invariant, reflection-positive", "Classical result (1970s)", GOOD),
            ("UV stability of the partition function on a torus", "Balaban (1980s)", GOOD),
            ("Existence of pure 4D quantum Yang–Mills", "AI proof, Lean-verified, affirmed by the panel", GOOD),
            ("Existence of QCD (Yang–Mills + quarks)", "Claimed by OpenAI; review separate", MUTED),
            ("Uniqueness of the infinite-volume limit", "Not shown", WARN),
            ("Mass gap Δ > 0", "Open: the $1M Millennium Prize stands", WARN),
            ("Confinement (area law)", "Open", WARN)):
        pg.card([(claim, "body", FG), (status, "small", col)])
    pg.h2("Sources")
    pg.text("Scientific American (Nov 2026), “Scientists confirm OpenAI's blockbuster quantum "
            "physics result”. Coverage of the Gross committee assessment by Startup Fortune, "
            "Kingy AI, The Century Report and OfficeChai. Jaffe & Witten, official Clay problem "
            "description (2000). The background mathematics is standard textbook material.",
            "small", MUTED)


SECTIONS = [
    ("1 · Overview", sec_overview),
    ("2 · Classical theory", sec_classical),
    ("3 · Running coupling [calc]", sec_running),
    ("4 · Mass gap [calc]", sec_massgap),
    ("5 · Lattice [calc]", sec_lattice),
    ("6 · RG flow [calc]", sec_rg),
    ("7 · Confinement [calc]", sec_confinement),
    ("8 · Building the theory", sec_proof),
    ("9 · Lean & scorecard", sec_lean),
]


# ===================================================================== app ==
class App:
    def __init__(self, root):
        self.root = root
        root.title("Yang–Mills Explorer")
        root.configure(bg=BG)
        self.vars = {}
        self.defaults = {}
        self.widgets = []
        self.idx = 0
        self.W = 0
        self.total_h = 1
        self._pending = None
        self._drag = None

        family = tkfont.nametofont("TkDefaultFont").actual().get("family", "Helvetica")
        mono = tkfont.nametofont("TkFixedFont").actual().get("family", "Courier")
        self.fonts = {
            "h1": tkfont.Font(family=family, weight="bold"),
            "h2": tkfont.Font(family=family, weight="bold"),
            "body": tkfont.Font(family=family),
            "bold": tkfont.Font(family=family, weight="bold"),
            "small": tkfont.Font(family=family),
            "tag": tkfont.Font(family=family, weight="bold"),
            "math": tkfont.Font(family=family),
            "mono": tkfont.Font(family=mono),
        }
        start_w = root.winfo_screenwidth() if IS_ANDROID else 480
        self._size_fonts(start_w)

        bar = tk.Frame(root, bg=CARD)
        bar.pack(side="top", fill="x")
        self.prev_btn = tk.Button(bar, text="◀", command=self.prev, bg=FIELD, fg=FG,
                                  activebackground=LINE, activeforeground=FG, relief="flat",
                                  font=self.fonts["bold"], bd=0, padx=14, pady=6)
        self.next_btn = tk.Button(bar, text="▶", command=self.next, bg=FIELD, fg=FG,
                                  activebackground=LINE, activeforeground=FG, relief="flat",
                                  font=self.fonts["bold"], bd=0, padx=14, pady=6)
        self.sec_var = tk.StringVar(value=SECTIONS[0][0])
        self.menu_btn = tk.Menubutton(bar, textvariable=self.sec_var, bg=FIELD, fg=FG,
                                      activebackground=LINE, activeforeground=FG,
                                      relief="flat", font=self.fonts["small"], anchor="w",
                                      padx=10, pady=6)
        menu = tk.Menu(self.menu_btn, tearoff=0, bg=CARD, fg=FG, activebackground=ACCENT,
                       activeforeground=BG, font=self.fonts["body"])
        for i, (name, _fn) in enumerate(SECTIONS):
            menu.add_command(label=name, command=lambda i=i: self.go(i))
        self.menu_btn["menu"] = menu
        self.prev_btn.grid(row=0, column=0, padx=(6, 3), pady=6, sticky="ns")
        self.menu_btn.grid(row=0, column=1, padx=3, pady=6, sticky="ew")
        self.next_btn.grid(row=0, column=2, padx=(3, 6), pady=6, sticky="ns")
        bar.columnconfigure(1, weight=1)

        body = tk.Frame(root, bg=BG)
        body.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=0, bd=0)
        self.sb = tk.Scrollbar(body, orient="vertical", command=self.canvas.yview,
                               width=max(12, int(self.fonts["body"].metrics("linespace") * 0.5)))
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind_all("<MouseWheel>", self._wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))
        root.after(120, self.render)

    # ---- fonts scale with the real drawing width
    def _size_fonts(self, W):
        base = max(13, min(48, int(round(W / 26.0))))
        sizes = {"h1": 1.45, "h2": 1.18, "body": 1.0, "bold": 1.0, "small": 0.86,
                 "tag": 0.74, "math": 0.98, "mono": 0.80}
        for k, f in sizes.items():
            self.fonts[k].configure(size=-max(10, int(base * f)))

    # ---- inputs
    def form(self, pg, fields):
        fr = tk.Frame(self.canvas, bg=CARD, highlightbackground=LINE, highlightthickness=2)
        wrap = int(pg.inner * 0.56)
        for r, (key, label, default) in enumerate(fields):
            if key not in self.vars:
                self.vars[key] = tk.StringVar(value=str(default))
                self.defaults[key] = str(default)
            tk.Label(fr, text=label, bg=CARD, fg=FG, font=self.fonts["small"],
                     wraplength=wrap, justify="left", anchor="w").grid(
                row=r, column=0, sticky="w", padx=(10, 6), pady=6)
            tk.Entry(fr, textvariable=self.vars[key], font=self.fonts["body"], width=7,
                     bg=FIELD, fg=FG, insertbackground=FG, relief="flat",
                     highlightthickness=1, highlightbackground=LINE,
                     highlightcolor=ACCENT).grid(row=r, column=1, sticky="ew",
                                                 padx=(6, 10), pady=6)
        fr.columnconfigure(1, weight=1)
        btns = tk.Frame(fr, bg=CARD)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 10))
        tk.Button(btns, text="Compute", command=self.compute, bg=ACCENT, fg=BG,
                  activebackground=GOOD, activeforeground=BG, relief="flat", bd=0,
                  font=self.fonts["bold"], pady=6).pack(side="left", fill="x", expand=True,
                                                        padx=(0, 6))
        tk.Button(btns, text="Reset", command=lambda: self.reset(fields), bg=FIELD, fg=FG,
                  activebackground=LINE, activeforeground=FG, relief="flat", bd=0,
                  font=self.fonts["bold"], pady=6).pack(side="left", fill="x", expand=True,
                                                        padx=(6, 0))
        pg.widget(fr)

    def num(self, key, kind, lo, hi, name):
        raw = self.vars[key].get().strip().replace(",", ".")
        try:
            v = float(raw)
        except ValueError:
            raise ValueError("%s: “%s” is not a number." % (name, raw))
        if not math.isfinite(v):
            raise ValueError("%s must be a finite number." % name)
        if kind is int:
            if abs(v - round(v)) > 1e-9:
                raise ValueError("%s must be a whole number." % name)
            v = int(round(v))
        if v < lo or v > hi:
            raise ValueError("%s must be between %s and %s." % (name, fmt(lo, 4), fmt(hi, 4)))
        return v

    def compute(self):
        self.root.focus_set()
        self.render(scroll_mark="out")

    def reset(self, fields):
        for key, _l, default in fields:
            self.vars[key].set(str(default))
        self.render(scroll_mark="out")

    # ---- navigation
    def go(self, i):
        self.idx = i % len(SECTIONS)
        self.render()

    def prev(self):
        self.go(self.idx - 1)

    def next(self):
        self.go(self.idx + 1)

    # ---- scrolling
    def _press(self, e):
        self._drag = (e.y, self.canvas.canvasy(0))

    def _motion(self, e):
        if not self._drag:
            return
        y0, top0 = self._drag
        view = max(self.canvas.winfo_height(), 1)
        top = min(max(top0 + (y0 - e.y), 0), max(self.total_h - view, 0))
        self.canvas.yview_moveto(top / float(self.total_h))

    def _wheel(self, e):
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def _on_configure(self, e):
        # Only width changes need a new layout. Height changes (e.g. the
        # Android soft keyboard opening) must not rebuild the input boxes.
        if abs(e.width - self.W) > 4:
            if self._pending:
                self.root.after_cancel(self._pending)
            self._pending = self.root.after(150, self.render)

    # ---- drawing
    def render(self, scroll_mark=None):
        self._pending = None
        W = self.canvas.winfo_width()
        if W < 100:
            W = self.root.winfo_width() - self.sb.winfo_width()
        if W < 100:
            self.root.after(150, self.render)
            return
        if W != self.W:
            self.W = W
            self._size_fonts(W)
        for w in self.widgets:
            w.destroy()
        self.widgets = []
        self.canvas.delete("all")
        pg = Page(self)
        name, fn = SECTIONS[self.idx]
        try:
            fn(self, pg)
        except Exception as ex:  # keep the app alive whatever happens
            pg.callout("Drawing error", "%s: %s" % (type(ex).__name__, ex), "open")
        nav = "Next: %s  ▶" % SECTIONS[(self.idx + 1) % len(SECTIONS)][0]
        pg.space(0.5)
        pg.text(nav, "small", MUTED, center=True)
        self.total_h = max(pg.y + pg.pad, 1)
        self.canvas.configure(scrollregion=(0, 0, W, self.total_h))
        if scroll_mark and scroll_mark in pg.marks:
            self.canvas.yview_moveto(pg.marks[scroll_mark] / float(self.total_h))
        else:
            self.canvas.yview_moveto(0)
        self.sec_var.set(name)


def main():
    root = tk.Tk()
    if not IS_ANDROID:
        root.geometry("480x860")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
