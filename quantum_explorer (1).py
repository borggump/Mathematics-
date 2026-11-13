#!/usr/bin/env python3
"""
Quantum Computing Explorer
==========================
An interactive, touch-friendly companion to the explainer on how quantum
computers (such as IBM's Quantum System Two) work.

Runs on Pydroid 3 (Android) and on desktop Python 3. Uses only the standard
library (tkinter, math, cmath, random), so nothing needs to be installed.

Pages
-----
  Qubit    : Bloch sphere, angle input, gates, probabilities, measurement
  2 Qubits : circuit builder, entanglement (concurrence), Bell state
  Grover   : search speedup calculator and success-probability chart
  Noise    : gate-error decay and a simple error-correction comparison
  Learn    : the mathematics, in plain text

Layout rules used to avoid overlapping text and graphics
--------------------------------------------------------
  * All explanatory / numeric text lives in Label widgets, never on top of
    drawings. Labels re-wrap to the screen width automatically.
  * Each drawing reserves margins measured from the current font, and the
    only canvas text sits inside those margins (axis labels, tick labels).
  * Bar / tick labels are thinned automatically when they would collide.
  * Drawings keep a fixed aspect ratio and redraw on resize or font change.
  * Use the A- / A+ buttons to change text size; everything re-lays out.
"""

import os
import math
import cmath
import random
import tkinter as tk
from tkinter import font as tkfont

IS_ANDROID = any(k in os.environ for k in
                 ("ANDROID_ROOT", "ANDROID_ARGUMENT", "ANDROID_DATA"))

# ----------------------------------------------------------------- colours
BG = "#f6f6f3"
PANEL = "#ffffff"
INK = "#1d1d1f"
MUTED = "#66666c"
BORDER = "#cfcfca"
FAINT = "#e4e4df"
ACCENT = "#2a5db0"
ACCENT2 = "#c0472c"
ACCENT3 = "#2f8a5b"
PURPLE = "#7a4fb5"
ERR = "#b00020"
BAR_COLORS = [ACCENT, ACCENT2, ACCENT3, PURPLE]

# ----------------------------------------------------------------- fonts
F = {}


def init_fonts(root, base):
    F["body"] = tkfont.Font(root, family="Helvetica", size=base)
    F["small"] = tkfont.Font(root, family="Helvetica", size=max(base - 2, 6))
    F["head"] = tkfont.Font(root, family="Helvetica", size=base + 2, weight="bold")
    F["title"] = tkfont.Font(root, family="Helvetica", size=base + 4, weight="bold")
    F["mono"] = tkfont.Font(root, family="Courier", size=base)
    F["btn"] = tkfont.Font(root, family="Helvetica", size=base, weight="bold")


def set_font_size(base):
    F["body"].configure(size=base)
    F["small"].configure(size=max(base - 2, 6))
    F["head"].configure(size=base + 2)
    F["title"].configure(size=base + 4)
    F["mono"].configure(size=base)
    F["btn"].configure(size=base)


def line_h(key="body"):
    return F[key].metrics("linespace")


# ================================================================ QUANTUM MATH
SQ2 = 1 / math.sqrt(2)

GATES = {
    "H": ((SQ2, SQ2), (SQ2, -SQ2)),
    "X": ((0, 1), (1, 0)),
    "Y": ((0, -1j), (1j, 0)),
    "Z": ((1, 0), (0, -1)),
    "S": ((1, 0), (0, 1j)),
    "T": ((1, 0), (0, cmath.exp(1j * math.pi / 4))),
}


def ry(theta):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return ((c, -s), (s, c))


def apply_1q(g, s):
    """Matrix-vector product for a 2x2 gate on a 1-qubit state [a, b]."""
    return [g[0][0] * s[0] + g[0][1] * s[1],
            g[1][0] * s[0] + g[1][1] * s[1]]


def apply_on(state, g, q):
    """Apply 2x2 gate g to qubit q (0 = left/most significant) of a 2-qubit state."""
    shift = 1 - q
    new = [0j] * 4
    for i in range(4):
        bit = (i >> shift) & 1
        for b in (0, 1):
            j = (i & ~(1 << shift)) | (b << shift)
            new[i] += g[bit][b] * state[j]
    return new


def apply_cnot(state, ctrl, tgt):
    cm, tm = 1 << (1 - ctrl), 1 << (1 - tgt)
    return [state[i ^ tm] if (i & cm) else state[i] for i in range(4)]


def remove_global_phase(a, b):
    ref = a if abs(a) > 1e-12 else b
    ph = cmath.exp(-1j * cmath.phase(ref))
    return a * ph, b * ph


def angles_from_state(a, b):
    a, b = remove_global_phase(a, b)
    th = 2 * math.acos(max(-1.0, min(1.0, abs(a))))
    phi = cmath.phase(b) % (2 * math.pi) if abs(b) > 1e-9 and abs(a) > 1e-9 else 0.0
    return math.degrees(th), math.degrees(phi)


def bloch_vector(a, b):
    ab = a.conjugate() * b
    return 2 * ab.real, 2 * ab.imag, abs(a) ** 2 - abs(b) ** 2


def fmt_c(z):
    re = 0.0 if abs(z.real) < 5e-4 else z.real
    im = 0.0 if abs(z.imag) < 5e-4 else z.imag
    if im == 0:
        return "%+.3f" % re
    if re == 0:
        return "%+.3fi" % im
    return "%+.3f%+.3fi" % (re, im)


def sample(probs, shots):
    counts = [0] * len(probs)
    for k in random.choices(range(len(probs)), weights=probs, k=shots):
        counts[k] += 1
    return counts


def nice_step(span, max_ticks):
    if span <= 0 or max_ticks < 1:
        return 1
    raw = span / max_ticks
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 5, 10):
        if m * mag >= raw:
            return m * mag
    return 10 * mag


# ================================================================ WIDGET HELPERS
CANVASES = []   # every drawing, so we can redraw after a font change
SCALES = []     # sliders, so their touch size follows the font


