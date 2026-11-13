"""
Quantum Zeno Effect explorer for Pydroid 3 (Android).

Uses only tkinter (built into Pydroid 3) and math, so nothing needs to be
installed with pip. Everything is drawn on a tkinter Canvas.

Model: two-level system, H = (hbar*Omega/2) sigma_x, start in |0>.
  No measurement : P(T)   = cos^2(Omega*T/2)
  N measurements : P_N(T) = [cos^2(Omega*T/(2N))]^N  ~  exp(-Omega^2 T^2 / 4N)
Time is measured in units of 1/Omega, so Omega = 1 and the Zeno time is 2.
"""
import math
import tkinter as tk
from tkinter import messagebox

NMAX = 200
X_MIN, X_MAX = 0.5, 6.0   # range for Omega*T

BG = "#fbfaf7"
FG = "#1d1d1f"
GRID = "#d9d6cf"
BLUE = "#2563eb"
RED = "#dc2626"
GREEN = "#059669"


def p_none(x):
    """Survival probability with no measurement; x = Omega*T."""
    return math.cos(x / 2.0) ** 2


def p_exact(x, n):
    """Exact survival probability with n evenly spaced measurements."""
    return (math.cos(x / (2.0 * n)) ** 2) ** n


def p_approx(x, n):
    """Exponential approximation exp(-x^2 / 4n)."""
    return math.exp(-(x * x) / (4.0 * n))


