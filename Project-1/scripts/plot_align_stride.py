#!/usr/bin/env python3
"""Phase 4 plots: tail study, alignment, stride and gather. Usage: plot_align_stride.py <SID>"""
import sys, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import analyze
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10})
SID = sys.argv[1] if len(sys.argv) > 1 else "phase4"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GHZ, _ = analyze.freq_ghz([f"{ROOT}/data/raw/freq_{SID}.csv"])
COL = {"scalar": "#8c8c8c", "scalar_unroll8": "#1f77b4", "auto": "#d95f02", "auto_forcevec": "#7570b3"}
def save(fig, name, relayout=True):
    if relayout: fig.tight_layout()
    analyze.plain_log_axes(fig); fig.savefig(f"{ROOT}/plots/{name}.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{ROOT}/plots/{name}.pdf", bbox_inches="tight"); plt.close(fig)
def ser(g, build, kernel, dtype, key_idx, filt=lambda k: True):
    ks = sorted([k for k in g if k[0] == build and k[1] == kernel and k[2] == dtype and filt(k)], key=lambda k: k[key_idx])
    return ks, [analyze.stats(g[k]) for k in ks]

out = []
# ---- Tail study
rows = analyze.load([f"{ROOT}/data/raw/tail_{SID}.csv"]); g, thr = analyze.group(rows)
fig, axs = plt.subplots(2, 2, figsize=(14, 8))
for j, dt in enumerate(("f32", "f64")):
    for b in ("scalar", "scalar_unroll8", "auto"):
        ks, st = ser(g, b, "saxpy", dt, 3, lambda k: k[3] <= 160)
        n = np.array([k[3] for k in ks]); m = np.array([s["median"] for s in st]); lo = np.array([s["q1"] for s in st]); hi = np.array([s["q3"] for s in st])
        axs[0, j].errorbar(n, m, yerr=[m - lo, hi - m], color=COL[b], marker=".", ms=3, lw=0.8, capsize=1, label=b)
        axs[1, j].plot(n, m / n * GHZ, color=COL[b], marker=".", ms=3, lw=0.8, label=b)
    axs[0, j].set_title(f"SAXPY {dt}: time per call vs N (N = 1..160)"); axs[0, j].set_xlabel("N (elements)"); axs[0, j].set_ylabel("ns per call (call overhead subtracted)")
    axs[1, j].set_title(f"{dt}: cycles per element vs N (at {GHZ:.2f} GHz)"); axs[1, j].set_yscale("log"); axs[1, j].set_xlabel("N"); axs[1, j].set_ylabel("cycles per element")
    lanes = 4 if dt == "f32" else 2
    for a in axs[:, j]:
        for x in range(0, 161, 16): a.axvline(x, color="k", lw=0.3, ls=":")
    axs[0, j].legend(fontsize=7)
save(fig, "exp3_tail_small_n")
# affine fit for N >= 16 and sawtooth numbers
fit = {}
for dt in ("f32", "f64"):
    for b in ("scalar", "scalar_unroll8", "auto"):
        ks, st = ser(g, b, "saxpy", dt, 3, lambda k: 32 <= k[3] <= 160)
        n = np.array([k[3] for k in ks], float); m = np.array([s["median"] for s in st])
        A = np.vstack([n, np.ones_like(n)]).T; (slope, icpt), *_ = np.linalg.lstsq(A, m, rcond=None)
        fit[(dt, b)] = (slope, icpt); out.append(f"fit {dt} {b}: ns = {slope:.4f} * N + {icpt:.2f}   (N 32..160)")
