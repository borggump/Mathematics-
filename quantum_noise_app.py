# Quantum noise -> logical error explorer
# For Pydroid 3 on Android (also runs on a desktop). Uses only tkinter,
# which ships with Pydroid 3, so there is nothing to pip install.
#
# Layout rule used everywhere to prevent overlap: every piece of text is
# measured after it is drawn, and the next item starts below its bottom
# edge. Nothing is placed at a hard-coded position.

import math
import os
import sys
import tkinter as tk
import tkinter.font as tkfont

ON_ANDROID = hasattr(sys, "getandroidapilevel") or "ANDROID_ROOT" in os.environ

BG = "#f4f4ef"
CARD = "#ffffff"
FG = "#1d1d1b"
MUTED = "#5b5b57"
BLUE = "#2b59c3"
ORANGE = "#c2410c"
GREEN = "#15803d"
PURPLE = "#7e22ce"
RED = "#b91c1c"
LINE = "#cfcfc8"

FIELDS = [
    ("e1", "1-qubit gate error eps1 (%)", "0.1"),
    ("e2", "2-qubit gate error eps2 (%)", "0.5"),
    ("n1", "1-qubit gates per round, N1", "2"),
    ("n2", "2-qubit gates per round, N2", "4"),
    ("pth", "Threshold p_th (%)", "1.0"),
    ("A", "Prefactor A", "0.1"),
    ("d", "Code distance d (odd, 3 or more)", "5"),
]


def sci(v):
    if v == 0:
        return "0"
    if 0.001 <= abs(v) < 1000:
        return "%.4g" % v
    return "%.2e" % v


def pct(v):
    return "%.4g%%" % (v * 100.0)


def compute(vals):
    """All the math. Returns a dict of results."""
    e1 = vals["e1"] / 100.0
    e2 = vals["e2"] / 100.0
    pth = vals["pth"] / 100.0
    A = vals["A"]
    d = int(vals["d"])
    # Average gate error -> Pauli error probability.
    # F_avg = (D*F_pro + 1)/(D + 1), F_pro = 1 - p
    #   D = 2:  eps1 = 2*p1/3   ->  p1 = 3*eps1/2
    #   D = 4:  eps2 = 4*p2/5   ->  p2 = 5*eps2/4
    p1 = 1.5 * e1
    p2 = 1.25 * e2
    p_round = vals["n1"] * p1 + vals["n2"] * p2
    ratio = p2 / pth

    def p_logical(dist, p=p2):
        return min(1.0, A * (p / pth) ** ((dist + 1) / 2.0))

    return {
        "e1": e1, "e2": e2, "pth": pth, "A": A, "d": d,
        "n1": vals["n1"], "n2": vals["n2"],
        "p1": p1, "p2": p2, "p_round": p_round, "ratio": ratio,
        "lam": (pth / p2) if p2 > 0 else float("inf"),
        "pL": p_logical(d), "pL_fn": p_logical,
        "qubits": 2 * d * d - 1,
        "delta": 2.0 * math.acos(math.sqrt(max(0.0, 1.0 - p1))),
    }


