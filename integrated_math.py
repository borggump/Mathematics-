"""
Integrated Math Explorer — Pydroid3 / Android
Run with: python integrated_math.py
Requires: tkinter (built-in to Pydroid3)
"""

import tkinter as tk
from tkinter import ttk
import math

# ── Palette ────────────────────────────────────────────────────
BG      = "#0e0f1a"
SURFACE = "#161724"
BORDER  = "#252640"
ALG     = "#4f8ef7"   # blue  – algebra
GEO     = "#f7a24f"   # amber – geometry
TRIG    = "#a24ff7"   # violet– trigonometry
STAT    = "#4ff7a2"   # green – statistics
TEXT    = "#e8e9f4"
MUTED   = "#7b7d9e"
WHITE   = "#ffffff"

# ── Fonts (Pydroid3-safe) ──────────────────────────────────────
F_TITLE  = ("sans-serif", 15, "bold")
F_HEAD   = ("sans-serif", 12, "bold")
F_BODY   = ("sans-serif", 10)
F_MONO   = ("monospace", 10)
F_MONO_S = ("monospace",  9)
F_BIG    = ("sans-serif", 22, "bold")

# ══════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Integrated Math Explorer")
        self.configure(bg=BG)
        # Full-screen-ish for a phone (~360×640 logical)
        self.geometry("380x680")
        self.resizable(True, True)

        # Tab bar
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook",            background=BG,      borderwidth=0)
        style.configure("TNotebook.Tab",        background=SURFACE, foreground=MUTED,
                        padding=[8, 6],         font=("sans-serif", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", WHITE)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("Pathways",  PathwaysTab),
            ("Algebra",   AlgebraTab),
            ("Geometry",  GeometryTab),
            ("Trig",      TrigTab),
            ("Compare",   CompareTab),
        ]
        for name, cls in tabs:
            frame = cls(nb)
            nb.add(frame, text=name)


# ── Shared scrollable frame ────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, **kw)
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=self.inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=canvas.winfo_width())
        self.inner.bind("<Configure>", _resize)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        # Touch scroll
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll( 1, "units"))


def section_label(parent, text, color=MUTED):
    tk.Label(parent, text=text, bg=BG, fg=color,
             font=("monospace", 8), anchor="w").pack(fill="x", padx=16, pady=(16, 2))

def heading(parent, text):
    tk.Label(parent, text=text, bg=BG, fg=WHITE,
             font=F_HEAD, anchor="w", wraplength=340).pack(fill="x", padx=16, pady=(0, 8))

def body(parent, text, color=MUTED):
    tk.Label(parent, text=text, bg=BG, fg=color,
             font=F_BODY, anchor="w", justify="left",
             wraplength=340).pack(fill="x", padx=16, pady=(0, 8))

def card(parent, bg=SURFACE):
    f = tk.Frame(parent, bg=bg, bd=0, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER)
    f.pack(fill="x", padx=12, pady=6)
    return f

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12, pady=8)


