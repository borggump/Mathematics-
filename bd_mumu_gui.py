# bd_mumu_gui.py - run in Pydroid 3
import math
import tkinter as tk
from tkinter import messagebox

BG = "#1b1d22"
PANEL = "#2a2d35"
INK = "#ecebe6"
MUTED = "#9a9aa3"
ACCENT = "#6aa8ff"
RED = "#e05a47"
GREEN = "#6cc68f"
GOLD = "#ffd166"
F = ("Helvetica", 12)
FB = ("Helvetica", 14, "bold")
FS = ("Helvetica", 10)   # font for text drawn on canvases
FX = ("Helvetica", 9)

TOPICS = {
    "Overview": (
        "B_d -> mu+ mu- is a very rare decay of the B_d meson into two muons. "
        "The Standard Model predicts a branching fraction of order 1e-10, so about "
        "one decay per 10 billion B_d mesons. LHCb reported first evidence (3.2 sigma)."
    ),
    "B_d meson": (
        "The B_d is a bound state of a bottom antiquark and a down quark, (b-bar d). "
        "Mass about 5.28 GeV/c^2. Lifetime about 1.5 ps (1.5e-12 s)."
    ),
    "Flavour-changing neutral current": (
        "The quark-level process b -> d mu+ mu- changes flavour without changing charge "
        "via a neutral current. Z exchanges cannot change flavour at tree level, so the "
        "leading diagram must be a loop (penguin or box)."
    ),
    "Loop suppression": (
        "The top-quark and W-boson loop contributes a factor of alpha/(4 pi) or g^2/(16 pi^2), "
        "which is a small number. This is one of three suppressions that make the decay rare."
    ),
    "CKM suppression": (
        "The amplitude carries V_tb V_td*. With |V_td| about 8.6e-3, |V_tb V_td*|^2 is "
        "about 7.4e-5."
    ),
    "Helicity suppression": (
        "The B_d is spinless, so the muon pair must be produced with a helicity flip. "
        "The rate is proportional to m_mu^2, giving a factor (m_mu/m_B)^2 of about 4e-4."
    ),
    "Branching fraction": (
        "BR = Gamma(decay) / Gamma(total). Equivalently BR = Gamma(decay) x tau, "
        "since tau = hbar / Gamma_total (natural units)."
    ),
    "Wilson coefficient C10": (
        "C10 is computed from short-distance electroweak physics. New particles in the loop "
        "would change it, so measuring the rate tests for new physics."
    ),
    "Decay constant f_B": (
        "f_B encodes the quark-antiquark overlap inside the meson. It comes from lattice QCD "
        "and is a main source of theory uncertainty."
    ),
    "Sigma (significance)": (
        "Z = (x - mu0) / sigma. A one-sided p-value is 0.5 * erfc(Z / sqrt(2)). "
        "3 sigma is conventionally 'evidence'; 5 sigma (p about 2.9e-7) is 'discovery'."
    ),
    "Measured vs SM ratio": (
        "R = BR_measured / BR_SM. R far from 1 with good precision would signal new physics. "
        "The LHCb result agrees with the Standard Model."
    ),
}