# mod-16 sawtooth at moderate N
fig, axs = plt.subplots(1, 3, figsize=(15, 4.3))
for j, (lo_n, hi_n, ttl) in enumerate(((250, 266, "N = 250..265"), (1020, 1030, "N = 1020..1029"), (4090, 4112, "N = 4090..4111"))):
    for b in ("scalar_unroll8", "auto"):
        ks, st = ser(g, b, "saxpy", "f32", 3, lambda k: lo_n <= k[3] < hi_n)
        n = np.array([k[3] for k in ks]); m = np.array([s["median"] for s in st]); lo = np.array([s["q1"] for s in st]); hi = np.array([s["q3"] for s in st])
        axs[j].errorbar(n, m, yerr=[m - lo, hi - m], color=COL[b], marker="o", ms=3, capsize=1.5, label=b)
        if b == "auto":
            sl, ic = fit[("f32", "auto")]
            for x_, y_ in zip(n, m): pass
            out.append(f"tail residual {ttl} auto f32 vs affine fit: " + ", ".join(f"{int(a)}:{(c - (sl * a + ic)):+.1f}" for a, c in zip(n, m)))
    axs[j].set_title("SAXPY f32 " + ttl); axs[j].set_xlabel("N"); axs[j].set_ylabel("ns per call")
    for x in range((lo_n // 16) * 16, hi_n, 16): axs[j].axvline(x, color="k", lw=0.4, ls=":")
axs[0].legend(fontsize=7)
save(fig, "exp3_tail_mod16")

# ---- Alignment
rows = analyze.load([f"{ROOT}/data/raw/align_{SID}.csv"]); g, thr = analyze.group(rows)
fig, axs = plt.subplots(1, 3, figsize=(16, 4.3))
wss = sorted(set(k[3] for k in g))
for j, n in enumerate(wss):
    for b in ("scalar_unroll8", "auto"):
        ks, st = ser(g, b, "saxpy", "f32", 4, lambda k: k[3] == n)
        off = np.array([k[4] for k in ks]); m = np.array([s["median"] for s in st]); lo = np.array([s["q1"] for s in st]); hi = np.array([s["q3"] for s in st])
        base = m[off == 0][0]
        axs[j].errorbar(off, m / base, yerr=[(m - lo) / base, (hi - m) / base], color=COL[b], marker="o", ms=3, capsize=1.5, label=b)
        out.append(f"align {b} n={n} ws={n*8}: ratio to offset 0: " + ", ".join(f"{int(o)}:{r:.3f}" for o, r in zip(off, m / base)))
    axs[j].set_title(f"SAXPY f32 alignment, working set {n*8//1024} KiB"); axs[j].set_xlabel("array start offset (bytes, both arrays)"); axs[j].set_ylabel("time relative to offset 0")
    axs[j].axhline(1, color="gray", lw=0.6)
    for x in (16, 64, 128): axs[j].axvline(x, color="k", lw=0.4, ls=":")
axs[0].legend(fontsize=7)
save(fig, "exp3_alignment")

# ---- Stride and gather
rows = analyze.load([f"{ROOT}/data/raw/stride_{SID}.csv"])
NOMINAL = [32768, 524288, 8388608, 67108864, 536870912]   # requested footprints (scripts/exp_align_stride.sh); n rounding makes actual ws_bytes differ slightly per kernel
for r in rows: r["wsn"] = min(NOMINAL, key=lambda w: abs(np.log(w / r["ws_bytes"])))
nom_present = sorted(set(r["wsn"] for r in rows))
g, thr = analyze.group(rows, keys=("build", "kernel", "dtype", "wsn", "stride", "n"))
wss = sorted(set(k[3] for k in g))
kern_order = ["saxpy_s1", "saxpy_s2", "saxpy_s4", "saxpy_s8", "saxpy_s16", "saxpy_s32", "gather"]
fig, axs = plt.subplots(2, 3, figsize=(12.5, 7.6)); axf = axs.ravel()
for j, ws in enumerate(wss):
    ax = axf[j]
    for b in ("scalar_unroll8", "auto", "auto_forcevec"):
        xs, ns_el, nlo, nhi = [], [], [], []
        for ki, k in enumerate(kern_order):
            keys = [kk for kk in g if kk[0] == b and kk[1] == k and kk[3] == ws]
            if not keys: continue
            kk = keys[0]; s = analyze.stats(g[kk]); n = kk[5]
            d = analyze.derive(k, "f32", n, s["median"])
            xs.append(ki); ns_el.append(s["median"] / n); nlo.append(s["q1"] / n); nhi.append(s["q3"] / n)
            out.append(f"stride ws={ws} {b} {k}: {s['median']/n:.4f} ns/elem, {d['gibs']:.1f} GiB/s useful, {s['median']/n*GHZ:.2f} cyc/elem")
        ns_el, nlo, nhi = map(np.array, (ns_el, nlo, nhi))
        ax.errorbar(xs, ns_el, yerr=[ns_el - nlo, nhi - ns_el], color=COL[b], marker="o", ms=5, lw=1.4, capsize=2, label=b)
    ax.set_xticks(range(len(kern_order))); ax.set_xticklabels(["1", "2", "4", "8", "16", "32", "gather"]); ax.set_yscale("log"); ax.grid(alpha=0.25, which="both", lw=0.4)
    ax.set_title(f"footprint {ws // 1024} KiB" if ws < 2**20 else f"footprint {ws // 2**20} MiB", loc="left"); ax.set_xlabel("stride (f32 elements) or random gather")
    ax.set_ylabel("ns per touched element")
for ax in axf[len(wss):]: ax.axis("off")
h, l = axf[0].get_legend_handles_labels()
axf[5].legend(h, l, loc="center", frameon=False, fontsize=12, title="build")
save(fig, "exp4_stride_gather")
open(f"{ROOT}/data/processed/phase4_summary_{SID}.txt", "w").write("\n".join(out) + "\n")
print("done", len(out), "summary lines; throttled dropped:", sum(thr.values()))
