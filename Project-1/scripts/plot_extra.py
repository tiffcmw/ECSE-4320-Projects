#!/usr/bin/env python3
"""Plots and tables for the final-submission experiments (A pointer chase, B traffic accounting, C dot decomposition,
D relative misalignment, E stride-jump probes). Usage: plot_extra.py <SID> [<SWEEP_SID>]
Reads data/raw/{chase,ceiling,dotdec,misalign,stridejump}_<SID>.csv and freq_<SID>.csv; the SAXPY sweep of <SWEEP_SID> (default phase3)
supplies the bandwidth curve for the latency comparison. Writes plots/exp9..exp13 (PNG and PDF) and data/processed/extra_*.
"""
import sys, os, csv, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import analyze

SID = sys.argv[1] if len(sys.argv) > 1 else "ext1"
SW = sys.argv[2] if len(sys.argv) > 2 else "phase3"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = f"{ROOT}/data/raw"
os.makedirs(f"{ROOT}/plots", exist_ok=True); os.makedirs(f"{ROOT}/data/processed", exist_ok=True)
GHZ, GERR = analyze.freq_ghz([f"{D}/freq_{SID}.csv"])
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10})
COL = {"scalar": "#8c8c8c", "scalar_unroll8": "#1f77b4", "auto": "#d95f02", "fastmath": "#7570b3", "native": "#1b9e77"}
out = [f"session {SID}: effective clock {GHZ:.3f} GHz (IQR half-width {GERR:.3f})"]
L1, L2 = 128 * 1024, 16 * 2**20


def save(fig, name):
    analyze.plain_log_axes(fig); fig.savefig(f"{ROOT}/plots/{name}.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{ROOT}/plots/{name}.pdf", bbox_inches="tight"); plt.close(fig)