class App:
    def __init__(self, root):
        self.root = root
        root.title("Gate noise to logical error")
        root.configure(bg=BG)
        if ON_ANDROID:
            root.geometry("%dx%d+0+0" % (root.winfo_screenwidth(),
                                         root.winfo_screenheight()))
        else:
            root.geometry("480x800")
        self.vars = {k: tk.StringVar(value=dflt) for k, _, dflt in FIELDS}
        self.W = 0
        self._job = None
        self._y0 = 0
        self._f0 = 0.0
        self.canvas = None
        root.bind("<Configure>", self._on_resize)
        root.bind_all("<ButtonPress-1>", self._press)
        root.bind_all("<B1-Motion>", self._drag)
        root.bind_all("<MouseWheel>", self._wheel)
        root.bind_all("<Button-4>", lambda e: self._scroll_units(-3))
        root.bind_all("<Button-5>", lambda e: self._scroll_units(3))
        root.update_idletasks()
        self.build(root.winfo_width())

    # ---------- scrolling by finger drag ----------
    def _press(self, e):
        self._y0 = e.y_root
        if self.canvas:
            self._f0 = self.canvas.yview()[0]

    def _drag(self, e):
        if not self.canvas or isinstance(e.widget, tk.Scrollbar):
            return
        box = self.canvas.bbox("all")
        if not box:
            return
        total = box[3] - box[1]
        if total > 0:
            self.canvas.yview_moveto(self._f0 + (self._y0 - e.y_root) / total)

    def _wheel(self, e):
        self._scroll_units(-1 if e.delta > 0 else 1)

    def _scroll_units(self, n):
        if self.canvas:
            self.canvas.yview_scroll(n, "units")

    # ---------- rebuild on rotation / resize ----------
    def _on_resize(self, e):
        if e.widget is not self.root:
            return
        if abs(e.width - self.W) > 20:
            if self._job:
                self.root.after_cancel(self._job)
            self._job = self.root.after(250, lambda: self.build(self.root.winfo_width()))

    # ---------- page skeleton ----------
    def build(self, width):
        self._job = None
        width = max(width, 240)
        self.W = width
        for child in self.root.winfo_children():
            child.destroy()

        px = max(13, width // 26)          # text size in pixels
        self.px = px
        self.f = tkfont.Font(family="Helvetica", size=-px)
        self.fb = tkfont.Font(family="Helvetica", size=-px, weight="bold")
        self.fh = tkfont.Font(family="Helvetica", size=-int(px * 1.25), weight="bold")
        self.fs = tkfont.Font(family="Helvetica", size=-int(px * 0.85))

        sb_w = max(14, width // 28)
        self.pad = pad = max(8, width // 40)
        self.cw = width - sb_w - 2 * pad   # usable content width

        sb = tk.Scrollbar(self.root, orient="vertical", width=sb_w)
        sb.pack(side="right", fill="y")
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0,
                                yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.config(command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.canvas.create_window(0, 0, window=self.inner, anchor="nw",
                                  width=width - sb_w)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        self.label(self.inner, "From gate noise to logical error", self.fh, FG)
        self.label(self.inner,
                   "Enter gate errors for a quantum processor. The app converts "
                   "them to a Pauli noise model and predicts the logical error "
                   "rate of a surface code, the chain described in the Rigetti / "
                   "Quantum Elements article.", self.f, MUTED)

        # ----- inputs -----
        self.heading(self.inner, "Inputs")
        box = self.card(self.inner)
        for key, text, _ in FIELDS:
            tk.Label(box, text=text, font=self.f, bg=CARD, fg=FG, anchor="w",
                     justify="left", wraplength=self.cw - 2 * pad
                     ).pack(fill="x", padx=pad, pady=(pad // 2, 0))
            ent = tk.Entry(box, textvariable=self.vars[key], font=self.f,
                           relief="solid", bd=1)
            ent.pack(fill="x", padx=pad, pady=(2, pad // 2), ipady=px // 4)
            ent.bind("<Return>", lambda e: self.calculate(True))
        tk.Button(box, text="Calculate", font=self.fb, bg=BLUE, fg="white",
                  activebackground=BLUE, activeforeground="white", relief="flat",
                  command=lambda: self.calculate(True)
                  ).pack(fill="x", padx=pad, pady=pad, ipady=px // 3)
        self.err = tk.Label(box, text="", font=self.f, bg=CARD, fg=RED,
                            anchor="w", justify="left",
                            wraplength=self.cw - 2 * pad)

        self.out = tk.Frame(self.inner, bg=BG)
        self.out.pack(fill="x")
        self.calculate(False)

    # ---------- small widget helpers ----------
    def label(self, parent, text, font, fg, bg=BG):
        w = tk.Label(parent, text=text, font=font, fg=fg, bg=bg, anchor="w",
                     justify="left", wraplength=self.cw)
        w.pack(fill="x", padx=self.pad, pady=(self.pad // 2, 0))
        return w

    def heading(self, parent, text):
        tk.Label(parent, text=text, font=self.fh, fg=FG, bg=BG, anchor="w",
                 justify="left", wraplength=self.cw
                 ).pack(fill="x", padx=self.pad, pady=(self.pad * 2, self.pad // 2))

    def card(self, parent):
        fr = tk.Frame(parent, bg=CARD, highlightbackground=LINE,
                      highlightthickness=1)
        fr.pack(fill="x", padx=self.pad, pady=(0, self.pad // 2))
        return fr

    def new_canvas(self, parent):
        c = tk.Canvas(parent, width=self.cw, height=10, bg=CARD,
                      highlightbackground=LINE, highlightthickness=1)
        c.pack(padx=self.pad, pady=(0, self.pad // 2))
        return c

    def ctext(self, c, x, y, text, font, width, fill=FG, anchor="nw"):
        """Draw wrapped text and return the y coordinate of its bottom edge."""
        item = c.create_text(x, y, text=text, font=font, width=max(40, width),
                             fill=fill, anchor=anchor, justify="left")
        return c.bbox(item)[3]

    # ---------- input handling ----------
    def calculate(self, scroll):
        vals = {}
        problem = ""
        for key, text, _ in FIELDS:
            try:
                vals[key] = float(self.vars[key].get().strip().replace(",", "."))
            except ValueError:
                problem = "'%s' needs a number." % text
                break
        if not problem:
            if vals["e1"] < 0 or vals["e2"] <= 0 or vals["e1"] >= 50 or vals["e2"] >= 50:
                problem = "Gate errors must be above 0 and below 50%."
            elif vals["pth"] <= 0 or vals["A"] <= 0:
                problem = "Threshold and prefactor must be above 0."
            elif vals["n1"] < 0 or vals["n2"] < 0:
                problem = "Gate counts cannot be negative."
            elif vals["d"] != int(vals["d"]) or vals["d"] < 3 or int(vals["d"]) % 2 == 0:
                problem = "Code distance must be an odd whole number, 3 or more."
            elif vals["d"] > 99:
                problem = "Code distance must be 99 or less."
        if problem:
            self.err.config(text=problem)
            self.err.pack(fill="x", padx=self.pad, pady=(0, self.pad))
            return
        self.err.pack_forget()
        r = compute(vals)
        for child in self.out.winfo_children():
            child.destroy()
        self.show_results(r)
        self.draw_pipeline(r)
        self.draw_pauli(r)
        self.draw_plot(r)
        self.show_math()
        if scroll:
            self.root.update_idletasks()
            total = max(1, self.inner.winfo_height())
            self.canvas.yview_moveto(self.out.winfo_y() / total)

    # ---------- results ----------
    def show_results(self, r):
        self.heading(self.out, "Results")
        box = self.card(self.out)
        below = r["ratio"] < 1.0
        rows = [
            ("Pauli error per 1-qubit gate", "p1 = 3/2 x eps1 = " + pct(r["p1"])),
            ("Pauli error per 2-qubit gate", "p2 = 5/4 x eps2 = " + pct(r["p2"])),
            ("Rough error budget per round",
             "N1 x p1 + N2 x p2 = " + pct(r["p_round"])),
            ("Distance from threshold", "p2 / p_th = " + sci(r["ratio"])),
            ("Suppression per +2 in distance", "Lambda = p_th / p2 = " + sci(r["lam"])),
            ("Logical error rate at d = %d" % r["d"], "p_L = " + sci(r["pL"])),
            ("Physical qubits for d = %d" % r["d"], "2 d^2 - 1 = %d" % r["qubits"]),
            ("Coherent rotation with the same 1-qubit infidelity",
             "delta = %.3g deg" % math.degrees(r["delta"])),
        ]
        wrap = self.cw - 2 * self.pad
        for name, value in rows:
            tk.Label(box, text=name, font=self.fs, fg=MUTED, bg=CARD, anchor="w",
                     justify="left", wraplength=wrap
                     ).pack(fill="x", padx=self.pad, pady=(self.pad // 2, 0))
            tk.Label(box, text=value, font=self.fb, fg=FG, bg=CARD, anchor="w",
                     justify="left", wraplength=wrap
                     ).pack(fill="x", padx=self.pad)
        if below:
            msg = ("Below threshold: each step of +2 in distance divides the "
                   "logical error by about %s." % sci(r["lam"]))
            color = GREEN
        else:
            msg = ("At or above threshold: larger codes do not help, and the "
                   "scaling formula is no longer reliable.")
            color = RED
        tk.Label(box, text=msg, font=self.f, fg=color, bg=CARD, anchor="w",
                 justify="left", wraplength=wrap
                 ).pack(fill="x", padx=self.pad, pady=self.pad)

        # table: distance / qubits / logical error
        self.label(self.out, "Logical error by code distance", self.fb, FG)
        tbl = self.card(self.out)
        for col in range(3):
            tbl.columnconfigure(col, weight=1, uniform="t")
        ds = sorted(set([3, 5, 7, 9, 11, r["d"]]))
        cells = [("d", "qubits", "p_L")]
        cells += [(str(d), str(2 * d * d - 1), sci(r["pL_fn"](d))) for d in ds]
        for i, row in enumerate(cells):
            for j, text in enumerate(row):
                mark = i > 0 and ds[i - 1] == r["d"]
                tk.Label(tbl, text=text, bg=CARD,
                         font=self.fb if (i == 0 or mark) else self.f,
                         fg=BLUE if mark else FG
                         ).grid(row=i, column=j, sticky="w",
                                padx=self.pad, pady=self.pad // 3)

    # ---------- diagram 1: pipeline, stacked top to bottom ----------
    def draw_pipeline(self, r):
        self.heading(self.out, "Diagram 1: the pipeline")
        c = self.new_canvas(self.out)
        pad, cw = self.pad, self.cw
        steps = [
            ("1. Processor", "36-qubit and 108-qubit chips. Gates are measured "
                             "on the real hardware.", BLUE),
            ("2. Constellation simulation", "A digital twin solves the device "
                                            "dynamics on a classical computer.", BLUE),
            ("3. Gate error rates", "eps1 = %s,  eps2 = %s" %
             (pct(r["e1"]), pct(r["e2"])), BLUE),
            ("4. Noise model (Pauli channel)", "p1 = %s,  p2 = %s" %
             (pct(r["p1"]), pct(r["p2"])), ORANGE),
            ("5. Error correction simulation", "Surface code, distance %d, "
                                               "%d physical qubits." %
             (r["d"], r["qubits"]), GREEN),
            ("6. Logical error rate", "p_L = %s" % sci(r["pL"]), GREEN),
        ]
        x0, x1 = pad, cw - pad
        inner_w = x1 - x0 - 2 * pad
        gap = int(self.px * 1.6)
        y = pad
        for i, (title, body, color) in enumerate(steps):
            top = y
            y = self.ctext(c, x0 + pad, top + pad, title, self.fb, inner_w)
            y = self.ctext(c, x0 + pad, y + 2, body, self.f, inner_w, MUTED)
            bottom = y + pad
            rect = c.create_rectangle(x0, top, x1, bottom, outline=color, width=2,
                                      fill=CARD)
            c.tag_lower(rect)
            y = bottom
            if i < len(steps) - 1:
                c.create_line(cw // 2, y + 3, cw // 2, y + gap - 3, width=2,
                              fill=MUTED, arrow="last",
                              arrowshape=(gap // 3, gap // 3, gap // 6))
                y += gap
        c.config(height=y + pad)

    # ---------- diagram 2: Pauli weights, one row per bar ----------
    def draw_pauli(self, r):
        self.heading(self.out, "Diagram 2: 1-qubit Pauli weights")
        c = self.new_canvas(self.out)
        pad, cw = self.pad, self.cw
        y = self.ctext(c, pad, pad,
                       "How the 1-qubit error p1 = %s splits between the "
                       "Pauli operators." % pct(r["p1"]), self.f, cw - 2 * pad, MUTED)
        y += pad
        p1 = r["p1"]
        rows = [("I", 1.0 - p1, BLUE), ("X", p1 / 3, ORANGE),
                ("Y", p1 / 3, ORANGE), ("Z", p1 / 3, ORANGE)]
        values = [sci(v) for _, v, _ in rows]
        lab_w = self.fb.measure("W") + pad
        val_w = max(self.f.measure(s) for s in values) + pad
        bar_x0 = pad + lab_w
        bar_x1 = cw - pad - val_w
        bar_w = max(20, bar_x1 - bar_x0)
        row_h = int(self.f.metrics("linespace") * 1.7)
        decades = 6.0
        for (name, v, color), s in zip(rows, values):
            mid = y + row_h // 2
            c.create_text(pad, mid, text=name, font=self.fb, fill=FG, anchor="w")
            frac = 0.0 if v <= 0 else (math.log10(v) + decades) / decades
            length = max(3, int(bar_w * min(1.0, max(0.0, frac))))
            c.create_rectangle(bar_x0, y + row_h * 0.2, bar_x0 + length,
                               y + row_h * 0.8, fill=color, outline="")
            c.create_text(cw - pad, mid, text=s, font=self.f, fill=FG, anchor="e")
            y += row_h
        y = self.ctext(c, pad, y + pad // 2,
                       "Bar length uses a log scale from 1e-6 to 1, so the small "
                       "error terms stay visible. I means no error.",
                       self.fs, cw - 2 * pad, MUTED)
        c.config(height=y + pad)

    # ---------- diagram 3: log-log plot, legend kept outside the plot ----------
    def draw_plot(self, r):
        self.heading(self.out, "Diagram 3: logical vs physical error")
        c = self.new_canvas(self.out)
        pad, cw = self.pad, self.cw
        line_h = self.fs.metrics("linespace")
        y = self.ctext(c, pad, pad,
                       "Up: logical error p_L. Across: physical error p. "
                       "Both axes are log scale.", self.fs, cw - 2 * pad, MUTED)

        pth, A, p_user = r["pth"], r["A"], r["p2"]
        lx0 = math.log10(min(pth / 100.0, p_user / 3.0))
        lx1 = math.log10(max(pth * 3.0, p_user * 3.0))
        ly0, ly1 = -12.0, 0.0

        left = pad + self.fs.measure("1e-12") + 8
        right = cw - pad - self.fs.measure("0.0001%") // 2 - 2
        pw = max(60, right - left)
        ph = int(pw * 0.9)
        top = y + line_h
        bottom = top + ph

        def X(lp):
            return left + (lp - lx0) / (lx1 - lx0) * pw

        def Y(lp):
            return bottom - (lp - ly0) / (ly1 - ly0) * ph

        # y grid and labels (wider step if rows would touch)
        step = 2 if ph / 6.0 >= line_h * 1.3 else 4
        e = int(ly0)
        while e <= ly1:
            yy = Y(e)
            c.create_line(left, yy, right, yy, fill=LINE)
            c.create_text(left - 6, yy, text="1" if e == 0 else "1e%d" % e,
                          font=self.fs, fill=MUTED, anchor="e")
            e += step

        # x grid and labels (a label is skipped if it would touch the last one).
        # They start below the lowest y label, which hangs half a line under
        # the axis.
        x_label_y = bottom + line_h // 2 + 6
        last_right = -1e9
        k = math.floor(lx0)
        while k <= lx1:
            for mult in (1.0, 3.0):
                lp = k + math.log10(mult)
                if lp < lx0 - 1e-9 or lp > lx1 + 1e-9:
                    continue
                xx = X(lp)
                c.create_line(xx, top, xx, bottom, fill=LINE)
                text = "%g%%" % float("%.3g" % (10 ** lp * 100))
                w = self.fs.measure(text)
                if xx - w / 2 > last_right + 8 and xx + w / 2 <= cw - 2:
                    c.create_text(xx, x_label_y, text=text, font=self.fs,
                                  fill=MUTED, anchor="n")
                    last_right = xx + w / 2
            k += 1
        c.create_rectangle(left, top, right, bottom, outline=MUTED)

        # threshold line
        xt = X(math.log10(pth))
        c.create_line(xt, top, xt, bottom, fill=RED, width=2, dash=(6, 4))

        # curves
        palette = {3: MUTED, 5: BLUE, 7: GREEN}
        ds = sorted(set([3, 5, 7, r["d"]]))
        legend = []
        for d in ds:
            color = palette.get(d, PURPLE)
            if d == r["d"] and d not in palette:
                color = PURPLE
            pts = []
            n = 80
            for i in range(n + 1):
                lp = lx0 + (lx1 - lx0) * i / n
                lpl = math.log10(A) + (d + 1) / 2.0 * (lp - math.log10(pth))
                if ly0 <= lpl <= ly1:
                    pts += [X(lp), Y(lpl)]
            if len(pts) >= 4:
                c.create_line(*pts, fill=color, width=3 if d == r["d"] else 2)
            legend.append(("line", color,
                           "d = %d%s" % (d, "  (your code)" if d == r["d"] else "")))

        # the user's operating point
        lpl_user = math.log10(r["pL"]) if r["pL"] > 0 else ly0
        off_scale = lpl_user < ly0
        ux = X(math.log10(p_user))
        uy = Y(max(ly0, min(ly1, lpl_user)))
        rad = max(4, self.px // 4)
        c.create_oval(ux - rad, uy - rad, ux + rad, uy + rad, fill=FG, outline=CARD)

        legend.append(("dash", RED, "Threshold p_th = %s" % pct(pth)))
        point = "Your point: p = %s, p_L = %s" % (pct(p_user), sci(r["pL"]))
        if off_scale:
            point += " (below the chart, drawn on the bottom edge)"
        legend.append(("dot", FG, point))

        # legend rows below the plot: sample on the left, text on the right
        y = x_label_y + line_h + pad
        sample = self.px * 2
        text_x = pad + sample + 8
        for kind, color, text in legend:
            mid = y + self.f.metrics("linespace") // 2
            if kind == "line":
                c.create_line(pad, mid, pad + sample, mid, fill=color, width=3)
            elif kind == "dash":
                c.create_line(pad, mid, pad + sample, mid, fill=color, width=2,
                              dash=(6, 4))
            else:
                c.create_oval(pad + sample // 2 - rad, mid - rad,
                              pad + sample // 2 + rad, mid + rad, fill=color,
                              outline=CARD)
            y = self.ctext(c, text_x, y, text, self.f, cw - text_x - pad) + pad // 2
        c.config(height=y + pad)

    # ---------- formulas ----------
    def show_math(self):
        self.heading(self.out, "The math used")
        box = self.card(self.out)
        wrap = self.cw - 2 * self.pad
        items = [
            ("Gate error", "eps = 1 - F_avg"),
            ("Pauli channel", "E(rho) = sum over k of  p_k P_k rho P_k"),
            ("Fidelity link (D = 2 or 4)", "F_avg = (D F_pro + 1) / (D + 1),  "
                                           "F_pro = 1 - p"),
            ("So", "eps1 = 2 p1 / 3   and   eps2 = 4 p2 / 5"),
            ("Coherent rotation by angle delta", "F_pro = cos^2(delta / 2), "
                                                 "about 1 - delta^2 / 4"),
            ("Surface code scaling", "p_L(d) = A (p / p_th)^((d + 1) / 2)"),
            ("Suppression factor", "Lambda = p_L(d) / p_L(d + 2) = p_th / p"),
        ]
        for name, formula in items:
            tk.Label(box, text=name, font=self.fs, fg=MUTED, bg=CARD, anchor="w",
                     justify="left", wraplength=wrap
                     ).pack(fill="x", padx=self.pad, pady=(self.pad // 2, 0))
            tk.Label(box, text=formula, font=self.fb, fg=FG, bg=CARD, anchor="w",
                     justify="left", wraplength=wrap
                     ).pack(fill="x", padx=self.pad)
        tk.Label(box, text="These are standard textbook models. The app takes p2 "
                           "as the physical error rate p, since 2-qubit gates "
                           "usually dominate. It does not reproduce "
                           "Constellation's own method, which the article does "
                           "not publish.",
                 font=self.fs, fg=MUTED, bg=CARD, anchor="w", justify="left",
                 wraplength=wrap).pack(fill="x", padx=self.pad, pady=self.pad)
        tk.Frame(self.out, bg=BG, height=self.pad * 4).pack(fill="x")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
