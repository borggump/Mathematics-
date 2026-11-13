# -*- coding: utf-8 -*-
"""
Analog In-Memory FFT Simulator  (for Pydroid 3 on Android, also runs on desktop)
=============================================================================

Simulates the method described in Xiao et al., "Analogue fast Fourier transforms
for scalable and efficient signal processing", Nature Electronics (2026):

  * A large N-point DFT is split as N = N1 x N2 (Cooley-Tukey, one level).
  * Stage 1: N2 small N1-point DFTs, each one matrix-vector multiply (MVM)
    on an analog memory array that stores the N1-point DFT matrix.
  * Twiddle: N element-wise complex multiplies, done digitally.
  * Stage 2: N1 small N2-point DFTs, again on the analog array.

Analog non-idealities that are modelled (simplified):
  * conductance programming error (static, per cell, relative %)
  * read noise (per read, % of the output full scale)
  * DAC input quantisation and ADC output quantisation (bits, 0 = ideal)

Complex weights -> real block [[A,-B],[B,A]]  (2M x 2M)
Signed weights  -> differential pair G+ / G-  (2M x 4M physical cells)
For M = 256 this is the 512 x 1024 block mentioned in the article.

Pydroid 3: open this file and press the Run button. Tkinter is built in.
Optional but recommended: Menu -> Pip -> install "numpy" (much faster,
needed for the 65,536-point article case in reasonable time).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math
import cmath
import random
import threading
import time
import traceback
from operator import mul

try:
    import numpy as np
    HAVE_NP = True
except Exception:
    np = None
    HAVE_NP = False

SIZES = ["4", "8", "16", "32", "64", "128", "256"]
SIGNALS = ["Sum of sines", "Square wave", "Chirp", "Impulse",
           "Random noise", "Custom values"]

COL_EXACT = "#9ca3af"
COL_ANALOG = "#0f766e"
COL_IDEAL = "#b45309"
COL_SIGNAL = "#2563eb"


# ---------------------------------------------------------------------------
#  Signal generation
# ---------------------------------------------------------------------------
def make_signal(p):
    N = p["N"]
    kind = p["kind"]
    fr = p["freqs"]
    am = p["amps"]
    a0 = am[0] if am else 1.0
    rnd = random.Random(p["seed"] + 12345)
    x = [0.0] * N

    if kind == "Sum of sines":
        for i, f in enumerate(fr):
            a = am[i] if i < len(am) else 1.0
            w = 2 * math.pi * f / N
            for n in range(N):
                x[n] += a * math.sin(w * n)
    elif kind == "Square wave":
        f = fr[0] if fr else 10.0
        for n in range(N):
            x[n] = a0 if math.sin(2 * math.pi * f * n / N) >= 0 else -a0
    elif kind == "Chirp":
        f0 = fr[0] if fr else 0.0
        f1 = fr[1] if len(fr) > 1 else N / 4.0
        for n in range(N):
            t = n / N
            x[n] = a0 * math.sin(2 * math.pi * (f0 * t + 0.5 * (f1 - f0) * t * t))
    elif kind == "Impulse":
        n0 = int(fr[0]) % N if fr else 0
        x[n0] = a0
    elif kind == "Random noise":
        for n in range(N):
            x[n] = a0 * rnd.gauss(0, 1)
    elif kind == "Custom values":
        vals = p["custom"] or [0.0]
        for n in range(N):
            x[n] = vals[n % len(vals)]

    if p["noise"] > 0:
        for n in range(N):
            x[n] += p["noise"] * rnd.gauss(0, 1)
    if p["window"] == "Hann":
        for n in range(N):
            x[n] *= 0.5 - 0.5 * math.cos(2 * math.pi * n / N)
    return x


# ---------------------------------------------------------------------------
#  Exact reference FFT (pure Python radix-2)
# ---------------------------------------------------------------------------
def fft_pure(x):
    a = [complex(v) for v in x]
    n = len(a)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    length = 2
    while length <= n:
        half = length // 2
        tw = [cmath.exp(-2j * math.pi * k / length) for k in range(half)]
        for s in range(0, n, length):
            for k in range(half):
                u = a[s + k]
                v = a[s + k + half] * tw[k]
                a[s + k] = u + v
                a[s + k + half] = u - v
        length <<= 1
    return a


# ---------------------------------------------------------------------------
#  Analog array model: pure Python backend
# ---------------------------------------------------------------------------
def build_array_pure(M, prog, rnd):
    """Return (Weff, Gp, Gm) as lists of rows. Weff is 2M x 2M real."""
    Weff, Gp, Gm = [], [], []
    for r in range(2 * M):
        k = r % M
        rowp, rowm = [], []
        for c in range(2 * M):
            n = c % M
            ang = 2 * math.pi * ((k * n) % M) / M
            a = math.cos(ang)
            b = -math.sin(ang)
            if r < M:
                w = a if c < M else -b
            else:
                w = b if c < M else a
            gp = max(w, 0.0)
            gm = max(-w, 0.0)
            if prog > 0:
                gp = max(0.0, gp * (1 + prog * rnd.gauss(0, 1)))
                gm = max(0.0, gm * (1 + prog * rnd.gauss(0, 1)))
            rowp.append(gp)
            rowm.append(gm)
        Gp.append(rowp)
        Gm.append(rowm)
        Weff.append([p - m for p, m in zip(rowp, rowm)])
    return Weff, Gp, Gm


def mvm_pure(W, vecs, cfg, rnd):
    read, adc, dac = cfg
    Ld = 2 ** (dac - 1) - 1 if dac else 0
    La = 2 ** (adc - 1) - 1 if adc else 0
    out = []
    for v in vecs:
        vmax = max(abs(a) for a in v) or 1.0
        u = [a / vmax for a in v]
        if dac:
            u = [round(a * Ld) / Ld for a in u]
        y = [sum(map(mul, row, u)) for row in W]
        fs = max(abs(a) for a in y) or 1.0
        if read > 0:
            y = [a + read * fs * rnd.gauss(0, 1) for a in y]
        if adc:
            y = [max(-La, min(La, round(a / fs * La))) * fs / La for a in y]
        out.append([a * vmax for a in y])
    return out


def pipeline_pure(x, N1, N2, W1, W2, cfg, rnd, times):
    N = N1 * N2
    t0 = time.perf_counter()
    vecs = []
    for n2 in range(N2):
        col = [x[N2 * n1 + n2] for n1 in range(N1)]
        vecs.append([c.real for c in col] + [c.imag for c in col])
    out1 = mvm_pure(W1, vecs, cfg, rnd)
    t1 = time.perf_counter()

    Z = [[0j] * N2 for _ in range(N1)]
    for n2 in range(N2):
        o = out1[n2]
        for k1 in range(N1):
            y = complex(o[k1], o[N1 + k1])
            Z[k1][n2] = y * cmath.exp(-2j * math.pi * ((k1 * n2) % N) / N)
    t2 = time.perf_counter()

    vecs2 = [[z.real for z in Z[k1]] + [z.imag for z in Z[k1]] for k1 in range(N1)]
    out2 = mvm_pure(W2, vecs2, cfg, rnd)
    X = [0j] * N
    for k1 in range(N1):
        o = out2[k1]
        for k2 in range(N2):
            X[k1 + N1 * k2] = complex(o[k2], o[N2 + k2])
    t3 = time.perf_counter()
    if times is not None:
        times["stage1"] = t1 - t0
        times["twiddle"] = t2 - t1
        times["stage2"] = t3 - t2
    return X


# ---------------------------------------------------------------------------
#  Analog array model: numpy backend
# ---------------------------------------------------------------------------
def build_array_np(M, prog, rng):
    k = np.arange(M)[:, None]
    n = np.arange(M)[None, :]
    ang = 2 * np.pi * ((k * n) % M) / M
    A = np.cos(ang)
    B = -np.sin(ang)
    W = np.block([[A, -B], [B, A]])
    Gp = np.maximum(W, 0.0)
    Gm = np.maximum(-W, 0.0)
    if prog > 0:
        Gp = np.clip(Gp * (1 + prog * rng.standard_normal(W.shape)), 0, None)
        Gm = np.clip(Gm * (1 + prog * rng.standard_normal(W.shape)), 0, None)
    return Gp - Gm, Gp, Gm


def mvm_np(W, U, cfg, rng):
    """U: (2M, K) real, columns are input vectors."""
    read, adc, dac = cfg
    vmax = np.max(np.abs(U), axis=0)
    vmax[vmax == 0] = 1.0
    u = U / vmax
    if dac:
        Ld = 2 ** (dac - 1) - 1
        u = np.round(u * Ld) / Ld
    Y = W @ u
    fs = np.max(np.abs(Y), axis=0)
    fs[fs == 0] = 1.0
    if read > 0:
        Y = Y + read * fs * rng.standard_normal(Y.shape)
    if adc:
        La = 2 ** (adc - 1) - 1
        Y = np.clip(np.round(Y / fs * La), -La, La) * fs / La
    return Y * vmax


def pipeline_np(x, N1, N2, W1, W2, cfg, rng, times):
    N = N1 * N2
    t0 = time.perf_counter()
    V = x.reshape(N1, N2)                       # V[n1, n2] = x[N2*n1 + n2]
    Yr = mvm_np(W1, np.vstack([V.real, V.imag]), cfg, rng)
    Y = Yr[:N1] + 1j * Yr[N1:]                  # Y[k1, n2]
    t1 = time.perf_counter()
    k1 = np.arange(N1)[:, None]
    n2 = np.arange(N2)[None, :]
    Z = Y * np.exp(-2j * np.pi * ((k1 * n2) % N) / N)
    t2 = time.perf_counter()
    ZT = Z.T                                    # (N2, N1): column k1 = row k1 of Z
    Xr = mvm_np(W2, np.vstack([ZT.real, ZT.imag]), cfg, rng)
    Xs = Xr[:N2] + 1j * Xr[N2:]                 # Xs[k2, k1]
    X = Xs.reshape(-1)                          # index k2*N1 + k1
    t3 = time.perf_counter()
    if times is not None:
        times["stage1"] = t1 - t0
        times["twiddle"] = t2 - t1
        times["stage2"] = t3 - t2
    return X


# ---------------------------------------------------------------------------
#  Full simulation
# ---------------------------------------------------------------------------
def simulate(p):
    N1, N2 = p["N1"], p["N2"]
    N = N1 * N2
    p["N"] = N
    cfg = (p["read"], p["adc"], p["dac"])
    ideal_cfg = (0.0, 0, 0)
    use_np = HAVE_NP and p["use_np"]
    times = {}

    x = make_signal(p)

    t = time.perf_counter()
    if use_np:
        rng = np.random.default_rng(p["seed"])
        W1, Gp, Gm = build_array_np(N1, p["prog"], rng)
        W2 = W1 if N2 == N1 else build_array_np(N2, p["prog"], rng)[0]
    else:
        rnd = random.Random(p["seed"])
        W1, Gp, Gm = build_array_pure(N1, p["prog"], rnd)
        W2 = W1 if N2 == N1 else build_array_pure(N2, p["prog"], rnd)[0]
    times["program"] = time.perf_counter() - t

    t = time.perf_counter()
    if use_np:
        xa = np.asarray(x, dtype=complex)
        Xref = np.fft.fft(xa).tolist()
    else:
        xa = [complex(v) for v in x]
        Xref = fft_pure(xa)
    times["reference"] = time.perf_counter() - t

    if use_np:
        X = pipeline_np(xa, N1, N2, W1, W2, cfg, rng, times).tolist()
    else:
        X = pipeline_pure(xa, N1, N2, W1, W2, cfg, rnd, times)

    Xideal = None
    if p["verify"]:
        if use_np:
            I1 = build_array_np(N1, 0.0, rng)[0]
            I2 = I1 if N2 == N1 else build_array_np(N2, 0.0, rng)[0]
            Xideal = pipeline_np(xa, N1, N2, I1, I2, ideal_cfg, rng, None).tolist()
        else:
            I1 = build_array_pure(N1, 0.0, rnd)[0]
            I2 = I1 if N2 == N1 else build_array_pure(N2, 0.0, rnd)[0]
            Xideal = pipeline_pure(xa, N1, N2, I1, I2, ideal_cfg, rnd, None)

    if use_np:
        Gp = Gp.tolist()
        Gm = Gm.tolist()

    return dict(p=p, x=x, X=X, Xref=Xref, Xideal=Xideal, Gp=Gp, Gm=Gm,
                times=times, backend="numpy" if use_np else "pure Python")


def error_metrics(X, Xref):
    sig = sum(abs(v) ** 2 for v in Xref)
    err = [abs(a - b) for a, b in zip(X, Xref)]
    en = sum(e * e for e in err)
    peak = max(abs(v) for v in Xref) or 1.0
    snr = 10 * math.log10(sig / en) if en > 0 else float("inf")
    return snr, max(err), max(err) / peak


def find_peaks(Xref, count=5):
    N = len(Xref)
    half = N // 2 + 1
    mags = [abs(Xref[k]) for k in range(half)]
    order = sorted(range(half), key=lambda k: -mags[k])
    picked = []
    for k in order:
        if all(abs(k - q) > 2 for q in picked):
            picked.append(k)
        if len(picked) >= count:
            break
    return sorted(picked)


# ---------------------------------------------------------------------------
#  Plot widget (pure Tk canvas)
# ---------------------------------------------------------------------------
def nice_ticks(lo, hi, n=5):
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = mag
    for m in (1, 2, 5, 10):
        step = m * mag
        if span / step <= n:
            break
    t = math.ceil(lo / step) * step
    out = []
    while t <= hi + 1e-9 * step:
        out.append(round(t, 10))
        t += step
    return out


class Plot(tk.Canvas):
    def __init__(self, master, height=260, **kw):
        tk.Canvas.__init__(self, master, height=height, bg="white",
                           highlightthickness=0, **kw)
        self.data = None
        self.bind("<Configure>", lambda e: self.redraw())

    def set(self, series, title="", xlabel="", ylabel="", xlim=None, ylim=None):
        self.data = (series, title, xlabel, ylabel, xlim, ylim)
        self.redraw()

    def redraw(self):
        self.delete("all")
        W = self.winfo_width()
        H = self.winfo_height()
        if W < 80 or H < 80:
            return
        if not self.data:
            self.create_text(W / 2, H / 2, text="Press  ▶ Run", fill="#9ca3af",
                             font=("Helvetica", 14))
            return
        series, title, xlabel, ylabel, xlim, ylim = self.data
        ml, mr, mt, mb = 62, 14, 30, 42
        pw, ph = W - ml - mr, H - mt - mb

        allx = [v for s in series for v in (s[0][0], s[0][-1])] if series else [0, 1]
        xmin, xmax = xlim if xlim else (min(allx), max(allx))
        if xmax <= xmin:
            xmax = xmin + 1
        if ylim:
            ymin, ymax = ylim
        else:
            ys = [y for s in series for x, y in zip(s[0], s[1]) if xmin <= x <= xmax]
            ymin, ymax = (min(ys), max(ys)) if ys else (0, 1)
            pad = 0.05 * (ymax - ymin or 1)
            ymin, ymax = ymin - pad, ymax + pad

        def px(x):
            return ml + (x - xmin) / (xmax - xmin) * pw

        def py(y):
            y = min(max(y, ymin), ymax)
            return mt + (ymax - y) / (ymax - ymin) * ph

        f = ("Helvetica", 9)
        for t in nice_ticks(ymin, ymax, 5):
            yy = py(t)
            self.create_line(ml, yy, ml + pw, yy, fill="#eef0f3")
            self.create_text(ml - 5, yy, text="%g" % t, anchor="e", font=f, fill="#5b6370")
        for t in nice_ticks(xmin, xmax, 5):
            xx = px(t)
            self.create_line(xx, mt, xx, mt + ph, fill="#eef0f3")
            self.create_text(xx, mt + ph + 4, text="%g" % t, anchor="n", font=f, fill="#5b6370")
        self.create_rectangle(ml, mt, ml + pw, mt + ph, outline="#c4c9d0")
        self.create_text(ml, 14, text=title, anchor="w", font=("Helvetica", 11, "bold"))
        self.create_text(ml + pw / 2, H - 10, text=xlabel, font=f, fill="#5b6370")
        self.create_text(12, mt + ph / 2, text=ylabel, angle=90, font=f, fill="#5b6370")

        for xs, ys, color, label in series:
            buckets = {}
            for x, y in zip(xs, ys):
                if x < xmin or x > xmax:
                    continue
                c = int(px(x))
                b = buckets.get(c)
                if b is None:
                    buckets[c] = [y, y]
                else:
                    if y < b[0]:
                        b[0] = y
                    if y > b[1]:
                        b[1] = y
            pts = []
            for c in sorted(buckets):
                lo, hi = buckets[c]
                pts += [c, py(lo)]
                if hi != lo:
                    pts += [c, py(hi)]
            if len(pts) >= 4:
                self.create_line(*pts, fill=color, width=1.5)
            elif len(pts) == 2:
                self.create_oval(pts[0] - 2, pts[1] - 2, pts[0] + 2, pts[1] + 2,
                                 fill=color, outline=color)

        lx = ml + pw - 8
        ly = mt + 10
        for xs, ys, color, label in series:
            if not label:
                continue
            self.create_text(lx, ly, text=label, anchor="e", font=f)
            tw = 7 * len(label)
            self.create_line(lx - tw - 22, ly, lx - tw - 6, ly, fill=color, width=3)
            ly += 15


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------
class ScrollFrame(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=28)
        self.inner = ttk.Frame(self.canvas)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.win, width=e.width))


def text_box(master, mono=True):
    fr = ttk.Frame(master)
    txt = tk.Text(fr, wrap="word", font=("Courier", 10) if mono else ("Helvetica", 11),
                  padx=8, pady=8, relief="flat")
    sb = tk.Scrollbar(fr, command=txt.yview, width=28)
    txt.configure(yscrollcommand=sb.set)
    txt.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return fr, txt


def set_text(txt, s):
    txt.configure(state="normal")
    txt.delete("1.0", "end")
    txt.insert("1.0", s)
    txt.configure(state="disabled")


def parse_list(s):
    s = s.replace(";", ",").replace(" ", ",")
    return [float(v) for v in s.split(",") if v.strip()]


def make_palette():
    stops = [(11, 29, 42), (15, 118, 110), (253, 224, 71)]
    pal = []
    for i in range(256):
        t = i / 255 * 2
        j = min(int(t), 1)
        f = t - j
        c = [int(stops[j][q] + (stops[j + 1][q] - stops[j][q]) * f) for q in range(3)]
        pal.append("#%02x%02x%02x" % tuple(c))
    return pal


PALETTE = make_palette()

MATH_TEXT = u"""HOW THE ANALOG FFT WORKS
========================