def wsfmt(ax, lo=12, hi=31, step=2):
    ax.set_xscale("log", base=2)
    t = [2**k for k in range(lo, hi + 1, step)]
    ax.set_xticks(t); ax.set_xticklabels([("%d KiB" % (v // 1024)) if v < 2**20 else ("%d MiB" % (v // 2**20)) if v < 2**30 else "%d GiB" % (v // 2**30) for v in t], rotation=45, ha="right")


def mark_caches(ax, label=True):
    for name, b in (("L1D 128 KiB", L1), ("L2 16 MiB", L2)):
        ax.axvline(b, color="k", ls=":", lw=0.9)
        if label: ax.text(b, 0.98, " " + name, rotation=90, va="top", ha="right", fontsize=9, transform=ax.get_xaxis_transform())


def fmt_ws(v):
    return ("%d KiB" % (v // 1024)) if v < 2**20 else ("%d MiB" % (v // 2**20)) if v < 2**30 else "%.1f GiB" % (v / 2**30)

# ------------------------------------------------------------------ A: pointer chase
rows = list(csv.DictReader(open(f"{D}/chase_{SID}.csv")))
byws = collections.defaultdict(list); thr = 0; flt = collections.defaultdict(int)
for r in rows:
    if max(int(r["therm_before"]), int(r["therm_after"])) >= 1: thr += 1; continue
    byws[int(r["ws_bytes"])].append(float(r["ns_per_load"])); flt[int(r["ws_bytes"])] += int(r["minflt_timed"])
ws = np.array(sorted(byws)); st = [analyze.stats(byws[w]) for w in ws]
med = np.array([s["median"] for s in st]); q1 = np.array([s["q1"] for s in st]); q3 = np.array([s["q3"] for s in st])
out.append(f"chase: {len(rows)} samples, {thr} throttled dropped, page faults in timed regions: {sum(flt.values())}")
with open(f"{ROOT}/data/processed/extra_chase_{SID}.csv", "w") as f:
    f.write("ws_bytes,median_ns,q1_ns,q3_ns,median_cycles,samples\n")
    for w, s_ in zip(ws, st): f.write("%d,%.4f,%.4f,%.4f,%.3f,%d\n" % (w, s_["median"], s_["q1"], s_["q3"], s_["median"] * GHZ, s_["n"]))
def plateau(lo, hi):
    m = (ws >= lo) & (ws <= hi); v = med[m]
    return (float(np.median(v)), float(v.min()), float(v.max())) if len(v) else None
regions = [("L1 (4 to 64 KiB)", 4096, 64 * 1024), ("L2 (256 KiB to 8 MiB)", 256 * 1024, 8 * 2**20), ("16 to 32 MiB", 16 * 2**20, 32 * 2**20),
           ("48 to 192 MiB", 48 * 2**20, 192 * 2**20), ("DRAM (>= 512 MiB)", 512 * 2**20, 2**32)]
for name, lo, hi in regions:
    p = plateau(lo, hi)
    if p: out.append(f"chase plateau {name}: median {p[0]:.2f} ns = {p[0] * GHZ:.1f} cycles (range of medians {p[1]:.2f} to {p[2]:.2f} ns)")
steps = [(int(ws[i]), float(med[i] / med[i - 1])) for i in range(1, len(ws)) if med[i] / med[i - 1] > 1.15]
out.append("chase steps (> 15% rise between neighbouring sizes): " + ", ".join(f"{fmt_ws(w)} x{r:.2f}" for w, r in steps))
# SAXPY bandwidth curve from the sweep (auto, f32) for the implied-concurrency comparison
sw = analyze.load(sorted(__import__("glob").glob(f"{D}/sweep_{SW}_*.csv"))); gs, _ = analyze.group(sw)
bwk = sorted([k for k in gs if k[0] == "auto" and k[1] == "saxpy" and k[2] == "f32" and k[4] == 0 and k[5] == 1], key=lambda k: k[3])
bw_ws = np.array([k[3] * 8 for k in bwk]); bw = np.array([analyze.derive("saxpy", "f32", k[3], analyze.stats(gs[k])["median"])["gibs"] for k in bwk])
lat = np.interp(np.log(bw_ws), np.log(ws), med)           # ns at the SAXPY working sets
lines = bw * 2**30 * lat * 1e-9 / 128.0                    # implied 128 B lines in flight = bytes/s x latency / 128 B
fig, axs = plt.subplots(2, 2, figsize=(12.5, 9.0))
ax = axs[0, 0]
ax.fill_between(ws, q1, q3, color="#d95f02", alpha=0.25, lw=0); ax.plot(ws, med, "o-", color="#d95f02", ms=3.5, lw=1.3)
ax.set_yscale("log"); wsfmt(ax); mark_caches(ax); ax.set_xlabel("working set (bytes; one 128 B node per cache line)"); ax.set_ylabel("load-to-use latency (ns per dependent load)")
ax.set_title("(a) pointer-chase latency, median and IQR of 15 samples", loc="left", fontsize=11); ax.grid(alpha=0.25, which="both", lw=0.4)
sec = ax.secondary_yaxis("right", functions=(lambda y: y * GHZ, lambda c: c / GHZ)); sec.set_ylabel(f"cycles (at {GHZ:.2f} GHz)")
ax = axs[0, 1]
ax.plot(bw_ws, bw, "s-", color="#1b9e77", ms=3.5, lw=1.3); ax.set_ylim(0, 300); wsfmt(ax); mark_caches(ax)
ax.set_xlabel("SAXPY working set (bytes, x and y)"); ax.set_ylabel("SAXPY f32 bandwidth (GiB/s, counted bytes)"); ax.set_title("(b) SAXPY bandwidth from the locality sweep", loc="left", fontsize=11); ax.grid(alpha=0.25, which="both", lw=0.4)
ax = axs[1, 0]
ax.plot(bw_ws, lines, "s-", color="#7570b3", ms=3.5, lw=1.3); ax.set_yscale("log"); wsfmt(ax); mark_caches(ax)
ax.set_xlabel("SAXPY working set (bytes, x and y)"); ax.set_ylabel("implied 128 B lines in flight"); ax.set_title("(c) bandwidth x latency / 128 B", loc="left", fontsize=11); ax.grid(alpha=0.25, which="both", lw=0.4)
ax = axs[1, 1]
prow = list(csv.DictReader(open(f"{D}/chasepage_{SID}.csv"))); pd_ = collections.defaultdict(list)
for r in prow:
    if max(int(r["therm_before"]), int(r["therm_after"])) < 1: pd_[int(r["nodes"])].append(float(r["ns_per_load"]))
pn = np.array(sorted(pd_)); pst = [analyze.stats(pd_[n]) for n in pn]
pm = np.array([x["median"] for x in pst]); pq1 = np.array([x["q1"] for x in pst]); pq3 = np.array([x["q3"] for x in pst])
ax.fill_between(pn, pq1, pq3, color="#1f77b4", alpha=0.25, lw=0); ax.plot(pn, pm, "o-", color="#1f77b4", ms=3.5, lw=1.3)
ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.axvline(1024, color="k", ls=":", lw=0.9); ax.text(1024, 0.98, " 1024 lines = L1D", rotation=90, va="top", ha="right", fontsize=9, transform=ax.get_xaxis_transform())
ax.set_xlabel("nodes = pages touched (one node per 16 KiB page, one cache line each)"); ax.set_ylabel("load-to-use latency (ns per dependent load)"); ax.set_title("(d) page-granular chase (TLB test)", loc="left", fontsize=11); ax.grid(alpha=0.25, which="both", lw=0.4)
sec = ax.secondary_yaxis("right", functions=(lambda y: y * GHZ, lambda c: c / GHZ)); sec.set_ylabel(f"cycles (at {GHZ:.2f} GHz)")
fig.tight_layout(); save(fig, "exp9_chase_latency")
with open(f"{ROOT}/data/processed/extra_chasepage_{SID}.csv", "w") as f:
    f.write("nodes,median_ns,q1_ns,q3_ns,median_cycles\n")
    for n, x in zip(pn, pst): f.write("%d,%.4f,%.4f,%.4f,%.3f\n" % (n, x["median"], x["q1"], x["q3"], x["median"] * GHZ))
def pg(lo, hi):
    m = (pn >= lo) & (pn <= hi); return float(np.median(pm[m])) if m.any() else float("nan")
out.append(f"page-granular chase: pages 16 to 152 median {pg(16, 152):.2f} ns; 215 to 1024 median {pg(215, 1024):.2f} ns ({pg(215, 1024) * GHZ:.1f} cycles); 1217 to 1448 median {pg(1217, 1448):.2f} ns; 3444 to 16384 median {pg(3444, 16384):.2f} ns ({pg(3444, 16384) * GHZ:.1f} cycles)")
first = [int(n) for n, v in zip(pn, pm) if v > 1.4 * pg(16, 64)]
out.append(f"page-granular chase: first page count above 1.4x the 16-to-64 page latency: {first[0] if first else 'none'}")
for w in (2**15, 2**17, 2**20, 4 * 2**20, 16 * 2**20, 64 * 2**20, 256 * 2**20, 2**30):
    i = int(np.argmin(np.abs(np.log(bw_ws / w))))
    out.append(f"implied lines in flight at SAXPY ws {fmt_ws(int(bw_ws[i]))}: bandwidth {bw[i]:.0f} GiB/s x latency {lat[i]:.1f} ns / 128 B = {lines[i]:.1f}")

# ------------------------------------------------------------------ B: traffic accounting
rows = analyze.load([f"{D}/ceiling_{SID}.csv"]); g, thrc = analyze.group(rows)
COUNTED = {"read": 4, "incr": 8, "copy": 8, "scale": 8, "add": 12, "triad": 12, "saxpy": 12, "saxpy_oop": 12}       # compulsory bytes per element
WALLOC = {"read": 0, "incr": 0, "copy": 4, "scale": 4, "add": 4, "triad": 4, "saxpy": 0, "saxpy_oop": 4}              # extra bytes if every write-only line is first read (write-allocate)
ORDER = ["read", "incr", "saxpy", "copy", "scale", "add", "triad", "saxpy_oop"]
NICE = {"read": "read-only", "incr": "incr (y += a)", "saxpy": "SAXPY in place", "copy": "copy", "scale": "scale", "add": "add", "triad": "triad", "saxpy_oop": "SAXPY out of place"}
wsl = sorted(set(round(k[3] * COUNTED["saxpy"] * 4 / 1) for k in g if k[1] == "saxpy"))
def nominal(k):
    return k[3] * {"read": 4, "incr": 4, "copy": 8, "scale": 8, "add": 12, "triad": 12, "saxpy": 8, "saxpy_oop": 12}[k[1]]
NOM = [32768, 4194304, 67108864, 268435456, 1073741824]
tab = {}
for k in g:
    if k[2] != "f32": continue
    w = min(NOM, key=lambda v: abs(np.log(v / max(nominal(k), 1))))
    s_ = analyze.stats(g[k]); n = k[3]
    tab[(k[0], k[1], w)] = {"counted": COUNTED[k[1]] * n / s_["median"] * 1e9 / 2**30, "actual": (COUNTED[k[1]] + WALLOC[k[1]]) * n / s_["median"] * 1e9 / 2**30,
                            "lo": COUNTED[k[1]] * n / s_["q3"] * 1e9 / 2**30, "hi": COUNTED[k[1]] * n / s_["q1"] * 1e9 / 2**30, "ns_el": s_["median"] / n}
with open(f"{ROOT}/data/processed/extra_traffic_{SID}.csv", "w") as f:
    f.write("build,kernel,footprint_bytes,counted_GiB_s,counted_q1,counted_q3,with_write_allocate_GiB_s,ns_per_element\n")
    for (b, kn, w), v in sorted(tab.items()): f.write("%s,%s,%d,%.2f,%.2f,%.2f,%.2f,%.4f\n" % (b, kn, w, v["counted"], v["lo"], v["hi"], v["actual"], v["ns_el"]))
for w in NOM:
    for b in ("auto", "scalar_unroll8"):
        if all((b, kn, w) in tab for kn in ORDER):
            out.append(f"traffic {b} footprint {fmt_ws(w)}: counted GiB/s " + ", ".join(f"{kn} {tab[(b, kn, w)]['counted']:.1f}" for kn in ORDER))
            out.append(f"traffic {b} footprint {fmt_ws(w)}: with write-allocate GiB/s " + ", ".join(f"{kn} {tab[(b, kn, w)]['actual']:.1f}" for kn in ORDER))
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6), sharey=True)
dram = max(w for w in NOM if ("auto", "triad", w) in tab)
for ax, key, ttl in ((axs[0], "counted", "counted traffic (compulsory reads + writes)"), (axs[1], "actual", "counted + one allocate read per write-only stream")):
    x = np.arange(len(ORDER)); wd = 0.38
    for j, b in enumerate(("scalar_unroll8", "auto")):
        v = [tab[(b, kn, dram)][key] if (b, kn, dram) in tab else np.nan for kn in ORDER]
        if key == "counted":
            lo = [tab[(b, kn, dram)][key] - tab[(b, kn, dram)]["lo"] if (b, kn, dram) in tab else 0 for kn in ORDER]; hi = [tab[(b, kn, dram)]["hi"] - tab[(b, kn, dram)][key] if (b, kn, dram) in tab else 0 for kn in ORDER]
            ax.bar(x + (j - 0.5) * wd, v, wd, color=COL[b], label=b, yerr=[lo, hi], capsize=2)
        else:
            ax.bar(x + (j - 0.5) * wd, v, wd, color=COL[b], label=b)
    ax.set_xticks(x); ax.set_xticklabels([NICE[k] for k in ORDER], rotation=40, ha="right"); ax.set_title(ttl); ax.set_xlabel(f"kernel (f32, footprint {fmt_ws(dram)})"); ax.grid(axis="y", alpha=0.3)
axs[0].set_ylabel("GiB/s"); axs[0].legend(loc="upper right")
fig.tight_layout(); save(fig, "exp10_traffic_accounting")

# ------------------------------------------------------------------ C: dot decomposition
rows = analyze.load([f"{D}/dotdec_{SID}.csv"]); g, thrd = analyze.group(rows)
def dser(b, k, dt):
    ks = sorted([x for x in g if x[0] == b and x[1] == k and x[2] == dt], key=lambda x: x[3])
    w = np.array([x[3] * 2 * analyze.SIZEOF[dt] for x in ks]); s_ = [analyze.stats(g[x]) for x in ks]
    n = np.array([x[3] for x in ks])
    return w, np.array([s["median"] for s in s_]) / n * GHZ, np.array([s["q1"] for s in s_]) / n * GHZ, np.array([s["q3"] for s in s_]) / n * GHZ
curves = [("scalar", "dot_a1", "1 accumulator", "#8c8c8c", "-"), ("scalar", "dot_a4", "4 accumulators", "#1f77b4", "-"), ("scalar", "dot_a8", "8 accumulators", "#2ca02c", "-"),
          ("scalar", "dot_a16", "16 accumulators", "#17becf", "-"), ("auto", "dot_a16", "16 accumulators, NEON (auto)", "#d95f02", "-"), ("auto", "dot", "plain loop -O3 (strict, vector multiply)", "#e7298a", "--"),
          ("fastmath", "dot", "plain loop -O3 -ffast-math", "#7570b3", "-")]
fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.8), sharey=True)
for ax, dt in zip(axs, ("f32", "f64")):
    for b, k, lab, col, ls in curves:
        w, m, lo, hi = dser(b, k, dt)
        if len(w) == 0: continue
        ax.plot(w, m, ls, color=col, marker="o", ms=2.5, lw=1.3, label=lab); ax.fill_between(w, lo, hi, color=col, alpha=0.15, lw=0)
    ax.set_yscale("log"); wsfmt(ax); mark_caches(ax); ax.set_title(f"dot product {dt}"); ax.set_xlabel("working set (bytes, x and y)"); ax.grid(alpha=0.25, which="both", lw=0.4)
axs[0].set_ylabel(f"cycles per element (at {GHZ:.2f} GHz, assumed constant)")
axs[1].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)
fig.tight_layout(); save(fig, "exp11_dot_decomposition")
def dval(b, k, dt, w):
    ww, m, lo, hi = dser(b, k, dt); i = int(np.argmin(np.abs(np.log(ww / w)))); return m[i]
dtab = []
for dt in ("f32", "f64"):
    for lab, w in (("L1 32 KiB", 32768), ("L2 4 MiB", 4 * 2**20), ("DRAM 1 GiB", 2**30)):
        c = {nm: dval(b, k, dt, w) for nm, (b, k) in {"unroll8": ("scalar_unroll8", "dot"), "plain_scalar": ("scalar", "dot"), "a1": ("scalar", "dot_a1"), "a4": ("scalar", "dot_a4"), "a8": ("scalar", "dot_a8"),
                                                       "a16": ("scalar", "dot_a16"), "a16_neon": ("auto", "dot_a16"), "strict_auto": ("auto", "dot"), "fastmath": ("fastmath", "dot")}.items()}
        best = min(c["a4"], c["a8"], c["a16"])
        dtab.append((dt, lab, c["unroll8"], c["a1"], c["a4"], c["a8"], c["a16"], c["a16_neon"], c["fastmath"], c["unroll8"] / best, best / c["fastmath"], c["unroll8"] / c["fastmath"], best / c["a16_neon"]))
        out.append(f"dot {dt} {lab}: cycles/elem unroll8 {c['unroll8']:.2f}, a1 {c['a1']:.2f}, a4 {c['a4']:.2f}, a8 {c['a8']:.2f}, a16 {c['a16']:.2f}, a16 NEON {c['a16_neon']:.2f}, strict auto {c['strict_auto']:.2f}, fastmath {c['fastmath']:.2f}; "
                   f"chain-break gain (unroll8 / best scalar) {c['unroll8'] / best:.2f}x, SIMD gain (best scalar / fastmath) {best / c['fastmath']:.2f}x, total {c['unroll8'] / c['fastmath']:.2f}x, best scalar / a16 NEON {best / c['a16_neon']:.2f}x")
with open(f"{ROOT}/data/processed/extra_dot_decomposition_{SID}.csv", "w") as f:
    f.write("dtype,regime,unroll8_cyc,a1_cyc,a4_cyc,a8_cyc,a16_cyc,a16_neon_cyc,fastmath_cyc,chain_break_gain,simd_gain_over_best_scalar,total_gain,best_scalar_over_a16_neon\n")
    for t in dtab: f.write("%s,%s,%s\n" % (t[0], t[1], ",".join("%.3f" % x for x in t[2:])))

# ------------------------------------------------------------------ D: relative misalignment
rows = analyze.load([f"{D}/misalign_{SID}.csv"])
for r in rows: r["offset_y"] = int(r["offset_y"])
g, thrm = analyze.group(rows, keys=("build", "kernel", "dtype", "n", "offset", "offset_y"))
OFFS = [0, 4, 8, 16, 32, 64]
nset = sorted(set(k[3] for k in g)); builds = ("auto", "scalar_unroll8")
mal = {}
for b in builds:
    for n in nset:
        base = analyze.stats(g[(b, "saxpy", "f32", n, 0, 0)])["median"]
        for ox in OFFS:
            for oy in OFFS:
                kk = (b, "saxpy", "f32", n, ox, oy)
                if kk in g: mal[(b, n, ox, oy)] = analyze.stats(g[kk])["median"] / base
with open(f"{ROOT}/data/processed/extra_misalign_{SID}.csv", "w") as f:
    f.write("build,ws_bytes,x_offset,y_offset,time_ratio_to_0_0\n")
    for (b, n, ox, oy), v in sorted(mal.items()): f.write("%s,%d,%d,%d,%.4f\n" % (b, n * 8, ox, oy, v))
fig, axs = plt.subplots(1, len(nset), figsize=(6.3 * len(nset), 5.2))
axs = np.atleast_1d(axs)
for ax, n in zip(axs, nset):
    M = np.array([[mal.get(("auto", n, ox, oy), np.nan) for oy in OFFS] for ox in OFFS])
    im = ax.imshow(M, origin="lower", cmap="YlOrRd", vmin=1.0, vmax=max(1.5, np.nanmax(M)))
    for i in range(len(OFFS)):
        for j in range(len(OFFS)): ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=9)
    ax.set_xticks(range(len(OFFS))); ax.set_xticklabels(OFFS); ax.set_yticks(range(len(OFFS))); ax.set_yticklabels(OFFS)
    ax.set_xlabel("y start offset (bytes)"); ax.set_ylabel("x start offset (bytes)"); ax.set_title(f"{fmt_ws(n * 8)} working set", loc="left")
