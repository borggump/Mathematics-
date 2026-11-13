#!/usr/bin/env python3
"""
Quantum Entanglement Lab
========================
Touch-friendly tkinter app for Pydroid 3 (Android). Also runs on any
desktop Python that has tkinter. No pip packages needed.

HOW TO USE
  1. Open this file in Pydroid 3 and tap the yellow Play button.
  2. Setup tab: pick a Bell state, set Alice's and Bob's polarizer angles,
     the pair purity p (noise) and the number of pairs per measurement.
  3. Bottom buttons:
       Run    simulate one measurement, see counts and correlation E
       CHSH   Bell/CHSH test with the best angle settings
       Sweep  measure E at many Bob angles and plot them on the curve
       Reset  restore defaults
  4. Tabs: Setup | Diagram | Graphs | Results

If text looks too small or too big on your phone, change SCALE below.

PHYSICS (two photons, polarization qubits, basis H=|0>, V=|1>)
  State:  rho = p |Bell><Bell| + (1-p) I/4        (Werner state)
  A polarizer at angle t projects onto
        |+t> = cos t |H> + sin t |V>      (result +1, photon passes)
        |-t> = -sin t |H> + cos t |V>     (result -1, photon blocked)
  Joint probability  P(a,b) = <a_t, b_f| rho |a_t, b_f>
  Correlation        E = P(++) + P(--) - P(+-) - P(-+)
  CHSH               S = E(a,b) + E(a,b') + E(a',b) - E(a',b')
                     |S| <= 2 for local hidden variables, up to 2*sqrt(2)
                     for quantum mechanics.
"""
import math
import random
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------- UI settings
SCALE = 1.0          # increase for bigger text, decrease for smaller

BG = "#0f172a"
TXT = "#e5e7eb"
GRID = "#334155"
ACC = "#38bdf8"
ALICE_C = "#38bdf8"
BOB_C = "#fb923c"
PURPLE = "#a78bfa"
GREEN = "#22c55e"
RED = "#ef4444"
GREY = "#94a3b8"


def F(size, bold=False):
    return ("Helvetica", max(6, int(round(size * SCALE))),
            "bold" if bold else "normal")


def FM(size):
    return ("Courier", max(6, int(round(size * SCALE))))


# -------------------------------------------------------------------- physics
S2 = 1.0 / math.sqrt(2.0)

# basis order: |HH>, |HV>, |VH>, |VV>
BELL = {
    "Phi+": ([S2, 0.0, 0.0, S2], "(|HH> + |VV>)/sqrt2"),
    "Phi-": ([S2, 0.0, 0.0, -S2], "(|HH> - |VV>)/sqrt2"),
    "Psi+": ([0.0, S2, S2, 0.0], "(|HV> + |VH>)/sqrt2"),
    "Psi-": ([0.0, S2, -S2, 0.0], "(|HV> - |VH>)/sqrt2"),
}
FORMULA = {
    "Phi+": "+cos 2(a-b)",
    "Phi-": "+cos 2(a+b)",
    "Psi+": "-cos 2(a+b)",
    "Psi-": "-cos 2(a-b)",
}
STATES = ["Phi+", "Phi-", "Psi+", "Psi-"]
OUTCOMES = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
LABEL = {(1, 1): "++", (1, -1): "+-", (-1, 1): "-+", (-1, -1): "--"}
TSIRELSON = 2.0 * math.sqrt(2.0)


def density(name, p):
    """Werner-type state: p * |Bell><Bell| + (1-p) * I/4."""
    v = BELL[name][0]
    return [[p * v[i] * v[j] + (((1.0 - p) / 4.0) if i == j else 0.0)
             for j in range(4)] for i in range(4)]


def pol_vec(angle_deg, outcome):
    t = math.radians(angle_deg)
    if outcome == 1:
        return (math.cos(t), math.sin(t))
    return (-math.sin(t), math.cos(t))