def wrap_label(parent, text="", fk="body", fg=INK, bg=BG, **kw):
    lab = tk.Label(parent, text=text, font=F[fk], fg=fg, bg=bg,
                   justify="left", anchor="w", **kw)

    def rewrap(e, lab=lab):
        wl = max(e.width - 2 * int(float(str(lab.cget("padx")))) - 6, 60)
        if int(float(str(lab.cget("wraplength")) or 0)) != wl:
            lab.configure(wraplength=wl)
    lab.bind("<Configure>", rewrap)
    return lab


def section(parent, text):
    wrap_label(parent, text, fk="head").pack(fill="x", padx=10, pady=(16, 4))


def output_box(parent, fk="mono"):
    lab = wrap_label(parent, "", fk=fk, bg=PANEL, relief="solid", bd=1,
                     padx=10, pady=8)
    lab.pack(fill="x", padx=10, pady=4)
    return lab


def status_label(parent):
    lab = wrap_label(parent, "", fk="small", fg=ERR)
    lab.pack(fill="x", padx=10)
    return lab


def button(parent, text, cmd, **kw):
    opts = dict(font=F["btn"], bg=PANEL, fg=INK, activebackground=FAINT,
                relief="raised", bd=1, padx=4, pady=6, command=cmd)
    opts.update(kw)
    return tk.Button(parent, text=text, **opts)


def button_grid(parent, items, cols):
    fr = tk.Frame(parent, bg=BG)
    fr.pack(fill="x", padx=8, pady=4)
    for i, (text, cmd) in enumerate(items):
        button(fr, text, cmd).grid(row=i // cols, column=i % cols,
                                   sticky="ew", padx=2, pady=2)
    for c in range(cols):
        fr.columnconfigure(c, weight=1, uniform="g")
    return fr


def entry(parent, value, width=8):
    e = tk.Entry(parent, font=F["body"], width=width, relief="solid", bd=1,
                 justify="center", bg=PANEL, fg=INK)
    e.insert(0, str(value))
    return e


def read_num(e, name, lo, hi, integer=False):
    s = e.get().strip().replace(",", "")
    try:
        v = float(s)
    except ValueError:
        raise ValueError("%s must be a number." % name)
    if not math.isfinite(v):
        raise ValueError("%s must be a finite number." % name)
    if integer:
        if v != int(v):
            raise ValueError("%s must be a whole number." % name)
        v = int(v)
    if not lo <= v <= hi:
        raise ValueError("%s must be between %s and %s." % (name, lo, hi))
    return v


def slider(parent, frm, to, cmd):
    s = tk.Scale(parent, from_=frm, to=to, orient="horizontal", showvalue=0,
                 resolution=1, command=cmd, bg=BG, troughcolor=FAINT,
                 highlightthickness=0, bd=0, activebackground=ACCENT,
                 sliderlength=int(line_h() * 2), width=int(line_h() * 1.1))
    SCALES.append(s)
    return s


class AspectCanvas(tk.Canvas):
    """A canvas that keeps height = width * ratio and redraws itself."""

    def __init__(self, master, ratio, draw_fn):
        super().__init__(master, bg=PANEL, height=200, highlightthickness=1,
                         highlightbackground=BORDER, bd=0)
        self.ratio = ratio
        self.draw_fn = draw_fn
        self.bind("<Configure>", self._on_configure)
        CANVASES.append(self)

    def _on_configure(self, e):
        want = int(e.width * self.ratio)
        if abs(want - e.height) > 4:
            self.configure(height=want)
            return
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w > 40 and h > 40:
            self.draw_fn(self, w, h)


def draw_message(c, w, h, text):
    c.create_text(w / 2, h / 2, text=text, font=F["small"], fill=MUTED,
                  width=w - 20, justify="center")


def draw_bars(c, w, h, labels, values, colors, vmax=None, fmt="%.3f",
              title=None):
    """Bar chart with reserved bands: title | values | bars | labels."""
    fs = F["small"]
    lh = fs.metrics("linespace")
    n = len(values)
    if n == 0:
        return
    vmax = vmax if vmax else (max(values) or 1)
    y = 6
    if title:
        c.create_text(w / 2, y, text=title, anchor="n", font=fs, fill=MUTED)
        y += lh + 4
    top = y + lh + 4                 # band for value text
    bottom = h - (lh + 10)           # band for category labels
    left, right = 10, 10
    slot = (w - left - right) / n
    barw = slot * 0.62
    avail = bottom - top
    c.create_line(left, bottom, w - right, bottom, fill=BORDER)

    widest_val = max(fs.measure(fmt % v) for v in values)
    show_vals = widest_val + 4 <= slot
    widest_lab = max(fs.measure(str(l)) for l in labels)
    step = max(1, math.ceil((widest_lab + 8) / slot))

    for i, (lab, v) in enumerate(zip(labels, values)):
        x = left + slot * (i + 0.5)
        bh = avail * max(0.0, min(1.0, v / vmax))
        c.create_rectangle(x - barw / 2, bottom - bh, x + barw / 2, bottom,
                           fill=colors[i % len(colors)], outline="")
        if show_vals:
            c.create_text(x, bottom - bh - 2, text=fmt % v, anchor="s",
                          font=fs, fill=INK)
        if i % step == 0:
            c.create_text(x, bottom + 5, text=str(lab), anchor="n",
                          font=fs, fill=MUTED)


