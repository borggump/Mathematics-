# -*- coding: utf-8 -*-
"""
Quantum Advantage Explorer  -  for Pydroid 3 (Android) or any desktop Python 3
==============================================================================
Interactive calculators for the problems described in the Nov 2026 study
"24 problems where quantum computers could gain an edge" (arXiv preprint,
reported by The Quantum Insider).

Uses only the standard library (tkinter + math). In Pydroid 3, open this file
and press the yellow Run button. Then pick a problem from the menu at the top,
edit the inputs, and tap COMPUTE.

All models are simplified textbook scalings meant for intuition, not resource
estimates. Constants and defaults are illustrative.
"""

import math
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------- settings --
UI_SCALE = 1.0          # make everything bigger (1.2) or smaller (0.8)
FAM = "Helvetica"       # Tk substitutes the system font if missing
MONO = "Courier"
COL_C = "#d9822b"       # classical
COL_Q = "#6d4bd8"       # quantum
COL_Q2 = "#9aa0a6"      # comparison line
COL_MARK = "#2f6fde"
BG = "#fbfaf7"

# Pixel sizes, set from the real screen width in main(). Fonts are given in
# PIXELS (negative Tk sizes) so they don't balloon on high-DPI phones.
PX = 24                 # base font height in pixels
SW = 1080               # screen width in pixels


def F(mult=1.0, *style):
    return (FAM, -max(8, int(PX * mult))) + style


# ----------------------------------------------------------------- helpers --
def fmt_time(log10_sec):
    """Format a duration given as log10(seconds)."""
    if log10_sec is None or math.isnan(log10_sec):
        return "-"
    if log10_sec > 300:
        return "10^%.0f s (forever)" % log10_sec
    s = 10.0 ** log10_sec
    year = 3.156e7
    if s < 1e-6:
        return "%.3g ns" % (s * 1e9)
    if s < 1e-3:
        return "%.3g µs" % (s * 1e6)
    if s < 1:
        return "%.3g ms" % (s * 1e3)
    if s < 120:
        return "%.3g s" % s
    if s < 7200:
        return "%.3g min" % (s / 60)
    if s < 2 * 86400:
        return "%.3g hours" % (s / 3600)
    if s < 2 * year:
        return "%.3g days" % (s / 86400)
    if s < 1e6 * year:
        return "%.3g years" % (s / year)
    return "10^%.1f years" % (math.log10(s / year))


def fmt_pow(log10_v):
    """Format a big number given as log10(value)."""
    if abs(log10_v) < 4:
        return "%.4g" % (10 ** log10_v)
    e = math.floor(log10_v)
    m = 10 ** (log10_v - e)
    return "%.2f×10^%d" % (m, e)


def lg(x):
    return math.log10(x)


def winner_line(log_tc, log_tq):
    d = log_tc - log_tq
    if d > 0:
        return "→ QUANTUM faster, ×%s" % fmt_pow(d)
    return "→ CLASSICAL faster, ×%s" % fmt_pow(-d)


# ------------------------------------------------------------------ plot ----
YTICKS = [(-9, "1ns"), (-6, "1µs"), (-3, "1ms"), (0, "1s"), (math.log10(60), "1min"),
          (math.log10(3600), "1h"), (math.log10(86400), "1day"),
          (math.log10(3.156e7), "1yr"), (math.log10(3.156e10), "1kyr"),
          (math.log10(3.156e13), "1Myr"), (math.log10(3.156e16), "1Gyr")] + \
         [(math.log10(3.156e7) + e, "1e%dyr" % e) for e in range(12, 300, 3)]