def joint_probs(rho, a_deg, b_deg):
    probs = {}
    for a in (1, -1):
        ea = pol_vec(a_deg, a)
        for b in (1, -1):
            fb = pol_vec(b_deg, b)
            v = [ea[0] * fb[0], ea[0] * fb[1], ea[1] * fb[0], ea[1] * fb[1]]
            s = 0.0
            for i in range(4):
                for j in range(4):
                    s += v[i] * rho[i][j] * v[j]
            probs[(a, b)] = s
    return probs


def corr_from_probs(pr):
    return pr[(1, 1)] + pr[(-1, -1)] - pr[(1, -1)] - pr[(-1, 1)]


def expect(rho, a_deg, b_deg):
    return corr_from_probs(joint_probs(rho, a_deg, b_deg))


def sample_counts(probs, n):
    keys = OUTCOMES
    weights = [max(0.0, probs[k]) for k in keys]
    counts = {k: 0 for k in keys}
    for k in random.choices(keys, weights=weights, k=n):
        counts[k] += 1
    return counts


def corr_from_counts(counts, n):
    return (counts[(1, 1)] + counts[(-1, -1)]
            - counts[(1, -1)] - counts[(-1, 1)]) / float(n)


def chsh_best(rho):
    """Search a 7.5-degree grid for the settings that maximise |S|."""
    angles = [i * 7.5 for i in range(24)]          # 0 .. 172.5
    tbl = {}
    for t in angles:
        for f in angles:
            tbl[(t, f)] = expect(rho, t, f)
    a = 0.0
    best_val, best = -1.0, None
    for a2 in angles:
        for b in angles:
            for b2 in angles:
                s = tbl[(a, b)] + tbl[(a, b2)] + tbl[(a2, b)] - tbl[(a2, b2)]
                if abs(s) > best_val + 1e-12:
                    best_val, best = abs(s), (a, a2, b, b2)
    return best


# ------------------------------------------------------------- UI components
def wlabel(parent, text, size=11, **kw):
    """Label that re-wraps itself to its width."""
    lab = tk.Label(parent, text=text, font=F(size), justify="left",
                   anchor="w", **kw)
    lab.bind("<Configure>",
             lambda e: lab.config(wraplength=max(100, e.width - 8)))
    lab.pack(fill="x", padx=8, pady=3)
    return lab