class ZenoApp:
    def __init__(self, root):
        self.root = root
        root.title("Quantum Zeno Effect")
        root.configure(bg=BG)

        self.view = tk.StringVar(value="N")
        self.x_var = tk.DoubleVar(value=3.0)
        self.n_var = tk.IntVar(value=5)
        self.x_text = tk.StringVar(value="3.00")
        self.n_text = tk.StringVar(value="5")

        big = ("Helvetica", 14)
        bold = ("Helvetica", 14, "bold")

        tk.Label(root, text="Quantum Zeno Effect", font=("Helvetica", 18, "bold"),
                 bg=BG, fg=FG).pack(pady=(8, 0))
        tk.Label(root, text="Two-level system, start in |0>", font=("Helvetica", 11),
                 bg=BG, fg="#6b6b70").pack()

        # ---- input: sliders + typed entries ----
        inp = tk.Frame(root, bg=BG)
        inp.pack(fill="x", padx=10, pady=6)
        inp.columnconfigure(1, weight=1)

        tk.Label(inp, text="Ω·T", font=bold, bg=BG, fg=FG).grid(row=0, column=0, sticky="w")
        tk.Scale(inp, from_=X_MIN, to=X_MAX, resolution=0.05, orient="horizontal",
                 variable=self.x_var, command=self.on_slider, showvalue=False,
                 sliderlength=40, width=26, bg=BG, highlightthickness=0
                 ).grid(row=0, column=1, sticky="ew", padx=6)
        tk.Entry(inp, textvariable=self.x_text, width=6, font=big, justify="center"
                 ).grid(row=0, column=2)

        tk.Label(inp, text="N", font=bold, bg=BG, fg=FG).grid(row=1, column=0, sticky="w")
        tk.Scale(inp, from_=1, to=NMAX, resolution=1, orient="horizontal",
                 variable=self.n_var, command=self.on_slider, showvalue=False,
                 sliderlength=40, width=26, bg=BG, highlightthickness=0
                 ).grid(row=1, column=1, sticky="ew", padx=6)
        tk.Entry(inp, textvariable=self.n_text, width=6, font=big, justify="center"
                 ).grid(row=1, column=2)

        btns = tk.Frame(root, bg=BG)
        btns.pack(fill="x", padx=10)
        tk.Button(btns, text="Apply typed values", font=big, command=self.apply_entries
                  ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Button(btns, text="Reset", font=big, command=self.reset
                  ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # ---- view selector ----
        sel = tk.Frame(root, bg=BG)
        sel.pack(fill="x", padx=10, pady=(6, 0))
        tk.Radiobutton(sel, text="P vs N", variable=self.view, value="N", font=big,
                       bg=BG, command=self.redraw, indicatoron=False
                       ).pack(side="left", expand=True, fill="x", padx=(0, 4))
        tk.Radiobutton(sel, text="P vs time", variable=self.view, value="t", font=big,
                       bg=BG, command=self.redraw, indicatoron=False
                       ).pack(side="left", expand=True, fill="x", padx=(4, 0))

        # ---- output: canvas + text ----
        self.canvas = tk.Canvas(root, bg="white", highlightthickness=1,
                                highlightbackground=GRID, height=260)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=6)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        self.out = tk.Label(root, text="", justify="left", anchor="w",
                            font=("Courier", 12), bg=BG, fg=FG)
        self.out.pack(fill="x", padx=10, pady=(0, 8))

        self.redraw()

    # ---------- input handling ----------
    def on_slider(self, _=None):
        self.x_text.set("%.2f" % self.x_var.get())
        self.n_text.set(str(self.n_var.get()))
        self.redraw()

    def apply_entries(self):
        try:
            x = float(self.x_text.get())
            n = int(float(self.n_text.get()))
        except ValueError:
            messagebox.showerror("Invalid input", "Enter numbers for Ω·T and N.")
            return
        if not (0 < x <= 50) or not (1 <= n <= 100000):
            messagebox.showerror("Out of range",
                                 "Use 0 < Ω·T <= 50 and 1 <= N <= 100000.")
            return
        # sliders clamp to their own range; the typed value is used for results
        self.x_var.set(x)
        self.n_var.set(n)
        self.x_text.set("%.2f" % x)
        self.n_text.set(str(n))
        self.redraw()

    def reset(self):
        self.x_var.set(3.0)
        self.n_var.set(5)
        self.on_slider()

    def current(self):
        """Return (x, n), preferring the typed values if they are valid."""
        try:
            x = float(self.x_text.get())
            n = int(float(self.n_text.get()))
            if 0 < x <= 50 and n >= 1:
                return x, n
        except ValueError:
            pass
        return self.x_var.get(), self.n_var.get()

    # ---------- drawing helpers ----------
    def frame(self, w, h, xmin, xmax, xlabel, xticks):
        """Draw axes and return (X, Y) mapping functions."""
        c = self.canvas
        L, R, T, B = 48, 12, 14, 40
        pw, ph = w - L - R, h - T - B

        def X(v):
            return L + (v - xmin) / (xmax - xmin) * pw

        def Y(p):
            return T + (1 - p) * ph

        for p in (0, 0.25, 0.5, 0.75, 1.0):
            c.create_line(L, Y(p), w - R, Y(p), fill=GRID, dash=(2, 4))
            c.create_text(L - 6, Y(p), text="%.2f" % p, anchor="e", font=("Helvetica", 10))
        for t in xticks:
            c.create_text(X(t), h - B + 12, text=("%g" % t), font=("Helvetica", 10))
        c.create_line(L, T, L, h - B, fill="#6b6b70")
        c.create_line(L, h - B, w - R, h - B, fill="#6b6b70")
        c.create_text((L + w - R) / 2, h - 10, text=xlabel, font=("Helvetica", 11))
        c.create_text(12, (T + h - B) / 2, text="P", font=("Helvetica", 11, "bold"))
        return X, Y

    def redraw(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        x, n = self.current()
        if self.view.get() == "N":
            self.draw_vs_n(w, h, x, n)
        else:
            self.draw_vs_time(w, h, x, n)
        self.write_output(x, n)

    def draw_vs_n(self, w, h, x, n):
        c = self.canvas
        X, Y = self.frame(w, h, 1, NMAX, "Number of measurements N",
                          [1, 50, 100, 150, 200])
        # no-measurement baseline
        p0 = p_none(x)
        c.create_line(X(1), Y(p0), X(NMAX), Y(p0), fill=RED, width=2)
        # exponential approximation (dashed)
        pts = []
        for k in range(1, NMAX + 1):
            pts += [X(k), Y(p_approx(x, k))]
        c.create_line(*pts, fill=GREEN, width=2, dash=(6, 4))
        # exact values (dots)
        for k in range(1, NMAX + 1):
            if k <= 20 or k % 5 == 0:
                px, py = X(k), Y(p_exact(x, k))
                c.create_oval(px - 2.5, py - 2.5, px + 2.5, py + 2.5, fill=BLUE, outline=BLUE)
        # selected N
        nn = min(n, NMAX)
        c.create_line(X(nn), Y(0), X(nn), Y(1), fill="#6b6b70", dash=(3, 3))
        px, py = X(nn), Y(p_exact(x, n))
        c.create_oval(px - 6, py - 6, px + 6, py + 6, outline=BLUE, width=2)
        self.legend(w, [(RED, "no measurement"), (BLUE, "exact"), (GREEN, "approx")])

    def draw_vs_time(self, w, h, x, n):
        c = self.canvas
        X, Y = self.frame(w, h, 0, x, "Time  Ω·t  (reset at each measurement)",
                          [round(x * i / 4, 2) for i in range(5)])
        # free evolution
        pts = []
        for i in range(201):
            t = x * i / 200
            pts += [X(t), Y(p_none(t))]
        c.create_line(*pts, fill=RED, width=2)
        # repeated measurements: sawtooth, resets to 1 after each measurement
        tau = x / n
        steps = 12 if n <= 40 else 3
        pts = []
        for k in range(n):
            for s in range(steps + 1):
                t = tau * s / steps
                pts += [X(k * tau + t), Y(p_none(t))]
            pts += [X((k + 1) * tau), Y(1.0)]  # collapse back to |0>
        c.create_line(*pts, fill=BLUE, width=2)
        self.legend(w, [(RED, "no measurement"), (BLUE, "with N measurements")])

    def legend(self, w, items):
        c = self.canvas
        xpos = 56
        for color, label in items:
            c.create_line(xpos, 24, xpos + 18, 24, fill=color, width=3)
            tid = c.create_text(xpos + 22, 24, text=label, anchor="w", font=("Helvetica", 10))
            xpos = c.bbox(tid)[2] + 14

    def write_output(self, x, n):
        p0 = p_none(x)
        pe = p_exact(x, n)
        pa = p_approx(x, n)
        tau = x / n
        tau_z = 2.0              # in units of 1/Omega
        gamma = tau / tau_z ** 2  # effective decay rate / Omega
        regime = "Zeno regime (tau << tau_Z)" if tau < 0.3 * tau_z else \
                 "too few measurements for Zeno"
        self.out.config(text=(
            "No measurement  P = %.4f\n"
            "Exact P_N       = %.4f\n"
            "Approx P_N      = %.4f\n"
            "tau = T/N = %.4f   tau_Z = %.1f\n"
            "Gamma_eff ~ %.4f  (units of Omega)\n"
            "%s" % (p0, pe, pa, tau, tau_z, gamma, regime)))


def main():
    root = tk.Tk()
    ZenoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