# ══════════════════════════════════════════════════════════════
# TAB 1 — PATHWAYS
# ══════════════════════════════════════════════════════════════
class PathwaysTab(ScrollFrame):
    def __init__(self, parent):
        super().__init__(parent)
        p = self.inner

        section_label(p, "PART 1 · STRUCTURE")
        heading(p, "Two Pathways Through High School Math")
        body(p, "Tap a year block to learn what's taught and why it matters.")

        # Traditional
        tk.Label(p, text="Traditional AGA Sequence", bg=BG, fg=MUTED,
                 font=("sans-serif", 9, "bold")).pack(anchor="w", padx=16, pady=(8,2))
        traditional = [
            ("9th",  "Algebra I",          ALG,  alg_detail),
            ("10th", "Geometry",            GEO,  geo_detail),
            ("11th", "Algebra II",          ALG,  alg2_detail),
            ("12th", "Pre-Calc / Calculus", TRIG, calc_detail),
        ]
        for yr, name, color, detail_fn in traditional:
            self._year_block(p, yr, name, color, detail_fn)

        divider(p)

        # Integrated
        tk.Label(p, text="Integrated Math Sequence", bg=BG, fg=MUTED,
                 font=("sans-serif", 9, "bold")).pack(anchor="w", padx=16, pady=(4,2))
        integrated = [
            ("9th",  "Integrated Math I",  [ALG, GEO, TRIG],  int1_detail),
            ("10th", "Integrated Math II", [ALG, GEO, TRIG],  int2_detail),
        ]
        for yr, name, colors, detail_fn in integrated:
            self._blend_block(p, yr, name, colors, detail_fn)

        tk.Label(p, text="──  foundational math complete  ──",
                 bg=BG, fg=MUTED, font=("monospace", 8)).pack(pady=4)

        self._year_block(p, "11th", "Statistics / Data Science", STAT, stat_detail)
        self._year_block(p, "12th", "Calculus  OR  AP Stats",    TRIG, calc_detail)

        divider(p)
        body(p, "Key insight: in the traditional path, a 10th grader spends an entire year "
                "in geometry with NO algebraic practice — yet state math tests at 10th grade "
                "test algebra heavily. Integrated math fixes this gap.", MUTED)

    def _year_block(self, parent, yr, name, color, detail_fn):
        f = tk.Frame(parent, bg=SURFACE,
                     highlightthickness=1, highlightbackground=color)
        f.pack(fill="x", padx=12, pady=3)
        tk.Label(f, text=yr, bg=SURFACE, fg=MUTED,
                 font=("monospace", 8), width=4, anchor="w").pack(side="left", padx=(10,4), pady=8)
        tk.Label(f, text=name, bg=SURFACE, fg=color,
                 font=("sans-serif", 10, "bold"), anchor="w").pack(side="left", padx=4, pady=8)
        btn = tk.Button(f, text="▸", bg=SURFACE, fg=color, font=("sans-serif", 10),
                        bd=0, activebackground=SURFACE, cursor="hand2",
                        command=lambda d=detail_fn: DetailWindow(self, d()))
        btn.pack(side="right", padx=10)

    def _blend_block(self, parent, yr, name, colors, detail_fn):
        f = tk.Frame(parent, bg=SURFACE,
                     highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="x", padx=12, pady=3)
        # colour stripe
        stripe = tk.Frame(f, bg=SURFACE)
        stripe.pack(side="left", fill="y", padx=0)
        for c in colors:
            tk.Frame(stripe, bg=c, width=4).pack(side="left", fill="y")

        tk.Label(f, text=yr, bg=SURFACE, fg=MUTED,
                 font=("monospace", 8), width=4, anchor="w").pack(side="left", padx=(6,4), pady=8)
        tk.Label(f, text=name, bg=SURFACE, fg=WHITE,
                 font=("sans-serif", 10, "bold"), anchor="w").pack(side="left", padx=4, pady=8)
        # dots
        dot_frame = tk.Frame(f, bg=SURFACE)
        dot_frame.pack(side="right", padx=6)
        for c in colors:
            tk.Frame(dot_frame, bg=c, width=8, height=8,
                     bd=0).pack(side="left", padx=2, pady=10)
        btn = tk.Button(f, text="▸", bg=SURFACE, fg=WHITE, font=("sans-serif", 10),
                        bd=0, activebackground=SURFACE, cursor="hand2",
                        command=lambda d=detail_fn: DetailWindow(self, d()))
        btn.pack(side="right", padx=4)


# ── Detail pop-up ──────────────────────────────────────────────
class DetailWindow(tk.Toplevel):
    def __init__(self, parent, info):
        super().__init__(parent)
        self.title(info["title"])
        self.configure(bg=BG)
        self.geometry("360x420")
        color = info.get("color", WHITE)
        tk.Label(self, text=info["title"], bg=BG, fg=color,
                 font=F_HEAD, wraplength=320).pack(padx=16, pady=(16,4), anchor="w")
        tk.Label(self, text=info["body"], bg=BG, fg=TEXT,
                 font=F_BODY, wraplength=320, justify="left").pack(padx=16, pady=4, anchor="w")
        if "math" in info:
            tk.Label(self, text=info["math"], bg=SURFACE, fg=WHITE,
                     font=F_MONO, wraplength=320, justify="left").pack(
                         padx=16, pady=8, fill="x", anchor="w")
        tk.Button(self, text="Close", bg=SURFACE, fg=MUTED,
                  font=F_BODY, bd=0, command=self.destroy).pack(pady=12)


