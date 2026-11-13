import math
import cmath

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is not available in this Pydroid 3 install.")
    print("Try updating Pydroid 3, or install the Tkinter add-on from")
    print("Pydroid's Plugins section, then run this file again.")
    raise SystemExit


class BlochApp:
    def __init__(self, root):
        self.root = root
        root.title("Qubit State Explorer")
        root.configure(bg="#fafaf7")

        # ---------- Input controls ----------
        controls = tk.Frame(root, bg="#fafaf7")
        controls.pack(fill="x", padx=10, pady=(10, 0))

        self.theta = tk.Scale(
            controls, from_=0, to=180, orient="horizontal",
            label="θ  (polar angle, degrees)", length=300,
            bg="#fafaf7", highlightthickness=0,
            command=lambda _v: self.update_view())
        self.theta.set(90)
        self.theta.pack(fill="x")

        self.phi = tk.Scale(
            controls, from_=0, to=360, orient="horizontal",
            label="φ  (relative phase, degrees)", length=300,
            bg="#fafaf7", highlightthickness=0,
            command=lambda _v: self.update_view())
        self.phi.set(0)
        self.phi.pack(fill="x")

        self.decoh = tk.Scale(
            controls, from_=0, to=500, orient="horizontal",
            label="decoherence  t/τ  (×0.01)", length=300,
            bg="#fafaf7", highlightthickness=0,
            command=lambda _v: self.update_view())
        self.decoh.set(0)
        self.decoh.pack(fill="x")

        # ---------- Output ----------
        body = tk.Frame(root, bg="#fafaf7")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(body, width=300, height=300,
                                bg="white", highlightthickness=1,
                                highlightbackground="#ccc")
        self.canvas.pack()

        self.bars = tk.Canvas(body, width=300, height=60,
                              bg="white", highlightthickness=1,
                              highlightbackground="#ccc")
        self.bars.pack(pady=(8, 0))

        self.readout = tk.Label(body, text="", justify="left",
                                font=("Courier", 10), bg="#fafaf7",
                                anchor="w")
        self.readout.pack(fill="x", pady=(8, 0))

        self.update_view()

    # ---------- Physics ----------
    def state(self):
        th = math.radians(self.theta.get())
        ph = math.radians(self.phi.get())
        alpha = complex(math.cos(th / 2), 0)
        beta = cmath.exp(1j * ph) * math.sin(th / 2)
        return alpha, beta, th, ph

    def bloch_vector(self, th, ph):
        return (math.sin(th) * math.cos(ph),
                math.sin(th) * math.sin(ph),
                math.cos(th))

    # ---------- Drawing ----------
    def draw_bloch(self, th, ph):
        c = self.canvas
        c.delete("all")
        cx, cy, R = 150, 150, 110

        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline="#999")
        c.create_oval(cx - R, cy - 36, cx + R, cy + 36,
                      outline="#bbb", dash=(4, 4))
        c.create_line(cx, 30, cx, 270, fill="#666")
        c.create_line(40, cy, 260, cy, fill="#ccc")
        c.create_text(160, 24, text="|0⟩", anchor="w")
        c.create_text(160, 280, text="|1⟩", anchor="w")

        x, y, z = self.bloch_vector(th, ph)
        sx = cx + R * (x + 0.35 * y)
        sy = cy - R * (z + 0.35 * y)
        c.create_line(cx, cy, sx, sy, fill="#c0562b", width=3)
        c.create_oval(sx - 7, sy - 7, sx + 7, sy + 7,
                      fill="#c0562b", outline="")

    def draw_bars(self, P0, P1):
        b = self.bars
        b.delete("all")
        width = 240
        b.create_text(10, 15, text="P(0)", anchor="w")
        b.create_rectangle(60, 8, 60 + width, 22, outline="#ccc")
        b.create_rectangle(60, 8, 60 + width * P0, 22,
                           fill="#2f5fb3", outline="")
        b.create_text(10, 45, text="P(1)", anchor="w")
        b.create_rectangle(60, 38, 60 + width, 52, outline="#ccc")
        b.create_rectangle(60, 38, 60 + width * P1, 52,
                           fill="#2f5fb3", outline="")

    def update_view(self):
        alpha, beta, th, ph = self.state()
        P0 = abs(alpha) ** 2
        P1 = abs(beta) ** 2

        # Off-diagonal coherence, damped by decoherence factor e^{-t/τ}
        damp = math.exp(-self.decoh.get() / 100.0)
        rho01 = alpha * beta.conjugate() * damp
        visibility = damp

        self.draw_bloch(th, ph)
        self.draw_bars(P0, P1)

        def fmt_c(z):
            sign = "+" if z.imag >= 0 else "-"
            return f"{z.real:+.3f} {sign} {abs(z.imag):.3f}i"

        text = (
            f"alpha = cos(θ/2)          = {alpha.real:+.3f}\n"
            f"beta  = e^(iφ) sin(θ/2)   = {fmt_c(beta)}\n"
            f"\n"
            f"P(0) = |alpha|^2          = {P0:.3f}\n"
            f"P(1) = |beta|^2           = {P1:.3f}\n"
            f"\n"
            f"rho_01 (coherence)        = {fmt_c(rho01)}\n"
            f"|rho_01|                  = {abs(rho01):.3f}\n"
            f"interference visibility   = {visibility:.3f}"
        )
        self.readout.config(text=text)


if __name__ == "__main__":
    root = tk.Tk()
    BlochApp(root)
    root.mainloop()