def p_one_sided(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


class App:
    def __init__(self, root):
        self.root = root
        self.current_z = 3.2
        root.title("B_d -> mu mu Explainer")
        root.configure(bg=BG)

        # ---- scrollable container
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.frame = tk.Frame(self.canvas, bg=BG)
        self.win_id = self.canvas.create_window(0, 0, window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.win_id, width=e.width))
        root.bind_all("<ButtonPress-1>", lambda e: setattr(self, "_last_y", e.y))
        root.bind_all("<B1-Motion>", self._drag)
        root.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        root.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))

        f = self.frame
        tk.Label(f, text="Search or pick a topic", fg=INK, bg=BG, font=FB).pack(
            fill="x", pady=(10, 4), padx=12)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_list())
        tk.Entry(f, textvariable=self.search_var, bg=PANEL, fg=INK, insertbackground=INK,
                 font=F).pack(fill="x", padx=12)

        self.listbox = tk.Listbox(f, height=5, bg=PANEL, fg=INK, selectbackground="#1f5fa8",
                                  font=F, activestyle="none", exportselection=False)
        self.listbox.pack(fill="x", padx=12, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        tk.Label(f, text="Explanation", fg=INK, bg=BG, font=FB).pack(
            fill="x", padx=12, anchor="w")
        self.output = tk.Text(f, height=14, wrap="word", bg=PANEL, fg=INK, font=F,
                              relief="flat", padx=8, pady=8)
        self.output.pack(fill="x", padx=12, pady=(2, 10))

        tk.Label(f, text="Penguin-loop diagram", fg=INK, bg=BG, font=FB).pack(
            fill="x", padx=12, anchor="w")
        self.dcanvas = tk.Canvas(f, height=330, bg=PANEL, highlightthickness=0)
        self.dcanvas.pack(fill="x", padx=12, pady=(2, 12))
        self.dcanvas.bind("<Configure>", self.draw_diagram)

        tk.Label(f, text="Significance (Gaussian tail)", fg=INK, bg=BG, font=FB).pack(
            fill="x", padx=12, anchor="w")
        self.gcanvas = tk.Canvas(f, height=330, bg=PANEL, highlightthickness=0)
        self.gcanvas.pack(fill="x", padx=12, pady=(2, 10))
        self.gcanvas.bind("<Configure>", self.draw_gauss)

        row = tk.Frame(f, bg=BG)
        row.pack(fill="x", padx=12, pady=4)
        tk.Label(row, text="Z (sigma):", fg=INK, bg=BG, font=F).pack(side="left")
        self.z_entry = tk.Entry(row, width=7, bg=PANEL, fg=INK, insertbackground=INK, font=F)
        self.z_entry.insert(0, "3.2")
        self.z_entry.pack(side="left", padx=8)
        self.z_entry.bind("<Return>", lambda e: self.compute_p())
        tk.Button(row, text="Compute", command=self.compute_p, bg="#1f5fa8", fg="white",
                  font=F).pack(side="left")

        self.result = tk.Label(f, text="", fg=INK, bg=BG, font=F, justify="left",
                               anchor="w")
        self.result.pack(fill="x", padx=12, pady=(6, 24))

        self.refresh_list()
        self.show("Overview")
        self.compute_p(initial=True)

    # ---- scrolling
    def _drag(self, e):
        last = getattr(self, "_last_y", e.y)
        dy = last - e.y
        self._last_y = e.y
        region = self.canvas.bbox("all")
        total = max(1, region[3] - region[1]) if region else 1
        top, _ = self.canvas.yview()
        self.canvas.yview_moveto(top + dy / total)

    # ---- topics
    def refresh_list(self):
        q = self.search_var.get().strip().lower()
        self.listbox.delete(0, "end")
        self.names = [n for n in TOPICS if q in n.lower() or q in TOPICS[n].lower()]
        for n in self.names:
            self.listbox.insert("end", n)

    def on_select(self, _e):
        sel = self.listbox.curselection()
        if sel:
            self.show(self.names[sel[0]])

    def show(self, name):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", f"{name}\n\n{TOPICS[name]}")
        self.output.config(state="disabled")

    # ---- graphics
    def _size(self, canvas, default_w=360):
        w = canvas.winfo_width()
        return (w if w > 50 else default_w), int(canvas["height"])

    def draw_diagram(self, _e=None):
        c = self.dcanvas
        c.delete("all")
        w, h = self._size(c)
        y = h * 0.52            # height of the quark line
        rx = w * 0.28           # horizontal half-width of loop
        ry = h * 0.15           # vertical half-height of loop
        cx = w / 2
        xl, xr = cx - rx, cx + rx

        # incoming b-bar
        c.create_line(12, y, xl, y, arrow=tk.LAST, width=3, fill=INK)
        c.create_text(12, y - 18, text="b-bar", anchor="w", fill=INK, font=FS)
        # loop (top quark)
        c.create_oval(xl, y - ry, xr, y + ry, outline=ACCENT, width=3)
        c.create_text(cx, y + ry * 0.55, text="top quark", fill=ACCENT, font=FS)
        # outgoing d
        c.create_line(xr, y, w - 12, y, arrow=tk.LAST, width=3, fill=INK)
        c.create_text(w - 12, y - 18, text="d", anchor="e", fill=INK, font=FS)
        # muons leaving the top of the loop
        top = y - ry
        ex, ey = w * 0.12, h * 0.17
        c.create_line(cx, top, cx - ex, top - ey, arrow=tk.LAST, width=2, fill=GREEN)
        c.create_line(cx, top, cx + ex, top - ey, arrow=tk.LAST, width=2, fill=GREEN)
        c.create_text(cx - ex - 6, top - ey - 4, text="mu-", anchor="se", fill=GREEN, font=FS)
        c.create_text(cx + ex + 6, top - ey - 4, text="mu+", anchor="sw", fill=GREEN, font=FS)
        # caption
        c.create_text(cx, h - 12, text="loop + CKM + helicity -> rate ~ 1e-10",
                      fill=MUTED, font=FX)

    def draw_gauss(self, _e=None):
        c = self.gcanvas
        c.delete("all")
        w, h = self._size(c)
        pl, pr, pt, pb = 28, 28, 72, 40   # top band reserved for the readout
        xmin, xmax, ymax = -4.0, 6.0, 0.45
        z = max(xmin, min(self.current_z, xmax))
        X = lambda x: pl + (x - xmin) / (xmax - xmin) * (w - pl - pr)
        Y = lambda y: h - pb - (y / ymax) * (h - pt - pb)
        phi = lambda x: math.exp(-x * x / 2) / math.sqrt(2 * math.pi)

        # readout band (above the plot, so it never overlaps the curve)
        p = p_one_sided(self.current_z)
        c.create_text(pl, 8, anchor="nw", fill=INK, font=FS,
                      text=f"Z = {self.current_z:.2f}")
        c.create_text(pl, 30, anchor="nw", fill=GOLD, font=FS,
                      text=f"one-sided p = {p:.3g}  (1 in {1 / p:,.0f})" if p > 0 else "p ~ 0")

        # shaded tail beyond Z
        pts = [X(z), Y(0)]
        for i in range(101):
            x = z + (xmax - z) * i / 100
            pts += [X(x), Y(phi(x))]
        pts += [X(xmax), Y(0)]
        c.create_polygon(pts, fill=RED, outline="")

        # bell curve
        curve = []
        for i in range(201):
            x = xmin + (xmax - xmin) * i / 200
            curve += [X(x), Y(phi(x))]
        c.create_line(curve, fill=ACCENT, width=3, smooth=True)

        # axis and ticks (every 2 sigma)
        c.create_line(pl, Y(0), w - pr, Y(0), fill=MUTED)
        for t in range(-4, 7, 2):
            c.create_line(X(t), Y(0), X(t), Y(0) + 4, fill=MUTED)
            c.create_text(X(t), h - pb + 14, text=f"{t}s", fill=MUTED, font=FX)

        # 5-sigma discovery line
        c.create_line(X(5), Y(0), X(5), pt, fill=MUTED, dash=(2, 4))
        c.create_text(X(5), pt - 4, text="5s", anchor="s", fill=MUTED, font=FX)

        # current Z marker
        c.create_line(X(z), Y(0), X(z), Y(phi(z)), fill=GOLD, width=2, dash=(4, 3))

    # ---- calculator
    def compute_p(self, initial=False):
        try:
            z = float(self.z_entry.get())
        except ValueError:
            if not initial:
                messagebox.showerror("Input error", "Enter a number, for example 3.2")
            return
        self.current_z = z
        p = p_one_sided(z)
        two = 2 * p
        odds = f"about 1 in {1 / p:,.0f}" if p > 0 else "effectively zero"
        verdict = ("discovery threshold reached" if z >= 5
                   else "evidence level" if z >= 3 else "below evidence level")
        self.result.config(
            text=(f"One-sided p = {p:.3g}  ({odds})\n"
                  f"Two-sided p = {two:.3g}\n{verdict}"),
            wraplength=max(200, self.canvas.winfo_width() - 70))
        self.draw_gauss()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()