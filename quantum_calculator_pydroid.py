"""
Quantum Hardware Simulation Calculator
--------------------------------------
Touch-friendly tkinter GUI for Pydroid 3 (Android). Uses only the Python
standard library (tkinter), so nothing needs to be installed with pip.

Modules (same physics as the HTML explainer):
  Resonator  - LC resonance frequency and impedance
  Qubit      - transmon f01, coupling g, dispersive shift chi   (+ plot)
  Photonics  - waveguide loss, resonator Q, guided wavelength   (+ plot)
  Crosstalk  - capacitance-matrix crosstalk and charging energy
  Thermal    - thermal photon occupation, T2                    (+ plot)
  Transport  - Landauer conductance and current

Usage: tap a module, edit the numbers, tap Calculate.
Drag on empty space to scroll.
"""

import math
import tkinter as tk
import tkinter.font as tkfont

# ---------------------------------------------------------------- constants
H = 6.62607015e-34      # Planck constant, J s
KB = 1.380649e-23       # Boltzmann constant, J/K
E = 1.602176634e-19     # elementary charge, C
G0 = 2 * E ** 2 / H     # conductance quantum (spin-degenerate), S

# ------------------------------------------------------------------- colors
BG = "#f7f8fa"
CARD = "#ffffff"
INK = "#1d2433"
MUTED = "#5b6474"
ACC = "#2b59c3"
ACC2 = "#0f9d8a"
ERR = "#c2410c"
LINE = "#d9dee8"


# ------------------------------------------------------------------ helpers
def g4(x):
    return "%.4g" % x


def eng(x, unit):
    """Format a number with an SI prefix, e.g. 6.2e-7 A -> '620 nA'."""
    if x == 0:
        return "0 " + unit
    prefixes = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1, ""),
                (1e-3, "m"), (1e-6, "\u00b5"), (1e-9, "n"), (1e-12, "p")]
    for scale, p in prefixes:
        if abs(x) >= scale:
            return "%.4g %s%s" % (x / scale, p, unit)
    return "%.3g %s" % (x, unit)


# ------------------------------------------------------------ calculations
def calc_lc(v):
    L = v["L"] * 1e-9
    C = v["C"] * 1e-12
    if L <= 0 or C <= 0:
        raise ValueError("L and C must be positive.")
    w = 1.0 / math.sqrt(L * C)
    f = w / (2 * math.pi)
    z0 = math.sqrt(L / C)
    text = (
        "Resonance  f = %s GHz\n"
        "Angular  \u03c9 = %s rad/ns\n"
        "Impedance  Z\u2080 = %s \u03a9"
    ) % (g4(f / 1e9), g4(w / 1e9), g4(z0))
    return text, None