class Plot(tk.Canvas):
    """Tiny plotting widget. y values are always log10(seconds).
    The legend sits above the plot box and labels are thinned so they never overlap."""

    def __init__(self, master):
        super().__init__(master, height=int(SW * 0.9), bg="white", highlightthickness=0)
        self._last = None
        self.bind("<Configure>", lambda e: self._last and self.draw(*self._last))

    def draw(self, series, xlabel, xlog=True, marks=()):
        self._last = (series, xlabel, xlog, marks)
        self.delete("all")
        W = max(self.winfo_width(), 200)
        H = max(self.winfo_height(), 150)
        fp = max(10, int(PX * 0.72))           # plot font, pixels
        font = (FAM, -fp)
        row = int(fp * 1.5)
        lw = max(3, fp // 6)
        T = row * len(series) + fp             # room for legend
        L = int(fp * 3.6)                      # refined below from tick labels
        R = int(fp * 1.0)
        B = int(fp * 3.4)
        pts = [p for s in series for p in s["pts"]
               if p[1] is not None and math.isfinite(p[1])]
        if not pts:
            return
        tx = (lambda x: math.log10(x)) if xlog else (lambda x: x)
        xs = [tx(p[0]) for p in pts]
        ys = [p[1] for p in pts]
        x0, x1 = min(xs), max(xs)
        y1 = max(ys)
        y0 = max(min(ys), y1 - 40)
        if y1 - y0 < 1:
            y1 += 0.5; y0 -= 0.5
        if x1 == x0:
            x1 += 1
        cand = [(y, l) for y, l in YTICKS if y0 <= y <= y1]
        if len(cand) < 2:
            stp = max(1, math.ceil((y1 - y0) / 5))
            cand = [(v, "1e%ds" % v) for v in range(math.ceil(y0), int(math.floor(y1)) + 1, stp)]
        L = int(fp * 0.62 * max([len(l) for _, l in cand] + [3]) + fp * 0.8)
        X = lambda xv: L + (xv - x0) / (x1 - x0) * (W - L - R)
        Y = lambda y: H - B - (min(max(y, y0), y1) - y0) / (y1 - y0) * (H - T - B)

        # legend (above the plot box)
        for i, s in enumerate(series):
            yy = fp * 0.6 + i * row + fp * 0.5
            self.create_line(L, yy, L + fp * 2, yy, fill=s["color"], width=lw,
                             dash=s.get("dash", ()))
            self.create_text(L + fp * 2.5, yy, text=s["name"], anchor="w", font=font)

        # y ticks: named time units, thinned so labels never collide
        last = None
        for y, l in cand:
            py = Y(y)
            if last is not None and abs(last - py) < fp * 1.5:
                continue
            last = py
            self.create_line(L, py, W - R, py, fill="#eee")
            self.create_text(L - 5, py, text=l, anchor="e", font=font)

        # x ticks: at most 5, at round values
        span = x1 - x0
        step = 1
        for s_ in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000):
            step = s_
            if span / s_ <= 4:
                break
        v = math.ceil(x0 / step) * step
        while v <= x1 + 1e-9:
            px = X(v)
            self.create_line(px, T, px, H - B, fill="#eee")
            lab = ("10^%d" % round(v)) if xlog else ("%d" % round(v))
            anchor = "n"
            if px - L < fp * 1.5:
                anchor = "nw"
            elif W - R - px < fp * 1.5:
                anchor = "ne"
            self.create_text(px, H - B + 5, text=lab, anchor=anchor, font=font)
            v += step
        self.create_text((L + W - R) / 2, H - fp * 0.7, text=xlabel, font=font)
        self.create_rectangle(L, T, W - R, H - B, outline="#bbb")

        # curves
        for s in series:
            coords = []
            for xv, y in s["pts"]:
                if y is None or not math.isfinite(y):
                    continue
                coords += [X(tx(xv)), Y(y)]
            if len(coords) >= 4:
                self.create_line(*coords, fill=s["color"], width=lw, dash=s.get("dash", ()))

        # markers (label placed toward the inside so it isn't cut off)
        for (mx, my, ml) in marks:
            if my is None or not math.isfinite(my) or not (y0 <= my <= y1):
                continue
            px, py = X(tx(mx)), Y(my)
            if not (L <= px <= W - R):
                continue
            r = fp * 0.35
            self.create_oval(px - r, py - r, px + r, py + r, fill=COL_MARK, outline="")
            right_half = px > (L + W - R) / 2
            ty = py + fp if py < T + fp * 1.5 else py - fp
            self.create_text(px + (-r - 4 if right_half else r + 4), ty, text=ml,
                             anchor="e" if right_half else "w", font=font, fill=COL_MARK)


