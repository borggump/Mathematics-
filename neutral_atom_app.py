"""
Neutral-Atom Quantum Computing Explorer
For Pydroid 3 (Android). Uses only tkinter + the standard library,
so no pip installs are needed.

Tabs:
  1. Qubit     - Bloch sphere, state amplitudes from theta/phi
  2. Rabi      - Rabi oscillation P_r(t) with Omega and Delta sliders
  3. Blockade  - Rydberg blockade radius R_b = (C6/Omega)^(1/6)
  4. Error     - Surface-code logical error vs distance, qubit overhead
  5. Notes     - Key equations
"""

import math
import cmath
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

BG = "#16171a"
CARD = "#1f2024"
FG = "#e8e8ea"
MUTED = "#9a9aa2"
BLUE = "#63a4e8"
ORANGE = "#ed8936"
GREEN = "#68d391"
GRID = "#33353b"

FONT = ("sans-serif", 11)
FONT_B = ("sans-serif", 12, "bold")
FONT_S = ("sans-serif", 9)


# ---------------------------------------------------------------- helpers
def make_slider(parent, text, lo, hi, step, init, callback, fmt="{:.2f}"):
    """Touch-friendly labelled slider. Returns the DoubleVar."""
    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="x", padx=8, pady=(4, 0))
    var = tk.DoubleVar(value=init)
    label = tk.Label(frame, bg=BG, fg=FG, anchor="w", font=FONT)
    label.pack(fill="x")

    def refresh():
        label.config(text="%s: %s" % (text, fmt.format(var.get())))

    def on_move(_value=None):
        refresh()
        callback()

    scale = tk.Scale(
        frame, from_=lo, to=hi, resolution=step, orient="horizontal",
        variable=var, showvalue=False, command=on_move,
        sliderlength=44, width=28, bg=BG, fg=FG, troughcolor=CARD,
        highlightthickness=0, activebackground=BLUE,
    )
    scale.pack(fill="x")
    refresh()
    return var


def make_readout(parent):
    """Auto-wrapping text label for results."""
    label = tk.Label(parent, bg=BG, fg=GREEN, anchor="w", justify="left",
                     font=("monospace", 10))
    label.pack(fill="x", padx=8, pady=4)
    parent.bind("<Configure>",
                lambda e: label.config(wraplength=max(e.width - 20, 100)),
                add="+")
    return label


def make_canvas(parent, height=260):
    c = tk.Canvas(parent, bg=CARD, height=height, highlightthickness=0)
    c.pack(fill="both", expand=True, padx=8, pady=4)
    return c


def new_tab(nb, title):
    f = tk.Frame(nb, bg=BG)
    nb.add(f, text=title)
    return f


