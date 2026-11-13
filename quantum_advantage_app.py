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
FONT_SIZE = 13          # raise to 16-18 if text looks tiny on your phone
FAM = "Helvetica"       # Tk substitutes the system font if missing
MONO = "Courier"
PLOT_HEIGHT = 330
COL_C = "#d9822b"       # classical
COL_Q = "#6d4bd8"       # quantum
COL_Q2 = "#9aa0a6"      # comparison line
COL_MARK = "#2f6fde"
BG = "#fbfaf7"


# ----------------------------------------------------------------- helpers --
def fmt_time(log10_sec):
    """Format a duration given as log10(seconds)."""
    if log10_sec is None or math.isnan(log10_sec):
        return "-"
    if log10_sec > 300:
        return "10^%.0f s (effectively forever)" % log10_sec
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
        return "QUANTUM faster by ~10^%.1f  (×%s)" % (d, fmt_pow(d))
    return "CLASSICAL faster by ~10^%.1f  (×%s)" % (-d, fmt_pow(-d))


# ------------------------------------------------------------------ plot ----
class Plot(tk.Canvas):
    """Tiny plotting widget. y values are always log10(seconds)."""

    def __init__(self, master, **kw):
        super().__init__(master, height=PLOT_HEIGHT, bg="white",
                         highlightthickness=1, highlightbackground="#ddd", **kw)
        self._last = None
        self.bind("<Configure>", lambda e: self._last and self.draw(*self._last))

    def draw(self, series, xlabel, xlog=True, marks=(), title=""):
        self._last = (series, xlabel, xlog, marks, title)
        self.delete("all")
        W = max(self.winfo_width(), 300)
        H = max(self.winfo_height(), 200)
        L, R, T, B = 62, 14, 30, 46
        pts = [p for s in series for p in s["pts"]
               if p[1] is not None and math.isfinite(p[1])]
        if not pts:
            return
        tx = (lambda x: lg(x)) if xlog else (lambda x: x)
        xs = [tx(p[0]) for p in pts]
        ys = [p[1] for p in pts]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        y0 = max(y0, y1 - 40)            # clip absurd ranges
        if y1 - y0 < 1:
            y1 += 0.5; y0 -= 0.5
        if x1 - x0 == 0:
            x1 += 1
        X = lambda x: L + (tx(x) - x0) / (x1 - x0) * (W - L - R)
        Y = lambda y: H - B - (min(max(y, y0), y1) - y0) / (y1 - y0) * (H - T - B)
        f = (FAM, max(FONT_SIZE - 3, 8))

        # y grid: nice time ticks
        ticks = [(-9, "1ns"), (-6, "1µs"), (-3, "1ms"), (0, "1s"),
                 (lg(3600), "1h"), (lg(86400), "1d"), (lg(3.156e7), "1yr"),
                 (lg(3.156e10), "1kyr"), (lg(3.156e13), "1Myr"),
                 (lg(4.3e17), "age of\nuniverse")]
        ytk = [(y, l) for y, l in ticks if y0 <= y <= y1]
        if len(ytk) < 3:
            step = max(1, round((y1 - y0) / 6))
            ytk = [(v, "1e%d s" % v) for v in range(math.ceil(y0), int(y1) + 1, step)]
        for y, l in ytk:
            self.create_line(L, Y(y), W - R, Y(y), fill="#eee")
            self.create_text(L - 4, Y(y), text=l, anchor="e", font=f)
        # x grid
        n = 5
        for i in range(n + 1):
            xv = x0 + (x1 - x0) * i / n
            xp = L + (xv - x0) / (x1 - x0) * (W - L - R)
            self.create_line(xp, T, xp, H - B, fill="#eee")
            lab = ("1e%.1f" % xv).replace(".0", "") if xlog else "%.4g" % xv
            self.create_text(xp, H - B + 12, text=lab, font=f)
        self.create_text((L + W - R) / 2, H - 12, text=xlabel, font=f)
        self.create_text(L, 12, text=title or "runtime (log scale)", anchor="w", font=f)
        self.create_rectangle(L, T, W - R, H - B, outline="#bbb")

        # series
        ly = T + 6
        for s in series:
            coords = []
            for x, y in s["pts"]:
                if y is None or not math.isfinite(y):
                    continue
                coords += [X(x), Y(y)]
            if len(coords) >= 4:
                self.create_line(*coords, fill=s["color"], width=3,
                                 dash=s.get("dash", ()))
            self.create_line(W - R - 150, ly + 6, W - R - 128, ly + 6,
                             fill=s["color"], width=3, dash=s.get("dash", ()))
            self.create_text(W - R - 124, ly + 6, text=s["name"], anchor="w", font=f)
            ly += 18
        for (mx, my, ml) in marks:
            if my is None or not (y0 <= my <= y1) or not math.isfinite(my):
                continue
            px, py = X(mx), Y(my)
            if L <= px <= W - R:
                self.create_oval(px - 6, py - 6, px + 6, py + 6, fill=COL_MARK, outline="")
                self.create_text(px + 9, py - 10, text=ml, anchor="w", font=f, fill=COL_MARK)


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
    TITLE = "0. Crossover: why > quadratic"
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
               "Break-even M* = r^(k/(k-1)) = %s classical steps" % fmt_pow(lM),
               "Break-even wall-clock time  T* = %s" % fmt_time(lT),
               "Quantum wins only for problems LARGER than this.", "",
               "Same overhead, other speedup degrees:"]
        for kk in (2, 3, 4, 6, 10):
            m = log_reff * kk / (kk - 1)
            out.append("  k=%-3d  M*=%-14s T*=%s" % (kk, fmt_pow(m), fmt_time(log_cc + m)))
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
    TITLE = "1. Linear systems Ax = b"
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
    TITLE = "2. Molecular ground-state energy"
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
    TITLE = "3. Patterns in noise (tensor PCA / k-XOR)"
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
    TITLE = "4. Factoring (number theory)"
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
    TITLE = "5. End-to-end pipeline check"
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
    TITLE = "6. About: evidence & stages"
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
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont"):
            try:
                import tkinter.font as tkfont
                tkfont.nametofont(name).configure(size=FONT_SIZE)
            except Exception:
                pass
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Big.TButton", font=(FAM, FONT_SIZE + 1, "bold"), padding=8)

        # top selector
        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=6, pady=4)
        tk.Label(top, text="Problem:", bg=BG).pack(side="left")
        self.choice = tk.StringVar(value=PANELS[0].TITLE)
        om = tk.OptionMenu(top, self.choice, *[p.TITLE for p in PANELS],
                           command=lambda _=None: self.show())
        om.config(font=(FAM, FONT_SIZE))
        om["menu"].config(font=(FAM, FONT_SIZE))
        om.pack(side="left", fill="x", expand=True)

        # scrollable body
        outer = tk.Frame(root, bg=BG)
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        # touch / mouse drag scrolling on empty areas
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(0, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(0, e.y, gain=1))
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-int(e.delta / 120), "units"))
        self.show()

    def show(self):
        for w in self.body.winfo_children():
            w.destroy()
        panel = next(p for p in PANELS if p.TITLE == self.choice.get())
        self.panel = panel
        wrap = max(min(self.root.winfo_screenwidth(), 900) - 60, 300)

        tk.Label(self.body, text=panel.TITLE, bg=BG,
                 font=(FAM, FONT_SIZE + 3, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        tk.Label(self.body, text=panel.INFO, bg=BG, fg="#444", justify="left",
                 wraplength=wrap).pack(anchor="w", padx=8, pady=(0, 6))

        self.vars = {}
        if panel.FIELDS:
            form = tk.Frame(self.body, bg=BG)
            form.pack(fill="x", padx=8)
            form.columnconfigure(1, weight=1)
            for r, f in enumerate(panel.FIELDS):
                key, label, default = f[0], f[1], f[2]
                tk.Label(form, text=label, bg=BG, anchor="w", justify="left",
                         wraplength=int(wrap * 0.55)).grid(row=r, column=0, sticky="w", pady=3)
                var = tk.StringVar(value=default)
                if len(f) > 3:
                    w = tk.OptionMenu(form, var, *f[3])
                    w.config(font=(FAM, FONT_SIZE))
                    w["menu"].config(font=(FAM, FONT_SIZE))
                else:
                    w = tk.Entry(form, textvariable=var, font=(FAM, FONT_SIZE + 1), width=12)
                w.grid(row=r, column=1, sticky="ew", padx=(6, 0), pady=3)
                self.vars[key] = var

            btns = tk.Frame(self.body, bg=BG)
            btns.pack(fill="x", padx=8, pady=6)
            ttk.Button(btns, text="COMPUTE", style="Big.TButton",
                       command=self.run).pack(side="left", fill="x", expand=True)
            ttk.Button(btns, text="Reset", style="Big.TButton",
                       command=self.show).pack(side="left", padx=(6, 0))

            self.out = tk.Text(self.body, height=13, wrap="word", font=(MONO, FONT_SIZE - 1),
                               bg="white", relief="solid", bd=1)
            self.out.pack(fill="x", padx=8, pady=4)
            self.plot = Plot(self.body)
            self.plot.pack(fill="x", padx=8, pady=(4, 20))
            self.root.after(150, self.run)
        self.canvas.yview_moveto(0)

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
        self.plot.draw(series, xlabel, xlog, marks)


def main():
    root = tk.Tk()
    try:
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d+0+0" % (min(sw, 900), min(sh, 1800)))
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
