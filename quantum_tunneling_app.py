"""
Quantum Tunneling Simulator  -  for Pydroid 3 (Android)
=======================================================
Pure tkinter, no pip installs needed.

Inputs  : sliders for barrier height V0, energy ratio E/V0, barrier width a,
          and particle mass (log scale), plus preset buttons.
Outputs : live wave-function picture, transmission-vs-width graph, and a
          numeric readout (kappa, k, T exact, T thick-barrier, R).

Physics (rectangular barrier, 0 < E < V0):
    k     = sqrt(2 m E) / hbar
    kappa = sqrt(2 m (V0 - E)) / hbar
    T     = 1 / (1 + V0^2 sinh^2(kappa a) / (4 E (V0 - E)))      (exact)
    T    ~= 16 E (V0 - E) / V0^2 * exp(-2 kappa a)               (kappa a >> 1)
"""

import math
import cmath
import tkinter as tk

# ---------------------------------------------------------------- constants
HBAR = 1.054571817e-34      # J s
ME = 9.1093837015e-31       # kg (electron mass)
EV = 1.602176634e-19        # J per eV
LN10 = math.log(10)


# ---------------------------------------------------------------- physics
def wavenumbers(V0_eV, E_eV, m_kg):
    """Return (k, kappa) in 1/nm."""
    k = math.sqrt(2 * m_kg * E_eV * EV) / HBAR * 1e-9
    kappa = math.sqrt(2 * m_kg * (V0_eV - E_eV) * EV) / HBAR * 1e-9
    return k, kappa


def log10_T_exact(V0, E, kappa, a):
    """log10 of the exact transmission coefficient, safe for huge kappa*a."""
    x = kappa * a
    pref = V0 * V0 / (4.0 * E * (V0 - E))
    if x < 300:
        s = math.sinh(x)
        return -math.log10(1.0 + pref * s * s)
    # sinh(x)^2 ~ exp(2x)/4  ->  T ~ (4/pref') exp(-2x) with the "1+" negligible
    return math.log10(1.0 / pref * 4.0) - 2.0 * x / LN10


def log10_T_approx(V0, E, kappa, a):
    return math.log10(16.0 * E * (V0 - E) / (V0 * V0)) - 2.0 * kappa * a / LN10


def fmt_log(logv):
    """Format 10**logv readably even if the exponent is enormous."""
    if logv > -4:
        return "%.4g" % (10 ** logv)
    if abs(logv) < 1e5:
        e = math.floor(logv)
        mant = 10 ** (logv - e)
        return "%.2fe%d" % (mant, e)
    return "10^(%.3g)" % logv


def wave_coeffs(k, kappa, a):
    """Complex amplitudes for incident A=1:  B (reflected), C, D (inside), G
    where G = F*exp(i k a) is the transmitted wave at the barrier's far edge."""
    q = k / kappa - kappa / k
    den = (2 + 1j * q) * math.exp(-kappa * a) + (2 - 1j * q) * math.exp(kappa * a)
    G = 4.0 / den
    C = G * (1 + 1j * k / kappa) / 2 * math.exp(-kappa * a)
    D = G * (1 - 1j * k / kappa) / 2 * math.exp(kappa * a)
    B = C + D - 1
    return B, C, D, G


