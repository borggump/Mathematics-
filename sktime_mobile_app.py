"""
sktime Time-Series Forecasting — Mobile GUI App
Compatible with Pydroid 3 on Android (Python 3.x + tkinter + matplotlib)

Install in Pydroid 3 terminal:
  pip install numpy pandas scikit-learn matplotlib

For full sktime support:
  pip install sktime statsmodels pmdarima
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import math
import random

# ── Attempt imports, show friendly errors if missing ──────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.gridspec as gridspec
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ── Colour Palette ─────────────────────────────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
SURFACE2 = "#1f2937"
BORDER   = "#2d3748"
ACCENT   = "#38bdf8"
ACCENT2  = "#f472b6"
ACCENT3  = "#34d399"
ACCENT4  = "#fbbf24"
TEXT     = "#e2e8f0"
MUTED    = "#94a3b8"

# ── Fonts (Pydroid 3 has limited fonts — keep to system defaults) ──────────────
FNT_TITLE  = ("sans-serif", 15, "bold")
FNT_HEAD   = ("sans-serif", 12, "bold")
FNT_BODY   = ("sans-serif", 10)
FNT_MONO   = ("monospace", 9)
FNT_SMALL  = ("sans-serif", 8)

# ══════════════════════════════════════════════════════════════════════════════
#  Pure-Python fallback implementations (no sktime required)
# ══════════════════════════════════════════════════════════════════════════════

def generate_hvac_data(n_days=90, seed=42):
    """Generate synthetic HVAC sensor data."""
    if seed is not None:
        random.seed(seed)
        if HAS_NUMPY:
            np.random.seed(seed)

    n_hours = n_days * 24
    temperature = []
    timestamps = []

    for i in range(n_hours):
        trend = 5.0 * i / n_hours
        hour_of_day = i % 24
        seasonal = 4.0 * math.sin(2 * math.pi * (hour_of_day - 4) / 24)
        if HAS_NUMPY:
            noise = float(np.random.normal(0, 0.8))
        else:
            noise = random.gauss(0, 0.8)
        val = 20.0 + trend + seasonal + noise
        temperature.append(val)

    # Inject 5 NaN-like values (use None)
    for idx in [300, 301, 302, 1440, 1441]:
        if idx < len(temperature):
            temperature[idx] = None

    return temperature


def linear_impute(series):
    """Fill None values with linear interpolation."""
    result = series[:]
    n = len(result)
    i = 0
    while i < n:
        if result[i] is None:
            left_idx = i - 1
            right_idx = i
            while right_idx < n and result[right_idx] is None:
                right_idx += 1
            left_val  = result[left_idx]  if left_idx  >= 0 else 0.0
            right_val = result[right_idx] if right_idx < n  else left_val
            span = right_idx - left_idx
            for j in range(left_idx + 1, right_idx):
                frac = (j - left_idx) / span
                result[j] = left_val + frac * (right_val - left_val)
            i = right_idx
        else:
            i += 1
    return result


def fit_linear_trend(series):
    """OLS linear trend: returns (beta0, beta1)."""
    n = len(series)
    sx  = sum(range(n))
    sy  = sum(series)
    sxy = sum(i * series[i] for i in range(n))
    sx2 = sum(i * i for i in range(n))
    denom = n * sx2 - sx * sx
    if denom == 0:
        return sy / n, 0.0
    beta1 = (n * sxy - sx * sy) / denom
    beta0 = (sy - beta1 * sx) / n
    return beta0, beta1


def detrend(series, beta0, beta1):
    return [series[i] - (beta0 + beta1 * i) for i in range(len(series))]


def fit_seasonal_index(series, sp=24):
    """Compute mean value at each phase (hour 0..sp-1)."""
    buckets = [[] for _ in range(sp)]
    for i, v in enumerate(series):
        buckets[i % sp].append(v)
    return [sum(b) / len(b) if b else 0.0 for b in buckets]


def deseasonalize(series, s_index):
    sp = len(s_index)
    return [series[i] - s_index[i % sp] for i in range(len(series))]


def reseasonalize(series, s_index, offset=0):
    sp = len(s_index)
    return [series[i] + s_index[(i + offset) % sp] for i in range(len(series))]


def retrend(series, beta0, beta1, offset=0):
    return [series[i] + (beta0 + beta1 * (i + offset)) for i in range(len(series))]


def ses_forecast(train_residuals, h, alpha=0.3):
    """Simple Exponential Smoothing forecast for h steps."""
    level = train_residuals[0]
    for v in train_residuals[1:]:
        level = alpha * v + (1 - alpha) * level
    return [level] * h


def arima_forecast(train_residuals, h):
    """
    Lightweight ARIMA(1,1,1)-like forecast:
      Difference once, fit AR(1) + MA(1) via 1-step OLS approximation.
    """
    n = len(train_residuals)
    diff = [train_residuals[i] - train_residuals[i - 1] for i in range(1, n)]
    # Fit AR(1): Δy_t = c + φ·Δy_{t-1} + ε
    if len(diff) < 2:
        return [train_residuals[-1]] * h
    x = diff[:-1]
    y = diff[1:]
    sx  = sum(x);  sy = sum(y)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    sx2 = sum(xi * xi for xi in x)
    nv  = len(x)
    denom = nv * sx2 - sx * sx
    if denom == 0:
        phi = 0.0; c = sum(y) / nv if nv > 0 else 0.0
    else:
        phi = (nv * sxy - sx * sy) / denom
        c   = (sy - phi * sx) / nv
    # One-step residuals (MA term)
    errors = []
    d_hat = [c + phi * x[i] for i in range(len(x))]
    for i in range(len(y)):
        errors.append(y[i] - d_hat[i])
    theta = sum(errors) / len(errors) if errors else 0.0
    # Forecast by cumulative sum from last level
    last_diff  = diff[-1]
    last_error = errors[-1] if errors else 0.0
    last_level = train_residuals[-1]
    preds = []
    cur_level = last_level
    cur_diff  = last_diff
    cur_err   = last_error
    for k in range(h):
        next_diff  = c + phi * cur_diff + theta * cur_err
        cur_level += next_diff
        preds.append(cur_level)
        cur_diff = next_diff
        cur_err  = 0.0   # future errors are 0 in expectation
    return preds


def run_pipeline(n_days, test_days, model_choice, alpha, sp):
    """
    Full pipeline:
      generate → impute → detrend → deseasonalize → forecast → reconstruct
    Returns dict of results for plotting + metrics.
    """
    temperature = generate_hvac_data(n_days=n_days)

    n_total = len(temperature)
    h       = test_days * 24
    n_train = n_total - h

    train_raw = temperature[:n_train]
    test_raw  = temperature[n_train:]

    # 1. Impute
    train_imp = linear_impute(train_raw)

    # 2. Detrend
    beta0, beta1 = fit_linear_trend(train_imp)
    train_det = detrend(train_imp, beta0, beta1)

    # 3. Deseasonalize
    s_index = fit_seasonal_index(train_det, sp=sp)
    train_res = deseasonalize(train_det, s_index)

    # 4. Forecast residuals
    if model_choice == "SES":
        fcast_res = ses_forecast(train_res, h, alpha=alpha)
    else:
        fcast_res = arima_forecast(train_res, h)

    # 5. Inverse: reseasonalize + retrend
    fcast_seas = reseasonalize(fcast_res, s_index, offset=n_train)
    fcast_full = retrend(fcast_seas, beta0, beta1, offset=n_train)

    # 6. Compute test actuals (imputed)
    test_imp = linear_impute(test_raw)

    # 7. Metrics
    errors = [abs((test_imp[i] or 0) - fcast_full[i]) for i in range(h)]
    mae    = sum(errors) / h
    mape_vals = []
    for i in range(h):
        actual = test_imp[i]
        if actual and actual != 0:
            mape_vals.append(abs(actual - fcast_full[i]) / abs(actual) * 100)
    mape = sum(mape_vals) / len(mape_vals) if mape_vals else 0.0

    # 8. Seasonal index for display
    trend_line = [beta0 + beta1 * i for i in range(n_total)]
    s_full     = [s_index[i % sp] for i in range(n_total)]

    return {
        "temperature": [v if v is not None else float("nan") for v in temperature],
        "train_imp":   train_imp,
        "train_res":   train_res,
        "fcast_full":  fcast_full,
        "test_imp":    test_imp,
        "trend_line":  trend_line,
        "s_full":      s_full,
        "n_train":     n_train,
        "h":           h,
        "n_total":     n_total,
        "mae":         mae,
        "mape":        mape,
        "beta0":       beta0,
        "beta1":       beta1,
        "s_index":     s_index,
        "model":       model_choice,
        "alpha":       alpha,
        "sp":          sp,
        "n_days":      n_days,
        "test_days":   test_days,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  GUI Application
# ══════════════════════════════════════════════════════════════════════════════

class SktimeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("sktime Forecasting")
        self.configure(bg=BG)

        # Mobile screen sizing — detect screen size
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.resizable(True, True)

        # State
        self.result = None
        self._build_ui()

    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg=SURFACE, height=50)
        topbar.pack(fill="x", side="top")
        tk.Label(topbar, text="📈  sktime Forecasting", bg=SURFACE,
                 fg=ACCENT, font=FNT_TITLE, pady=10).pack(side="left", padx=14)
        tk.Label(topbar, text="Python · Mobile", bg=SURFACE,
                 fg=MUTED, font=FNT_SMALL).pack(side="right", padx=14)

        # ── Notebook (tabs) ──
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",       background=BG,      borderwidth=0)
        style.configure("TNotebook.Tab",   background=SURFACE2, foreground=MUTED,
                        padding=[14, 8],   font=FNT_BODY)
        style.map("TNotebook.Tab",
                  background=[("selected", SURFACE)],
                  foreground=[("selected", ACCENT)])
        style.configure("TScale",  background=BG, troughcolor=SURFACE2)
        style.configure("TCombobox", fieldbackground=SURFACE2, background=SURFACE2,
                        foreground=TEXT, selectbackground=ACCENT)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._tab_config()
        self._tab_charts()
        self._tab_math()
        self._tab_results()

    # ══ TAB 1: CONFIG ══════════════════════════════════════════════════════════
    def _tab_config(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="⚙ Config")

        canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview,
                              bg=SURFACE2)
        inner  = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        PAD = dict(padx=16, pady=6, sticky="ew")

        def section(text):
            f = tk.Frame(inner, bg=SURFACE, bd=0)
            f.pack(fill="x", padx=12, pady=(14, 2))
            tk.Label(f, text=text, bg=SURFACE, fg=ACCENT,
                     font=FNT_HEAD, pady=8, padx=12).pack(anchor="w")
            return f

        def labeled_slider(parent, label, var, lo, hi, res, unit="", fmt="{:.0f}"):
            row = tk.Frame(parent, bg=BG)
            row.pack(fill="x", padx=14, pady=4)
            top = tk.Frame(row, bg=BG)
            top.pack(fill="x")
            tk.Label(top, text=label, bg=BG, fg=TEXT, font=FNT_BODY).pack(side="left")
            val_lbl = tk.Label(top, text=fmt.format(var.get()) + unit,
                               bg=BG, fg=ACCENT4, font=FNT_MONO)
            val_lbl.pack(side="right")

            def on_slide(v):
                val_lbl.config(text=fmt.format(float(v)) + unit)

            sc = ttk.Scale(row, from_=lo, to=hi, variable=var,
                           orient="horizontal", command=on_slide)
            sc.pack(fill="x", pady=2)
            return val_lbl

        # ── Dataset ──
        section("📊  Dataset Parameters")
        self.v_ndays    = tk.DoubleVar(value=90)
        self.v_testdays = tk.DoubleVar(value=7)
        labeled_slider(inner, "Total days of sensor data", self.v_ndays,    30, 180, 1, " days")
        labeled_slider(inner, "Hold-out test days",        self.v_testdays,  3,  30, 1, " days")

        # ── Model ──
        section("🤖  Model Selection")
        model_row = tk.Frame(inner, bg=BG)
        model_row.pack(fill="x", padx=14, pady=8)
        tk.Label(model_row, text="Forecasting model:", bg=BG,
                 fg=TEXT, font=FNT_BODY).pack(side="left")
        self.v_model = tk.StringVar(value="SES")
        for txt, val in [("Exp. Smoothing (SES)", "SES"),
                         ("ARIMA(1,1,1)",          "ARIMA")]:
            tk.Radiobutton(inner, text=txt, variable=self.v_model, value=val,
                           bg=BG, fg=TEXT, selectcolor=SURFACE2,
                           activebackground=BG, activeforeground=ACCENT,
                           font=FNT_BODY).pack(anchor="w", padx=28)

        # ── Hyper-params ──
        section("🔧  Hyperparameters")
        self.v_alpha = tk.DoubleVar(value=0.3)
        self.v_sp    = tk.DoubleVar(value=24)
        labeled_slider(inner, "SES smoothing α",  self.v_alpha, 0.05, 0.95, 0.05, fmt="{:.2f}")
        labeled_slider(inner, "Seasonal period sp", self.v_sp,   4,    48,   1,   " hrs")

        # ── Info box ──
        info = tk.Frame(inner, bg=SURFACE, bd=0)
        info.pack(fill="x", padx=12, pady=12)
        info_text = (
            "Pipeline steps:\n"
            "  1. Impute missing values (linear)\n"
            "  2. Remove linear trend (OLS)\n"
            "  3. Remove seasonality (sp-cycle)\n"
            "  4. Forecast stationary residuals\n"
            "  5. Reconstruct in original °C scale\n\n"
            "No sktime install needed — built-in\n"
            "pure-Python implementations used."
        )
        tk.Label(info, text=info_text, bg=SURFACE, fg=MUTED,
                 font=FNT_MONO, justify="left", pady=10, padx=12).pack(anchor="w")

        # ── Run button ──
        btn_row = tk.Frame(inner, bg=BG)
        btn_row.pack(fill="x", padx=14, pady=16)
        self.run_btn = tk.Button(
            btn_row, text="▶  RUN FORECAST",
            bg=ACCENT, fg="#0d1117", font=("sans-serif", 13, "bold"),
            relief="flat", bd=0, pady=14,
            activebackground=ACCENT2,
            command=self._run_forecast
        )
        self.run_btn.pack(fill="x")

        self.status_lbl = tk.Label(inner, text="⬤  Ready", bg=BG,
                                   fg=ACCENT3, font=FNT_SMALL)
        self.status_lbl.pack(pady=4)

    # ══ TAB 2: CHARTS ══════════════════════════════════════════════════════════
    def _tab_charts(self):
        self.chart_frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(self.chart_frame, text="📈 Charts")

        if not HAS_MPL:
            tk.Label(self.chart_frame,
                     text="matplotlib not installed.\npip install matplotlib",
                     bg=BG, fg=ACCENT2, font=FNT_HEAD).pack(expand=True)
            self.chart_canvas = None
            return

        # Placeholder figure
        self.fig = Figure(figsize=(4.5, 9), dpi=90, facecolor=BG)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        self._draw_placeholder()

    def _draw_placeholder(self):
        if not HAS_MPL or self.chart_canvas is None:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(SURFACE)
        ax.text(0.5, 0.5, "Run a forecast to\nsee charts here",
                ha="center", va="center", color=MUTED,
                fontsize=13, transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        self.fig.patch.set_facecolor(BG)
        self.chart_canvas.draw()

    def _draw_charts(self, r):
        if not HAS_MPL or self.chart_canvas is None:
            return
        self.fig.clear()

        n    = r["n_total"]
        ntr  = r["n_train"]
        h    = r["h"]
        temp = r["temperature"]
        xs   = list(range(n))
        xtr  = list(range(ntr))
        xte  = list(range(ntr, ntr + h))

        gs = gridspec.GridSpec(4, 1, figure=self.fig,
                               hspace=0.55, top=0.95, bottom=0.05,
                               left=0.12, right=0.97)

        def styled_ax(ax, title, ylabel):
            ax.set_facecolor(SURFACE)
            ax.set_title(title, color=TEXT, fontsize=8, pad=5, loc="left")
            ax.set_ylabel(ylabel, color=MUTED, fontsize=7)
            ax.tick_params(colors=MUTED, labelsize=6)
            for sp in ax.spines.values():
                sp.set_color(BORDER)
            ax.grid(color=BORDER, linewidth=0.4, linestyle="--")

        # ── Plot 1: Raw data + missing ──────────────────────────────────────
        ax1 = self.fig.add_subplot(gs[0])
        styled_ax(ax1, "1 · Raw Sensor Data (°C)", "°C")
        clean = [(x, v) for x, v in zip(xs, temp) if not math.isnan(v)]
        if clean:
            cx, cv = zip(*clean)
            ax1.plot(cx, cv, color=ACCENT, lw=0.7, alpha=0.8)
        missing_x = [x for x, v in zip(xs, temp) if math.isnan(v)]
        for mx in missing_x:
            ax1.axvline(mx, color=ACCENT2, lw=1.5, alpha=0.8)
        ax1.axvline(ntr, color=ACCENT4, lw=1.5, linestyle="--", alpha=0.9)
        ax1.legend(
            handles=[
                mpatches.Patch(color=ACCENT,  label="Temperature"),
                mpatches.Patch(color=ACCENT2, label="Missing (NaN)"),
                mpatches.Patch(color=ACCENT4, label="Train/Test cut"),
            ],
            fontsize=5.5, facecolor=SURFACE2, edgecolor=BORDER,
            labelcolor=TEXT, loc="upper left"
        )

        # ── Plot 2: Decomposition ────────────────────────────────────────────
        ax2 = self.fig.add_subplot(gs[1])
        styled_ax(ax2, "2 · Decomposition: Trend + Seasonality", "°C")
        ax2.plot(xtr, r["trend_line"][:ntr], color=ACCENT4, lw=1.2, label="Trend T(t)")
        ax2.plot(xtr, r["s_full"][:ntr],     color=ACCENT2, lw=0.8, alpha=0.7, label="Season S(t)")
        ax2.plot(xtr, r["train_res"],         color=ACCENT3, lw=0.6, alpha=0.5, label="Residual r_t")
        ax2.legend(fontsize=5.5, facecolor=SURFACE2, edgecolor=BORDER,
                   labelcolor=TEXT, loc="upper left")

        # ── Plot 3: Seasonal index (24h cycle) ───────────────────────────────
        ax3 = self.fig.add_subplot(gs[2])
        styled_ax(ax3, f"3 · Seasonal Index (sp={r['sp']} hrs)", "°C offset")
        si = r["s_index"]
        ax3.bar(range(len(si)), si,
                color=[ACCENT if v >= 0 else ACCENT2 for v in si],
                alpha=0.8, width=0.8)
        ax3.axhline(0, color=MUTED, lw=0.8)
        ax3.set_xlabel("Hour of day", color=MUTED, fontsize=7)

        # ── Plot 4: Forecast vs Actual ───────────────────────────────────────
        ax4 = self.fig.add_subplot(gs[3])
        styled_ax(ax4, f"4 · Forecast vs Actual  (MAE={r['mae']:.3f}°C, MAPE={r['mape']:.2f}%)", "°C")
        ax4.plot(xte, r["test_imp"],   color=TEXT,    lw=1.0, label="Actual",   alpha=0.9)
        ax4.plot(xte, r["fcast_full"], color=ACCENT3, lw=1.2, label=r["model"], linestyle="--")
        err_hi = [r["fcast_full"][i] + r["mae"] for i in range(h)]
        err_lo = [r["fcast_full"][i] - r["mae"] for i in range(h)]
        ax4.fill_between(xte, err_lo, err_hi, color=ACCENT3, alpha=0.12, label="±MAE band")
        ax4.legend(fontsize=5.5, facecolor=SURFACE2, edgecolor=BORDER,
                   labelcolor=TEXT, loc="upper left")

        self.fig.patch.set_facecolor(BG)
        self.chart_canvas.draw()

    # ══ TAB 3: MATH ════════════════════════════════════════════════════════════
    def _tab_math(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="∑ Math")

        canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview,
                              bg=SURFACE2)
        inner  = tk.Frame(canvas, bg=BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        sections = [
            ("1 · Additive Decomposition Model", ACCENT, [
                ("Formula", "y_t = μ + T(t) + S(t) + ε_t", ACCENT),
                ("Base temp", "μ = 20 °C"),
                ("Trend", "T(t) = 5·(t / n)   [+5°C over n hrs]"),
                ("Seasonality", "S(t) = 4·sin(2π·(h_t − 4) / 24)"),
                ("Noise", "ε_t ~ N(0, 0.8²)"),
                ("Hour", "h_t = t mod 24"),
            ]),
            ("2 · Train / Test Split", ACCENT2, [
                ("Constraint", "∀ t_train < t_test  (NO shuffling)", ACCENT4),
                ("Train", "y_train = y[0 : n−h]"),
                ("Test", "y_test  = y[n−h : n]"),
                ("h", "h = test_days × 24  (forecast horizon)"),
            ]),
            ("3 · Step 1 — Imputation", ACCENT3, [
                ("Method", "Linear interpolation between neighbours"),
                ("Formula", "ŷ_t = y_{t-1} + (y_{t+1}−y_{t-1})·k/span"),
                ("Where", "k = position within the gap"),
            ]),
            ("4 · Step 2 — Detrender", ACCENT4, [
                ("OLS fit", "T̂(t) = β₀ + β₁·t"),
                ("β₁", "β₁ = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)"),
                ("β₀", "β₀ = (Σy − β₁·Σx) / n"),
                ("Remove", "y_t* = y_t − T̂(t)   ← detrended"),
                ("Restore", "ŷ_{t+k} += T̂(t+k)  ← on predict"),
            ]),
            ("5 · Step 3 — Deseasonalizer", ACCENT, [
                ("Index", "Ŝ(h) = (1/D)·Σ_{d=1}^{D} y*_{d,h}"),
                ("D", "D = number of complete seasonal cycles"),
                ("Remove", "r_t = y_t* − Ŝ(h_t)   ← stationary"),
                ("Restore", "ŷ += Ŝ(h_{t+k})        ← on predict"),
            ]),
            ("6 · Model A — SES", ACCENT2, [
                ("Update", "ℓ_t = α·r_t + (1−α)·ℓ_{t-1}"),
                ("Forecast", "r̂_{t+k} = ℓ_t  (flat)"),
                ("α", "Smoothing weight; high α → trust recent data"),
            ]),
            ("7 · Model B — ARIMA(1,1,1)", ACCENT3, [
                ("Difference", "Δr_t = r_t − r_{t-1}"),
                ("Model", "Δr_t = c + φ·Δr_{t-1} + θ·ε_{t-1} + ε_t"),
                ("φ", "AR(1) coefficient — memory of past values"),
                ("θ", "MA(1) coefficient — memory of past errors"),
                ("Forecast", "Cumulative sum from last level"),
            ]),
            ("8 · Evaluation Metrics", ACCENT4, [
                ("MAE", "MAE = (1/H)·Σ|y_{t+k} − ŷ_{t+k}|"),
                ("MAPE", "MAPE = (1/H)·Σ|y−ŷ|/|y| × 100%"),
                ("Units", "MAE in °C; MAPE in %"),
            ]),
        ]

        for title, col, items in sections:
            # Section header
            hdr = tk.Frame(inner, bg=SURFACE, bd=0)
            hdr.pack(fill="x", padx=12, pady=(12, 0))
            tk.Label(hdr, text=title, bg=SURFACE, fg=col,
                     font=FNT_HEAD, pady=8, padx=12).pack(anchor="w")

            # Items
            for item in items:
                label = item[0]; formula = item[1]
                item_col = item[2] if len(item) > 2 else ACCENT3
                row = tk.Frame(inner, bg=BG)
                row.pack(fill="x", padx=20, pady=2)
                tk.Label(row, text=f"{label}:", bg=BG, fg=MUTED,
                         font=FNT_SMALL, width=12, anchor="w").pack(side="left")
                tk.Label(row, text=formula, bg=BG, fg=item_col,
                         font=FNT_MONO, anchor="w", wraplength=260,
                         justify="left").pack(side="left", padx=4)

    # ══ TAB 4: RESULTS ════════════════════════════════════════════════════════
    def _tab_results(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="📋 Results")

        # Metric cards at top
        self.metric_frame = tk.Frame(frame, bg=BG)
        self.metric_frame.pack(fill="x", padx=12, pady=12)
        self._make_metric_card(self.metric_frame, "MAE", "—", "°C", ACCENT,  side="left")
        self._make_metric_card(self.metric_frame, "MAPE", "—", "%",  ACCENT3, side="left")
        self._make_metric_card(self.metric_frame, "Model", "—", "",  ACCENT2, side="left")

        # Output log
        tk.Label(frame, text="Run Log", bg=BG, fg=MUTED,
                 font=FNT_SMALL).pack(anchor="w", padx=14)
        self.log = scrolledtext.ScrolledText(
            frame, bg=SURFACE, fg=TEXT, font=FNT_MONO,
            insertbackground=ACCENT, relief="flat",
            wrap="word", state="disabled"
        )
        self.log.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        # Forecast table header
        tk.Label(frame, text="Sample Forecast Values (first 24 hrs)",
                 bg=BG, fg=MUTED, font=FNT_SMALL).pack(anchor="w", padx=14)
        tbl_frame = tk.Frame(frame, bg=SURFACE, bd=0)
        tbl_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.tbl = ttk.Treeview(tbl_frame, columns=("hr","actual","fcast","err"),
                                show="headings", height=8)
        for col, hd, w in [("hr","Hour",50), ("actual","Actual°C",90),
                            ("fcast","Forecast°C",90), ("err","|Error|",70)]:
            self.tbl.heading(col, text=hd)
            self.tbl.column(col, width=w, anchor="center")
        style = ttk.Style()
        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                        foreground=TEXT, rowheight=22)
        style.configure("Treeview.Heading", background=SURFACE2, foreground=ACCENT,
                        font=FNT_SMALL)
        self.tbl.pack(fill="x")

    def _make_metric_card(self, parent, label, value, unit, color, side="left"):
        card = tk.Frame(parent, bg=SURFACE, bd=0)
        card.pack(side=side, expand=True, fill="both", padx=4, pady=4)
        tk.Label(card, text=label, bg=SURFACE, fg=MUTED,
                 font=FNT_SMALL, pady=4).pack()
        lbl = tk.Label(card, text=value + unit, bg=SURFACE, fg=color,
                       font=("sans-serif", 15, "bold"))
        lbl.pack(pady=(0, 6))
        # Store reference
        setattr(self, f"_metric_{label.lower().replace(' ','_')}", lbl)
        return lbl

    # ── FORECAST RUNNER ────────────────────────────────────────────────────────
    def _run_forecast(self):
        self.run_btn.config(state="disabled", text="Running…")
        self.status_lbl.config(text="⬤  Computing…", fg=ACCENT4)
        threading.Thread(target=self._forecast_thread, daemon=True).start()

    def _forecast_thread(self):
        try:
            n_days    = max(10, int(self.v_ndays.get()))
            test_days = max(1,  int(self.v_testdays.get()))
            model     = self.v_model.get()
            alpha     = round(self.v_alpha.get(), 2)
            sp        = max(2, int(self.v_sp.get()))

            if test_days >= n_days:
                test_days = n_days // 4

            r = run_pipeline(n_days, test_days, model, alpha, sp)
            self.result = r
            self.after(0, lambda: self._update_ui(r))
        except Exception as ex:
            self.after(0, lambda: self._show_error(str(ex)))

    def _update_ui(self, r):
        # Metrics
        self._metric_mae.config(   text=f"{r['mae']:.3f} °C")
        self._metric_mape.config(  text=f"{r['mape']:.2f}%")
        self._metric_model.config( text=r["model"])

        # Log
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        lines = [
            f"═══ FORECAST COMPLETE ═══",
            f"",
            f"Dataset",
            f"  Days       : {r['n_days']}",
            f"  Total hrs  : {r['n_total']}",
            f"  Train hrs  : {r['n_train']}",
            f"  Test hrs   : {r['h']}",
            f"",
            f"Pipeline",
            f"  Imputer    : linear interpolation",
            f"  Detrender  : OLS  β₀={r['beta0']:.4f}  β₁={r['beta1']:.6f}",
            f"  Deseas.    : sp={r['sp']} hrs",
            f"  Model      : {r['model']}",
            f"  α (SES)    : {r['alpha']}",
            f"",
            f"Metrics",
            f"  MAE        : {r['mae']:.4f} °C",
            f"  MAPE       : {r['mape']:.4f} %",
            f"",
            f"Seasonal Index (first 12 hrs):",
        ]
        for i, v in enumerate(r["s_index"][:12]):
            lines.append(f"  Hour {i:02d}    : {v:+.4f} °C")
        self.log.insert("end", "\n".join(lines))
        self.log.config(state="disabled")

        # Table
        for row in self.tbl.get_children():
            self.tbl.delete(row)
        for i in range(min(24, r["h"])):
            actual = r["test_imp"][i]
            fcast  = r["fcast_full"][i]
            err    = abs(actual - fcast)
            tag = "hi" if err > r["mae"] else "ok"
            self.tbl.insert("", "end",
                            values=(f"{i:02d}:00",
                                    f"{actual:.2f}",
                                    f"{fcast:.2f}",
                                    f"{err:.3f}"),
                            tags=(tag,))
        self.tbl.tag_configure("hi", foreground=ACCENT2)
        self.tbl.tag_configure("ok", foreground=ACCENT3)

        # Charts
        self._draw_charts(r)

        # Switch to charts tab
        self.nb.select(1)

        # Reset button
        self.run_btn.config(state="normal", text="▶  RUN FORECAST")
        self.status_lbl.config(text="⬤  Done", fg=ACCENT3)

    def _show_error(self, msg):
        self.run_btn.config(state="normal", text="▶  RUN FORECAST")
        self.status_lbl.config(text="⬤  Error", fg=ACCENT2)
        messagebox.showerror("Error", msg)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    missing = []
    if not HAS_NUMPY:    missing.append("numpy")
    if not HAS_PANDAS:   missing.append("pandas")
    if not HAS_MPL:      missing.append("matplotlib")

    app = SktimeApp()

    if missing:
        # Show install notice but still launch app
        notice = tk.Toplevel(app)
        notice.title("Install Required")
        notice.configure(bg=BG)
        notice.geometry("320x200")
        msg = "Some packages are missing.\nCharts require matplotlib.\n\nInstall in Pydroid 3 terminal:\n\npip install " + " ".join(missing)
        tk.Label(notice, text=msg, bg=BG, fg=ACCENT4,
                 font=FNT_BODY, wraplength=280, justify="center", pady=20).pack(expand=True)
        tk.Button(notice, text="OK  (app still works)",
                  bg=ACCENT, fg=BG, font=FNT_BODY, relief="flat",
                  command=notice.destroy).pack(pady=10, ipadx=20, ipady=6)

    app.mainloop()


if __name__ == "__main__":
    main()