1) The DFT
   X[k] = Σ_{n=0}^{N-1} x[n] · W_N^{nk},   W_N = e^{-j2π/N}
   As a matrix: X = F_N · x  (N×N matrix -> N² multiplies).

2) Cooley-Tukey split, N = N1 · N2
   n = N2·n1 + n2      k = k1 + N1·k2
   Using W_N^N = 1:
     W_N^{(N2 n1)(k1+N1 k2)} = W_N1^{n1 k1}
     W_N^{n2 (N1 k2)}        = W_N2^{n2 k2}
   leaving one cross term W_N^{n2 k1} (the twiddle).

   Stage 1 (analog):  Y[k1,n2] = Σ_n1 x[N2 n1 + n2] · W_N1^{n1 k1}
   Twiddle (digital): Z[k1,n2] = W_N^{n2 k1} · Y[k1,n2]
   Stage 2 (analog):  X[k1 + N1 k2] = Σ_n2 Z[k1,n2] · W_N2^{n2 k2}

   In practice: reshape x into an N1×N2 grid, DFT every column,
   multiply by twiddles, DFT every row, read out in k1 + N1·k2 order.

3) Matrix-vector multiply as physics
   Each cell stores a conductance G_ij. Input voltages v_j drive the
   columns; Kirchhoff's current law sums the row currents:
     i_i = Σ_j G_ij · v_j     (one read = one whole MVM)