def calc_qubit(v):
    EJ = v["EJ"]
    EC = v["EC"] / 1000.0          # GHz
    fr = v["fr"]
    Cg, C1, C2 = v["Cg"], v["C1"], v["C2"]
    if EJ <= 0 or EC <= 0 or fr <= 0 or C1 <= 0 or C2 <= 0:
        raise ValueError("EJ, EC, fr, C1 and C2 must be positive.")
    f01 = math.sqrt(8 * EJ * EC) - EC            # GHz
    if f01 <= 0:
        raise ValueError("Qubit frequency is not positive; check EJ and EC.")
    alpha = -EC * 1000.0                          # MHz
    delta = (f01 - fr) * 1000.0                   # MHz
    g = 0.5 * Cg / math.sqrt(C1 * C2) * math.sqrt(f01 * fr) * 1000.0  # MHz
    if delta == 0 or delta + alpha == 0:
        raise ValueError("Detuning \u0394 is zero or equals \u2212\u03b1; "
                         "the formula diverges.")
    chi = g * g / delta * alpha / (delta + alpha)
    ratio = abs(g / delta)

    lines = [
        "Qubit  f\u2080\u2081 \u2248 %s GHz   (EJ/EC = %s)" % (g4(f01), g4(EJ / EC)),
        "Anharmonicity  \u03b1 \u2248 %s MHz" % g4(alpha),
        "Detuning  \u0394 = f\u2080\u2081 \u2212 f\u1d63 = %s MHz" % g4(delta),
        "Coupling  g \u2248 %s MHz" % g4(g),
        "Dispersive shift  \u03c7 = %s MHz" % g4(chi),
        "|g/\u0394| = %s" % g4(ratio),
    ]
    if ratio > 0.3:
        lines.append("Warning: g/\u0394 is not small, so the dispersive "
                     "formula is unreliable.")
    if EJ / EC < 20:
        lines.append("Note: EJ/EC < 20, so the transmon approximation "
                     "is rough.")

    # Plot |chi| versus |detuning| with g and alpha held fixed
    sign = 1.0 if delta >= 0 else -1.0
    # range always includes the current detuning so the "now" marker shows
    start = max(min(4 * abs(g), abs(delta) * 0.5), 50.0)
    end = max(start * 4, abs(delta) * 2.0)
    xs, ys = [], []
    n = 80
    for i in range(n + 1):
        x = start + (end - start) * i / n
        d = sign * x
        # skip the pole at d = -alpha, where the formula diverges
        if abs(d + alpha) < 0.05 * abs(alpha):
            continue
        xs.append(x)
        ys.append(abs(g * g / d * alpha / (d + alpha)))
    marker = (abs(delta), abs(chi))
    plot = dict(xs=xs, ys=ys, ylog=True, marker=marker,
                xlabel="|\u0394| (MHz)",
                ylabel="|\u03c7| (MHz), g and \u03b1 fixed")
    return "\n".join(lines), plot


def calc_photonic(v):
    L, pin, pout = v["L"], v["Pin"], v["Pout"]
    f0, df = v["f0"], v["df"]
    neff, lam = v["neff"], v["lam"]
    if L <= 0 or pin <= 0 or pout <= 0:
        raise ValueError("Length and both powers must be positive.")
    if pout > pin:
        raise ValueError("Output power cannot exceed input power.")
    if f0 <= 0 or df <= 0 or neff <= 0 or lam <= 0:
        raise ValueError("f0, \u0394f, n_eff and \u03bb0 must be positive.")
    a_db = 10.0 / L * math.log10(pin / pout)
    a_np = math.log(pin / pout) / L
    q = f0 * 1000.0 / df                    # f0 in THz -> GHz
    lam_g = lam / neff
    text = (
        "Propagation loss  \u03b1 = %s dB/cm\n"
        "                  = %s Np/cm\n"
        "Quality factor  Q = f\u2080/\u0394f = %s\n"
        "Guided wavelength  \u03bb = \u03bb\u2080/n_eff = %s nm"
    ) % (g4(a_db), g4(a_np), g4(q), g4(lam_g))

    xs, ys = [], []
    for i in range(-60, 61):
        x = i * 0.05
        xs.append(x)
        ys.append(1.0 - 1.0 / (1.0 + (2.0 * x) ** 2))
    plot = dict(xs=xs, ys=ys, ylog=False, ymin=0.0, ymax=1.0, marker=None,
                xlabel="(f \u2212 f\u2080) / \u0394f",
                ylabel="Transmission T(f)")
    return text, plot


def calc_cross(v):
    c11, c22, c12 = v["C11"], v["C22"], v["C12"]
    if c11 <= 0 or c22 <= 0:
        raise ValueError("C11 and C22 must be positive.")
    det = c11 * c22 - c12 * c12
    if det <= 0:
        raise ValueError("Mutual capacitance is too large for these "
                         "self-capacitances.")
    xi = c12 / math.sqrt(c11 * c22)
    k = E * E / (2 * H)                      # Hz * F
    ec1_0 = k / (c11 * 1e-15) / 1e6          # MHz
    ec2_0 = k / (c22 * 1e-15) / 1e6
    # Maxwell matrix [[C11, -C12], [-C12, C22]] has inverse
    # [[C22, C12], [C12, C11]] / det
    ec1 = k * (c22 / det * 1e15) / 1e6
    ec2 = k * (c11 / det * 1e15) / 1e6
    text = (
        "Crosstalk  \u03be = C\u2081\u2082/\u221a(C\u2081\u2081C\u2082\u2082) = %s  (%s %%)\n"
        "Qubit 1  E_C = %s MHz  (alone: %s, shift %s)\n"
        "Qubit 2  E_C = %s MHz  (alone: %s, shift %s)"
    ) % (g4(xi), g4(xi * 100), g4(ec1), g4(ec1_0), g4(ec1 - ec1_0),
         g4(ec2), g4(ec2_0), g4(ec2 - ec2_0))
    return text, None


