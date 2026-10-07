#!/usr/bin/env python3
"""Phase 3 plots from data/raw/sweep_<SID>_*.csv: speedup and throughput vs working set (Exp 1), SAXPY locality (Exp 2),
dtype comparison (Exp 5). Usage: plot_sweep.py <SID>   Writes PNG and PDF to plots/ and a table to data/processed/."""
import sys, os, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import analyze
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10})

SID = sys.argv[1] if len(sys.argv) > 1 else "phase3"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(f"{ROOT}/plots", exist_ok=True); os.makedirs(f"{ROOT}/data/processed", exist_ok=True)
rows = analyze.load(sorted(glob.glob(f"{ROOT}/data/raw/sweep_{SID}_*.csv")))
GHZ, GHZ_ERR = analyze.freq_ghz([f"{ROOT}/data/raw/freq_{SID}.csv"])
g, thr = analyze.group(rows)
CACHE = [("L1D 128 KiB", 128 * 1024), ("L2 16 MiB", 16 * 2**20)]   # Super-tier values from sysctl hw.perflevel0 (unverified which tier runs)
COL = {"scalar": "#8c8c8c", "scalar_unroll8": "#1f77b4", "auto": "#d95f02", "fastmath": "#7570b3", "native": "#1b9e77"}
LAB = {"scalar": "scalar (-fno-vectorize)", "scalar_unroll8": "scalar, unroll 8 (primary baseline)", "auto": "auto -O3", "fastmath": "-O3 -ffast-math", "native": "-mcpu=native"}

def series(build, kernel, dtype):
    keys = sorted([k for k in g if k[0] == build and k[1] == kernel and k[2] == dtype and k[4] == 0 and k[5] == 1], key=lambda k: k[3])
    ws, med, lo, hi, nn = [], [], [], [], []
    na = 3 if kernel == "mul" else 2
    for k in keys:
        s = analyze.stats(g[k]); ws.append(k[3] * na * analyze.SIZEOF[dtype]); med.append(s["median"]); lo.append(s["q1"]); hi.append(s["q3"]); nn.append(k[3])
    return np.array(ws), np.array(med), np.array(lo), np.array(hi), np.array(nn)

def metric(kernel, dtype, nn, ns):
    return np.array([analyze.derive(kernel, dtype, int(n), t)["gibs"] for n, t in zip(nn, ns)]), np.array([analyze.derive(kernel, dtype, int(n), t)["gflops"] for n, t in zip(nn, ns)])

def vlines(ax):
    for name, b in CACHE:
        ax.axvline(b, color="k", ls=":", lw=0.8); ax.text(b, 0.98, " " + name, rotation=90, va="top", ha="right", fontsize=8.5, transform=ax.get_xaxis_transform())