fig.suptitle("SAXPY f32, auto build: time relative to x and y both at offset 0 (median of 15 samples)", fontsize=12, y=1.02)
fig.colorbar(im, ax=axs.tolist(), shrink=0.8, label="time ratio"); save(fig, "exp12_relative_misalignment")
for b in builds:
    for n in nset:
        out.append(f"misalign {b} ws {fmt_ws(n * 8)}: " + "; ".join(f"x{ox}/y{oy} {mal[(b, n, ox, oy)]:.3f}" for ox, oy in ((4, 0), (0, 4), (4, 4), (4, 8), (8, 4), (8, 8), (16, 0), (0, 16), (16, 4), (4, 16), (32, 32), (64, 64), (64, 4)) if (b, n, ox, oy) in mal))

# ------------------------------------------------------------------ E: stride-jump probes
rows = analyze.load([f"{D}/stridejump_{SID}.csv"])
NOMS = [8388608, 67108864, 536870912]
byk = collections.defaultdict(list)
for r in rows:
    if r["therm"] >= 1: continue
    byk[(r["build"], r["kernel"], r["n"], r["ws_bytes"])].append(r["ns"])
def sj(build, kernel, wsn):
    c = [(k, v) for k, v in byk.items() if k[0] == build and k[1] == kernel and abs(np.log(k[3] / wsn)) < 0.15]
    if not c: return None
    k, v = min(c, key=lambda t: abs(np.log(t[0][3] / wsn))); s_ = analyze.stats(v); return s_["median"] / k[2], s_["q1"] / k[2], s_["q3"] / k[2], k[2]