# ── Detail data functions ──────────────────────────────────────
def alg_detail():
    return {"title": "Algebra I", "color": ALG,
            "body": "Students learn to manipulate variables, solve linear and quadratic equations, "
                    "graph lines, and work with inequalities. Foundation for almost all later math.",
            "math": "Solve:  2x + 3 = 11\n  → 2x = 8\n  → x = 4\n\nSlope: m = (y₂−y₁)/(x₂−x₁)"}

def geo_detail():
    return {"title": "Geometry", "color": GEO,
            "body": "Proofs, angles, triangles, circles, area, volume, and coordinate geometry. "
                    "In AGA, students spend a FULL YEAR here with no algebra — causing the '10th-grade gap'.",
            "math": "Pythagorean theorem:\n  a² + b² = c²\n\nArea of circle:\n  A = πr²\n\nSum of angles in triangle = 180°"}

def alg2_detail():
    return {"title": "Algebra II", "color": ALG,
            "body": "Returns to algebra with more depth: polynomial functions, rational expressions, "
                    "exponential/logarithmic functions, complex numbers, and sequences.",
            "math": "Quadratic formula:\n  x = (−b ± √(b²−4ac)) / 2a\n\nLog rule:\n  log(ab) = log a + log b"}

def calc_detail():
    return {"title": "Pre-Calc / Calculus", "color": TRIG,
            "body": "Limits, derivatives, and integrals. Essential for physics, engineering, "
                    "economics. In integrated math, students reach this same place by 12th grade.",
            "math": "Derivative (slope of curve):\n  f'(x) = lim[h→0] (f(x+h)−f(x))/h\n\nIntegral (area under curve):\n  ∫f(x)dx"}

def int1_detail():
    return {"title": "Integrated Math I (9th)", "color": WHITE,
            "body": "Blends linear algebra (equations, graphs), basic geometry (angles, triangles), "
                    "and intro trig (sin/cos as ratios). Students practice all three in the same year.",
            "math": "Algebra:    y = mx + b\nGeometry:   a² + b² = c²\nTrig:       sin θ = opp/hyp"}

def int2_detail():
    return {"title": "Integrated Math II (10th)", "color": WHITE,
            "body": "Deeper quadratics and polynomials, circle geometry, transformations, "
                    "and trigonometric functions on the unit circle. Foundational math is COMPLETE by end of this year.",
            "math": "Quadratic:  y = ax² + bx + c\nUnit circle: x² + y² = 1\nTrig:       (cos θ, sin θ)"}

def stat_detail():
    return {"title": "Statistics / Data Science (11th)", "color": STAT,
            "body": "Mean, median, standard deviation, probability, regression, and data visualisation. "
                    "Relevant for business, social science, nursing, and everyday life.",
            "math": "Mean:    x̄ = Σxᵢ / n\nStd dev: σ = √(Σ(xᵢ−x̄)²/n)\nCorrelation: r = Σ(xᵢ−x̄)(yᵢ−ȳ)/(nσxσy)"}