def thermal_n(f_hz, t_k):
    x = H * f_hz / (KB * t_k)
    # numerically stable form of 1/(exp(x)-1)
    return x, math.exp(-x) / (-math.expm1(-x))


def calc_thermal(v):
    f, t_mk, t1, tphi = v["f"], v["T"], v["T1"], v["Tphi"]
    if f <= 0 or t_mk <= 0 or t1 <= 0 or tphi <= 0:
        raise ValueError("All values must be positive.")
    x, n = thermal_n(f * 1e9, t_mk * 1e-3)
    t2 = 1.0 / (1.0 / (2.0 * t1) + 1.0 / tphi)
    text = (
        "hf/k\u1d2eT = %s\n"
        "Thermal photons  n\u0304 = %s\n"
        "Coherence  T\u2082 = %s \u00b5s   (T\u2081 = %s, T\u03c6 = %s)"
    ) % (g4(x), g4(n), g4(t2), g4(t1), g4(tphi))

    xs, ys = [], []
    for i in range(0, 96):
        tt = 10.0 + 2.0 * i                   # 10 .. 200 mK
        xs.append(tt)
        ys.append(thermal_n(f * 1e9, tt * 1e-3)[1])
    marker = (t_mk, n) if 10.0 <= t_mk <= 200.0 else None
    plot = dict(xs=xs, ys=ys, ylog=True, marker=marker,
                xlabel="Temperature (mK)",
                ylabel="n\u0304 at %s GHz" % g4(f))
    return text, plot


def calc_transport(v):
    t, vb, nch = v["T"], v["V"], v["N"]
    if not 0.0 <= t <= 1.0:
        raise ValueError("Transmission T must be between 0 and 1.")
    if nch < 1:
        raise ValueError("Number of channels must be at least 1.")
    g = G0 * nch * t
    i = g * vb * 1e-3
    r = "infinite" if g == 0 else eng(1.0 / g, "\u03a9")
    text = (
        "Conductance quantum  G\u2080 = 2e\u00b2/h = %s\n"
        "Conductance  G = G\u2080 N T = %s\n"
        "Resistance  R = %s\n"
        "Current  I = G V = %s"
    ) % (eng(G0, "S"), eng(g, "S"), r, eng(i, "A"))
    return text, None