class ScrollFrame(tk.Frame):
    """Vertically scrolling frame; drag on empty areas to scroll (touch)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.inner,
                                                anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        self._y = 0
        self._top = 0.0

    def enable_drag(self):
        self._bind(self.canvas)
        self._bind(self.inner)

    def _bind(self, w):
        if isinstance(w, (tk.Scale, tk.Button, tk.Radiobutton, tk.Scrollbar)):
            return
        w.bind("<ButtonPress-1>", self._press, add="+")
        w.bind("<B1-Motion>", self._drag, add="+")
        for ch in w.winfo_children():
            self._bind(ch)

    def _press(self, e):
        self._y = e.y_root
        self._top = self.canvas.yview()[0]

    def _drag(self, e):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return
        h = bbox[3] - bbox[1]
        if h <= self.canvas.winfo_height():
            return
        self.canvas.yview_moveto(self._top - (e.y_root - self._y) / float(h))


# ------------------------------------------------------------------------ app
class App:
    def __init__(self, root):
        self.root = root
        self.ready = False
        root.title("Quantum Entanglement Lab")

        self.state = tk.StringVar(value="Phi+")
        self.alice = tk.DoubleVar(value=0.0)
        self.bob = tk.DoubleVar(value=22.5)
        self.purity = tk.DoubleVar(value=1.0)
        self.shots = tk.DoubleVar(value=2000)
        self.ket_var = tk.StringVar(value="")

        self.last = None      # last single measurement
        self.chsh = None      # last CHSH test
        self.sweep = None     # last angle sweep

        self.anim_t = None
        self.anim_show = False
        self.anim_result = None
        self.anim_job = None
        self._ty = 0

        self.build_ui()
        self.ready = True
        self.on_change()

    # ------------------------------------------------------------- building
    def build_ui(self):
        root = self.root

        # bottom action bar (always visible)
        bar = tk.Frame(root)
        bar.pack(side="bottom", fill="x")
        buttons = [("Run", self.run_measurement), ("CHSH", self.run_chsh),
                   ("Sweep", self.run_sweep), ("Reset", self.reset)]
        for i, (txt, cmd) in enumerate(buttons):
            tk.Button(bar, text=txt, font=F(14, True), command=cmd).grid(
                row=0, column=i, sticky="nsew", padx=2, pady=4)
            bar.columnconfigure(i, weight=1)

        self.status = tk.Label(root, text="Set the controls, then tap Run.",
                               font=F(11), anchor="w", justify="left")
        self.status.pack(side="bottom", fill="x", padx=6)
        self.status.bind(
            "<Configure>",
            lambda e: self.status.config(wraplength=max(100, e.width - 12)))

        style = ttk.Style()
        style.configure("TNotebook.Tab", font=F(12, True), padding=[12, 8])
        self.nb = ttk.Notebook(root)
        self.nb.pack(side="top", fill="both", expand=True)
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self.build_setup_tab()
        self.build_diagram_tab()
        self.build_graphs_tab()
        self.build_results_tab()

    def slider(self, parent, text, var, lo, hi, res, step, fmt, presets=None):
        box = tk.Frame(parent, bd=1, relief="groove")
        box.pack(fill="x", padx=8, pady=5)
        head = tk.Frame(box)
        head.pack(fill="x", padx=4)
        tk.Label(head, text=text, font=F(12, True)).pack(side="left")
        val = tk.Label(head, font=F(12, True), fg="#0369a1")
        val.pack(side="right")

        def show():
            val.config(text=fmt.format(var.get()))

        def changed(*_):
            show()
            self.on_change()

        def setv(v):
            var.set(round(max(lo, min(hi, v)), 4))
            changed()

        row = tk.Frame(box)
        row.pack(fill="x")
        tk.Button(row, text="-", font=F(14, True), width=3,
                  command=lambda: setv(var.get() - step)).pack(
            side="left", padx=2, pady=2)
        tk.Scale(row, from_=lo, to=hi, resolution=res, orient="horizontal",
                 variable=var, showvalue=0, sliderlength=int(46 * SCALE),
                 width=int(30 * SCALE), command=changed).pack(
            side="left", fill="x", expand=True)
        tk.Button(row, text="+", font=F(14, True), width=3,
                  command=lambda: setv(var.get() + step)).pack(
            side="left", padx=2, pady=2)
        if presets:
            pr = tk.Frame(box)
            pr.pack(fill="x", pady=(0, 3))
            for v in presets:
                tk.Button(pr, text="%g" % v, font=F(10),
                          command=lambda v=v: setv(v)).pack(
                    side="left", expand=True, fill="x", padx=1)
        show()

    def build_setup_tab(self):
        sf = ScrollFrame(self.nb)
        self.tab_setup = sf
        body = sf.inner

        tk.Label(body, text="Quantum Entanglement Lab",
                 font=F(17, True)).pack(pady=(8, 2))
        wlabel(body,
               "A source sends one photon to Alice and one to Bob. Each "
               "sends it through a polarizer at a chosen angle and records "
               "+ (passes) or - (blocked). Alone, each result is random. "
               "Together they are correlated. Try Phi+ with equal angles "
               "(E = +1), then run CHSH.")

        tk.Label(body, text="Entangled state", font=F(13, True),
                 anchor="w").pack(fill="x", padx=8, pady=(8, 0))
        grid = tk.Frame(body)
        grid.pack(fill="x", padx=8)
        for i, name in enumerate(STATES):
            tk.Radiobutton(grid, text=name, value=name, variable=self.state,
                           indicatoron=0, font=F(14, True), pady=8,
                           selectcolor="#38bdf8",
                           command=self.on_change).grid(
                row=i // 2, column=i % 2, sticky="nsew", padx=3, pady=3)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        tk.Label(body, textvariable=self.ket_var, font=F(12),
                 fg="#4338ca").pack(pady=2)

        presets = [0, 22.5, 45, 67.5, 90, 135]
        self.slider(body, "Alice polarizer angle", self.alice,
                    0, 180, 0.5, 1, "{:.1f}\u00b0", presets)
        self.slider(body, "Bob polarizer angle", self.bob,
                    0, 180, 0.5, 1, "{:.1f}\u00b0", presets)
        self.slider(body, "Pair purity p (noise)", self.purity,
                    0, 1, 0.01, 0.05, "{:.2f}")
        self.slider(body, "Pairs per measurement", self.shots,
                    100, 20000, 100, 500, "{:.0f}")

        wlabel(body,
               "Purity p: 1 = perfect pairs, 0 = pure noise. The pair is "
               "entangled only for p > 1/3, and violates the CHSH limit "
               "only for p > 0.707.", size=10)
        wlabel(body, "Drag on empty space to scroll this page.", size=10)

        sf.enable_drag()
        self.nb.add(sf, text="Setup")

    def build_diagram_tab(self):
        t = tk.Frame(self.nb)
        self.tab_diagram = t
        tk.Button(t, text="Animate one photon pair", font=F(13),
                  command=self.animate).pack(side="bottom", fill="x",
                                             padx=6, pady=4)
        self.cv_diag = tk.Canvas(t, bg=BG, highlightthickness=0)
        self.cv_diag.pack(fill="both", expand=True)
        self.cv_diag.bind("<Configure>", lambda e: self.draw_diagram())
        self.nb.add(t, text="Diagram")

    def build_graphs_tab(self):
        t = tk.Frame(self.nb)
        self.tab_graphs = t
        self.cv_curve = tk.Canvas(t, bg=BG, highlightthickness=0)
        self.cv_curve.pack(fill="both", expand=True, pady=(0, 2))
        self.cv_curve.bind("<Configure>", lambda e: self.draw_curve())
        self.cv_chsh = tk.Canvas(t, bg=BG, highlightthickness=0)
        self.cv_chsh.pack(fill="both", expand=True)
        self.cv_chsh.bind("<Configure>", lambda e: self.draw_chsh_bars())
        self.nb.add(t, text="Graphs")

    def build_results_tab(self):
        t = tk.Frame(self.nb)
        self.tab_results = t
        sb = tk.Scrollbar(t, width=int(34 * SCALE))
        sb.pack(side="right", fill="y")
        self.txt = tk.Text(t, font=FM(11), wrap="word", bg="#0b1220",
                           fg=TXT, padx=8, pady=8, state="disabled",
                           cursor="arrow", yscrollcommand=sb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self.txt.yview)
        self.txt.bind("<ButtonPress-1>", self._tpress)
        self.txt.bind("<B1-Motion>", self._tdrag)
        self.nb.add(t, text="Results")

    def _tpress(self, e):
        self._ty = e.y
        return "break"

    def _tdrag(self, e):
        step = max(8, int(18 * SCALE))
        dy = self._ty - e.y
        if abs(dy) >= step:
            self.txt.yview_scroll(int(dy / step), "units")
            self._ty = e.y
        return "break"

    # -------------------------------------------------------------- helpers
    def rho(self):
        return density(self.state.get(), self.purity.get())

    def key(self):
        return (self.state.get(), round(self.purity.get(), 3),
                round(self.alice.get(), 2))

    def cancel_anim(self):
        if self.anim_job is not None:
            try:
                self.root.after_cancel(self.anim_job)
            except Exception:
                pass
            self.anim_job = None

    def on_change(self, *_):
        if not self.ready:
            return
        self.cancel_anim()
        self.anim_t = None
        self.anim_show = False
        name = self.state.get()
        self.ket_var.set("%s = %s" % (name, BELL[name][1]))
        self.refresh_all()

    def refresh_all(self):
        if not self.ready:
            return
        self.draw_diagram()
        self.draw_curve()
        self.draw_chsh_bars()
        self.update_report()

    # ------------------------------------------------------------ animation
    def animate(self):
        self.cancel_anim()
        probs = joint_probs(self.rho(), self.alice.get(), self.bob.get())
        self.anim_result = random.choices(
            OUTCOMES, weights=[max(0.0, probs[k]) for k in OUTCOMES])[0]
        self.anim_t = 0.0
        self.anim_show = False
        self._tick()

    def _tick(self):
        self.anim_t += 0.05
        if self.anim_t >= 1.0:
            self.anim_t = 1.0
            self.anim_show = True
            self.anim_job = None
            self.draw_diagram()
            a, b = self.anim_result
            self.status.config(
                text="Pair result: Alice %s, Bob %s. Tap again to repeat."
                % ("+" if a == 1 else "-", "+" if b == 1 else "-"))
            return
        self.draw_diagram()
        self.anim_job = self.root.after(35, self._tick)

    # -------------------------------------------------------------- drawing
    def draw_diagram(self):
        c = self.cv_diag
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        c.delete("all")
        cy = h * 0.34
        sx = w * 0.5
        ax, bx = w * 0.23, w * 0.77
        dax, dbx = w * 0.07, w * 0.93
        r = min(w * 0.085, h * 0.15)

        c.create_text(w / 2, h * 0.05, text="Entangled photon pair",
                      fill=TXT, font=F(14, True))
        c.create_line(dax, cy, dbx, cy, fill=GRID, dash=(5, 4), width=2)

        # source
        c.create_rectangle(sx - w * 0.09, cy - h * 0.08, sx + w * 0.09,
                           cy + h * 0.08, fill="#312e81", outline=PURPLE,
                           width=2)
        c.create_text(sx, cy, text="Source\n" + self.state.get(),
                      fill=TXT, font=F(11, True), justify="center")

        # polarizers
        self._polarizer(c, ax, cy, r, self.alice.get(), ALICE_C, "Alice", h)
        self._polarizer(c, bx, cy, r, self.bob.get(), BOB_C, "Bob", h)

        # detectors
        res_a = res_b = None
        if self.anim_show and self.anim_result is not None:
            res_a, res_b = self.anim_result
        self._detector(c, dax, cy, w * 0.045, res_a)
        self._detector(c, dbx, cy, w * 0.045, res_b)

        # photons in flight
        if self.anim_t is not None and not self.anim_show:
            t = self.anim_t
            rad = max(4, h * 0.018)
            for tx in (dax, dbx):
                px = sx + (tx - sx) * t
                c.create_oval(px - rad, cy - rad, px + rad, cy + rad,
                              fill=PURPLE, outline="")

        # text block
        E = expect(self.rho(), self.alice.get(), self.bob.get())
        y = h * 0.64
        lines = [
            ("Correlation E (theory): %+.3f" % E, TXT, True),
            ("E = +1: always the same result", GREY, False),
            ("E = -1: always opposite results", GREY, False),
            ("Each photon alone: random 50/50", GREY, False),
        ]
        for text, col, bold in lines:
            c.create_text(w / 2, y, text=text, fill=col,
                          font=F(12, bold))
            y += h * 0.075
        if self.anim_show and self.anim_result is not None:
            a, b = self.anim_result
            same = (a == b)
            c.create_text(w / 2, y + h * 0.02,
                          text="This pair: Alice %s, Bob %s (%s)" % (
                              "+" if a == 1 else "-", "+" if b == 1 else "-",
                              "same" if same else "opposite"),
                          fill=GREEN, font=F(13, True))

    def _polarizer(self, c, x, y, r, ang, color, name, h):
        c.create_oval(x - r, y - r, x + r, y + r, outline=color, width=3)
        c.create_line(x - r, y, x + r, y, fill=GRID, dash=(2, 3))
        t = math.radians(ang)
        dx, dy = r * math.cos(t), -r * math.sin(t)
        c.create_line(x - dx, y - dy, x + dx, y + dy, fill=color, width=5,
                      capstyle="round")
        c.create_text(x, y + r + h * 0.065,
                      text="%s\n%.1f\u00b0" % (name, ang), fill=color,
                      font=F(12, True), justify="center")

    def _detector(self, c, x, y, s, outcome):
        if outcome is None:
            fill, txt = "#1f2937", "?"
        elif outcome == 1:
            fill, txt = "#166534", "+"
        else:
            fill, txt = "#991b1b", "-"
        c.create_rectangle(x - s, y - s, x + s, y + s, fill=fill,
                           outline=TXT, width=2)
        c.create_text(x, y, text=txt, fill=TXT, font=F(16, True))

    def draw_curve(self):
        c = self.cv_curve
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        c.delete("all")
        L, R, T, B = w * 0.13, w * 0.96, h * 0.17, h * 0.78
        A = self.alice.get()
        rho = self.rho()

        def X(a):
            return L + a / 180.0 * (R - L)

        def Y(e):
            return T + (1 - e) / 2.0 * (B - T)

        c.create_text(w / 2, h * 0.07,
                      text="Correlation E vs Bob angle (Alice = %.1f\u00b0)" % A,
                      fill=TXT, font=F(12, True))
        for e in (1, 0, -1):
            c.create_line(L, Y(e), R, Y(e), fill=GRID)
            c.create_text(L - 6, Y(e), text=("%+d" % e) if e else "0",
                          anchor="e", fill=GREY, font=F(10))
        for a in (0, 45, 90, 135, 180):
            c.create_line(X(a), T, X(a), B, fill=GRID)
            c.create_text(X(a), B + 6, text=str(a), anchor="n", fill=GREY,
                          font=F(10))
        c.create_text(w / 2, h * 0.97, text="Bob polarizer angle (deg)",
                      anchor="s", fill=GREY, font=F(10))

        pts = []
        for i in range(0, 181, 3):
            pts += [X(i), Y(expect(rho, A, i))]
        c.create_line(*pts, fill=ACC, width=3, smooth=True)

        rad = max(3, min(w, h) * 0.014)
        # sweep points
        if self.sweep and self.sweep["key"] == self.key():
            for ang, em in self.sweep["points"]:
                c.create_oval(X(ang) - rad, Y(em) - rad, X(ang) + rad,
                              Y(em) + rad, fill=GREEN, outline="")
        # last single run
        if self.last and self.last["key"] == self.key():
            x, y = X(self.last["B"]), Y(self.last["E"])
            c.create_rectangle(x - rad, y - rad, x + rad, y + rad,
                               fill=RED, outline="")
        # current setting marker
        cur = self.bob.get()
        c.create_line(X(cur), T, X(cur), B, fill=BOB_C, dash=(4, 3))
        ec = expect(rho, A, cur)
        c.create_oval(X(cur) - rad - 1, Y(ec) - rad - 1, X(cur) + rad + 1,
                      Y(ec) + rad + 1, outline=BOB_C, width=2)

    def draw_chsh_bars(self):
        c = self.cv_chsh
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        c.delete("all")
        p = self.purity.get()
        items = [("Classical limit", 2.0, GREY),
                 ("Quantum limit", TSIRELSON, PURPLE),
                 ("Theory (this p)", p * TSIRELSON, ACC)]
        if self.chsh and self.chsh["key"] == (self.state.get(),
                                              round(p, 3)):
            items.append(("Measured", abs(self.chsh["S_meas"]), GREEN))
        c.create_text(w / 2, h * 0.08,
                      text="CHSH value |S| (above 2: no local hidden variables)",
                      fill=TXT, font=F(11, True))
        L, R = w * 0.36, w * 0.95
        maxv = 3.0
        top, bottom = h * 0.18, h * 0.95
        rowh = (bottom - top) / 4.0
        for i, (label, val, col) in enumerate(items):
            yc = top + rowh * (i + 0.5)
            c.create_text(L - 8, yc, text=label, anchor="e", fill=TXT,
                          font=F(10))
            c.create_rectangle(L, yc - rowh * 0.3,
                               L + val / maxv * (R - L), yc + rowh * 0.3,
                               fill=col, outline="")
            c.create_text(L + val / maxv * (R - L) + 4, yc,
                          text="%.2f" % val, anchor="w", fill=TXT,
                          font=F(10, True))
        x2 = L + 2.0 / maxv * (R - L)
        c.create_line(x2, top, x2, bottom, fill=RED, dash=(4, 3), width=2)

    # --------------------------------------------------------------- actions
    def run_measurement(self):
        n = int(self.shots.get())
        rho = self.rho()
        A, B = self.alice.get(), self.bob.get()
        probs = joint_probs(rho, A, B)
        counts = sample_counts(probs, n)
        Em = corr_from_counts(counts, n)
        Eth = corr_from_probs(probs)
        self.last = dict(state=self.state.get(), p=self.purity.get(), A=A,
                         B=B, n=n, counts=counts, E=Em, Eth=Eth,
                         key=self.key())
        self.status.config(
            text="Measured E = %+.3f (theory %+.3f) from %d pairs."
            % (Em, Eth, n))
        self.refresh_all()
        self.nb.select(self.tab_results)

    def run_chsh(self):
        self.status.config(text="Running CHSH test...")
        self.root.update_idletasks()
        n = int(self.shots.get())
        rho = self.rho()
        a, a2, b, b2 = chsh_best(rho)
        pairs = [("E(a,b)", a, b, 1), ("E(a,b')", a, b2, 1),
                 ("E(a',b)", a2, b, 1), ("E(a',b')", a2, b2, -1)]
        S_th = S_m = var = 0.0
        rows = []
        for name, x, y, sgn in pairs:
            probs = joint_probs(rho, x, y)
            eth = corr_from_probs(probs)
            em = corr_from_counts(sample_counts(probs, n), n)
            S_th += sgn * eth
            S_m += sgn * em
            var += (1.0 - em * em) / n
            rows.append((name, x, y, eth, em))
        self.chsh = dict(key=(self.state.get(), round(self.purity.get(), 3)),
                         angles=(a, a2, b, b2), rows=rows, S_th=S_th,
                         S_meas=S_m, sigma=math.sqrt(var), n=n)
        verdict = "violates" if abs(S_m) > 2.0 else "does not violate"
        self.status.config(
            text="CHSH |S| = %.3f, classical limit 2: %s the bound."
            % (abs(S_m), verdict))
        self.refresh_all()
        self.nb.select(self.tab_results)

    def run_sweep(self):
        self.status.config(text="Sweeping Bob angle...")
        self.root.update_idletasks()
        n = int(self.shots.get())
        rho = self.rho()
        A = self.alice.get()
        pts = []
        for ang in range(0, 181, 10):
            probs = joint_probs(rho, A, ang)
            pts.append((ang, corr_from_counts(sample_counts(probs, n), n)))
        self.sweep = dict(key=self.key(), points=pts, n=n)
        self.status.config(text="Sweep done: green dots are measured E.")
        self.refresh_all()
        self.nb.select(self.tab_graphs)

    def reset(self):
        self.cancel_anim()
        self.state.set("Phi+")
        self.alice.set(0.0)
        self.bob.set(22.5)
        self.purity.set(1.0)
        self.shots.set(2000)
        self.last = self.chsh = self.sweep = None
        self.anim_t = None
        self.anim_show = False
        self.status.config(text="Reset. Set the controls, then tap Run.")
        # sliders' value labels refresh via re-selecting the tab
        self.nb.select(self.tab_setup)
        self.on_change()
        self._refresh_setup_labels()

    def _refresh_setup_labels(self):
        # Scale widgets follow their variables; value labels need a nudge.
        def walk(w):
            for ch in w.winfo_children():
                if isinstance(ch, tk.Scale):
                    ch.set(ch.get())
                walk(ch)
        walk(self.tab_setup)

    # --------------------------------------------------------------- report
    def update_report(self):
        name = self.state.get()
        p = self.purity.get()
        A, B = self.alice.get(), self.bob.get()
        rho = self.rho()
        pr = joint_probs(rho, A, B)
        E = corr_from_probs(pr)
        conc = max(0.0, (3 * p - 1) / 2.0)
        L = []
        L.append("== CURRENT SETUP ==")
        L.append("State : %s" % name)
        L.append("        %s" % BELL[name][1])
        L.append("Purity: p = %.2f" % p)
        L.append("Entangled: %s (concurrence %.3f)"
                 % ("YES" if p > 1.0 / 3.0 else "NO", conc))
        L.append("Alice %.1f deg, Bob %.1f deg" % (A, B))
        L.append("")
        L.append("Theory (quantum mechanics):")
        for k in OUTCOMES:
            L.append("  P(%s) = %.4f" % (LABEL[k], pr[k]))
        L.append("  E = %+.4f" % E)
        L.append("  E = p x (%s)" % FORMULA[name])
        L.append("  a = Alice angle, b = Bob angle")
        pa = pr[(1, 1)] + pr[(1, -1)]
        pb = pr[(1, 1)] + pr[(-1, 1)]
        L.append("Alice alone P(+) = %.3f" % pa)
        L.append("Bob alone   P(+) = %.3f" % pb)
        L.append("Each side random, yet joint")
        L.append("results are correlated.")
        L.append("(No-signaling: Alice's")
        L.append("statistics never depend on")
        L.append("Bob's angle.)")

        if self.last:
            d = self.last
            n = d["n"]
            L += ["", "== LAST RUN ==",
                  "%s p=%.2f a=%.1f b=%.1f" % (d["state"], d["p"],
                                               d["A"], d["B"]),
                  "%d pairs" % n]
            for k in OUTCOMES:
                L.append("  %s: %5d (%.3f)" % (LABEL[k], d["counts"][k],
                                               d["counts"][k] / float(n)))
            sig = math.sqrt(max(0.0, 1 - d["E"] ** 2) / n)
            L.append("E measured = %+.4f +/- %.4f" % (d["E"], sig))
            L.append("E theory   = %+.4f" % d["Eth"])

        if self.chsh:
            d = self.chsh
            a, a2, b, b2 = d["angles"]
            L += ["", "== CHSH TEST ==",
                  "state %s, p=%.2f, %d pairs/setting" % (
                      d["key"][0], d["key"][1], d["n"]),
                  "Best settings (deg):",
                  "  a=%.1f a'=%.1f" % (a, a2),
                  "  b=%.1f b'=%.1f" % (b, b2)]
            for nm, x, y, eth, em in d["rows"]:
                L.append("  %-9s th %+.3f  meas %+.3f" % (nm, eth, em))
            L.append("S = E(a,b)+E(a,b')+E(a',b)-E(a',b')")
            L.append("S theory   = %+.4f" % d["S_th"])
            L.append("S measured = %+.4f +/- %.4f" % (d["S_meas"],
                                                      d["sigma"]))
            L.append("Classical limit |S| <= 2")
            L.append("Quantum limit 2*sqrt2 = %.4f" % TSIRELSON)
            if abs(d["S_meas"]) > 2.0:
                if d["sigma"] > 0:
                    L.append("VIOLATION by %.1f sigma:" %
                             ((abs(d["S_meas"]) - 2.0) / d["sigma"]))
                else:
                    L.append("VIOLATION:")
                L.append("no local hidden-variable")
                L.append("model can explain this.")
            else:
                L.append("No violation: classical")
                L.append("correlations could explain it.")

        if self.sweep:
            d = self.sweep
            dev = []
            rho_s = density(d["key"][0], d["key"][1])
            for ang, em in d["points"]:
                dev.append(em - expect(rho_s, d["key"][2], ang))
            rms = math.sqrt(sum(x * x for x in dev) / len(dev))
            L += ["", "== SWEEP ==",
                  "%s p=%.2f, Alice %.1f deg" % d["key"],
                  "%d angles x %d pairs" % (len(d["points"]), d["n"]),
                  "RMS deviation from theory:",
                  "  %.4f" % rms]

        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("end", "\n".join(L))
        self.txt.config(state="disabled")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