# ---------------------------------------------------------------- the app
class App:
    BG = "#17171a"
    FG = "#ececea"
    MUTED = "#a4a29b"
    ACCENT = "#7fb3e6"
    WARM = "#f0a070"
    BARRIER = "#4a3d33"
    PANEL = "#211f24"

    def __init__(self, root):
        self.root = root
        root.title("Quantum Tunneling")
        root.configure(bg=self.BG)
        self.mode = "wave"          # "wave" or "graph"

        # ---- variables
        self.V0 = tk.DoubleVar(value=2.0)        # eV
        self.ratio = tk.DoubleVar(value=0.50)    # E / V0
        self.width = tk.DoubleVar(value=1.0)     # nm
        self.mlog = tk.DoubleVar(value=0.0)      # log10(m / m_electron)

        # ---- top button row
        bar = tk.Frame(root, bg=self.BG)
        bar.pack(fill="x", padx=6, pady=(6, 2))
        self._btn(bar, "Wave", lambda: self.set_mode("wave")).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(bar, "T vs width", lambda: self.set_mode("graph")).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(bar, "Theory", self.show_theory).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(bar, "Human?", self.show_human).pack(side="left", expand=True, fill="x", padx=2)

        # ---- canvas
        self.canvas = tk.Canvas(root, bg=self.BG, highlightthickness=0, height=230)
        self.canvas.pack(fill="both", expand=True, padx=6, pady=2)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        # ---- readout
        self.readout = tk.Label(root, text="", justify="left", anchor="w",
                                bg=self.PANEL, fg=self.FG, font=("Courier", 11),
                                padx=8, pady=4)
        self.readout.pack(fill="x", padx=6, pady=2)

        # ---- sliders
        self.vlabels = {}
        self._slider("Barrier height V0 (eV)", self.V0, 0.5, 10.0, 0.1, "V0")
        self._slider("Energy ratio E / V0", self.ratio, 0.05, 0.95, 0.01, "ratio")
        self._slider("Barrier width a (nm)", self.width, 0.05, 3.0, 0.05, "width")
        self._slider("Mass: log10(m / electron)", self.mlog, -1.0, 5.0, 0.05, "mlog")

        # ---- presets
        pr = tk.Frame(root, bg=self.BG)
        pr.pack(fill="x", padx=6, pady=(2, 6))
        self._btn(pr, "Electron", lambda: self.preset(0.0)).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(pr, "Proton", lambda: self.preset(math.log10(1.6726e-27 / ME))).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(pr, "Alpha", lambda: self.preset(math.log10(6.6447e-27 / ME))).pack(side="left", expand=True, fill="x", padx=2)
        self._btn(pr, "Reset", self.reset).pack(side="left", expand=True, fill="x", padx=2)

        for var in (self.V0, self.ratio, self.width, self.mlog):
            var.trace_add("write", lambda *a: self.redraw())
        self.redraw()

    # ------------------------------------------------------------ widgets
    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg="#2d2b33", fg=self.FG,
                         activebackground="#3d3a45", activeforeground=self.FG,
                         relief="flat", font=("Helvetica", 12), pady=6)

    def _slider(self, text, var, lo, hi, step, key):
        row = tk.Frame(self.root, bg=self.BG)
        row.pack(fill="x", padx=6, pady=1)
        lab = tk.Label(row, text=text, bg=self.BG, fg=self.MUTED, font=("Helvetica", 10), anchor="w")
        lab.pack(fill="x")
        s = tk.Scale(row, variable=var, from_=lo, to=hi, resolution=step, orient="horizontal",
                     showvalue=True, bg=self.BG, fg=self.FG, troughcolor="#2d2b33",
                     highlightthickness=0, sliderlength=44, width=26, bd=0,
                     activebackground=self.ACCENT, font=("Helvetica", 10))
        s.pack(fill="x")

    def preset(self, mlog):
        self.mlog.set(round(mlog, 2))

    def reset(self):
        self.V0.set(2.0)
        self.ratio.set(0.50)
        self.width.set(1.0)
        self.mlog.set(0.0)

    def set_mode(self, mode):
        self.mode = mode
        self.redraw()

    # ------------------------------------------------------------ state
    def params(self):
        V0 = self.V0.get()
        E = self.ratio.get() * V0
        a = self.width.get()
        m = ME * 10 ** self.mlog.get()
        k, kappa = wavenumbers(V0, E, m)
        return V0, E, a, m, k, kappa

    # ------------------------------------------------------------ drawing
    def redraw(self):
        try:
            V0, E, a, m, k, kappa = self.params()
        except (tk.TclError, ValueError):
            return
        logT = log10_T_exact(V0, E, kappa, a)
        logTa = log10_T_approx(V0, E, kappa, a)
        T_is_one = logT > -1e-9
        R_txt = "1 - T" if logT < -8 else "%.6f" % (1 - 10 ** logT)
        mass_ratio = m / ME
        self.readout.config(text=(
            "k      = %.4g /nm     kappa = %.4g /nm\n"
            "kappa*a = %.4g\n"
            "T exact  = %s\n"
            "T approx = %s\n"
            "R = %s     mass = %.4g m_e"
            % (k, kappa, kappa * a, fmt_log(logT), fmt_log(logTa), R_txt, mass_ratio)))
        self.canvas.delete("all")
        if self.mode == "wave":
            self.draw_wave(V0, E, a, k, kappa, logT)
        else:
            self.draw_graph(V0, E, a, kappa, logT)

    def draw_wave(self, V0, E, a, k, kappa, logT):
        c = self.canvas
        W = max(c.winfo_width(), 200)
        H = max(c.winfo_height(), 120)
        top, bot = 22, H - 22
        left, right = 10, W - 10

        # barrier on screen: width grows with a
        frac = 0.08 + 0.32 * (a - 0.05) / 2.95
        bw = frac * (right - left)
        bx0 = (left + right) / 2 - bw / 2
        bx1 = bx0 + bw

        # barrier + energy lines
        c.create_rectangle(bx0, top, bx1, bot, fill=self.BARRIER, outline="")
        c.create_line(left, top, right, top, fill=self.WARM, dash=(6, 4))
        yE = bot - (bot - top) * (E / V0)
        c.create_line(left, yE, right, yE, fill=self.ACCENT, dash=(3, 3))
        c.create_line(left, bot, right, bot, fill=self.MUTED)
        c.create_text(left + 2, top - 10, text="V0 = %.2f eV" % V0, fill=self.WARM, anchor="w", font=("Helvetica", 10))
        c.create_text(left + 2, yE - 9, text="E = %.2f eV" % E, fill=self.ACCENT, anchor="w", font=("Helvetica", 10))

        # wave function (real part), drawn around the energy line
        # keep the picture meaningful for extreme kappa*a
        a_d = min(a, 50.0 / kappa)
        B, C, D, G = wave_coeffs(k, kappa, a_d)
        F_amp = abs(G)

        amp_px = min((yE - top), (bot - yE)) * 0.8
        left_len = bx0 - left
        right_len = right - bx1
        # phase rate in rad per pixel, capped so the picture never aliases
        rate = k * a_d / bw
        rate = min(rate, 2 * math.pi * 7 / max(min(left_len, right_len), 1))
        rate = max(rate, 2 * math.pi * 1.5 / max(min(left_len, right_len), 1))
        # inside the barrier x (nm) = (px - bx0)/bw * a_d

        pts = []
        steps = int(right - left)
        for i in range(steps + 1):
            px = left + i
            if px < bx0:
                x = -(bx0 - px) * rate / k      # x <= 0 in 1/k units
                psi = cmath.exp(1j * k * x) + B * cmath.exp(-1j * k * x)
            elif px <= bx1:
                t = (px - bx0) / bw * a_d
                psi = C * math.exp(kappa * t) + D * math.exp(-kappa * t)
            else:
                x = (px - bx1) * rate / k
                psi = G * cmath.exp(1j * k * x)
            y = yE - psi.real * amp_px / 2.0
            pts.extend([px, max(min(y, bot), top)])
        c.create_line(*pts, fill=self.FG, width=2, smooth=False)

        # labels
        c.create_text((bx0 + bx1) / 2, bot - 8, text="barrier", fill=self.MUTED, font=("Helvetica", 9))
        c.create_text(left + 4, bot - 8, text="incident + reflected", fill=self.MUTED, anchor="w", font=("Helvetica", 9))
        c.create_text(right - 4, bot - 8, text="transmitted", fill=self.MUTED, anchor="e", font=("Helvetica", 9))
        if logT < -3:
            c.create_text(right - 4, yE - 24,
                          text="(transmitted amplitude ~ %s: too small to see)" % fmt_log(logT / 2),
                          fill=self.WARM, anchor="e", font=("Helvetica", 9))

    def draw_graph(self, V0, E, a, kappa, logT):
        c = self.canvas
        W = max(c.winfo_width(), 200)
        H = max(c.winfo_height(), 120)
        L, R, T_, B_ = 46, W - 12, 14, H - 28

        a_max = 3.0
        n = 120
        vals = []
        for i in range(n + 1):
            ai = 0.05 + (a_max - 0.05) * i / n
            vals.append((ai, log10_T_exact(V0, E, kappa, ai)))
        floor = max(min(v for _, v in vals), -80.0)
        floor = min(floor, -2.0)

        def X(av):
            return L + (av - 0.05) / (a_max - 0.05) * (R - L)

        def Y(lv):
            lv = max(lv, floor)
            return T_ + (0 - lv) / (0 - floor) * (B_ - T_)

        c.create_rectangle(L, T_, R, B_, outline=self.MUTED)
        # y ticks
        nt = 4
        for j in range(nt + 1):
            lv = floor * j / nt
            y = Y(lv)
            c.create_line(L - 4, y, L, y, fill=self.MUTED)
            c.create_text(L - 6, y, text="1e%d" % round(lv), fill=self.MUTED, anchor="e", font=("Helvetica", 9))
        for av in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
            c.create_line(X(av), B_, X(av), B_ + 4, fill=self.MUTED)
            c.create_text(X(av), B_ + 13, text="%.1f" % av, fill=self.MUTED, font=("Helvetica", 9))
        c.create_text((L + R) / 2, H - 4, text="barrier width a (nm)", fill=self.MUTED, font=("Helvetica", 9))
        c.create_text(L + 6, T_ + 8, text="log10 T", fill=self.MUTED, anchor="w", font=("Helvetica", 9))

        pts = []
        for av, lv in vals:
            pts.extend([X(av), Y(lv)])
        c.create_line(*pts, fill=self.ACCENT, width=2)
        # current point
        px, py = X(a), Y(logT)
        c.create_oval(px - 6, py - 6, px + 6, py + 6, fill=self.WARM, outline="")
        c.create_line(px, py, px, B_, fill=self.WARM, dash=(3, 3))
        if logT < floor:
            c.create_text(R - 4, T_ + 8, text="(current T below plot floor)", fill=self.WARM, anchor="e", font=("Helvetica", 9))

    # ------------------------------------------------------------ popups
    def popup(self, title, body):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=self.BG)
        txt = tk.Text(win, wrap="word", bg=self.PANEL, fg=self.FG, font=("Helvetica", 12),
                      padx=10, pady=10, relief="flat")
        sb = tk.Scrollbar(win, command=txt.yview, width=22)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", body)
        txt.config(state="disabled")
        return win

    def show_theory(self):
        self.popup("Theory", (
            "QUANTUM TUNNELING\n\n"
            "A particle with energy E meets a barrier of height V0 > E. "
            "Classically it is always reflected. Quantum mechanically its wave "
            "function does not stop at the barrier; it decays inside and a small "
            "amplitude emerges on the far side.\n\n"
            "SCHRODINGER EQUATION\n"
            "  -(hbar^2 / 2m) psi'' + V(x) psi = E psi\n\n"
            "THREE REGIONS (barrier 0 <= x <= a)\n"
            "  x < 0      psi = A e^(ikx) + B e^(-ikx)\n"
            "  0 <= x <= a   psi = C e^(kappa x) + D e^(-kappa x)\n"
            "  x > a      psi = F e^(ikx)\n\n"
            "  k     = sqrt(2mE) / hbar\n"
            "  kappa = sqrt(2m(V0 - E)) / hbar\n\n"
            "Matching psi and psi' at x = 0 and x = a gives\n\n"
            "  T = 1 / ( 1 + V0^2 sinh^2(kappa a) / (4 E (V0 - E)) )\n\n"
            "THICK BARRIER (kappa a >> 1)\n"
            "  T ~ 16 E (V0 - E) / V0^2 * exp(-2 kappa a)\n\n"
            "Transmission falls exponentially with barrier width a and with "
            "sqrt(mass). Try the mass slider: raising it by a factor of 10 "
            "multiplies kappa by about 3.\n\n"
            "R = 1 - T (probability is conserved).\n\n"
            "REAL EXAMPLES\n"
            "  - Fusion in the Sun (protons tunnel the Coulomb barrier)\n"
            "  - Alpha decay\n"
            "  - Scanning tunneling microscope (I ~ exp(-2 kappa d))\n"
            "  - Flash memory (Fowler-Nordheim tunneling)\n\n"
            "NOTE: the wave drawing is schematic. T and kappa are exact; the "
            "number of wiggles is capped so the picture stays readable."))

    def show_human(self):
        m = 70.0                     # kg
        dE = 1.0                     # eV
        a = 0.1                      # m
        kappa = math.sqrt(2 * m * dE * EV) / HBAR      # 1/m
        logT = -2 * kappa * a / LN10
        self.popup("Can a human tunnel through a wall?", (
            "Person: m = 70 kg\n"
            "Energy shortfall: 1 eV\n"
            "Wall thickness: 0.1 m\n\n"
            "kappa = sqrt(2 m dE) / hbar = %.3g per metre\n"
            "kappa * a = %.3g\n\n"
            "T ~ exp(-2 kappa a) = 10^(%.3g)\n\n"
            "That is a 1 divided by a number with about %.2g digits. "
            "There are only about 10^80 atoms in the observable universe, "
            "so the probability is zero for every practical purpose."
            % (kappa, kappa * a, logT, abs(logT))))


def main():
    root = tk.Tk()
    # a sensible default size for desktop testing; Pydroid uses full screen
    try:
        root.geometry("420x760")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