# ------------------------------------------------------------- base panel ---
class Panel:
    """Each problem: TITLE, INFO, FIELDS = [(key, label, default)] or
    (key, label, default, [choices]) for a drop-down; compute(v) returns
    (text, series, xlabel, xlog, marks)."""
    TITLE = ""
    INFO = ""
    FIELDS = []

    def compute(self, v):
        raise NotImplementedError


# ---------------------------------------------------------------- panels ----
class Crossover(Panel):
    TITLE = "0 · Crossover (why > quadratic)"
    INFO = ("Classical time Tc = cC·M, quantum Tq = cQ·M^(1/k), where M = classical steps "
            "and r = cQ/cC is the cost of one error-corrected quantum step relative to one "
            "classical step. Break-even:  M* = r^(k/(k-1)).  Using P classical cores "
            "multiplies r by P, which hurts quadratic speedups the most.")
    FIELDS = [("k", "Speedup degree k (2 = quadratic)", "2"),
              ("logr", "log10 overhead r = cQ/cC", "7"),
              ("tc", "Classical step time (ns)", "1"),
              ("P", "Parallel classical cores P", "1")]

    def compute(self, v):
        k, logr, tc, P = float(v["k"]), float(v["logr"]), float(v["tc"]), float(v["P"])
        if k <= 1:
            raise ValueError("k must be > 1")
        log_cc1 = lg(tc * 1e-9)
        log_cc = log_cc1 - lg(P)
        log_cq = log_cc1 + logr
        log_reff = logr + lg(P)
        lM = log_reff * k / (k - 1)
        lT = log_cc + lM
        out = ["Effective overhead r·P = 10^%.2f" % log_reff,
               "Break-even size M* = r^(k/(k-1))\n  = %s classical steps" % fmt_pow(lM),
               "Break-even time T* = %s" % fmt_time(lT),
               "Quantum wins only on LARGER problems.", "",
               "Break-even time, same overhead:"]
        for kk in (2, 3, 4, 6, 10):
            m = log_reff * kk / (kk - 1)
            out.append("k=%d: %s" % (kk, fmt_time(log_cc + m)))
        xmax = max(lM + 3, 12)
        xs = [10 ** (xmax * i / 80) for i in range(81)]
        series = [
            {"name": "classical", "color": COL_C,
             "pts": [(x, log_cc + lg(x)) for x in xs]},
            {"name": "quantum k=%g" % k, "color": COL_Q,
             "pts": [(x, log_cq + lg(x) / k) for x in xs]}]
        if k != 2:
            series.append({"name": "quantum k=2", "color": COL_Q2, "dash": (5, 4),
                           "pts": [(x, log_cq + lg(x) / 2) for x in xs]})
        return "\n".join(out), series, "problem size M (classical steps)", True, \
            [(10 ** lM, lT, "break-even")]