4) Complex numbers
   (A + jB)(p + jq) = (Ap − Bq) + j(Bp + Aq)
   [p'; q'] = [[A, −B], [B, A]] · [p; q]     (M×M complex -> 2M×2M real)

5) Negative numbers
   w = G+ − G−  (differential pair), so 2M×2M -> 2M × 4M cells.
   For M = 256: 512 × 1024 = 524,288 cells, consistent with the
   "512 × 1,024 block" and "more than half a million devices" in the
   article (this encoding is an inference, not stated in the article).

6) Cost (N = 65,536 = 256 × 256)
   Direct DFT:        N²          ≈ 4.3 × 10⁹ complex MACs
   Two-stage analog:  N(N1+N2)    ≈ 3.4 × 10⁷ complex MACs, done as
                      N1 + N2 = 512 parallel array reads
   Twiddle:           N = 65,536 digital complex multiplies
   Radix-2 digital:   (N/2) log2 N = 524,288 butterflies

7) Error model used in this app (simplified)
   • Programming error: each cell G -> G·(1 + σ_prog·ε), fixed per run.
   • DAC: inputs scaled to ±1 per vector and rounded to b bits.
   • Read noise: + σ_read · (full scale) · ε on every output.
   • ADC: outputs rounded to b bits over an auto-ranged full scale.
   Errors from stage 1 are mixed by the stage-2 DFT, so they spread
   across all frequency bins: that is the noise floor you see on the
   Spectrum tab. The "ideal" curve (all errors = 0) checks that the
   split itself is exact (error ~1e-13, i.e. floating-point rounding).