# ---------------------------------------------------------------- app
class App:
    def __init__(self, root):
        self.root = root
        root.title("Neutral-Atom Explorer")
        root.configure(bg=BG)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=CARD, foreground=FG,
                        padding=(10, 8), font=FONT)
        style.map("TNotebook.Tab", background=[("selected", BLUE)],
                  foreground=[("selected", "#000000")])

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        self.build_qubit()
        self.build_rabi()
        self.build_blockade()
        self.build_error()
        self.build_notes()

        for fn in (self.draw_qubit, self.draw_rabi,
                   self.draw_blockade, self.draw_error):
            fn()

    # ============================================================ 1. QUBIT
    def build_qubit(self):
        tab = new_tab(self.nb, "Qubit")
        tk.Label(tab, text="|ψ> = cos(θ/2)|0> + e^{iφ} sin(θ/2)|1>",
                 bg=BG, fg=FG, font=FONT_B).pack(pady=(8, 0))
        self.q_theta = make_slider(tab, "θ (deg)", 0, 180, 1, 60,
                                   self.draw_qubit, "{:.0f}")
        self.q_phi = make_slider(tab, "φ (deg)", 0, 360, 1, 45,
                                 self.draw_qubit, "{:.0f}")
        self.q_out = make_readout(tab)
        self.q_canvas = make_canvas(tab, 280)
        self.q_canvas.bind("<Configure>", lambda e: self.draw_qubit())

    def draw_qubit(self):
        c = self.q_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60 or h < 60:
            return
        th = math.radians(self.q_theta.get())
        ph = math.radians(self.q_phi.get())
        alpha = math.cos(th / 2)
        beta = cmath.exp(1j * ph) * math.sin(th / 2)
        p0, p1 = abs(alpha) ** 2, abs(beta) ** 2
        self.q_out.config(text=(
            "alpha = %.3f\n"
            "beta  = %.3f %+.3fi\n"
            "P(0) = %.3f   P(1) = %.3f\n"
            "|alpha|^2+|beta|^2 = %.3f"
            % (alpha, beta.real, beta.imag, p0, p1, p0 + p1)))

        cx, cy = w / 2, h / 2
        R = min(w, h) / 2 - 28

        def proj(x, y, z):
            return (cx + R * (y - 0.3 * x), cy - R * (z - 0.3 * x))

        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=GRID, width=2)
        c.create_oval(cx - R, cy - R * 0.3, cx + R, cy + R * 0.3,
                      outline=GRID, dash=(4, 4))
        for (ax, label) in (((0, 0, 1), "|0>"), ((0, 0, -1), "|1>"),
                            ((1, 0, 0), "+x"), ((0, 1, 0), "+y")):
            ex, ey = proj(*ax)
            c.create_line(cx, cy, ex, ey, fill=MUTED, dash=(2, 3))
            c.create_text(ex + (0 if ax[2] else 14), ey + (-12 if ax[2] == 1 else
                                                          12 if ax[2] == -1 else 0),
                          text=label, fill=MUTED, font=FONT_S)

        x = math.sin(th) * math.cos(ph)
        y = math.sin(th) * math.sin(ph)
        z = math.cos(th)
        sx, sy = proj(x, y, z)
        c.create_line(cx, cy, sx, sy, fill=BLUE, width=4, arrow="last")
        c.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill=ORANGE, outline="")

    # ============================================================ 2. RABI
    def build_rabi(self):
        tab = new_tab(self.nb, "Rabi")
        tk.Label(tab, text="P_r(t) = Ω²/(Ω²+Δ²) · sin²(√(Ω²+Δ²)·t/2)",
                 bg=BG, fg=FG, font=FONT_B).pack(pady=(8, 0))
        self.r_om = make_slider(tab, "Ω Rabi freq (rad/μs)", 0.5, 6, 0.1, 2.0,
                                self.draw_rabi, "{:.1f}")
        self.r_de = make_slider(tab, "Δ detuning (rad/μs)", 0, 6, 0.1, 0.0,
                                self.draw_rabi, "{:.1f}")
        self.r_out = make_readout(tab)
        self.r_canvas = make_canvas(tab, 260)
        self.r_canvas.bind("<Configure>", lambda e: self.draw_rabi())

    def draw_rabi(self):
        c = self.r_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        om, de = self.r_om.get(), self.r_de.get()
        weff = math.hypot(om, de)
        pmax = om * om / (weff * weff)
        tmax = 4.0
        L, R, T, B = 46, w - 12, 14, h - 30

        for k in range(5):
            y = B - (B - T) * k / 4
            c.create_line(L, y, R, y, fill=GRID)
            c.create_text(L - 6, y, text="%.2f" % (k / 4), fill=MUTED,
                          anchor="e", font=FONT_S)
        for k in range(5):
            x = L + (R - L) * k / 4
            c.create_line(x, T, x, B, fill=GRID)
            c.create_text(x, B + 14, text="%d μs" % k, fill=MUTED,
                          font=FONT_S)
        c.create_rectangle(L, T, R, B, outline=MUTED)

        pts = []
        n = 300
        for i in range(n + 1):
            t = tmax * i / n
            p = pmax * math.sin(weff * t / 2) ** 2
            pts += [L + (R - L) * t / tmax, B - (B - T) * p]
        c.create_line(*pts, fill=BLUE, width=3)

        self.r_out.config(text=(
            "Ω_eff = %.2f rad/μs\n"
            "max P_r = %.3f\n"
            "π-pulse time (Δ=0): %.2f μs\n"
            "full cycle: %.2f μs"
            % (weff, pmax, math.pi / om, 2 * math.pi / weff)))

    # ============================================================ 3. BLOCKADE
    def build_blockade(self):
        tab = new_tab(self.nb, "Blockade")
        tk.Label(tab, text="V(r) = C6 / r⁶     R_b = (C6/Ω)^(1/6)",
                 bg=BG, fg=FG, font=FONT_B).pack(pady=(8, 0))
        self.b_c6 = make_slider(tab, "C6 (GHz·μm⁶)", 100, 2000, 10, 860,
                                self.draw_blockade, "{:.0f}")
        self.b_om = make_slider(tab, "Ω/2π (MHz)", 0.1, 10, 0.1, 1.0,
                                self.draw_blockade, "{:.1f}")
        self.b_r = make_slider(tab, "Atom spacing r (μm)", 2, 20, 0.1, 6.0,
                               self.draw_blockade, "{:.1f}")
        self.b_out = make_readout(tab)
        self.b_canvas = make_canvas(tab, 240)
        self.b_canvas.bind("<Configure>", lambda e: self.draw_blockade())

    def draw_blockade(self):
        c = self.b_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        c6_mhz = self.b_c6.get() * 1000.0   # GHz -> MHz
        om = self.b_om.get()
        r = self.b_r.get()
        rb = (c6_mhz / om) ** (1.0 / 6.0)
        v = c6_mhz / r ** 6
        blocked = r < rb

        extent = max(rb, r) * 1.3          # half-width shown, in μm
        scale = min((w / 2 - 20) / (extent * 1.0), (h / 2 - 15) / rb * 0.95)
        scale = min(scale, (w - 40) / (rb + r + rb * 0.4 + 0.1))
        cy = h / 2
        ax = w / 2 - r * scale / 2
        bx = ax + r * scale

        col = GREEN if blocked else ORANGE
        c.create_oval(ax - rb * scale, cy - rb * scale,
                      ax + rb * scale, cy + rb * scale,
                      outline=col, width=2, dash=(6, 4))
        c.create_line(ax, cy, bx, cy, fill=MUTED)
        for x in (ax, bx):
            c.create_oval(x - 9, cy - 9, x + 9, cy + 9, fill=BLUE, outline="")
        c.create_text(ax, cy - 20, text="atom A", fill=FG, font=FONT_S)
        c.create_text(bx, cy - 20, text="atom B", fill=FG, font=FONT_S)
        c.create_text((ax + bx) / 2, cy + 16, text="r = %.1f μm" % r,
                      fill=MUTED, font=FONT_S)
        c.create_text(10, 10, anchor="nw", fill=col, font=FONT_B,
                      text="BLOCKADE: |rr> forbidden" if blocked
                      else "No blockade: both can excite")

        self.b_out.config(text=(
            "R_b = %.2f μm\n"
            "V(r) = %.3g MHz\n"
            "r < R_b ?  %s\n"
            "Blockaded Rabi freq ≈ √2·Ω = %.2f MHz"
            % (rb, v, "YES (blockade)" if blocked else "NO", math.sqrt(2) * om)))

    # ============================================================ 4. ERROR
    def build_error(self):
        tab = new_tab(self.nb, "Error corr.")
        tk.Label(tab, text="p_L ≈ A·(p/p_th)^((d+1)/2),   A = 0.1",
                 bg=BG, fg=FG, font=FONT_B).pack(pady=(8, 0))
        self.e_p = make_slider(tab, "Physical error p", 0.0005, 0.008,
                               0.0001, 0.003, self.draw_error, "{:.4f}")
        self.e_th = make_slider(tab, "Threshold p_th", 0.005, 0.02, 0.0005,
                                0.01, self.draw_error, "{:.4f}")
        self.e_tgt = make_slider(tab, "Target log10(p_L)", -12, -3, 1, -6,
                                 self.draw_error, "{:.0f}")

        row = tk.Frame(tab, bg=BG)
        row.pack(fill="x", padx=8)
        tk.Label(row, text="Logical qubits:", bg=BG, fg=FG,
                 font=FONT).pack(side="left")
        self.e_n = tk.StringVar(value="100")
        sp = tk.Spinbox(row, from_=1, to=10000, textvariable=self.e_n,
                        width=7, font=FONT, command=self.draw_error)
        sp.pack(side="left", padx=8)
        sp.bind("<KeyRelease>", lambda e: self.draw_error())

        self.e_out = make_readout(tab)
        self.e_canvas = make_canvas(tab, 230)
        self.e_canvas.bind("<Configure>", lambda e: self.draw_error())

    def draw_error(self):
        c = self.e_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        A = 0.1
        p, pth = self.e_p.get(), self.e_th.get()
        tgt = 10.0 ** self.e_tgt.get()
        try:
            n_log = max(1, int(self.e_n.get()))
        except ValueError:
            n_log = 100
        ratio = p / pth

        def pl(d):
            return min(1.0, A * ratio ** ((d + 1) / 2))

        L, R, T, B = 52, w - 12, 12, h - 28
        dmin, dmax = 3, 21
        ymin, ymax = -12, 0

        def X(d):
            return L + (R - L) * (d - dmin) / (dmax - dmin)

        def Y(v):
            lv = max(math.log10(max(v, 1e-300)), ymin)
            return B - (B - T) * (lv - ymin) / (ymax - ymin)

        for e in range(ymin, ymax + 1, 3):
            y = Y(10.0 ** e)
            c.create_line(L, y, R, y, fill=GRID)
            c.create_text(L - 6, y, text="1e%d" % e, anchor="e",
                          fill=MUTED, font=FONT_S)
        for d in range(dmin, dmax + 1, 4):
            c.create_text(X(d), B + 14, text="d=%d" % d, fill=MUTED,
                          font=FONT_S)
        c.create_rectangle(L, T, R, B, outline=MUTED)

        ty = Y(tgt)
        c.create_line(L, ty, R, ty, fill=ORANGE, dash=(6, 4))
        c.create_text(R - 4, ty - 8, text="target", anchor="e",
                      fill=ORANGE, font=FONT_S)

        pts = []
        for d in range(dmin, dmax + 1, 2):
            pts += [X(d), Y(pl(d))]
        c.create_line(*pts, fill=GREEN, width=3)
        for i in range(0, len(pts), 2):
            c.create_oval(pts[i] - 3, pts[i + 1] - 3,
                          pts[i] + 3, pts[i + 1] + 3, fill=GREEN, outline="")

        if ratio >= 1:
            msg = ("p/p_th = %.2f  (>= 1)\n"
                   "ABOVE THRESHOLD: larger d does NOT help." % ratio)
        else:
            d_need = None
            for d in range(3, 201, 2):
                if pl(d) <= tgt:
                    d_need = d
                    break
            if d_need is None:
                msg = "p/p_th = %.2f\nNeeds d > 200 for this target." % ratio
            else:
                per = 2 * d_need * d_need - 1
                msg = ("p/p_th = %.2f\n"
                       "distance needed: d = %d\n"
                       "physical per logical: %d\n"
                       "total for %d logical: %s"
                       % (ratio, d_need, per, n_log, format(per * n_log, ",")))
        self.e_out.config(text=msg)

    # ============================================================ 5. NOTES
    def build_notes(self):
        tab = new_tab(self.nb, "Notes")
        box = ScrolledText(tab, bg=CARD, fg=FG, font=("monospace", 10),
                           wrap="word", borderwidth=0, highlightthickness=0)
        box.pack(fill="both", expand=True, padx=8, pady=8)
        box.insert("1.0", NOTES)
        box.config(state="disabled")