MODULES = [
    dict(name="Resonator",
         eq="\u03c9 = 1/\u221a(LC)     Z\u2080 = \u221a(L/C)",
         fields=[("L", "Inductance L (nH)", "10"),
                 ("C", "Capacitance C (pF)", "0.07")],
         fn=calc_lc, plot=False),
    dict(name="Qubit",
         eq="f\u2080\u2081 \u2248 \u221a(8 EJ EC) \u2212 EC\n"
            "g \u2248 \u00bd Cg/\u221a(C1 C2) \u00b7 \u221a(f\u2080\u2081 f\u1d63)\n"
            "\u03c7 = g\u00b2/\u0394 \u00b7 \u03b1/(\u0394+\u03b1)",
         fields=[("EJ", "Josephson energy EJ (GHz)", "20"),
                 ("EC", "Charging energy EC (MHz)", "250"),
                 ("fr", "Resonator freq fr (GHz)", "6.5"),
                 ("Cg", "Coupling cap Cg (fF)", "5"),
                 ("C1", "Qubit cap C1 (fF)", "80"),
                 ("C2", "Resonator cap C2 (fF)", "400")],
         fn=calc_qubit, plot=True),
    dict(name="Photonics",
         eq="\u03b1(dB) = (10/L) log\u2081\u2080(Pin/Pout)\n"
            "Q = f\u2080/\u0394f     \u03bb = \u03bb\u2080/n_eff\n"
            "T(f) = 1 \u2212 1/(1 + (2(f\u2212f\u2080)/\u0394f)\u00b2)",
         fields=[("L", "Waveguide length (cm)", "1"),
                 ("Pin", "Input power", "1"),
                 ("Pout", "Output power", "0.5"),
                 ("f0", "Resonance f0 (THz)", "193.4"),
                 ("df", "Linewidth \u0394f (GHz)", "1"),
                 ("neff", "Effective index n_eff", "2.4"),
                 ("lam", "Vacuum wavelength (nm)", "1550")],
         fn=calc_photonic, plot=True),
    dict(name="Crosstalk",
         eq="\u03be = C\u2081\u2082/\u221a(C\u2081\u2081C\u2082\u2082)\n"
            "E_C = e\u00b2/2h \u00b7 (C\u207b\u00b9)\u1d62\u1d62  with C = [[C11, \u2212C12], [\u2212C12, C22]]",
         fields=[("C11", "Self cap C11 (fF)", "80"),
                 ("C22", "Self cap C22 (fF)", "80"),
                 ("C12", "Mutual cap C12 (fF)", "2")],
         fn=calc_cross, plot=False),
    dict(name="Thermal",
         eq="n\u0304 = 1/(e^(hf/k\u1d2eT) \u2212 1)\n"
            "1/T\u2082 = 1/(2T\u2081) + 1/T\u03c6",
         fields=[("f", "Mode frequency (GHz)", "6"),
                 ("T", "Temperature (mK)", "20"),
                 ("T1", "T1 (\u00b5s)", "50"),
                 ("Tphi", "T\u03c6 (\u00b5s)", "100")],
         fn=calc_thermal, plot=True),
    dict(name="Transport",
         eq="G = (2e\u00b2/h) N T(E_F)     I = G V",
         fields=[("T", "Transmission T (0 to 1)", "0.8"),
                 ("N", "Channels N", "1"),
                 ("V", "Bias voltage V (mV)", "10")],
         fn=calc_transport, plot=False),
]