# ══════════════════════════════════════════════════════════════
# TAB 2 — ALGEBRA (interactive solver)
# ══════════════════════════════════════════════════════════════
class AlgebraTab(ScrollFrame):
    def __init__(self, parent):
        super().__init__(parent)
        p = self.inner

        section_label(p, "PART 2 · ALGEBRA")
        heading(p, "Find Where Two Lines Intersect")
        body(p, "Enter slopes (m) and y-intercepts (b) for two lines.\n"
                "y = m₁x + b₁  and  y = m₂x + b₂", MUTED)

        # Inputs
        fields = {}
        params = [("m₁ (slope, line 1)", "m1", "2"),
                  ("b₁ (y-intercept, line 1)", "b1", "1"),
                  ("m₂ (slope, line 2)", "m2", "-1"),
                  ("b₂ (y-intercept, line 2)", "b2", "7")]
        for label, key, default in params:
            row = tk.Frame(p, bg=BG)
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label, bg=BG, fg=MUTED,
                     font=F_MONO_S, width=22, anchor="w").pack(side="left")
            e = tk.Entry(row, bg=SURFACE, fg=ALG, insertbackground=ALG,
                         font=F_MONO, width=6, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER)
            e.insert(0, default)
            e.pack(side="left", padx=4)
            fields[key] = e

        # Solve button
        result_var = tk.StringVar()
        steps_var  = tk.StringVar()

        def solve():
            try:
                m1 = float(fields["m1"].get())
                b1 = float(fields["b1"].get())
                m2 = float(fields["m2"].get())
                b2 = float(fields["b2"].get())
            except ValueError:
                result_var.set("⚠  Enter valid numbers")
                return

            if m1 == m2:
                if b1 == b2:
                    result_var.set("Lines are identical — infinitely many solutions")
                else:
                    result_var.set("Lines are parallel — no intersection")
                steps_var.set("")
                draw_lines(m1, b1, m2, b2, None, None)
                return

            # Solve: m1*x + b1 = m2*x + b2  →  x = (b2-b1)/(m1-m2)
            x = (b2 - b1) / (m1 - m2)
            y = m1 * x + b1

            # Angle between lines
            denom = 1 + m1 * m2
            if abs(denom) < 1e-9:
                angle = 90.0
            else:
                angle = math.degrees(math.atan(abs((m1 - m2) / denom)))

            # Polar
            r = math.sqrt(x**2 + y**2)
            theta = math.degrees(math.atan2(y, x))

            result_var.set(f"Intersection: ({x:.3f}, {y:.3f})")
            steps_var.set(
                f"Step 1 — set equal:\n"
                f"  {m1:+.2f}x + {b1:+.2f} = {m2:+.2f}x + {b2:+.2f}\n\n"
                f"Step 2 — isolate x:\n"
                f"  ({m1-m2:.2f})x = {b2-b1:.2f}\n"
                f"  x = {x:.4f}\n\n"
                f"Step 3 — find y:\n"
                f"  y = {m1}({x:.4f}) + {b1} = {y:.4f}\n\n"
                f"Geometry — angle between lines:\n"
                f"  tan θ = |m₁−m₂| / |1+m₁m₂|\n"
                f"  θ ≈ {angle:.1f}°\n\n"
                f"Trig — polar form of intersection:\n"
                f"  r = √(x²+y²) = {r:.3f}\n"
                f"  θ_polar = arctan(y/x) ≈ {theta:.1f}°"
            )
            draw_lines(m1, b1, m2, b2, x, y)

        tk.Button(p, text="Solve & Draw", bg=ALG, fg=BG,
                  font=("sans-serif", 11, "bold"), relief="flat",
                  padx=12, pady=8, cursor="hand2",
                  command=solve).pack(pady=10)

        # Result label
        tk.Label(p, textvariable=result_var, bg=BG, fg=WHITE,
                 font=F_HEAD).pack(padx=16, anchor="w")

        # Canvas for line drawing
        self.line_canvas = tk.Canvas(p, bg=SURFACE, height=220,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.line_canvas.pack(fill="x", padx=12, pady=6)

        # Steps card
        steps_frame = card(p)
        tk.Label(steps_frame, textvariable=steps_var, bg=SURFACE, fg=TEXT,
                 font=F_MONO_S, justify="left", anchor="w",
                 wraplength=330).pack(padx=10, pady=10, anchor="w")

        def draw_lines(m1, b1, m2, b2, ix, iy):
            cv = self.line_canvas
            cv.delete("all")
            W = cv.winfo_width() or 356
            H = 220
            ox, oy = W // 2, H // 2
            sc = 28  # pixels per unit

            # Grid
            for i in range(-8, 9):
                x = ox + i * sc
                cv.create_line(x, 0, x, H, fill=BORDER)
            for j in range(-4, 5):
                y = oy - j * sc
                cv.create_line(0, y, W, y, fill=BORDER)

            # Axes
            cv.create_line(0, oy, W, oy, fill="#3a3d60", width=2)
            cv.create_line(ox, 0, ox, H, fill="#3a3d60", width=2)

            # Tick labels
            for i in [-4, -2, 2, 4]:
                x = ox + i * sc
                cv.create_text(x, oy + 12, text=str(i), fill=MUTED, font=("monospace", 7))
            for j in [-3, -1, 1, 3]:
                y = oy - j * sc
                cv.create_text(ox + 14, y, text=str(j), fill=MUTED, font=("monospace", 7))

            def px(x): return ox + x * sc
            def py(y): return oy - y * sc

            # Line 1
            pts1 = []
            for xi in range(-8, 9):
                yi = m1 * xi + b1
                if -5 < yi < 5:
                    pts1 += [px(xi), py(yi)]
            if len(pts1) >= 4:
                cv.create_line(*pts1, fill=ALG, width=2, smooth=True)

            # Line 2
            pts2 = []
            for xi in range(-8, 9):
                yi = m2 * xi + b2
                if -5 < yi < 5:
                    pts2 += [px(xi), py(yi)]
            if len(pts2) >= 4:
                cv.create_line(*pts2, fill=GEO, width=2, smooth=True)

            # Line labels
            cv.create_text(W - 8, py(m1 * 5 + b1) if -5 < m1*5+b1 < 5 else 14,
                           text=f"y={m1}x+{b1}", fill=ALG, font=("monospace", 8), anchor="e")
            cv.create_text(W - 8, py(m2 * 5 + b2) if -5 < m2*5+b2 < 5 else 30,
                           text=f"y={m2}x+{b2}", fill=GEO, font=("monospace", 8), anchor="e")

            # Intersection
            if ix is not None:
                ipx, ipy = px(ix), py(iy)
                if 0 < ipx < W and 0 < ipy < H:
                    cv.create_line(ipx, ipy, ipx, oy, fill=TRIG, dash=(4,3), width=1)
                    cv.create_line(ipx, ipy, ox, ipy, fill=TRIG, dash=(4,3), width=1)
                    cv.create_oval(ipx-6, ipy-6, ipx+6, ipy+6, fill=WHITE, outline=TRIG, width=2)
                    cv.create_text(ipx + 8, ipy - 12,
                                   text=f"({ix:.1f}, {iy:.1f})",
                                   fill=WHITE, font=("monospace", 8), anchor="w")

        # Trigger initial draw after layout
        p.after(200, solve)


# ══════════════════════════════════════════════════════════════
# TAB 3 — GEOMETRY
# ══════════════════════════════════════════════════════════════
class GeometryTab(ScrollFrame):
    def __init__(self, parent):
        super().__init__(parent)
        p = self.inner

        section_label(p, "PART 3 · GEOMETRY")
        heading(p, "Pythagorean Theorem & Right Triangles")
        body(p, "Enter two sides of a right triangle. The app finds the third "
                "and shows the triangle.", MUTED)

        fields = {}
        for label, key, default in [("Side a", "a", "3"), ("Side b", "b", "4"),
                                     ("Side c (hypotenuse)", "c", "")]:
            row = tk.Frame(p, bg=BG)
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label, bg=BG, fg=MUTED,
                     font=F_MONO_S, width=22, anchor="w").pack(side="left")
            e = tk.Entry(row, bg=SURFACE, fg=GEO, insertbackground=GEO,
                         font=F_MONO, width=8, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER)
            e.insert(0, default)
            e.pack(side="left", padx=4)
            fields[key] = e

        result_var = tk.StringVar()
        steps_var  = tk.StringVar()
        self.tri_canvas = tk.Canvas(p, bg=SURFACE, height=220,
                                    highlightthickness=1, highlightbackground=BORDER)
        self.tri_canvas.pack(fill="x", padx=12, pady=6)

        def solve():
            try:
                av = fields["a"].get().strip()
                bv = fields["b"].get().strip()
                cv = fields["c"].get().strip()
                vals = [float(x) if x else None for x in [av, bv, cv]]
                a, b, c = vals
            except ValueError:
                result_var.set("⚠  Enter valid numbers")
                return

            known = [(v, n) for v, n in zip([a,b,c],["a","b","c"]) if v is not None]
            if len(known) < 2:
                result_var.set("⚠  Enter at least 2 sides")
                return

            if a and b and not c:
                c = math.sqrt(a**2 + b**2)
            elif a and c and not b:
                if c <= a: result_var.set("⚠  c must be > a"); return
                b = math.sqrt(c**2 - a**2)
            elif b and c and not a:
                if c <= b: result_var.set("⚠  c must be > b"); return
                a = math.sqrt(c**2 - b**2)
            else:
                c = math.sqrt(a**2 + b**2)

            A = math.degrees(math.atan2(b, a))  # angle at hypotenuse base, opp b
            B = 90 - A
            area = 0.5 * a * b
            perim = a + b + c

            result_var.set(f"a={a:.3f}  b={b:.3f}  c={c:.3f}")
            steps_var.set(
                f"a² + b² = c²\n"
                f"{a:.3f}² + {b:.3f}² = {a**2:.3f} + {b**2:.3f} = {c**2:.3f}\n"
                f"c = √{c**2:.3f} = {c:.4f}\n\n"
                f"Angle α (opposite b) = arctan(b/a) = {A:.1f}°\n"
                f"Angle β (opposite a) = {B:.1f}°\n"
                f"(α + β + 90° = 180° ✓)\n\n"
                f"Area  = ½ · a · b = {area:.3f}\n"
                f"Perimeter = {perim:.3f}"
            )
            draw_triangle(a, b, c, A, B)

        tk.Button(p, text="Calculate & Draw", bg=GEO, fg=BG,
                  font=("sans-serif", 11, "bold"), relief="flat",
                  padx=12, pady=8, command=solve).pack(pady=10)

        tk.Label(p, textvariable=result_var, bg=BG, fg=WHITE, font=F_HEAD).pack(anchor="w", padx=16)

        steps_frame = card(p)
        tk.Label(steps_frame, textvariable=steps_var, bg=SURFACE, fg=TEXT,
                 font=F_MONO_S, justify="left", anchor="w",
                 wraplength=330).pack(padx=10, pady=10, anchor="w")

        def draw_triangle(a, b, c, A, B):
            cv = self.tri_canvas
            cv.delete("all")
            W = cv.winfo_width() or 356
            H = 220
            margin = 40
            # scale to fit
            max_side = max(a, b, c)
            sc = min((W - 2*margin) / b, (H - 2*margin) / a)
            # right angle at bottom-left
            x0, y0 = margin, H - margin           # bottom-left (right angle)
            x1, y1 = margin + b * sc, H - margin  # bottom-right
            x2, y2 = margin, H - margin - a * sc  # top-left

            cv.create_polygon(x0,y0, x1,y1, x2,y2, fill="#161728",
                               outline=GEO, width=2)
            # right-angle square
            sq = 10
            cv.create_rectangle(x0, y0-sq, x0+sq, y0, outline=GEO, fill=SURFACE)

            # side labels
            cv.create_text((x0+x1)/2, y0+14, text=f"b = {b:.2f}", fill=GEO, font=F_MONO_S)
            cv.create_text(x0-18, (y0+y2)/2, text=f"a = {a:.2f}", fill=ALG, font=F_MONO_S)
            cx, cy = (x1+x2)/2, (y1+y2)/2
            cv.create_text(cx+18, cy, text=f"c = {c:.2f}", fill=TRIG, font=F_MONO_S)

            # angle arcs
            cv.create_arc(x1-24, y1-24, x1+24, y1+24,
                          start=90, extent=int(B), outline=ALG, style="arc", width=1)
            cv.create_text(x1-18, y1-18, text=f"{B:.0f}°", fill=ALG, font=("monospace",7))
            cv.create_arc(x2-12, y2-12, x2+24, y2+24,
                          start=270, extent=int(A), outline=TRIG, style="arc", width=1)
            cv.create_text(x2+20, y2+14, text=f"{A:.0f}°", fill=TRIG, font=("monospace",7))

        p.after(200, solve)