def xfmt(ax):
    ax.set_xscale("log", base=2); ax.set_xlabel("working set (bytes, all arrays)")
    ticks = [2**k for k in range(12, 32, 4)]; ax.set_xticks(ticks); ax.set_xticklabels([("%d KiB" % (t // 1024)) if t < 2**20 else ("%d MiB" % (t // 2**20)) if t < 2**30 else "%d GiB" % (t // 2**30) for t in ticks], rotation=45, ha="right")

def save(fig, name, relayout=False):
    if relayout: fig.tight_layout()
    fig.savefig(f"{ROOT}/plots/{name}.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{ROOT}/plots/{name}.pdf", bbox_inches="tight"); plt.close(fig)

table = []
KERN = ["saxpy", "mul", "dot", "stencil"]
# Exp 1: throughput and speedup, fp32 and fp64: one row per kernel (left throughput, right speedup), shared legend above the grid
from matplotlib.lines import Line2D
for dtype in ("f32", "f64"):
    fig, axs = plt.subplots(4, 2, figsize=(10, 11.5))
    lanes = 4 if dtype == "f32" else 2
    for j, kernel in enumerate(KERN):
        base = series("scalar_unroll8", kernel, dtype); base0 = series("scalar", kernel, dtype)
        for build in ("scalar", "scalar_unroll8", "auto", "fastmath"):
            ws, med, lo, hi, nn = series(build, kernel, dtype)
            if len(ws) == 0: continue
            gib, _ = metric(kernel, dtype, nn, med); glo, _ = metric(kernel, dtype, nn, hi); ghi, _ = metric(kernel, dtype, nn, lo)
            axs[j, 0].errorbar(ws, gib, yerr=[gib - glo, ghi - gib], color=COL[build], marker="o", ms=2.5, lw=1.2, capsize=1.5)
        axs[j, 0].set_title(f"{kernel} {dtype}: throughput", loc="left"); axs[j, 0].set_yscale("log"); axs[j, 0].set_ylabel("GiB/s of useful data"); xfmt(axs[j, 0]); vlines(axs[j, 0])
        for build in ("auto", "fastmath"):
            ws, med, lo, hi, nn = series(build, kernel, dtype)
            for bname, bs, ls in (("scalar_unroll8", base, "-"), ("scalar", base0, "--")):
                if len(ws) == 0 or len(bs[0]) != len(ws): continue
                sp = bs[1] / med
                # propagate IQR: ratio of scalar median to (q3, q1) of the vector build
                axs[j, 1].errorbar(ws, sp, yerr=[sp - bs[1] / hi, bs[1] / lo - sp], color=COL[build], ls=ls, marker="o", ms=2.5, lw=1.2, capsize=1.5)
                for w, s_, n_ in zip(ws, sp, nn): table.append((kernel, dtype, build, bname, int(w), int(n_), float(s_)))
        axs[j, 1].axhline(lanes, color="k", ls="-.", lw=0.9); axs[j, 1].axhline(1, color="gray", lw=0.6)
        axs[j, 1].set_title(f"{kernel} {dtype}: speedup of the vector build", loc="left"); axs[j, 1].set_ylabel("speedup (median ratio)"); xfmt(axs[j, 1]); vlines(axs[j, 1])
        if kernel == "dot": axs[j, 1].set_yscale("log")
    h = [Line2D([], [], color=COL[b], marker="o", ms=4, label=LAB[b]) for b in ("scalar", "scalar_unroll8", "auto", "fastmath")]
    h += [Line2D([], [], color="k", ls="-", label="speedup vs unrolled scalar"), Line2D([], [], color="k", ls="--", label="speedup vs default scalar"),
          Line2D([], [], color="k", ls="-.", label=f"lane count ({lanes})"), Line2D([], [], color="k", ls=":", label="L1D and L2 size")]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=[0, 0, 1, 0.925])
    save(fig, f"exp1_sweep_{dtype}")

# Exp 2: SAXPY locality with dense region
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
for build in ("scalar_unroll8", "auto"):
    ws, med, lo, hi, nn = series(build, "saxpy", "f32")
    gib, gf = metric("saxpy", "f32", nn, med); glo, _ = metric("saxpy", "f32", nn, hi); ghi, _ = metric("saxpy", "f32", nn, lo)
    ax[0].errorbar(ws, gib, yerr=[gib - glo, ghi - gib], color=COL[build], marker="o", ms=3, lw=1.2, capsize=2, label=LAB[build])
    ax[1].errorbar(ws, med / nn * GHZ, yerr=[(med - lo) / nn * GHZ, (hi - med) / nn * GHZ], color=COL[build], marker="o", ms=3, lw=1.2, capsize=2, label=LAB[build])
ax[0].set_ylabel("GiB/s of useful data (3 x 4 B per element)"); ax[0].set_title("SAXPY f32: throughput"); xfmt(ax[0]); ax[0].set_yscale("log")
ax[1].set_ylabel(f"cycles per element (at {GHZ:.2f} GHz, assumed constant)"); ax[1].set_title("SAXPY f32: cycles per element"); xfmt(ax[1]); ax[1].set_yscale("log")
for a in ax: vlines(a); a.grid(alpha=0.25, which="both", lw=0.4)
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.03))
fig.tight_layout(rect=[0, 0, 1, 0.94]); save(fig, "exp2_saxpy_locality")

# Exp 5: dtypes, speedup of auto vs scalar_unroll8 for f32, f64, u32 (2 x 2 grid, one panel per kernel)
fig, axs = plt.subplots(2, 2, figsize=(10.5, 7.2)); axs = axs.ravel()
LS = {"f32": ("-", "#d95f02"), "f64": ("--", "#1b9e77"), "u32": (":", "#7570b3")}
for j, kernel in enumerate(KERN):
    for dtype in ("f32", "f64", "u32"):
        b = series("scalar_unroll8", kernel, dtype); a = series("auto", kernel, dtype)
        if len(a[0]) == 0 or len(a[0]) != len(b[0]): continue
        sp = b[1] / a[1]
        axs[j].errorbar(a[0], sp, yerr=[sp - b[1] / a[3], b[1] / a[2] - sp], color=LS[dtype][1], ls=LS[dtype][0], marker="o", ms=2.5, lw=1.3, capsize=1.5, label=dtype)
    axs[j].axhline(1, color="gray", lw=0.6); axs[j].set_title(f"{kernel}", loc="left"); axs[j].set_ylabel("speedup (auto / unrolled scalar)"); xfmt(axs[j]); vlines(axs[j]); axs[j].grid(alpha=0.25, which="both", lw=0.4)
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
fig.tight_layout(rect=[0, 0, 1, 0.95]); save(fig, "exp5_dtype")
# element throughput in cache vs DRAM, per dtype (bytes vs lanes)
fig, axs = plt.subplots(2, 2, figsize=(10.5, 7.2)); axs = axs.ravel()
for j, kernel in enumerate(KERN):
    for dtype in ("f32", "f64", "u32"):
        a = series("auto", kernel, dtype)
        if len(a[0]) == 0: continue
        axs[j].errorbar(a[0], a[4] / a[1], yerr=[a[4] / a[1] - a[4] / a[3], a[4] / a[2] - a[4] / a[1]], color=LS[dtype][1], ls=LS[dtype][0], marker="o", ms=2.5, lw=1.3, capsize=1.5, label=dtype)
    axs[j].set_yscale("log"); axs[j].set_title(f"{kernel} (auto build)", loc="left"); axs[j].set_ylabel("elements per ns"); xfmt(axs[j]); vlines(axs[j]); axs[j].grid(alpha=0.25, which="both", lw=0.4)
h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
fig.tight_layout(rect=[0, 0, 1, 0.95]); save(fig, "exp5_elements_per_ns")

with open(f"{ROOT}/data/processed/exp1_speedup_{SID}.csv", "w") as f:
    f.write("kernel,dtype,build,baseline,ws_bytes,n,speedup_median_ratio\n")
    for r in table: f.write("%s,%s,%s,%s,%d,%d,%.4f\n" % r)
print("thrown-away throttled samples:", sum(thr.values()), "of", len(rows))
print("plots written")

# key table cited by the report: speedups and cycles per element at three regimes
REG = [("L1 32KiB", 32 * 1024), ("L2 4MiB", 4 * 2**20), ("DRAM 1GiB", 2**30)]
def at(build, kernel, dtype, ws):
    w, med, lo, hi, nn = series(build, kernel, dtype)
    if len(w) == 0: return None
    i = int(np.argmin(np.abs(np.log(w / ws)))); return med[i], nn[i], w[i]
with open(f"{ROOT}/data/processed/exp1_key_table_{SID}.csv", "w") as f:
    f.write("dtype,kernel,regime,ws_bytes,auto_vs_unroll8,auto_vs_scalar,fastmath_vs_unroll8,auto_cycles_per_elem,unroll8_cycles_per_elem,scalar_cycles_per_elem,auto_GiB_s,auto_GFLOPs\n")
    for dtype in ("f32", "f64", "u32"):
        for kernel in KERN:
            for lab, ws in REG:
                a = at("auto", kernel, dtype, ws); u = at("scalar_unroll8", kernel, dtype, ws); s_ = at("scalar", kernel, dtype, ws); fm = at("fastmath", kernel, dtype, ws)
                if a is None or u is None: continue
                d = analyze.derive(kernel, dtype, int(a[1]), a[0])
                f.write("%s,%s,%s,%d,%.3f,%s,%.3f,%.3f,%.3f,%s,%.1f,%.2f\n" % (dtype, kernel, lab, a[2], u[0] / a[0], "%.3f" % (s_[0] / a[0]) if s_ else "", u[0] / fm[0] if fm else float("nan"),
                        a[0] / a[1] * GHZ, u[0] / u[1] * GHZ, "%.3f" % (s_[0] / s_[1] * GHZ) if s_ else "", d["gibs"], d["gflops"]))
print("key table written")