# ----------------------------------------------------------------- plotting
def draw_plot(cv, spec):
    cv.delete("all")
    W = cv.winfo_width()
    if W < 80:
        W = 340
    Ht = int(cv.cget("height"))
    ml, mr, mt, mb = 62, 16, 30, 46
    x0, x1, y0, y1 = ml, W - mr, mt, Ht - mb

    xs, ys = spec["xs"], spec["ys"]
    if len(xs) < 2:
        return
    xmin, xmax = min(xs), max(xs)
    if xmax == xmin:
        xmax = xmin + 1.0

    ylog = spec.get("ylog", False)
    if ylog:
        yt = [math.log10(max(y, 1e-300)) for y in ys]
        lo = math.floor(min(yt))
        hi = math.ceil(max(yt))
        if hi == lo:
            hi = lo + 1
        step = max(1, int((hi - lo) // 5))
        yticks = [(d, "1e%d" % d) for d in range(int(lo), int(hi) + 1, step)]
        tr = lambda y: math.log10(max(y, 1e-300))
    else:
        yt = list(ys)
        lo = spec.get("ymin", min(yt))
        hi = spec.get("ymax", max(yt))
        if hi == lo:
            hi = lo + 1.0
        yticks = [(lo + (hi - lo) * i / 4.0, "%.3g" % (lo + (hi - lo) * i / 4.0))
                  for i in range(5)]
        tr = lambda y: y

    def px(x):
        return x0 + (x - xmin) / (xmax - xmin) * (x1 - x0)

    def py(a):
        return y1 - (a - lo) / (hi - lo) * (y1 - y0)

    # grid and tick labels
    for a, label in yticks:
        yy = py(a)
        cv.create_line(x0, yy, x1, yy, fill=LINE)
        cv.create_text(x0 - 6, yy, text=label, anchor="e", fill=MUTED,
                       font=("TkDefaultFont", 9))
    for i in range(5):
        xv = xmin + (xmax - xmin) * i / 4.0
        xx = px(xv)
        cv.create_line(xx, y0, xx, y1, fill=LINE)
        cv.create_text(xx, y1 + 12, text="%.3g" % xv, fill=MUTED,
                       font=("TkDefaultFont", 9))
    cv.create_rectangle(x0, y0, x1, y1, outline=MUTED)

    # curve
    pts = []
    for x, y in zip(xs, ys):
        pts.extend([px(x), py(tr(y))])
    cv.create_line(*pts, fill=ACC, width=2)

    # marker for the current input
    m = spec.get("marker")
    if m:
        mx, my = px(m[0]), py(tr(m[1]))
        cv.create_oval(mx - 5, my - 5, mx + 5, my + 5, fill=ACC2, outline="")
        cv.create_text(mx, my - 12, text="now", fill=ACC2,
                       font=("TkDefaultFont", 9, "bold"))

    # axis labels
    cv.create_text(x0, 12, text=spec.get("ylabel", ""), anchor="w", fill=INK,
                   font=("TkDefaultFont", 10))
    cv.create_text((x0 + x1) / 2.0, Ht - 12, text=spec.get("xlabel", ""),
                   fill=INK, font=("TkDefaultFont", 10))


# ---------------------------------------------------------------------- app
class App:
    def __init__(self, root):
        self.root = root
        root.title("Quantum Sim Calculator")
        root.configure(bg=BG)

        base = tkfont.nametofont("TkDefaultFont")
        base.configure(size=12)
        self.f_base = base
        self.f_bold = base.copy()
        self.f_bold.configure(size=13, weight="bold")
        self.f_title = base.copy()
        self.f_title.configure(size=17, weight="bold")
        self.f_small = base.copy()
        self.f_small.configure(size=10)

        self.wrap = max(240, min(root.winfo_screenwidth() - 70, 620))
        self.vars = {}
        self.result = None
        self.plot_cv = None
        self.last_plot = None
        self.cur = 0

        self._build_scroll()
        self._build_header()
        self.content = tk.Frame(self.body, bg=BG)
        self.content.pack(fill="x")
        self.show(0)

    # ------------------------------------------------------------ layout
    def _build_scroll(self):
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.vsb = tk.Scrollbar(self.root, orient="vertical",
                                command=self.canvas.yview, width=16)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.body,
                                             anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.win, width=e.width))
        # touch-drag scrolling
        self.root.bind_all("<ButtonPress-1>", self._press, add="+")
        self.root.bind_all("<B1-Motion>", self._drag, add="+")
        self._drag_ok = False
        self._y0 = 0
        self._top = 0.0

    def _press(self, e):
        self._drag_ok = e.widget.winfo_class() not in (
            "Entry", "Button", "Scrollbar")
        self._y0 = e.y_root
        self._top = self.canvas.yview()[0]

    def _drag(self, e):
        if not self._drag_ok:
            return
        h = max(1, self.body.winfo_height())
        first, last = self.canvas.yview()
        span = last - first
        new = self._top + (self._y0 - e.y_root) / float(h)
        new = max(0.0, min(1.0 - span, new))
        self.canvas.yview_moveto(new)

    def _build_header(self):
        head = tk.Frame(self.body, bg=BG)
        head.pack(fill="x", padx=10, pady=(12, 4))
        tk.Label(head, text="Quantum Hardware Calculator", font=self.f_title,
                 bg=BG, fg=INK, anchor="w").pack(fill="x")
        tk.Label(head, text="Tap a module, edit the numbers, tap Calculate.",
                 font=self.f_small, bg=BG, fg=MUTED, anchor="w").pack(fill="x")
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill="x", padx=10, pady=6)
        self.mod_buttons = []
        for i, m in enumerate(MODULES):
            b = tk.Button(grid, text=m["name"], font=self.f_base,
                          relief="flat", bd=0, pady=8,
                          command=lambda i=i: self.show(i))
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=3)
            self.mod_buttons.append(b)
        for c in range(3):
            grid.columnconfigure(c, weight=1, uniform="mods")

    # ------------------------------------------------------------ modules
    def show(self, i):
        self.cur = i
        m = MODULES[i]
        for j, b in enumerate(self.mod_buttons):
            if j == i:
                b.configure(bg=ACC, fg="white", activebackground=ACC,
                            activeforeground="white")
            else:
                b.configure(bg="#e6eaf2", fg=INK, activebackground="#d5dbe8",
                            activeforeground=INK)
        for w in self.content.winfo_children():
            w.destroy()
        self.vars = {}
        self.last_plot = None
        self.plot_cv = None

        card = tk.Frame(self.content, bg=CARD, highlightbackground=LINE,
                        highlightthickness=1)
        card.pack(fill="x", padx=10, pady=6)
        tk.Label(card, text=m["name"], font=self.f_bold, bg=CARD, fg=ACC,
                 anchor="w").pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(card, text=m["eq"], font=self.f_small, bg=CARD, fg=MUTED,
                 anchor="w", justify="left",
                 wraplength=self.wrap).pack(fill="x", padx=12, pady=(2, 8))

        form = tk.Frame(card, bg=CARD)
        form.pack(fill="x", padx=12)
        form.columnconfigure(0, weight=1)
        for r, (key, label, default) in enumerate(m["fields"]):
            tk.Label(form, text=label, font=self.f_base, bg=CARD, fg=INK,
                     anchor="w").grid(row=r, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=default)
            self.vars[key] = var
            ent = tk.Entry(form, textvariable=var, width=10, justify="right",
                           font=self.f_base, relief="solid", bd=1)
            ent.grid(row=r, column=1, sticky="e", padx=(8, 0), pady=4,
                     ipady=4)
            ent.bind("<Return>", lambda e: self.calculate())

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", padx=12, pady=10)
        tk.Button(btns, text="Calculate", font=self.f_bold, bg=ACC,
                  fg="white", activebackground=ACC, activeforeground="white",
                  relief="flat", pady=8,
                  command=self.calculate).pack(side="left", fill="x",
                                               expand=True, padx=(0, 4))
        tk.Button(btns, text="Reset", font=self.f_base, bg="#e6eaf2",
                  fg=INK, relief="flat", pady=8,
                  command=lambda: self.show(self.cur)).pack(
                      side="left", fill="x", expand=True, padx=(4, 0))

        self.result = tk.Label(card, text="", font=self.f_base, bg=CARD,
                               fg=INK, anchor="w", justify="left",
                               wraplength=self.wrap)
        self.result.pack(fill="x", padx=12, pady=(0, 10))

        if m["plot"]:
            self.plot_cv = tk.Canvas(card, height=250, bg="white",
                                     highlightbackground=LINE,
                                     highlightthickness=1)
            self.plot_cv.pack(fill="x", padx=12, pady=(0, 12))
            self.plot_cv.bind("<Configure>", self._replot)

        self.canvas.yview_moveto(0)

    def _replot(self, _event=None):
        if self.plot_cv is not None and self.last_plot:
            draw_plot(self.plot_cv, self.last_plot)

    def calculate(self):
        m = MODULES[self.cur]
        try:
            vals = {k: float(var.get().strip().replace(",", "."))
                    for k, var in self.vars.items()}
        except ValueError:
            self.result.configure(text="Enter numbers only (for example 0.5 "
                                       "or 1e-3).", fg=ERR)
            return
        try:
            text, plot = m["fn"](vals)
        except (ValueError, ZeroDivisionError, OverflowError) as ex:
            self.result.configure(text="Check inputs: %s" % ex, fg=ERR)
            return
        self.result.configure(text=text, fg=INK)
        self.last_plot = plot
        if self.plot_cv is not None:
            self.root.update_idletasks()
            if plot:
                draw_plot(self.plot_cv, plot)
            else:
                self.plot_cv.delete("all")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