class LinearSystems(Panel):
    TITLE = "1 · Linear systems Ax=b"
    INFO = ("Classical conjugate gradient: N·s·√κ·log(1/ε) ops. Quantum (modern "
            "block-encoding solvers): κ·log(1/ε) queries per run, PLUS state loading "
            "(≈log N if data is structured, ≈N if arbitrary), PLUS readout (≈1/ε runs "
            "for one scalar via amplitude estimation, ≈N/ε² runs for the whole vector). "
            "The exponential gain survives only with structured input, small κ and "
            "scalar output.")
    FIELDS = [("N", "Matrix dimension N", "1e9"),
              ("s", "Nonzeros per row s", "10"),
              ("kappa", "Condition number κ", "100"),
              ("eps", "Target precision ε", "1e-3"),
              ("tc", "Classical op time (ns)", "1"),
              ("tq", "Quantum step time (µs)", "100"),
              ("load", "Input data", "structured", ["structured", "arbitrary"]),
              ("outp", "Output needed", "one scalar", ["one scalar", "full vector"])]

    @staticmethod
    def model(N, s, kappa, eps, tc, tq, load, outp):
        lc = lg(N) + lg(s) + 0.5 * lg(kappa) + lg(math.log(1 / eps)) + lg(tc * 1e-9)
        load_steps = math.log2(N) if load == "structured" else N
        core = kappa * math.log(1 / eps)
        lreps = -lg(eps) if outp == "one scalar" else lg(N) - 2 * lg(eps)
        lq = lreps + lg(load_steps + core) + lg(tq * 1e-6)
        return lc, lq, load_steps, core, lreps

    def compute(self, v):
        N, s, kappa, eps = (float(v[x]) for x in ("N", "s", "kappa", "eps"))
        tc, tq = float(v["tc"]), float(v["tq"])
        if N < 2 or kappa < 1 or not (0 < eps < 1):
            raise ValueError("Need N ≥ 2, κ ≥ 1, 0 < ε < 1")
        lc, lq, ls, core, lreps = self.model(N, s, kappa, eps, tc, tq, v["load"], v["outp"])
        stages = {"loading": ls, "quantum core": core}
        dom = max(stages, key=stages.get)
        out = ["Classical CG time:  %s" % fmt_time(lc),
               "Quantum time:       %s" % fmt_time(lq),
               winner_line(lc, lq), "",
               "Per quantum run: loading ≈ %s steps, core ≈ %s steps  (dominant: %s)"
               % (fmt_pow(lg(ls)), fmt_pow(lg(core)), dom),
               "Readout repetitions ≈ %s" % fmt_pow(lreps), ""]
        warn = []
        if v["load"] == "arbitrary":
            warn.append("• Arbitrary data costs ~N steps to load, which cancels the exponential gain.")
        if v["outp"] == "full vector":
            warn.append("• Reading every entry costs ~N/ε² runs, which cancels the gain.")
        if kappa > math.sqrt(N):
            warn.append("• κ is large relative to N; quantum cost grows linearly in κ.")
        warn.append("• If A is low-rank, 'dequantized' classical algorithms may match the quantum one.")
        out += warn
        Ns = [10 ** (2 + 13 * i / 60) for i in range(61)]
        sc, sq = [], []
        for n in Ns:
            a, b, *_ = self.model(n, s, kappa, eps, tc, tq, v["load"], v["outp"])
            sc.append((n, a)); sq.append((n, b))
        series = [{"name": "classical CG", "color": COL_C, "pts": sc},
                  {"name": "quantum", "color": COL_Q, "pts": sq}]
        return "\n".join(out), series, "matrix dimension N", True, [(N, lq, "your N")]


class GroundState(Panel):
    TITLE = "2 · Molecule ground energy"
    INFO = ("Quantum phase estimation (qubitization): one run takes ≈ π·λ/(2ε) walk "
            "steps, where λ = 1-norm of the Hamiltonian coefficients (Hartree). Each run "
            "returns the ground energy with probability γ² (γ = overlap of the trial state "
            "with the true ground state), so ≈1/γ² runs are needed, or ≈1/γ with amplitude "
            "amplification. Chemical accuracy ε ≈ 0.0016 Ha.")
    FIELDS = [("n", "Spin-orbitals (system qubits)", "100"),
              ("lam", "Hamiltonian 1-norm λ (Ha)", "500"),
              ("eps", "Precision ε (Ha)", "0.0016"),
              ("gamma", "Overlap γ = |<E0|psi0>|", "0.5"),
              ("tstep", "Time per walk step (ms)", "1"),
              ("aa", "Amplitude amplification", "no", ["no", "yes"])]

    def compute(self, v):
        n, lam, eps, g, ts = (float(v[x]) for x in ("n", "lam", "eps", "gamma", "tstep"))
        if not (0 < g <= 1) or eps <= 0 or lam <= 0:
            raise ValueError("Need 0 < γ ≤ 1, ε > 0, λ > 0")
        aa = v["aa"] == "yes"
        steps = math.pi * lam / (2 * eps)
        lrun = lg(steps) + lg(ts * 1e-3)

        def total(gg, use_aa):
            return lrun + (-lg(gg) if use_aa else -2 * lg(gg))

        lt = total(g, aa)
        out = ["Walk steps per run ≈ %s" % fmt_pow(lg(steps)),
               "Time per run ≈ %s" % fmt_time(lrun),
               "Runs needed ≈ %s" % fmt_pow((-lg(g)) if aa else (-2 * lg(g))),
               "TOTAL ≈ %s" % fmt_time(lt), "",
               "System register: %d logical qubits (1 per spin-orbital), plus ancillas." % n,
               "",
               "Orthogonality catastrophe: if γ decays like e^(-αn), e.g. α = 0.05:"]
        for nn in (50, 100, 200, 400):
            gg = math.exp(-0.05 * nn)
            out.append("  n=%-4d γ=%.2e  total ≈ %s" % (nn, gg, fmt_time(total(gg, aa))))
        out.append("A good initial state AND classical hardness are both required.")
        gs = [10 ** (-6 + 6 * i / 60) for i in range(61)]
        series = [{"name": "no amp. ampl.", "color": COL_Q,
                   "pts": [(x, total(x, False)) for x in gs]},
                  {"name": "with amp. ampl.", "color": COL_Q2, "dash": (5, 4),
                   "pts": [(x, total(x, True)) for x in gs]}]
        return "\n".join(out), series, "overlap γ", True, [(g, lt, "your γ")]