SK = ["saxpy_s1", "saxpy_s16", "saxpy_s24", "saxpy_s32", "saxpy_s48"]; SX = [1, 16, 24, 32, 48]
fig, ax = plt.subplots(figsize=(7.6, 4.8))
for wsn, col in zip(NOMS, ("#1b9e77", "#7570b3", "#d95f02")):
    for b, ls in (("auto", "-"), ("scalar_unroll8", "--")):
        pts = [(x, sj(b, k, wsn)) for x, k in zip(SX, SK)]; pts = [(x, p) for x, p in pts if p]
        ax.errorbar([x for x, _ in pts], [p[0] for _, p in pts], yerr=[[p[0] - p[1] for _, p in pts], [p[2] - p[0] for _, p in pts]], color=col, ls=ls, marker="o", ms=4, capsize=2, label=f"{fmt_ws(wsn)}, {b}")
        for x, p in pts: out.append(f"stridejump {b} footprint {fmt_ws(wsn)} stride {x}: {p[0]:.3f} ns per touched element (IQR {p[1]:.3f} to {p[2]:.3f}), n={p[3]}")
ax.set_yscale("log"); ax.set_xticks(SX); ax.set_xlabel("stride (f32 elements; 32 elements = 128 B = one cache line)"); ax.set_ylabel("ns per touched element"); ax.grid(alpha=0.25, which="both", lw=0.4)
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False); fig.tight_layout(); save(fig, "exp13_stride_jump")
for kern in ("saxpy_s16", "saxpy_s32"):
    for n in (2097152, 2097153, 2097216):
        v = [(k, x) for k, x in byk.items() if k[0] == "auto" and k[1] == kern and k[2] == n]
        if v: out.append(f"stridejump n-probe {kern} n={n}: {analyze.stats(v[0][1])['median'] / n:.3f} ns per element (IQR {analyze.stats(v[0][1])['q1'] / n:.3f} to {analyze.stats(v[0][1])['q3'] / n:.3f})")
out.append(f"throttled samples dropped: ceiling {sum(thrc.values())}, dotdec {sum(thrd.values())}, misalign {sum(thrm.values())}")
open(f"{ROOT}/data/processed/extra_summary_{SID}.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