Times shown are simulation times on this device, not chip timings.
"""


# ---------------------------------------------------------------------------
#  Application
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Analog In-Memory FFT Simulator")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", font=("Helvetica", 12))
        style.configure("TNotebook.Tab", padding=(10, 6))
        style.configure("Run.TButton", font=("Helvetica", 13, "bold"), padding=8)
        style.configure("Head.TLabel", font=("Helvetica", 12, "bold"), foreground="#0f766e")

        self.result = None
        self.worker_out = None
        self.zoom = None

        top = ttk.Frame(root)
        top.pack(fill="x", padx=6, pady=4)
        self.run_btn = ttk.Button(top, text="▶ Run", style="Run.TButton", command=self.run)
        self.run_btn.pack(side="left")
        self.status = tk.StringVar(value="numpy: %s" % ("yes" if HAVE_NP else
                                                         "no (pure Python, slower)"))
        ttk.Label(top, textvariable=self.status, wraplength=600).pack(side="left", padx=10)

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        self.build_input_tab()
        self.build_results_tab()
        self.build_signal_tab()
        self.build_spectrum_tab()
        self.build_array_tab()
        fr, txt = text_box(self.nb, mono=True)
        set_text(txt, MATH_TEXT)
        self.nb.add(fr, text="Math")

    # ---------------- input tab ----------------
    def build_input_tab(self):
        sf = ScrollFrame(self.nb)
        self.nb.add(sf, text="Input")
        f = sf.inner
        f.columnconfigure(1, weight=1)
        self.row = 0

        def head(text):
            ttk.Label(f, text=text, style="Head.TLabel").grid(
                row=self.row, column=0, columnspan=2, sticky="w", padx=8, pady=(14, 4))
            self.row += 1

        def add(label, widget):
            ttk.Label(f, text=label).grid(row=self.row, column=0, sticky="w", padx=8, pady=4)
            widget.grid(row=self.row, column=1, sticky="ew", padx=8, pady=4)
            self.row += 1

        def entry(default):
            v = tk.StringVar(value=default)
            return v, ttk.Entry(f, textvariable=v)

        def combo(values, default):
            v = tk.StringVar(value=default)
            return v, ttk.Combobox(f, textvariable=v, values=values, state="readonly")

        head("Signal")
        self.v_kind, w = combo(SIGNALS, "Sum of sines"); add("Type", w)
        self.v_freqs, w = entry("37, 120.5, 300"); add("Freqs (cycles/frame)", w)
        self.v_amps, w = entry("1, 0.3, 0.05"); add("Amplitudes", w)
        self.v_custom, w = entry("1, 0.5, 0, -0.5, -1, -0.5, 0, 0.5"); add("Custom values", w)
        self.v_noise, w = entry("0"); add("Added noise (std)", w)
        self.v_window, w = combo(["None", "Hann"], "None"); add("Window", w)
        ttk.Label(f, foreground="#5b6370", wraplength=520, text=(
            "Chirp uses freqs as start, end. Square/Impulse use the first freq "
            "(impulse: sample index). Custom values repeat to fill N.")).grid(
            row=self.row, column=0, columnspan=2, sticky="w", padx=8)
        self.row += 1

        head("FFT split  N = N1 × N2")
        self.v_n1, w = combo(SIZES, "32"); add("N1 (array DFT size)", w)
        self.v_n2, w = combo(SIZES, "32"); add("N2", w)
        self.n_label = ttk.Label(f, text="")
        self.n_label.grid(row=self.row, column=0, columnspan=2, sticky="w", padx=8)
        self.row += 1
        self.v_n1.trace_add("write", lambda *a: self.update_n())
        self.v_n2.trace_add("write", lambda *a: self.update_n())

        head("Analog non-idealities")
        self.v_prog, w = entry("1.0"); add("Programming error (%)", w)
        self.v_read, w = entry("0.5"); add("Read noise (% FS)", w)
        self.v_adc, w = entry("8"); add("ADC bits (0 = ideal)", w)
        self.v_dac, w = entry("8"); add("DAC bits (0 = ideal)", w)
        self.v_seed, w = entry("1"); add("Random seed", w)

        head("Options")
        self.v_verify = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Also run ideal (error-free) split as a check",
                        variable=self.v_verify).grid(row=self.row, column=0, columnspan=2,
                                                     sticky="w", padx=8)
        self.row += 1
        self.v_usenp = tk.BooleanVar(value=HAVE_NP)
        cb = ttk.Checkbutton(f, text="Use numpy backend", variable=self.v_usenp)
        if not HAVE_NP:
            cb.state(["disabled"])
        cb.grid(row=self.row, column=0, columnspan=2, sticky="w", padx=8)
        self.row += 1

        head("Presets")
        pf = ttk.Frame(f)
        pf.grid(row=self.row, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.row += 1
        ttk.Button(pf, text="Quick demo 32×32",
                   command=lambda: self.preset(32, 32, 1.0, 0.5, 8, 8)).pack(fill="x", pady=2)
        ttk.Button(pf, text="Article case 256×256 = 65,536",
                   command=lambda: self.preset(256, 256, 1.0, 0.5, 8, 8)).pack(fill="x", pady=2)
        ttk.Button(pf, text="Ideal hardware (no errors)",
                   command=lambda: self.preset(None, None, 0, 0, 0, 0)).pack(fill="x", pady=2)
        ttk.Button(pf, text="Noisy hardware (5%, 6-bit)",
                   command=lambda: self.preset(None, None, 5.0, 2.0, 6, 6)).pack(fill="x", pady=2)
        ttk.Label(f, text=" ").grid(row=self.row, column=0, pady=20)
        self.update_n()

    def update_n(self):
        try:
            n1, n2 = int(self.v_n1.get()), int(self.v_n2.get())
        except ValueError:
            return
        N = n1 * n2
        cells = (2 * n1) * (4 * n1)
        self.n_label.configure(text="N = %d points   |   array: %d × %d = %s cells"
                               % (N, 2 * n1, 4 * n1, format(cells, ",")))

    def preset(self, n1, n2, prog, read, adc, dac):
        if n1:
            self.v_n1.set(str(n1))
            self.v_n2.set(str(n2))
        self.v_prog.set(str(prog))
        self.v_read.set(str(read))
        self.v_adc.set(str(adc))
        self.v_dac.set(str(dac))
        if n1 == 256:
            self.v_freqs.set("1000, 5000.5, 12000")
            self.v_amps.set("1, 0.3, 0.05")

    # ---------------- results tab ----------------
    def build_results_tab(self):
        fr = ttk.Frame(self.nb)
        self.nb.add(fr, text="Results")
        self.pipe = tk.Canvas(fr, height=200, bg="white", highlightthickness=0)
        self.pipe.pack(fill="x")
        self.pipe.bind("<Configure>", lambda e: self.draw_pipeline())
        tf, self.res_txt = text_box(fr)
        tf.pack(fill="both", expand=True)
        set_text(self.res_txt, "Set inputs on the Input tab, then press ▶ Run.")

    def draw_pipeline(self):
        c = self.pipe
        c.delete("all")
        W = c.winfo_width()
        if W < 100:
            return
        r = self.result
        if r:
            n1, n2 = r["p"]["N1"], r["p"]["N2"]
            t = r["times"]
            ms = lambda s: "%.0f ms" % (1000 * s)
            info = [("Input x[n]", "%d samples" % (n1 * n2), "#f1f3f6", "#5b6370"),
                    ("Reshape", "%d × %d grid" % (n1, n2), "#fef3c7", "#b45309"),
                    ("Stage 1 ANALOG", "%d MVMs  %s" % (n2, ms(t["stage1"])), "#ccfbf1", "#0f766e"),
                    ("Twiddle DIGITAL", "%d mults  %s" % (n1 * n2, ms(t["twiddle"])), "#fef3c7", "#b45309"),
                    ("Stage 2 ANALOG", "%d MVMs  %s" % (n1, ms(t["stage2"])), "#ccfbf1", "#0f766e"),
                    ("Output X[k]", "k = k1 + N1·k2", "#f1f3f6", "#5b6370")]
        else:
            info = [("Input x[n]", "N samples", "#f1f3f6", "#5b6370"),
                    ("Reshape", "N1 × N2 grid", "#fef3c7", "#b45309"),
                    ("Stage 1 ANALOG", "N2 MVMs", "#ccfbf1", "#0f766e"),
                    ("Twiddle DIGITAL", "N mults", "#fef3c7", "#b45309"),
                    ("Stage 2 ANALOG", "N1 MVMs", "#ccfbf1", "#0f766e"),
                    ("Output X[k]", "k = k1 + N1·k2", "#f1f3f6", "#5b6370")]
        gap = 22
        bw = (W - 20 - 2 * gap) / 3.0
        bh = 62
        pos = []
        for i in range(3):                          # row 1 left -> right
            pos.append((10 + i * (bw + gap), 12))
        for i in range(3):                          # row 2 right -> left
            pos.append((10 + (2 - i) * (bw + gap), 12 + bh + 40))
        for (x, y), (title, sub, fill, edge) in zip(pos, info):
            c.create_rectangle(x, y, x + bw, y + bh, fill=fill, outline=edge, width=2)
            c.create_text(x + bw / 2, y + 22, text=title, font=("Helvetica", 10, "bold"))
            c.create_text(x + bw / 2, y + 43, text=sub, font=("Helvetica", 9), fill="#374151")
        ar = dict(arrow="last", width=2, fill="#5b6370")
        for i in (0, 1):
            x, y = pos[i]
            c.create_line(x + bw, y + bh / 2, x + bw + gap, y + bh / 2, **ar)
        x, y = pos[2]
        c.create_line(x + bw / 2, y + bh, x + bw / 2, y + bh + 40, **ar)
        for i in (3, 4):
            x, y = pos[i]
            c.create_line(x, y + bh / 2, x - gap, y + bh / 2, **ar)
        c.create_text(W / 2, 12 + 2 * bh + 52,
                      text="teal = analog in-memory   |   amber = digital",
                      font=("Helvetica", 9), fill="#5b6370")

    # ---------------- signal tab ----------------
    def build_signal_tab(self):
        fr = ttk.Frame(self.nb)
        self.nb.add(fr, text="Signal")
        self.sig_plot = Plot(fr)
        self.sig_plot.pack(fill="both", expand=True)
        self.sig_zoom = Plot(fr)
        self.sig_zoom.pack(fill="both", expand=True)

    # ---------------- spectrum tab ----------------
    def build_spectrum_tab(self):
        fr = ttk.Frame(self.nb)
        self.nb.add(fr, text="Spectrum")
        ctl = ttk.Frame(fr)
        ctl.pack(fill="x", padx=4, pady=4)
        ttk.Label(ctl, text="Bins").pack(side="left")
        self.v_z0 = tk.StringVar()
        self.v_z1 = tk.StringVar()
        ttk.Entry(ctl, textvariable=self.v_z0, width=7).pack(side="left", padx=2)
        ttk.Label(ctl, text="to").pack(side="left")
        ttk.Entry(ctl, textvariable=self.v_z1, width=7).pack(side="left", padx=2)
        ttk.Button(ctl, text="Zoom", command=self.apply_zoom).pack(side="left", padx=4)
        ttk.Button(ctl, text="All", command=self.reset_zoom).pack(side="left")
        self.spec_plot = Plot(fr)
        self.spec_plot.pack(fill="both", expand=True)
        self.err_plot = Plot(fr)
        self.err_plot.pack(fill="both", expand=True)

    def apply_zoom(self):
        try:
            a, b = float(self.v_z0.get()), float(self.v_z1.get())
            if b > a:
                self.zoom = (a, b)
                self.draw_spectrum()
        except ValueError:
            messagebox.showerror("Zoom", "Enter two numbers, e.g. 30 and 130.")

    def reset_zoom(self):
        self.zoom = None
        self.v_z0.set("")
        self.v_z1.set("")
        self.draw_spectrum()

    def draw_spectrum(self):
        r = self.result
        if not r:
            return
        X, Xref, Xi = r["X"], r["Xref"], r["Xideal"]
        N = len(X)
        half = N // 2 + 1
        peak = max(abs(v) for v in Xref) or 1.0
        ks = list(range(half))

        def db(v):
            return 20 * math.log10(v / peak + 1e-30)

        sa = [db(abs(X[k])) for k in ks]
        se = [db(abs(Xref[k])) for k in ks]
        floor = max(-160.0, math.floor(min(sa + se) / 10) * 10)
        self.spec_plot.set([(ks, se, COL_EXACT, "exact FFT"),
                            (ks, sa, COL_ANALOG, "analog")],
                           title="Magnitude spectrum", xlabel="frequency bin k",
                           ylabel="dB re peak", xlim=self.zoom, ylim=(floor, 5))
        ser = [(ks, [max(-300, db(abs(X[k] - Xref[k]))) for k in ks], COL_ANALOG, "analog error")]
        if Xi:
            ser.append((ks, [max(-300, db(abs(Xi[k] - Xref[k]))) for k in ks],
                        COL_IDEAL, "ideal split error"))
        self.err_plot.set(ser, title="Error vs exact FFT", xlabel="frequency bin k",
                          ylabel="dB re peak", xlim=self.zoom)

    # ---------------- array tab ----------------
    def build_array_tab(self):
        fr = ttk.Frame(self.nb)
        self.nb.add(fr, text="Array")
        self.arr_info = ttk.Label(fr, wraplength=560, justify="left",
                                  text="The programmed conductance map appears after a run.")
        self.arr_info.pack(fill="x", padx=8, pady=6)
        self.arr_canvas = tk.Canvas(fr, bg="#0b1d2a", highlightthickness=0)
        self.arr_canvas.pack(fill="both", expand=True)
        self.arr_img = None

    def draw_array(self):
        r = self.result
        Gp, Gm = r["Gp"], r["Gm"]
        M = r["p"]["N1"]
        rows, cols = 2 * M, 4 * M
        cw = max(self.arr_canvas.winfo_width(), 300)
        step = max(1, int(math.ceil(cols / float(min(cw, 512)))))
        out_cols = list(range(0, cols, step))
        out_rows = list(range(0, rows, step))
        lines = []
        for rr in out_rows:
            gp, gm = Gp[rr], Gm[rr]
            px = []
            for cc in out_cols:
                g = gp[cc // 2] if cc % 2 == 0 else gm[cc // 2]
                px.append(PALETTE[max(0, min(255, int(g * 255)))])
            lines.append("{" + " ".join(px) + "}")
        img = tk.PhotoImage(width=len(out_cols), height=len(out_rows))
        img.put(" ".join(lines))
        z = max(1, int(cw // len(out_cols)))
        if z > 1:
            img = img.zoom(z)
        self.arr_img = img
        self.arr_canvas.delete("all")
        self.arr_canvas.create_image(0, 0, image=img, anchor="nw")
        extra = ("Stage 2 reuses the same array." if r["p"]["N2"] == M else
                 "Stage 2 uses a second %d-point array (not shown)." % r["p"]["N2"])
        self.arr_info.configure(text=(
            "Stage-1 array: %d-point DFT -> %d rows × %d cols = %s flash cells "
            "(G+ and G− columns interleaved; dark = 0, yellow = 1). "
            "Programming error %.2f%%. %s"
            % (M, rows, cols, format(rows * cols, ","), r["p"]["prog"] * 100, extra)))

    # ---------------- run ----------------
    def gather(self):
        p = {}
        p["kind"] = self.v_kind.get()
        p["freqs"] = parse_list(self.v_freqs.get())
        p["amps"] = parse_list(self.v_amps.get())
        p["custom"] = parse_list(self.v_custom.get())
        p["noise"] = float(self.v_noise.get())
        p["window"] = self.v_window.get()
        p["N1"] = int(self.v_n1.get())
        p["N2"] = int(self.v_n2.get())
        p["prog"] = float(self.v_prog.get()) / 100.0
        p["read"] = float(self.v_read.get()) / 100.0
        p["adc"] = int(self.v_adc.get())
        p["dac"] = int(self.v_dac.get())
        p["seed"] = int(self.v_seed.get())
        p["verify"] = self.v_verify.get()
        p["use_np"] = self.v_usenp.get()
        for b in ("adc", "dac"):
            if p[b] < 0 or p[b] == 1 or p[b] > 24:
                raise ValueError("%s bits must be 0 or 2..24" % b.upper())
        if p["kind"] == "Custom values" and not p["custom"]:
            raise ValueError("Enter some custom values")
        return p

    def run(self):
        try:
            p = self.gather()
        except Exception as e:
            messagebox.showerror("Input error", str(e))
            return
        N = p["N1"] * p["N2"]
        if not (HAVE_NP and p["use_np"]) and N > 16384:
            if not messagebox.askyesno("Slow", "N = %d without numpy may take several "
                                               "minutes on a phone. Continue?" % N):
                return
        self.run_btn.state(["disabled"])
        self.status.set("Computing N = %d ..." % N)
        self.t_start = time.perf_counter()
        self.worker_out = None

        def work():
            try:
                self.worker_out = ("ok", simulate(p))
            except Exception:
                self.worker_out = ("err", traceback.format_exc())

        threading.Thread(target=work, daemon=True).start()
        self.root.after(150, self.poll)

    def poll(self):
        if self.worker_out is None:
            self.status.set("Computing ... %.1f s" % (time.perf_counter() - self.t_start))
            self.root.after(200, self.poll)
            return
        kind, val = self.worker_out
        self.run_btn.state(["!disabled"])
        if kind == "err":
            self.status.set("Error")
            messagebox.showerror("Error", val[-800:])
            return
        self.result = val
        self.status.set("Done in %.1f s  (%s)" % (time.perf_counter() - self.t_start,
                                                    val["backend"]))
        self.show_results()

    def show_results(self):
        r = self.result
        p = r["p"]
        N1, N2, N = p["N1"], p["N2"], p["N"]
        X, Xref, Xi = r["X"], r["Xref"], r["Xideal"]
        snr, emax, erel = error_metrics(X, Xref)
        t = r["times"]
        L = []
        L.append("SIZE")
        L.append("  N = N1 × N2 = %d × %d = %s" % (N1, N2, format(N, ",")))
        L.append("  Backend: %s" % r["backend"])
        L.append("")
        L.append("ANALOG ARRAY")
        L.append("  Stores the %d-point DFT matrix" % N1)
        L.append("  complex %d×%d -> real %d×%d -> cells %d×%d = %s"
                 % (N1, N1, 2 * N1, 2 * N1, 2 * N1, 4 * N1, format(8 * N1 * N1, ",")))
        L.append("  Stage 2: " + ("same array reused" if N1 == N2 else
                                  "second %d-point array" % N2))
        L.append("")
        L.append("WORK COUNT")
        L.append("  Analog array reads (MVMs): %d + %d = %d" % (N2, N1, N1 + N2))
        L.append("  Complex MACs in analog:    %s" % format(N * (N1 + N2), ","))
        L.append("  Digital twiddle mults:     %s" % format(N, ","))
        L.append("  Direct DFT (reference):    %s complex MACs" % format(N * N, ","))
        L.append("  Radix-2 FFT (reference):   %s butterflies"
                 % format(int(N // 2 * math.log2(N)), ","))
        L.append("  MAC reduction vs direct:   %.0f×" % (N / float(N1 + N2)))
        L.append("")
        L.append("ACCURACY vs exact FFT")
        L.append("  SNR:            %.1f dB" % snr)
        L.append("  Max |error|:    %.3g  (%.1f dB re peak)"
                 % (emax, 20 * math.log10(erel + 1e-30)))
        if Xi:
            s2, e2, r2 = error_metrics(Xi, Xref)
            L.append("  Ideal split:    max |error| %.2e  -> %s"
                     % (e2, "algorithm exact ✓" if r2 < 1e-9 else "CHECK"))
        L.append("")
        L.append("STRONGEST BINS (k: exact | analog)")
        for k in find_peaks(Xref):
            L.append("  %6d: %10.3f | %10.3f" % (k, abs(Xref[k]), abs(X[k])))
        L.append("")
        L.append("SIMULATION TIME on this device")
        L.append("  Program array: %7.1f ms" % (1000 * t["program"]))
        L.append("  Stage 1:       %7.1f ms" % (1000 * t["stage1"]))
        L.append("  Twiddle:       %7.1f ms" % (1000 * t["twiddle"]))
        L.append("  Stage 2:       %7.1f ms" % (1000 * t["stage2"]))
        L.append("  Exact FFT:     %7.1f ms" % (1000 * t["reference"]))
        L.append("  (Software timings, not hardware speed.)")
        set_text(self.res_txt, "\n".join(L))
        self.draw_pipeline()

        x = r["x"]
        n = list(range(N))
        self.sig_plot.set([(n, x, COL_SIGNAL, "")], title="Input x[n] (all %d samples)" % N,
                          xlabel="sample n", ylabel="amplitude")
        m = min(N, 256)
        self.sig_zoom.set([(n[:m], x[:m], COL_SIGNAL, "")],
                          title="First %d samples" % m, xlabel="sample n",
                          ylabel="amplitude")
        self.draw_spectrum()
        self.draw_array()
        self.nb.select(1)


def main():
    root = tk.Tk()
    try:
        root.geometry("720x1100")
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