class PlantedInference(Panel):
    TITLE = "3 · Patterns in noise"
    INFO = ("Planted model: T = λ·(v outer-product v ... p times) + noise. In the hard-but-possible signal window, "
            "classical Kikuchi spectral methods cost ~n^ℓ (level ℓ grows as the signal "
            "weakens). The quantum algorithm combines two square-root gains for ~n^(ℓ/4): "
            "a QUARTIC speedup. For p = 2 (ordinary matrix PCA) classical is already "
            "efficient, so there is no advantage. Article's cited estimate for one "
            "instance: ~15 h on ~74 million physical qubits.")
    FIELDS = [("n", "Number of variables n", "200"),
              ("l", "Kikuchi level ℓ (weaker signal → larger)", "8"),
              ("logr", "log10 overhead r = cQ/cC", "7"),
              ("tc", "Classical op time (ns)", "1"),
              ("p", "Tensor order p", "4")]

    def compute(self, v):
        n, l, logr, tc, p = (float(v[x]) for x in ("n", "l", "logr", "tc", "p"))
        if n < 2 or l <= 0:
            raise ValueError("Need n ≥ 2, ℓ > 0")
        lcc = lg(tc * 1e-9)
        f_c = lambda x: lcc + l * lg(x)
        f_q = lambda x: lcc + logr + (l / 4) * lg(x)
        lc, lq = f_c(n), f_q(n)
        ln_star = logr / (0.75 * l)
        out = []
        if p <= 2:
            out.append("p = 2 is ordinary matrix PCA: the top eigenvector costs ~n² classically, "
                       "so there is NO quantum advantage. Showing the p ≥ 3 model anyway.\n")
        out += ["Classical ~n^ℓ:      %s" % fmt_time(lc),
                "Quantum ~n^(ℓ/4):    %s" % fmt_time(lq),
                winner_line(lc, lq), "",
                "Break-even n* = r^(4/(3ℓ)) ≈ %.3g" % (10 ** ln_star),
                "Break-even time ≈ %s" % fmt_time(f_c(10 ** ln_star)), "",
                "Caveats: valid only inside the signal window; robustness to sparse or",
                "contaminated data is still open. Real hardware needs are large."]
        ns = [10 ** (1 + 3.5 * i / 60) for i in range(61)]
        series = [{"name": "classical n^ℓ", "color": COL_C, "pts": [(x, f_c(x)) for x in ns]},
                  {"name": "quantum n^(ℓ/4)", "color": COL_Q, "pts": [(x, f_q(x)) for x in ns]}]
        return "\n".join(out), series, "variables n", True, \
            [(10 ** ln_star, f_c(10 ** ln_star), "break-even"), (n, lq, "your n")]