NOTES = """KEY EQUATIONS

QUBIT
  |psi> = alpha|0> + beta|1>,  |alpha|^2 + |beta|^2 = 1
  Bloch form: cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>
  Bell state: (|00> + |11>)/sqrt(2)

RABI DRIVING (atom <-> Rydberg state)
  H = (Omega/2)(|g><r| + |r><g|) - Delta |r><r|
  P_r(t) = Omega^2/(Omega^2+Delta^2) *
           sin^2( sqrt(Omega^2+Delta^2) * t / 2 )
  pi-pulse: Omega * t = pi  (Delta = 0)

RYDBERG BLOCKADE
  V(r) = C6 / r^6
  R_b = (C6 / Omega)^(1/6)
  Inside R_b, |rr> is shifted off resonance, so only
  (|gr> + |rg>)/sqrt(2) is reachable, with Rabi frequency
  sqrt(2) * Omega.

CZ GATE
  CZ |a>|b> = (-1)^(ab) |a>|b>
  Only |11> picks up a -1 phase.

SIMULATION MODELS
  Ising:  H = -J sum sz_i sz_j - h sum sx_i
  t-J:    H = -t sum P(c+_i c_j + h.c.)P
              + J sum (S_i . S_j - n_i n_j / 4)

ERROR CORRECTION
  Repetition code (3 bits): p_L ~ 3p^2 - 2p^3
  Surface code distance d:
    physical qubits per logical ~ 2d^2 - 1
    p_L ~ A (p/p_th)^((d+1)/2),  p_th ~ 1%, A ~ 0.1
  Below threshold: raising d suppresses errors exponentially.
  Above threshold: adding qubits makes things worse.

CAVEAT
  The Tuoyuan report (via QbitAI) gives no hardware
  benchmarks, error-correction specs, or timeline. These
  numbers are generic physics and illustrative overheads,
  not measurements of any company's system.
"""


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