def draw_lines(c, w, h, series, xmax, xlabel, ylabel, hline=None):
    """series: list of (xs, ys, colour). y axis fixed to 0..1."""
    fs = F["small"]
    lh = fs.metrics("linespace")
    yticks = [0, 0.25, 0.5, 0.75, 1.0]
    ylabs = ["%g" % t for t in yticks]
    left = max(fs.measure(t) for t in ylabs) + 14
    right = 14
    top = lh * 2 + 6                  # y-axis title band
    bottom = h - (lh * 2 + 14)        # tick labels + x-axis title band
    pw, ph = w - left - right, bottom - top
    if pw < 40 or ph < 40:
        return

    def X(v):
        return left + pw * v / xmax

    def Y(v):
        return bottom - ph * v

    c.create_text(6, 4, text=ylabel, anchor="nw", font=fs, fill=MUTED)
    for t, s in zip(yticks, ylabs):
        c.create_line(left, Y(t), w - right, Y(t), fill=FAINT)
        c.create_text(left - 6, Y(t), text=s, anchor="e", font=fs, fill=MUTED)

    widest = fs.measure("%g" % xmax) + 18
    step = nice_step(xmax, max(1, int(pw // widest)))
    t = 0
    while t <= xmax + 1e-9:
        c.create_line(X(t), bottom, X(t), bottom + 4, fill=MUTED)
        c.create_text(X(t), bottom + 6, text="%g" % t, anchor="n", font=fs,
                      fill=MUTED)
        t += step
    c.create_text(left + pw / 2, h - 4, text=xlabel, anchor="s", font=fs,
                  fill=MUTED)
    c.create_line(left, top, left, bottom, fill=MUTED)
    c.create_line(left, bottom, w - right, bottom, fill=MUTED)

    if hline is not None:
        c.create_line(left, Y(hline), w - right, Y(hline), fill=ACCENT2,
                      dash=(4, 3))
    for xs, ys, col in series:
        pts = []
        for xv, yv in zip(xs, ys):
            pts += [X(xv), Y(max(0.0, min(1.0, yv)))]
        if len(pts) >= 4:
            c.create_line(*pts, fill=col, width=2)


# ================================================================ SCROLLING PAGE
class ScrollPage(tk.Frame):
    """Vertically scrollable page. Drag with a finger anywhere on text or
    drawings to scroll; sliders, entries and buttons keep their own touch."""

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.vsb = tk.Scrollbar(self, orient="vertical",
                                command=self.canvas.yview,
                                width=max(14, int(line_h() * 0.9)))
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window(0, 0, window=self.inner,
                                             anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner.bind("<Configure>", self._update_region)
        self.canvas.bind("<Configure>", self._fit_width)
        self._y = 0

    def _update_region(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _fit_width(self, e):
        self.canvas.itemconfigure(self.win, width=e.width)

    def enable_drag(self, widget=None):
        widget = widget or self.inner
        if not isinstance(widget, (tk.Scale, tk.Entry, tk.Button,
                                   tk.Scrollbar)):
            widget.bind("<ButtonPress-1>", self._press, add="+")
            widget.bind("<B1-Motion>", self._drag, add="+")
        for child in widget.winfo_children():
            self.enable_drag(child)

    def _press(self, e):
        self._y = e.y_root

    def _drag(self, e):
        dy = e.y_root - self._y
        self._y = e.y_root
        total = max(self.inner.winfo_height(), 1)
        first, last = self.canvas.yview()
        new = first - dy / total
        self.canvas.yview_moveto(max(0.0, min(new, 1.0 - (last - first))))

    def wheel(self, units):
        self.canvas.yview_scroll(units, "units")


# ================================================================ PAGE: QUBIT
AZ, EL = math.radians(40), math.radians(18)


def bloch_project(x, y, z):
    """Orthographic view. Returns (horizontal, vertical, depth-toward-viewer)."""
    u = -x * math.sin(AZ) + y * math.cos(AZ)
    d = x * math.cos(AZ) + y * math.sin(AZ)
    v = z * math.cos(EL) - d * math.sin(EL)
    return u, v, d


class QubitPage:
    def __init__(self, parent):
        self.state = [1 + 0j, 0j]
        self.history = []
        self.counts = None
        self.shots = 0
        self.cur_th = 0.0
        self.cur_ph = 0.0

        section(parent, "One qubit on the Bloch sphere")
        wrap_label(parent,
                   "A qubit is |psi> = a|0> + b|1> with |a|^2 + |b|^2 = 1. "
                   "Writing a = cos(theta/2) and b = e^(i*phi) sin(theta/2) "
                   "places every state on a sphere. Move the sliders, type "
                   "angles, or tap gates, and watch the red state vector.",
                   fg=MUTED).pack(fill="x", padx=10)

        self.bloch = AspectCanvas(parent, 0.9, self.draw_bloch)
        self.bloch.pack(fill="x", padx=10, pady=6)
        self.out = output_box(parent)

        section(parent, "Input: angles")
        sl = tk.Frame(parent, bg=BG)
        sl.pack(fill="x", padx=10)
        sl.columnconfigure(0, weight=1)
        self.th_lab = wrap_label(sl, "")
        self.th_lab.grid(row=0, column=0, sticky="ew")
        self.th_scale = slider(sl, 0, 180, self.on_slider)
        self.th_scale.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.ph_lab = wrap_label(sl, "")
        self.ph_lab.grid(row=2, column=0, sticky="ew")
        self.ph_scale = slider(sl, 0, 360, self.on_slider)
        self.ph_scale.grid(row=3, column=0, sticky="ew")

        ent = tk.Frame(parent, bg=BG)
        ent.pack(fill="x", padx=10, pady=6)
        tk.Label(ent, text="theta (deg)", font=F["small"], bg=BG,
                 fg=MUTED).grid(row=0, column=0, sticky="w")
        tk.Label(ent, text="phi (deg)", font=F["small"], bg=BG,
                 fg=MUTED).grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.th_e = entry(ent, 0)
        self.th_e.grid(row=1, column=0, sticky="ew")
        self.ph_e = entry(ent, 0)
        self.ph_e.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        button(ent, "Set", self.on_set).grid(row=1, column=2, sticky="ew",
                                             padx=(6, 0))
        for c in range(3):
            ent.columnconfigure(c, weight=1, uniform="e")
        self.status = status_label(parent)

        section(parent, "Input: gates (unitary matrices)")
        button_grid(parent, [
            ("H", lambda: self.gate("H")), ("X", lambda: self.gate("X")),
            ("Y", lambda: self.gate("Y")), ("Z", lambda: self.gate("Z")),
            ("S", lambda: self.gate("S")), ("T", lambda: self.gate("T")),
            ("Ry+15", lambda: self.gate("Ry")), ("Reset", self.reset),
        ], cols=4)
        self.hist_lab = wrap_label(parent, "", fk="small", fg=MUTED)
        self.hist_lab.pack(fill="x", padx=10)

        section(parent, "Output: Born-rule probabilities")
        self.prob = AspectCanvas(parent, 0.5, self.draw_probs)
        self.prob.pack(fill="x", padx=10, pady=4)

        section(parent, "Simulate measurement")
        mr = tk.Frame(parent, bg=BG)
        mr.pack(fill="x", padx=10, pady=4)
        tk.Label(mr, text="Shots", font=F["body"], bg=BG,
                 fg=INK).grid(row=0, column=0, sticky="w")
        self.shots_e = entry(mr, 1000)
        self.shots_e.grid(row=0, column=1, sticky="ew", padx=6)
        button(mr, "Measure", self.measure).grid(row=0, column=2, sticky="ew")
        for c in range(3):
            mr.columnconfigure(c, weight=1, uniform="m")
        self.m_status = status_label(parent)
        self.meas_out = output_box(parent)
        self.hist = AspectCanvas(parent, 0.5, self.draw_hist)
        self.hist.pack(fill="x", padx=10, pady=(4, 24))

        self.refresh()

    # ---- actions
    def set_angles(self, th, ph):
        t, p = math.radians(th), math.radians(ph)
        self.state = [complex(math.cos(t / 2)),
                      cmath.exp(1j * p) * math.sin(t / 2)]

    def on_slider(self, _v=None):
        th = float(self.th_scale.get())
        ph = float(self.ph_scale.get())
        dphi = abs((ph - self.cur_ph + 180) % 360 - 180)
        if abs(th - self.cur_th) <= 0.5 and dphi <= 0.5:
            return   # slider was only echoing a programmatic update
        self.set_angles(th, ph)
        self.refresh(sync_inputs=False, th=th, ph=ph)

    def on_set(self):
        try:
            th = read_num(self.th_e, "theta", 0, 180)
            ph = read_num(self.ph_e, "phi", 0, 360)
        except ValueError as err:
            self.status.configure(text=str(err))
            return
        self.set_angles(th, ph)
        self.refresh()

    def gate(self, name):
        g = ry(math.radians(15)) if name == "Ry" else GATES[name]
        self.state = apply_1q(g, self.state)
        self.history.append("Ry(15)" if name == "Ry" else name)
        self.refresh()

    def reset(self):
        self.state = [1 + 0j, 0j]
        self.history = []
        self.refresh()

    def measure(self):
        try:
            shots = read_num(self.shots_e, "Shots", 1, 100000, integer=True)
        except ValueError as err:
            self.m_status.configure(text=str(err))
            return
        self.m_status.configure(text="")
        a, b = self.state
        self.counts = sample([abs(a) ** 2, abs(b) ** 2], shots)
        self.shots = shots
        p0 = abs(a) ** 2
        f0 = self.counts[0] / shots
        se = math.sqrt(max(p0 * (1 - p0), 1e-12) / shots)
        self.meas_out.configure(text=(
            "Shots: %d\nCount(0) = %d  freq %.4f\nCount(1) = %d  freq %.4f\n"
            "Theory P(0) = %.4f\nStd. error ~ %.4f (shrinks as 1/sqrt(shots))"
            % (shots, self.counts[0], f0, self.counts[1], 1 - f0, p0, se)))
        self.hist.redraw()

    # ---- display
    def refresh(self, sync_inputs=True, th=None, ph=None):
        self.status.configure(text="")
        a, b = remove_global_phase(*self.state)
        self.state = [a, b]
        if th is None:
            th, ph = angles_from_state(a, b)
        self.cur_th, self.cur_ph = th, ph
        if sync_inputs:
            self.th_scale.set(round(th))
            self.ph_scale.set(round(ph) % 360)
            for e, v in ((self.th_e, th), (self.ph_e, ph)):
                e.delete(0, "end")
                e.insert(0, "%.1f" % v)
        x, y, z = bloch_vector(a, b)
        self.th_lab.configure(text="theta = %.1f deg" % th)
        self.ph_lab.configure(text="phi = %.1f deg" % ph)
        self.out.configure(text=(
            "a = %s\nb = %s\n|a|^2+|b|^2 = %.4f\n"
            "Bloch (x, y, z) =\n  (%.3f, %.3f, %.3f)"
            % (fmt_c(a), fmt_c(b), abs(a) ** 2 + abs(b) ** 2, x, y, z)))
        hist = self.history[-14:]
        more = "... " if len(self.history) > 14 else ""
        self.hist_lab.configure(text="Gates applied: " + (
            more + " -> ".join(hist) if hist else "none (state |0>)"))
        self.counts = None
        self.meas_out.configure(text="Press Measure to sample the state.")
        self.bloch.redraw()
        self.prob.redraw()
        self.hist.redraw()

    def draw_bloch(self, c, w, h):
        fb = F["body"]
        lh = fb.metrics("linespace")
        labels = ["|0>", "|1>", "+x", "+y"]
        labw = max(fb.measure(t) for t in labels) + 12
        r = min((w - 2 * labw) / 2, (h - 2 * (lh + 10)) / 2)
        if r < 20:
            return
        cx, cy = w / 2, h / 2

        def P(x, y, z):
            u, v, _ = bloch_project(x, y, z)
            return cx + r * u, cy - r * v

        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=MUTED, width=2)
        circles = (lambda t: (math.cos(t), math.sin(t), 0.0),
                   lambda t: (math.cos(t), 0.0, math.sin(t)))
        n = 72
        for circ in circles:
            for i in range(n):
                t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                p0, p1 = circ(t0), circ(t1)
                mid = circ((t0 + t1) / 2)
                front = bloch_project(*mid)[2] >= 0
                c.create_line(*P(*p0), *P(*p1),
                              fill=MUTED if front else BORDER,
                              dash=() if front else (3, 3))
        for ax in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            neg = tuple(-v for v in ax)
            c.create_line(*P(*neg), *P(*ax), fill=BORDER)

        # labels are always placed OUTSIDE the sphere outline
        c.create_text(cx, cy - r - 6, text="|0>", anchor="s", font=fb, fill=INK)
        c.create_text(cx, cy + r + 6, text="|1>", anchor="n", font=fb, fill=INK)
        for ax, txt in (((1, 0, 0), "+x"), ((0, 1, 0), "+y")):
            u, v, _ = bloch_project(*ax)
            dx, dy = u, -v
            L = math.hypot(dx, dy) or 1
            dx, dy = dx / L, dy / L
            px, py = cx + dx * (r + 6), cy + dy * (r + 6)
            anc = ("n" if dy > 0.35 else "s" if dy < -0.35 else "") + \
                  ("e" if dx < -0.35 else "w" if dx > 0.35 else "")
            c.create_text(px, py, text=txt, anchor=anc or "center", font=fb,
                          fill=MUTED)

        a, b = self.state
        bx, by, bz = bloch_vector(a, b)
        tx, ty = P(bx, by, bz)
        sx, sy = P(bx, by, 0)
        c.create_line(cx, cy, sx, sy, fill=ACCENT, dash=(2, 3))
        c.create_line(tx, ty, sx, sy, fill=ACCENT, dash=(2, 3))
        aw = max(8, lh * 0.6)
        c.create_line(cx, cy, tx, ty, fill=ACCENT2, width=3, arrow="last",
                      arrowshape=(aw, aw * 1.2, aw * 0.45))
        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=INK, outline="")

    def draw_probs(self, c, w, h):
        a, b = self.state
        draw_bars(c, w, h, ["P(0) = |a|^2", "P(1) = |b|^2"],
                  [abs(a) ** 2, abs(b) ** 2], [ACCENT, ACCENT2], vmax=1.0)

    def draw_hist(self, c, w, h):
        if not self.counts:
            draw_message(c, w, h, "No measurements yet")
            return
        draw_bars(c, w, h, ["0", "1"], self.counts, [ACCENT, ACCENT2],
                  vmax=max(self.counts) or 1, fmt="%d",
                  title="%d shots" % self.shots)


# ================================================================ PAGE: 2 QUBITS
BASIS = ["|00>", "|01>", "|10>", "|11>"]


class TwoQubitPage:
    def __init__(self, parent):
        self.history = []
        self.counts = None
        self.shots = 0

        section(parent, "Two qubits and entanglement")
        wrap_label(parent,
                   "Two qubits live in a 4-dimensional space with basis "
                   "|00>, |01>, |10>, |11>. Build a circuit with the buttons. "
                   "Tap 'Bell' for H on q0 then CNOT, which gives "
                   "(|00> + |11>)/sqrt(2), a state that cannot be split "
                   "into two separate qubits.", fg=MUTED).pack(fill="x", padx=10)

        self.circ = AspectCanvas(parent, 0.42, self.draw_circuit)
        self.circ.pack(fill="x", padx=10, pady=6)

        section(parent, "Input: gates")
        button_grid(parent, [
            ("H q0", lambda: self.add(("H", 0))),
            ("H q1", lambda: self.add(("H", 1))),
            ("X q0", lambda: self.add(("X", 0))),
            ("X q1", lambda: self.add(("X", 1))),
            ("Z q0", lambda: self.add(("Z", 0))),
            ("Z q1", lambda: self.add(("Z", 1))),
            ("CX 0->1", lambda: self.add(("CX", 0, 1))),
            ("CX 1->0", lambda: self.add(("CX", 1, 0))),
            ("Bell", self.bell),
            ("Undo", self.undo),
            ("Reset", self.reset),
        ], cols=3)

        section(parent, "Output: state vector")
        self.out = output_box(parent)
        self.ent = wrap_label(parent, "", fk="btn")
        self.ent.pack(fill="x", padx=10, pady=(2, 0))
        wrap_label(parent,
                   "Concurrence C = 2|c00*c11 - c01*c10|. C = 0 means a "
                   "product state; C = 1 means maximally entangled.",
                   fk="small", fg=MUTED).pack(fill="x", padx=10)

        section(parent, "Output: probabilities")
        self.prob = AspectCanvas(parent, 0.55, self.draw_probs)
        self.prob.pack(fill="x", padx=10, pady=4)

        section(parent, "Simulate measurement")
        mr = tk.Frame(parent, bg=BG)
        mr.pack(fill="x", padx=10, pady=4)
        tk.Label(mr, text="Shots", font=F["body"], bg=BG,
                 fg=INK).grid(row=0, column=0, sticky="w")
        self.shots_e = entry(mr, 1000)
        self.shots_e.grid(row=0, column=1, sticky="ew", padx=6)
        button(mr, "Measure", self.measure).grid(row=0, column=2, sticky="ew")
        for c in range(3):
            mr.columnconfigure(c, weight=1, uniform="m")
        self.m_status = status_label(parent)
        self.meas_out = output_box(parent)
        self.hist = AspectCanvas(parent, 0.55, self.draw_hist)
        self.hist.pack(fill="x", padx=10, pady=(4, 24))
        self.refresh()

    def compute(self):
        s = [1 + 0j, 0j, 0j, 0j]
        for g in self.history:
            if g[0] == "CX":
                s = apply_cnot(s, g[1], g[2])
            else:
                s = apply_on(s, GATES[g[0]], g[1])
        return s

    def add(self, g):
        self.history.append(g)
        self.refresh()

    def bell(self):
        self.history = [("H", 0), ("CX", 0, 1)]
        self.refresh()

    def undo(self):
        if self.history:
            self.history.pop()
        self.refresh()

    def reset(self):
        self.history = []
        self.refresh()

    def measure(self):
        try:
            shots = read_num(self.shots_e, "Shots", 1, 100000, integer=True)
        except ValueError as err:
            self.m_status.configure(text=str(err))
            return
        self.m_status.configure(text="")
        probs = [abs(c) ** 2 for c in self.state]
        self.counts = sample(probs, shots)
        self.shots = shots
        lines = ["Shots: %d" % shots]
        for k in range(4):
            lines.append("%s  %6d  freq %.4f  (P %.3f)"
                         % (BASIS[k], self.counts[k], self.counts[k] / shots,
                            probs[k]))
        agree = self.counts[0] + self.counts[3]
        lines.append("Qubits agree: %.1f%% of shots" % (100 * agree / shots))
        self.meas_out.configure(text="\n".join(lines))
        self.hist.redraw()

    def refresh(self):
        self.state = self.compute()
        s = self.state
        lines = ["basis  amplitude        prob"]
        for k in range(4):
            lines.append("%s  %-15s  %.3f" % (BASIS[k], fmt_c(s[k]),
                                              abs(s[k]) ** 2))
        self.out.configure(text="\n".join(lines))
        conc = 2 * abs(s[0] * s[3] - s[1] * s[2])
        if conc > 0.999:
            txt, col = "Maximally entangled (C = %.3f)" % conc, ACCENT2
        elif conc > 1e-6:
            txt, col = "Partly entangled (C = %.3f)" % conc, PURPLE
        else:
            txt, col = "Product state, not entangled (C = 0)", ACCENT3
        self.ent.configure(text=txt, fg=col)
        self.counts = None
        self.meas_out.configure(text="Press Measure to sample the state.")
        self.circ.redraw()
        self.prob.redraw()
        self.hist.redraw()

    def draw_circuit(self, c, w, h):
        fb, fs = F["body"], F["small"]
        lh = fb.metrics("linespace")
        left = max(fb.measure("q0 |0>"), fb.measure("q1 |0>")) + 16
        box = max(fb.measure("H") + 14, lh * 1.4)
        ys = (h * 0.32, h * 0.72)
        box = min(box, (ys[1] - ys[0]) * 0.75)
        meas_w = box * 1.3
        right = meas_w + 14
        avail = w - left - right
        if avail < box:
            return
        max_g = max(1, int(avail // (box * 1.3)))
        gates = list(self.history)
        hidden = 0
        if len(gates) > max_g:
            keep = max_g - 1
            hidden = len(gates) - keep
            gates = gates[-keep:] if keep > 0 else []
        slots = len(gates) + (1 if hidden else 0)
        slot = min(avail / max(slots, 1), box * 2.4)

        for i, y in enumerate(ys):
            c.create_text(6, y, text="q%d |0>" % i, anchor="w", font=fb,
                          fill=INK)
            c.create_line(left - 6, y, w - 8, y, fill=INK, width=2)

        x = left + slot / 2
        if hidden:
            c.create_text(x, (ys[0] + ys[1]) / 2, text="+%d" % hidden,
                          font=fs, fill=MUTED)
            x += slot
        for g in gates:
            if g[0] == "CX":
                yc, yt = ys[g[1]], ys[g[2]]
                rr = box * 0.32
                c.create_line(x, yc, x, yt + (rr if yt > yc else -rr),
                              fill=ACCENT2, width=2)
                c.create_oval(x - 5, yc - 5, x + 5, yc + 5, fill=ACCENT2,
                              outline="")
                c.create_oval(x - rr, yt - rr, x + rr, yt + rr,
                              outline=ACCENT2, width=2, fill=PANEL)
                c.create_line(x - rr, yt, x + rr, yt, fill=ACCENT2, width=2)
                c.create_line(x, yt - rr, x, yt + rr, fill=ACCENT2, width=2)
            else:
                y = ys[g[1]]
                c.create_rectangle(x - box / 2, y - box / 2, x + box / 2,
                                   y + box / 2, fill=PANEL, outline=ACCENT,
                                   width=2)
                c.create_text(x, y, text=g[0], font=F["btn"], fill=ACCENT)
            x += slot

        mx = w - right + 6
        for y in ys:
            c.create_rectangle(mx, y - box / 2, mx + meas_w, y + box / 2,
                               fill=PANEL, outline=MUTED, width=2)
            c.create_arc(mx + meas_w * 0.18, y - box * 0.15,
                         mx + meas_w * 0.82, y + box * 0.55, start=0,
                         extent=180, style="arc", outline=MUTED, width=2)
            c.create_line(mx + meas_w / 2, y + box * 0.2, mx + meas_w * 0.78,
                          y - box * 0.3, fill=MUTED, width=2)
        if not self.history:
            c.create_text(left + avail / 2, h - 6, text="empty circuit",
                          anchor="s", font=fs, fill=MUTED)

    def draw_probs(self, c, w, h):
        draw_bars(c, w, h, BASIS, [abs(x) ** 2 for x in self.state],
                  BAR_COLORS, vmax=1.0)

    def draw_hist(self, c, w, h):
        if not self.counts:
            draw_message(c, w, h, "No measurements yet")
            return
        draw_bars(c, w, h, BASIS, self.counts, BAR_COLORS,
                  vmax=max(self.counts) or 1, fmt="%d",
                  title="%d shots" % self.shots)


# ================================================================ PAGE: GROVER
class GroverPage:
    def __init__(self, parent):
        self.ks, self.ps, self.kopt = [], [], 0

        section(parent, "Grover's search: interference at work")
        wrap_label(parent,
                   "Search N unsorted items for one marked item. With "
                   "sin(theta) = 1/sqrt(N), after k iterations the chance of "
                   "measuring the right answer is P(k) = sin^2((2k+1)theta). "
                   "The best k is about (pi/4)*sqrt(N), versus about N/2 "
                   "guesses for a classical search.", fg=MUTED
                   ).pack(fill="x", padx=10)

        section(parent, "Input")
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", padx=10, pady=4)
        tk.Label(row, text="N items", font=F["body"], bg=BG,
                 fg=INK).grid(row=0, column=0, sticky="w")
        self.n_e = entry(row, 8, width=10)
        self.n_e.grid(row=0, column=1, sticky="ew", padx=6)
        button(row, "Compute", self.compute).grid(row=0, column=2, sticky="ew")
        for c in range(3):
            row.columnconfigure(c, weight=1, uniform="r")
        presets = tk.Frame(parent, bg=BG)
        presets.pack(fill="x", padx=8)
        for i, n in enumerate((4, 8, 64, 1024, 10 ** 6)):
            button(presets, "{:,}".format(n),
                   lambda n=n: self.preset(n)).grid(row=0, column=i,
                                                    sticky="ew", padx=2)
            presets.columnconfigure(i, weight=1, uniform="p")
        self.status = status_label(parent)

        section(parent, "Output")
        self.out = output_box(parent)
        self.chart = AspectCanvas(parent, 0.6, self.draw)
        self.chart.pack(fill="x", padx=10, pady=4)
        wrap_label(parent,
                   "Bars show P(k) for each iteration count k. The red bar is "
                   "the optimal k. Past it, probability falls again: "
                   "overshooting rotates the state past the answer.",
                   fk="small", fg=MUTED).pack(fill="x", padx=10, pady=(0, 24))
        self.compute()

    def preset(self, n):
        self.n_e.delete(0, "end")
        self.n_e.insert(0, str(n))
        self.compute()

    def compute(self):
        try:
            n = read_num(self.n_e, "N", 2, 10 ** 9, integer=True)
        except ValueError as err:
            self.status.configure(text=str(err))
            return
        self.status.configure(text="")
        th = math.asin(1 / math.sqrt(n))

        def P(k):
            return math.sin((2 * k + 1) * th) ** 2

        k0 = max(0, round(math.pi / (4 * th) - 0.5))
        kopt = max((k for k in (k0 - 1, k0, k0 + 1) if k >= 0), key=P)
        kmax = max(2 * kopt + 2, 4)
        if kmax + 1 <= 40:
            ks = list(range(kmax + 1))
        else:
            ks = sorted(set([round(i * kmax / 39) for i in range(40)] + [kopt]))
        self.ks, self.ps, self.kopt = ks, [P(k) for k in ks], kopt
        qubits = math.ceil(math.log2(n))
        classical = n / 2
        self.out.configure(text=(
            "N = {:,}  (needs {} qubits)\n"
            "theta = asin(1/sqrt(N)) = {:.5f} rad\n"
            "Optimal iterations k* = {:,}\n"
            "P(success at k*) = {:.4f}\n"
            "Classical average = {:,.0f} queries\n"
            "Speedup ~ {:,.1f}x fewer queries"
        ).format(n, qubits, th, kopt, P(kopt), classical,
                 classical / max(kopt, 1)))
        self.chart.redraw()

    def draw(self, c, w, h):
        if not self.ks:
            return
        cols = [ACCENT2 if k == self.kopt else ACCENT for k in self.ks]
        draw_bars(c, w, h, self.ks, self.ps, cols, vmax=1.0, fmt="%.2f",
                  title="P(success) vs iterations k")


# ================================================================ PAGE: NOISE
class NoisePage:
    def __init__(self, parent):
        self.series = []
        self.dmax = 100

        section(parent, "Noise: why depth is the enemy")
        wrap_label(parent,
                   "If each gate fails with probability p, a circuit of depth "
                   "d keeps its signal with probability about (1 - p)^d, an "
                   "exponential decay. A 3-qubit repetition code corrects any "
                   "single bit flip, so its logical error per step is "
                   "pL = 3p^2 - 2p^3 (bit-flip errors only, ideal correction).",
                   fg=MUTED).pack(fill="x", padx=10)

        section(parent, "Input")
        g = tk.Frame(parent, bg=BG)
        g.pack(fill="x", padx=10, pady=4)
        tk.Label(g, text="Error per gate p", font=F["small"], bg=BG,
                 fg=MUTED).grid(row=0, column=0, sticky="w")
        tk.Label(g, text="Max depth d", font=F["small"], bg=BG,
                 fg=MUTED).grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.p_e = entry(g, 0.01)
        self.p_e.grid(row=1, column=0, sticky="ew")
        self.d_e = entry(g, 200)
        self.d_e.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        button(g, "Compute", self.compute).grid(row=1, column=2, sticky="ew",
                                                padx=(6, 0))
        for c in range(3):
            g.columnconfigure(c, weight=1, uniform="n")
        self.status = status_label(parent)

        section(parent, "Output")
        self.out = output_box(parent)
        self.chart = AspectCanvas(parent, 0.7, self.draw)
        self.chart.pack(fill="x", padx=10, pady=4)
        leg = tk.Frame(parent, bg=BG)
        leg.pack(fill="x", padx=10, pady=(0, 24))
        wrap_label(leg, "Blue line: bare qubit, (1 - p)^d", fk="small",
                   fg=ACCENT).pack(fill="x")
        wrap_label(leg, "Green line: 3-qubit repetition code, (1 - pL)^d",
                   fk="small", fg=ACCENT3).pack(fill="x")
        wrap_label(leg, "Red dashed line: 50% survival", fk="small",
                   fg=ACCENT2).pack(fill="x")
        self.compute()

    def compute(self):
        try:
            p = read_num(self.p_e, "p", 1e-6, 0.5)
            d = read_num(self.d_e, "Max depth", 1, 100000, integer=True)
        except ValueError as err:
            self.status.configure(text=str(err))
            return
        self.status.configure(text="")
        pl = 3 * p ** 2 - 2 * p ** 3
        stride = max(1, d // 400)
        xs = list(range(0, d + 1, stride))
        if xs[-1] != d:
            xs.append(d)
        bare = [(1 - p) ** x for x in xs]
        code = [(1 - pl) ** x for x in xs]
        self.series = [(xs, code, ACCENT3), (xs, bare, ACCENT)]
        self.dmax = d
        half = math.log(0.5) / math.log(1 - p)
        half_c = math.log(0.5) / math.log(1 - pl) if pl > 0 else float("inf")
        self.out.configure(text=(
            "p = %g, logical pL = %.3g\n"
            "Bare survival at d=%d: %.4f\n"
            "Coded survival at d=%d: %.4f\n"
            "Depth for 50%% (bare):  %.1f\n"
            "Depth for 50%% (coded): %.1f\n"
            "Code helps when pL < p, i.e. p < 0.5"
            % (p, pl, d, (1 - p) ** d, d, (1 - pl) ** d, half, half_c)))
        self.chart.redraw()

    def draw(self, c, w, h):
        if self.series:
            draw_lines(c, w, h, self.series, self.dmax,
                       "circuit depth d", "survival probability", hline=0.5)


# ================================================================ PAGE: LEARN
LEARN = [
    ("The big picture",
     "IBM's Quantum System Two in Chicago runs on the Nighthawk processor. Like "
     "every gate-based quantum computer, it prepares a vector in a huge complex "
     "space, rotates it with unitary matrices, and samples the result. The "
     "pages of this app let you try each step."),
    ("1. Qubits",
     "|psi> = a|0> + b|1>, with a, b complex and |a|^2 + |b|^2 = 1.\n"
     "n qubits need 2^n amplitudes: 10 qubits need 1,024 numbers, and 50 "
     "qubits need about 10^15. That is why classical simulation breaks down."),
    ("2. Measurement (Born rule)",
     "P(0) = |a|^2 and P(1) = |b|^2. Measuring collapses the state, so one run "
     "gives one bit string. Probabilities are estimated by repeating the "
     "circuit many times, with error shrinking like 1/sqrt(shots)."),
    ("3. Gates",
     "Gates are unitary matrices (U^dagger U = I).\n"
     "X = [[0,1],[1,0]] flips the bit.\n"
     "Z = [[1,0],[0,-1]] flips the phase.\n"
     "H = (1/sqrt2)[[1,1],[1,-1]] makes superpositions: H|0> = (|0>+|1>)/sqrt2.\n"
     "Ry(t) = [[cos t/2, -sin t/2],[sin t/2, cos t/2]] is a tunable rotation."),
    ("4. Entanglement",
     "Two qubits: |Psi> = c00|00> + c01|01> + c10|10> + c11|11>.\n"
     "The Bell state (|00> + |11>)/sqrt2 cannot be written as a product of "
     "two single-qubit states. A product would need c00*c11 = c01*c10, but "
     "here 1/2 is not equal to 0. Its concurrence is 1."),
    ("5. Interference and Grover",
     "Amplitudes add and cancel like waves. Grover's algorithm uses two "
     "reflections per step to rotate the state by 2*theta toward the answer, "
     "where sin(theta) = 1/sqrt(N). It needs about (pi/4)sqrt(N) steps instead "
     "of about N/2: a quadratic, not exponential, speedup."),
    ("6. Chemistry (VQE)",
     "Drug-discovery work seeks the lowest energy E0 of a molecular "
     "Hamiltonian H = sum_j c_j P_j, where each P_j is a string of Pauli "
     "matrices. A parameterized circuit prepares |psi(t)>, the device "
     "measures E(t) = <psi(t)|H|psi(t)>, and a classical optimizer adjusts t. "
     "The variational principle guarantees E(t) >= E0."),
    ("7. Optimization (QAOA)",
     "Grid problems can be written as min x^T Q x over binary x. Substituting "
     "x_i = (1 - Z_i)/2 turns this into an Ising cost Hamiltonian C. QAOA "
     "alternates exp(-i*gamma*C) and exp(-i*beta*B), with B = sum X_i, p "
     "times. Larger p approximates better but needs deeper circuits."),
    ("8. Noise",
     "Real qubits decohere. A simple model is the depolarizing channel "
     "E(rho) = (1-p)rho + (p/3)(X rho X + Y rho Y + Z rho Z). Signal decays "
     "about as (1-p)^depth, so error correction spreads one logical qubit "
     "over many physical qubits."),
    ("Caveat",
     "VQE and QAOA have not been proven to beat the best classical methods on "
     "practical problems. IBM's claim of 'scientifically useful results' is "
     "the company's own assessment."),
]


class LearnPage:
    def __init__(self, parent):
        for title, body in LEARN:
            section(parent, title)
            wrap_label(parent, body).pack(fill="x", padx=10)
        tk.Frame(parent, bg=BG, height=30).pack()


# ================================================================ APP
class App:
    def __init__(self, root):
        self.root = root
        root.title("Quantum Explorer")
        root.configure(bg=BG)
        if not IS_ANDROID:
            root.geometry("430x840")
        self.base = 12 if IS_ANDROID else 11
        init_fonts(root, self.base)

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=8, pady=(8, 2))
        button(top, "A+", lambda: self.zoom(1), padx=10).pack(side="right")
        button(top, "A-", lambda: self.zoom(-1), padx=10).pack(side="right",
                                                              padx=4)
        wrap_label(top, "Quantum Explorer", fk="title").pack(
            side="left", fill="x", expand=True)

        nav = tk.Frame(root, bg=BG)
        nav.pack(fill="x", padx=6, pady=(0, 4))
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)

        pages = [("qubit", "Qubit", QubitPage),
                 ("two", "2 Qubits", TwoQubitPage),
                 ("grover", "Grover", GroverPage),
                 ("noise", "Noise", NoisePage),
                 ("learn", "Learn", LearnPage)]
        self.pages, self.navbtn, self.current = {}, {}, None
        for i, (key, label, cls) in enumerate(pages):
            b = button(nav, label, lambda k=key: self.show(k))
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=2, pady=2)
            self.navbtn[key] = b
            page = ScrollPage(body)
            cls(page.inner)
            page.enable_drag()
            self.pages[key] = page
        for c in range(3):
            nav.columnconfigure(c, weight=1, uniform="nav")

        root.bind_all("<MouseWheel>",
                      lambda e: self.wheel(-1 if e.delta > 0 else 1))
        root.bind_all("<Button-4>", lambda e: self.wheel(-1))
        root.bind_all("<Button-5>", lambda e: self.wheel(1))
        self.show("qubit")

    def wheel(self, units):
        if self.current:
            self.pages[self.current].wheel(units)

    def show(self, key):
        if self.current:
            self.pages[self.current].pack_forget()
            self.navbtn[self.current].configure(bg=PANEL, fg=INK)
        self.pages[key].pack(fill="both", expand=True)
        self.navbtn[key].configure(bg=ACCENT, fg="white")
        self.current = key
        self.root.after(50, self.redraw_all)

    def zoom(self, step):
        self.base = max(7, min(26, self.base + step))
        set_font_size(self.base)
        lh = line_h()
        for s in SCALES:
            s.configure(sliderlength=int(lh * 2), width=int(lh * 1.1))
        for p in self.pages.values():
            p.vsb.configure(width=max(14, int(lh * 0.9)))
        self.root.after(80, self.redraw_all)

    def redraw_all(self):
        for c in CANVASES:
            if c.winfo_ismapped():
                c.redraw()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