class Factoring(Panel):
    TITLE = "4 · Factoring"
    INFO = ("Classical general number field sieve: L = exp(1.923·(ln N)^(1/3)·(ln ln N)^(2/3)), "
            "calibrated here so RSA-768 ≈ 2000 core-years (the 2009 record). Shor's algorithm: "
            "≈ c·n³ logical operations for an n-bit number. Easy input, a tiny output that is "
            "classically verifiable, and a super-polynomial speedup: the cleanest case.")
    FIELDS = [("bits", "Key size n (bits)", "2048"),
              ("cores", "Classical cores", "1e6"),
              ("c", "Shor constant c (ops = c·n³)", "1"),
              ("top", "Quantum logical op time (µs)", "50")]

    @staticmethod
    def l_gnfs(bits):
        lnN = bits * math.log(2)
        return 1.923 * lnN ** (1 / 3) * math.log(lnN) ** (2 / 3) / math.log(10)

    def compute(self, v):
        bits, cores, c, top = (float(v[x]) for x in ("bits", "cores", "c", "top"))
        if bits < 64:
            raise ValueError("Use at least 64 bits")
        lref = lg(2000 * 3.156e7)
        f_c = lambda b: lref + self.l_gnfs(b) - self.l_gnfs(768) - lg(cores)
        f_q = lambda b: lg(c) + 3 * lg(b) + lg(top * 1e-6)
        lc, lq = f_c(bits), f_q(bits)
        out = ["Classical GNFS on %s cores: %s" % (fmt_pow(lg(cores)), fmt_time(lc)),
               "Shor (%s logical ops):  %s" % (fmt_pow(lg(c) + 3 * lg(bits)), fmt_time(lq)),
               winner_line(lc, lq), "",
               "Reference points (classical, same cores):"]
        for b in (512, 768, 1024, 2048, 4096):
            out.append("  %4d-bit: %s" % (b, fmt_time(f_c(b))))
        out.append("\nVerification is trivial: multiply the factors back together.")
        bs = [256 + (4096 - 256) * i / 60 for i in range(61)]
        series = [{"name": "classical GNFS", "color": COL_C, "pts": [(b, f_c(b)) for b in bs]},
                  {"name": "Shor", "color": COL_Q, "pts": [(b, f_q(b)) for b in bs]}]
        return "\n".join(out), series, "key size (bits)", False, [(bits, lq, "your key")]


class Pipeline(Panel):
    TITLE = "5 · End-to-end check"
    INFO = ("Generic check for ANY candidate: T_total = T_load + T_core + T_readout. "
            "Enter the quantum core's scaling as a power of log N (polylog) or of N, and "
            "pick how data enters and leaves. The slowest stage sets the total.")
    FIELDS = [("N", "Data size N", "1e8"),
              ("core_type", "Quantum core scaling", "polylog", ["polylog", "power of N"]),
              ("a", "Exponent a  [(log N)^a or N^a]", "3"),
              ("cl_exp", "Classical cost exponent b (N^b)", "1"),
              ("load", "Input", "oracle/structured", ["oracle/structured", "arbitrary data"]),
              ("outp", "Output", "few numbers", ["few numbers", "full state"]),
              ("eps", "Precision ε", "1e-3"),
              ("logr", "log10 overhead r", "7")]

    @staticmethod
    def model(N, ct, a, b, load, outp, eps, logr):
        core = (math.log2(N) ** a) if ct == "polylog" else N ** a
        ld = math.log2(N) if load.startswith("oracle") else N
        lreps = -lg(eps) if outp == "few numbers" else lg(N) - 2 * lg(eps)
        lq = -9 + logr + lreps + lg(core + ld)
        lc = -9 + b * lg(N)
        return lc, lq, core, ld, lreps

    def compute(self, v):
        N, a, b, eps, logr = (float(v[x]) for x in ("N", "a", "cl_exp", "eps", "logr"))
        lc, lq, core, ld, lreps = self.model(N, v["core_type"], a, b, v["load"], v["outp"], eps, logr)
        parts = {"loading": lg(ld) + lreps, "core": lg(core) + lreps}
        out = ["Classical (1 ns/op): %s" % fmt_time(lc),
               "Quantum total:       %s" % fmt_time(lq),
               winner_line(lc, lq), "",
               "Stage costs (quantum steps, incl. %s repetitions for readout):" % fmt_pow(lreps),
               "  loading ≈ %s" % fmt_pow(parts["loading"]),
               "  core    ≈ %s" % fmt_pow(parts["core"]),
               "Bottleneck: %s%s" % (max(parts, key=parts.get),
                                     " + readout" if v["outp"] == "full state" else "")]
        Ns = [10 ** (2 + 14 * i / 60) for i in range(61)]
        sc, sq = [], []
        for n in Ns:
            x, y, *_ = self.model(n, v["core_type"], a, b, v["load"], v["outp"], eps, logr)
            sc.append((n, x)); sq.append((n, y))
        series = [{"name": "classical", "color": COL_C, "pts": sc},
                  {"name": "quantum total", "color": COL_Q, "pts": sq}]
        return "\n".join(out), series, "data size N", True, [(N, lq, "your N")]