# ══════════════════════════════════════════════════════════════
# TAB 4 — TRIGONOMETRY
# ══════════════════════════════════════════════════════════════
class TrigTab(ScrollFrame):
    def __init__(self, parent):
        super().__init__(parent)
        p = self.inner

        section_label(p, "PART 4 · TRIGONOMETRY")
        heading(p, "Unit Circle Explorer")
        body(p, "Drag the slider to rotate the angle θ and see sin, cos, and tan update live.", MUTED)

        self.angle_var = tk.DoubleVar(value=50.0)
        slider = tk.Scale(p, from_=0, to=360, orient="horizontal",
                          variable=self.angle_var, bg=BG, fg=TRIG,
                          troughcolor=SURFACE, highlightthickness=0,
                          font=F_MONO_S, command=self._update)
        slider.pack(fill="x", padx=12, pady=4)

        self.trig_canvas = tk.Canvas(p, bg=SURFACE, height=240,
                                     highlightthickness=1, highlightbackground=BORDER)
        self.trig_canvas.pack(fill="x", padx=12, pady=4)

        # Value display
        self.sin_var = tk.StringVar()
        self.cos_var = tk.StringVar()
        self.tan_var = tk.StringVar()
        self.quad_var = tk.StringVar()

        vframe = card(p)
        for label, var, color in [("sin θ =", self.sin_var, TRIG),
                                   ("cos θ =", self.cos_var, ALG),
                                   ("tan θ =", self.tan_var, GEO),
                                   ("Quadrant:", self.quad_var, STAT)]:
            row = tk.Frame(vframe, bg=SURFACE)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=label, bg=SURFACE, fg=MUTED,
                     font=F_MONO_S, width=10, anchor="w").pack(side="left")
            tk.Label(row, textvariable=var, bg=SURFACE, fg=color,
                     font=("monospace", 11, "bold"), anchor="w").pack(side="left")

        body(p, "Key identities taught in integrated math:", MUTED)
        id_card = card(p)
        tk.Label(id_card, text=(
            "sin²θ + cos²θ = 1   (Pythagorean)\n"
            "tan θ  = sin θ / cos θ\n"
            "sin(90°−θ) = cos θ   (co-function)\n"
            "Area of triangle = ½ab·sin C"
        ), bg=SURFACE, fg=TEXT, font=F_MONO_S,
                 justify="left", anchor="w").pack(padx=10, pady=10, anchor="w")

        self._update(None)

    def _update(self, _):
        deg = self.angle_var.get()
        rad = math.radians(deg)
        s = math.sin(rad)
        c = math.cos(rad)
        t = math.tan(rad)

        self.sin_var.set(f"{s:+.4f}")
        self.cos_var.set(f"{c:+.4f}")
        self.tan_var.set("undefined" if abs(c) < 0.001 else f"{t:+.4f}")

        quad = (1 if deg < 90 else 2 if deg < 180 else 3 if deg < 270 else 4)
        signs = {1: "(+,+)", 2: "(−,+)", 3: "(−,−)", 4: "(+,−)"}
        self.quad_var.set(f"Q{quad}  {signs[quad]}  sin{'+'if s>=0 else'−'} cos{'+'if c>=0 else'−'}")

        self._draw(deg, s, c)

    def _draw(self, deg, s, c):
        cv = self.trig_canvas
        cv.delete("all")
        W = cv.winfo_width() or 356
        H = 240
        ox, oy = W // 2, H // 2
        R = min(W, H) // 2 - 32

        # Grid
        for i in range(-4, 5):
            u = ox + i * R
            cv.create_line(u, 0, u, H, fill=BORDER)
        for j in range(-3, 4):
            v = oy - j * R
            cv.create_line(0, v, W, v, fill=BORDER)

        # Axes
        cv.create_line(0, oy, W, oy, fill="#3a3d60", width=2)
        cv.create_line(ox, 0, ox, H, fill="#3a3d60", width=2)

        # Unit circle
        cv.create_oval(ox-R, oy-R, ox+R, oy+R, outline=ALG+"60", width=1)

        # Quadrant labels
        for (tx, ty, lbl) in [(ox+R//2, oy-R//2, "Q I"), (ox-R//2, oy-R//2, "Q II"),
                               (ox-R//2, oy+R//2, "Q III"), (ox+R//2, oy+R//2, "Q IV")]:
            cv.create_text(tx, ty, text=lbl, fill=BORDER, font=("monospace", 8))

        # Point on circle
        px = ox + c * R
        py = oy - s * R

        # Radius
        cv.create_line(ox, oy, px, py, fill=TRIG, width=2)

        # cos projection (horizontal)
        cv.create_line(ox, oy, px, oy, fill=ALG, width=2, dash=(5,3))
        # sin projection (vertical)
        cv.create_line(px, oy, px, py, fill=TRIG, width=2, dash=(5,3))

        # Angle arc
        cv.create_arc(ox-30, oy-30, ox+30, oy+30,
                      start=0, extent=int(deg), outline=STAT, style="arc", width=2)

        # Point
        cv.create_oval(px-6, py-6, px+6, py+6, fill=WHITE, outline=TRIG, width=2)

        # Labels
        cv.create_text((ox+px)//2, oy+14, text=f"cos={c:.3f}", fill=ALG, font=("monospace",8))
        cv.create_text(px+32, (oy+py)//2, text=f"sin={s:.3f}", fill=TRIG, font=("monospace",8))
        cv.create_text(ox+34, oy-16, text=f"{deg:.0f}°", fill=STAT, font=("monospace",9,"bold"))
        cv.create_text(px, py-14, text=f"({c:.2f},{s:.2f})", fill=WHITE, font=("monospace",7))

        # x²+y²=1 label
        cv.create_text(ox, 12, text="x² + y² = 1", fill=ALG+"80", font=("monospace",8))


# ══════════════════════════════════════════════════════════════
# TAB 5 — COMPARE
# ══════════════════════════════════════════════════════════════
class CompareTab(ScrollFrame):
    def __init__(self, parent):
        super().__init__(parent)
        p = self.inner

        section_label(p, "PART 5 · COMPARISON")
        heading(p, "Integrated vs Traditional: Key Facts")

        stats = [
            ("16%",    "of US districts offer integrated math (2023)", ALG),
            ("11→67%", "Chapman KS proficiency 2015→2025",             GEO),
            ("37%",    "California proficiency despite 10+ yrs",       TRIG),
            ("~3 mo",  "extra learning gain (Huffaker study)",         STAT),
            ("2027",   "Maryland mandates statewide integrated math",  ALG),
            ("27",     "states reworking math transition (Dana Ctr)",  GEO),
        ]
        for num, desc, color in stats:
            f = card(p)
            row = tk.Frame(f, bg=SURFACE)
            row.pack(fill="x", padx=10, pady=8)
            tk.Label(row, text=num, bg=SURFACE, fg=color,
                     font=("sans-serif", 20, "bold"), width=8, anchor="w").pack(side="left")
            tk.Label(row, text=desc, bg=SURFACE, fg=TEXT,
                     font=F_BODY, wraplength=200, justify="left",
                     anchor="w").pack(side="left", padx=4)

        divider(p)
        heading(p, "Tradeoffs at a Glance")

        rows = [
            ("Retention",       "Revisit topics yearly",    "Year-long gaps possible", ALG, GEO),
            ("10th-grade test", "Strong: sees both topics", "Algebra gap in geo year", GEO, TRIG),
            ("STEM depth",      "May be shallower",         "Strong calc foundation",  TRIG, ALG),
            ("Flexibility",     "Stats/Data path open",     "Race to calculus default",STAT, MUTED),
            ("Credit transfer", "Messy across schools",     "Clear & universal",       TRIG, GEO),
            ("Teacher load",    "Must know all areas",      "Can specialise",          TRIG, GEO),
        ]

        header = tk.Frame(p, bg=BG)
        header.pack(fill="x", padx=12)
        for txt, w, col in [("Topic", 100, MUTED), ("Integrated", 120, ALG), ("Traditional", 120, GEO)]:
            tk.Label(header, text=txt, bg=BG, fg=col,
                     font=("monospace", 8, "bold"), width=w//7, anchor="w").pack(side="left", padx=2)

        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=12, pady=2)

        for topic, int_txt, trad_txt, int_col, trad_col in rows:
            row = tk.Frame(p, bg=BG)
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=topic, bg=BG, fg=MUTED,
                     font=("monospace", 8), width=14, anchor="w").pack(side="left")
            tk.Label(row, text=int_txt, bg=BG, fg=int_col,
                     font=("monospace", 7), wraplength=120, anchor="w",
                     justify="left").pack(side="left", padx=2)
            tk.Label(row, text=trad_txt, bg=BG, fg=trad_col,
                     font=("monospace", 7), wraplength=120, anchor="w",
                     justify="left").pack(side="left", padx=2)
            tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=12)

        divider(p)
        body(p, "Bottom line: Integrated math shows real but modest gains (~2–3 months of "
                "additional learning). Its bigger value is structural — creating multiple "
                "math pathways instead of a single race to calculus.", MUTED)


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