class About(Panel):
    TITLE = "6 · About: evidence & stages"
    INFO = ("EVIDENCE LEVELS\n"
            " • Rigorous: proven separation (often relative to an oracle or a standard assumption).\n"
            " • Restricted classical: beats a specific family of classical methods only.\n"
            " • Numerical/heuristic: simulations and extrapolations.\n\n"
            "MATURITY\n"
            " • Stage I: an advantage is plausible, but concrete hard instances are not yet identified.\n"
            " • Stage II: explicit instances that are expected to beat the best classical methods.\n"
            " • Next: show that those instances answer a useful question, with verifiable output.\n\n"
            "This app models the problem families the article describes in detail. The full "
            "list of 24 entries (number theory, optimization, statistical inference, quantum "
            "simulation, linear algebra, topological data analysis) is in the arXiv paper.\n\n"
            "All comparisons are against the best KNOWN classical algorithms, which can improve.")
    FIELDS = []

    def compute(self, v):
        return "", [], "", True, []


PANELS = [Crossover(), LinearSystems(), GroundState(), PlantedInference(),
          Factoring(), Pipeline(), About()]


# --------------------------------------------------------------------- GUI --
class App:
    def __init__(self, root):
        self.root = root
        root.title("Quantum Advantage Explorer")
        root.configure(bg=BG)
        try:
            import tkinter.font as tkfont
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
                tkfont.nametofont(name).configure(family=FAM, size=-PX)
        except Exception:
            pass
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Big.TButton", font=F(1.0, "bold"), padding=int(PX * 0.35))
        style.configure("Vertical.TScrollbar", arrowsize=int(PX * 1.1))
        self.wrap = SW - int(PX * 3.5)   # leave room for padding and scrollbar

        # top selector: no pop-up menus (they don't open in Pydroid on Android).
        # [<] [ current problem v ] [>]  - tapping the middle shows a button list.
        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=6, pady=(4, 2))
        self.choice = tk.StringVar(value=PANELS[0].TITLE)
        bkw = dict(font=F(1.0, "bold"), bg="#e8e4f8", activebackground="#d6cff5",
                   relief="raised", bd=2)
        tk.Button(top, text="<", width=2, command=lambda: self.step(-1), **bkw).pack(side="left")
        tk.Button(top, text=">", width=2, command=lambda: self.step(1), **bkw).pack(side="right")
        self.menu_btn = tk.Button(top, textvariable=self.choice, anchor="w",
                                  command=self.toggle_list, **bkw)
        self.menu_btn.pack(side="left", fill="x", expand=True, padx=4)

        self.listbox = tk.Frame(root, bg=BG)          # hidden until tapped
        for p in PANELS:
            tk.Button(self.listbox, text=p.TITLE, anchor="w", font=F(0.95),
                      bg="white", activebackground="#e8e4f8", relief="groove", bd=2,
                      command=lambda t=p.TITLE: self.pick(t)).pack(fill="x", padx=6, pady=2)
        self.list_open = False

        # scrollable body
        outer = tk.Frame(root, bg=BG)
        outer.pack(fill="both", expand=True)
        self.outer = outer
        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-int(e.delta / 120), "units"))
        self.show()

    def toggle_list(self):
        if self.list_open:
            self.listbox.pack_forget()
        else:
            self.listbox.pack(fill="x", before=self.outer, pady=(0, 4))
        self.list_open = not self.list_open

    def pick(self, title):
        self.choice.set(title)
        if self.list_open:
            self.toggle_list()
        self.show()

    def step(self, d):
        titles = [p.TITLE for p in PANELS]
        i = (titles.index(self.choice.get()) + d) % len(titles)
        self.pick(titles[i])

    def _on_resize(self, e):
        self.canvas.itemconfigure(self.win, width=e.width)
        self.wrap = max(e.width - int(PX * 1.2), 200)
        for w in getattr(self, "_wrapped", []):
            try:
                w.configure(wraplength=self.wrap)
            except Exception:
                pass

    def _drag(self, widget):
        """Let a finger drag on labels/frames scroll the page."""
        widget.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(0, e.y_root))
        widget.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(0, e.y_root, gain=1))

    def show(self):
        for w in self.body.winfo_children():
            w.destroy()
        panel = next(p for p in PANELS if p.TITLE == self.choice.get())
        self.panel = panel
        pad = int(PX * 0.4)
        self._wrapped = []

        t = tk.Label(self.body, text=panel.TITLE, bg=BG, font=F(1.15, "bold"),
                     justify="left", wraplength=self.wrap)
        t.pack(anchor="w", padx=pad, pady=(pad, 2))
        info = tk.Label(self.body, text=panel.INFO, bg=BG, fg="#444", justify="left",
                        font=F(0.78), wraplength=self.wrap)
        info.pack(anchor="w", padx=pad, pady=(0, pad))
        self._wrapped += [t, info]
        self._drag(t); self._drag(info); self._drag(self.body)

        self.vars = {}
        if not panel.FIELDS:
            self.canvas.yview_moveto(0)
            return

        form = tk.Frame(self.body, bg=BG)
        form.pack(fill="x", padx=pad)
        self._drag(form)
        for f in panel.FIELDS:
            key, label, default = f[0], f[1], f[2]
            lab = tk.Label(form, text=label, bg=BG, anchor="w", justify="left",
                           font=F(0.8), wraplength=self.wrap)
            lab.pack(fill="x", pady=(int(PX * 0.3), 0))
            self._wrapped.append(lab)
            self._drag(lab)
            var = tk.StringVar(value=default)
            if len(f) > 3:
                w = tk.Frame(form, bg=BG)
                for c in f[3]:
                    tk.Radiobutton(w, text=c, value=c, variable=var, indicatoron=0,
                                   font=F(0.85), bg="white", selectcolor="#cfc3ff",
                                   activebackground="#e8e4f8", bd=2, pady=int(PX * 0.25)
                                   ).pack(side="left", fill="x", expand=True)
            else:
                w = tk.Entry(form, textvariable=var, font=F(1.0))
            w.pack(fill="x")
            self.vars[key] = var

        btns = tk.Frame(self.body, bg=BG)
        btns.pack(fill="x", padx=pad, pady=pad)
        ttk.Button(btns, text="COMPUTE", style="Big.TButton",
                   command=self.run).pack(side="left", fill="x", expand=True)
        ttk.Button(btns, text="Reset", style="Big.TButton",
                   command=self.show).pack(side="left", padx=(pad, 0))

        tk.Label(self.body, text="Result", bg=BG, font=F(0.85, "bold")).pack(anchor="w", padx=pad)
        self.out = tk.Text(self.body, height=14, wrap="word", font=(MONO, -max(9, int(PX * 0.66))),
                           bg="white", relief="solid", bd=1, padx=6, pady=6)
        self.out.pack(fill="x", padx=pad, pady=(2, pad))
        tk.Label(self.body, text="Chart (time on a log scale)", bg=BG,
                 font=F(0.85, "bold")).pack(anchor="w", padx=pad)
        self.plot = Plot(self.body)
        self.plot.pack(fill="x", padx=pad, pady=(2, PX * 2))
        self.canvas.yview_moveto(0)
        self.root.after(200, self.run)

    def run(self):
        vals = {k: v.get().strip() for k, v in self.vars.items()}
        self.out.delete("1.0", "end")
        try:
            text, series, xlabel, xlog, marks = self.panel.compute(vals)
        except Exception as e:
            self.out.insert("end", "Input error: %s\n\nCheck that every field is a number "
                                   "(scientific notation like 1e9 is fine)." % e)
            self.plot.delete("all")
            return
        self.out.insert("end", text)
        lines = int(self.out.index("end-1c").split(".")[0])
        self.out.configure(height=max(6, min(lines + 1, 24)))
        self.plot.draw(series, xlabel, xlog, marks)


def main():
    global PX, SW
    root = tk.Tk()
    try:
        SW = root.winfo_screenwidth()
    except Exception:
        SW = 1080
    # ~34 characters of base text across a phone screen; cap for desktops
    PX = int(max(14, min(SW / 34.0, 26)) * UI_SCALE)
    if SW > 1400:                          # desktop: use a phone-like window
        SW = 900
        root.geometry("900x1000")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
