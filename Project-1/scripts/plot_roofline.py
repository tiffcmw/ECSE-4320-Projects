#!/usr/bin/env python3
"""Exp 6 roofline and Exp 7/8 plots. Usage: plot_roofline.py <SWEEP_SID> <ROOF_SID>
Reads sweep_<SWEEP_SID>_*.csv, triad_/triadmp_/fmapeak_/alias_/restrict_smalln_/accuracy_/naive_ files of <ROOF_SID>."""
import sys, os, glob, csv, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import analyze
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10})
SW = sys.argv[1] if len(sys.argv) > 1 else "phase3"; RS = sys.argv[2] if len(sys.argv) > 2 else "phase5"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = f"{ROOT}/data/raw"
GHZ, GERR = analyze.freq_ghz([f"{D}/freq_{RS}.csv"])
def save(fig, name, relayout=True):
    if relayout: fig.tight_layout()
    fig.savefig(f"{ROOT}/plots/{name}.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{ROOT}/plots/{name}.pdf", bbox_inches="tight"); plt.close(fig)
out = []
# ---- FMA peak
r = list(csv.DictReader(open(f"{D}/fmapeak_{RS}.csv")))
fig, ax = plt.subplots(figsize=(7, 4.3)); peak = {}
for arr, col in (("4s", "#d95f02"), ("2d", "#1b9e77")):
    ns, med, lo, hi = [], [], [], []
    for n in range(1, 31):
        v = np.array([float(x["ns_per_fmla"]) for x in r if x["arrangement"] == arr and int(x["accumulators"]) == n])
        ns.append(n); med.append(1 / np.median(v) / GHZ); lo.append(1 / np.percentile(v, 75) / GHZ); hi.append(1 / np.percentile(v, 25) / GHZ)
    med, lo, hi = map(np.array, (med, lo, hi))
    ax.errorbar(ns, med, yerr=[med - lo, hi - med], color=col, marker="o", ms=3, capsize=1.5, label=f"fmla.{arr}")
    b = int(np.argmax(med)); flop = 8 if arr == "4s" else 4
    peak[arr] = (med[b] * flop * GHZ, lo[b] * flop * GHZ, hi[b] * flop * GHZ); out.append(f"fma peak {arr}: {med[b]:.2f} fmla/cycle at {ns[b]} accumulators = {peak[arr][0]:.1f} GFLOP/s (IQR {peak[arr][1]:.1f}-{peak[arr][2]:.1f}), plateau median over N>=12: {np.median(med[11:]):.2f}")
ax.set_xlabel("independent accumulators"); ax.set_ylabel(f"fmla per cycle (at {GHZ:.2f} GHz)"); ax.set_title("FMA throughput sweep (single thread)"); ax.legend(); ax.axhline(4, color="k", lw=0.5, ls=":")
save(fig, "exp6_fma_peak")
# ---- bandwidth ceilings from triad (single process) and multi-process aggregate
rows = analyze.load([f"{D}/triad_{RS}.csv"]); g, _ = analyze.group(rows)
bw = {}
for k in g:
    s = analyze.stats(g[k]); d = analyze.derive("triad", k[2], k[3], s["median"]); ws = k[3] * 3 * analyze.SIZEOF[k[2]]
    bw[(k[0], k[2], ws)] = d["gibs"]
BIG = 200 * 2**20  # DRAM-size threshold; sizes are rounded down slightly by the harness
dram = max(v for (b, dt, ws), v in bw.items() if b == "auto" and ws >= BIG)
dram_f = [v for (b, dt, ws), v in bw.items() if b == "auto" and ws >= BIG]
out.append(f"triad single-process DRAM-size bandwidth (auto, 256 MiB to 2 GiB, f32 and f64): min {min(dram_f):.1f}, max {max(dram_f):.1f} GiB/s of counted traffic (2 reads + 1 write)")
agg = {}
for f in glob.glob(f"{D}/triadmp_{RS}_k*_p*.csv"):
    k = int(f.split("_k")[1].split("_")[0]); rr = analyze.load([f]); v = [x["ns"] for x in rr]; agg.setdefault(k, []).append(analyze.derive("triad", "f32", rr[0]["n"], np.median(v))["gibs"])
for k in sorted(agg): out.append(f"triad {k} concurrent processes: aggregate {sum(agg[k]):.0f} GiB/s, per process {', '.join('%.0f' % x for x in sorted(agg[k]))}")
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ks = sorted(agg); ax.plot(ks, [sum(agg[k]) for k in ks], "o-", color="#d95f02", label="aggregate"); ax.plot(ks, [sum(agg[k]) / k for k in ks], "s--", color="#1f77b4", label="mean per process")
ax.set_xlabel("concurrent single-thread processes"); ax.set_ylabel("GiB/s (triad, f32, 512 MiB per process set)"); ax.set_title("Bandwidth scaling with process count"); ax.legend()
save(fig, "exp6_bandwidth_scaling")
# ---- roofline
rows = analyze.load(sorted(glob.glob(f"{D}/sweep_{SW}_*.csv"))); g, _ = analyze.group(rows)
AI = {("saxpy", "f32"): 2 / 12, ("saxpy", "f64"): 2 / 24, ("mul", "f32"): 1 / 12, ("mul", "f64"): 1 / 24, ("dot", "f32"): 2 / 8, ("dot", "f64"): 2 / 16, ("stencil", "f32"): 5 / 8, ("stencil", "f64"): 5 / 16}
na = {"mul": 3}
def pt(build, kernel, dt, ws):
    ks = [k for k in g if k[0] == build and k[1] == kernel and k[2] == dt]
    k = min(ks, key=lambda k: abs(np.log(k[3] * na.get(kernel, 2) * analyze.SIZEOF[dt] / ws)))
    s = analyze.stats(g[k]); d = analyze.derive(kernel, dt, k[3], s["median"]); dh = analyze.derive(kernel, dt, k[3], s["q1"]); dl = analyze.derive(kernel, dt, k[3], s["q3"])
    return d["gflops"], dl["gflops"], dh["gflops"]
# Bandwidth ceiling convention (counted compulsory bytes, no write-allocate). Single ceiling = the highest DRAM-size counted bandwidth of any
# pattern in the traffic experiment, which is in-place SAXPY; per dtype it is taken from the SAXPY sweep at about 1 GiB (same value within 5%).
# Alternatives drawn thinner: triad (STREAM-style, 2 reads + 1 write counted) and triad with one allocate read added (speculative).
fig, axs = plt.subplots(1, 2, figsize=(12.5, 7.4), sharey=True)
mk = {"saxpy": "o", "mul": "s", "dot": "^", "stencil": "D"}
regimes = [("L1 (32 KiB)", 32 * 1024, "#1b9e77"), ("L2 (4 MiB)", 4 * 2**20, "#7570b3"), ("DRAM (1 GiB)", 2**30, "#d95f02")]
tab = []
for ax, dt in zip(axs, ("f32", "f64")):
    pk = peak["4s"][0] if dt == "f32" else peak["2d"][0]
    x = np.logspace(-2.2, 1.2, 200)
    kk = [k for k in g if k[0] == "auto" and k[1] == "saxpy" and k[2] == dt]
    kk = min(kk, key=lambda k: abs(np.log(k[3] * 2 * analyze.SIZEOF[dt] / 2**30))); sx = analyze.derive("saxpy", dt, kk[3], analyze.stats(g[kk])["median"])["gibs"]
    dram_main = sx
    ax.plot(x, np.minimum(pk, x * dram_main * 2**30 / 1e9), "k-", lw=2.0, label=f"memory ceiling used: {dram_main:.0f} GiB/s (best counted DRAM-size rate of any pattern, SAXPY)")
    tri = [v for (b, d_, ws), v in bw.items() if b == "auto" and d_ == dt and ws >= BIG]
    ax.plot(x, np.minimum(pk, x * min(tri) * 2**30 / 1e9), color="gray", ls="--", lw=1.1, label=f"alternative: triad, counted {min(tri):.0f} GiB/s")
    ax.plot(x, np.minimum(pk, x * min(tri) * 4 / 3 * 2**30 / 1e9), color="gray", ls=":", lw=1.1, label=f"alternative: triad with one allocate read per written array, {min(tri) * 4 / 3:.0f} GiB/s (unverified)")
    ax.axhline(pk, color="#b22222", lw=1.2, label=f"compute peak {pk:.0f} GFLOP/s (fmla sweep)")
    l1c = [v for (b, d_, ws), v in bw.items() if ws <= 64 * 1024 and d_ == dt]
    l1 = max(l1c) if l1c else max(v for (b, d_, ws), v in bw.items() if d_ == dt)  # QUICK runs have no L1-size triad point
    ax.plot(x, np.minimum(pk, x * l1 * 2**30 / 1e9), "k-.", lw=0.9, label=f"L1 triad bandwidth {l1:.0f} GiB/s")
    for kernel in ("saxpy", "mul", "dot", "stencil"):
        for build, fill in (("auto", True), ("fastmath", False)):
            if kernel != "dot" and build == "fastmath": continue
            for lab, ws, col in regimes:
                m, lo, hi = pt(build, kernel, dt, ws); a = AI[(kernel, dt)]
                roof = min(pk, a * dram_main * 2**30 / 1e9)
                ax.errorbar(a, m, yerr=[[m - lo], [hi - m]], marker=mk[kernel], color=col, mfc=col if fill else "none", ms=8, capsize=2, lw=1)
                tab.append((dt, kernel, build, lab, a, m, roof, m / roof, m / min(pk, a * l1 * 2**30 / 1e9)))
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("arithmetic intensity (FLOP per byte of compulsory traffic)"); ax.set_title(f"{dt}", loc="left")
    ax.set_ylim(1, 600); ax.grid(alpha=0.25, which="both", lw=0.4)
    out.append(f"roofline {dt}: memory ceiling {dram_main:.1f} GiB/s (in-place SAXPY at about 1 GiB); triad counted min {min(tri):.1f} GiB/s over DRAM-size points; L1 {l1:.0f} GiB/s")
h, l = axs[0].get_legend_handles_labels()
for kernel, m_ in mk.items(): h.append(plt.Line2D([], [], marker=m_, color="gray", ls="", label=f"{kernel}" + (" (hollow: -ffast-math)" if kernel == "dot" else "")))
for lab, ws, col in regimes: h.append(plt.Line2D([], [], marker="o", color=col, ls="", label=lab))
fig.tight_layout(rect=[0, 0.255, 1, 1]); fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.0))
axs[0].set_ylabel("GFLOP/s")
save(fig, "exp6_roofline", relayout=False)
with open(f"{ROOT}/data/processed/roofline_points_{RS}.csv", "w") as f:
    f.write("dtype,kernel,build,regime,arithmetic_intensity,gflops,dram_roof_gflops,frac_of_dram_roof,frac_of_l1_roof\n")
    for t in tab: f.write("%s,%s,%s,%s,%.4f,%.3f,%.3f,%.3f,%.3f\n" % t)
for t in tab:
    if t[0] == "f32": out.append("roofline f32 %s %s %s: AI %.3f, %.1f GFLOP/s, %.0f%% of DRAM-roof, %.0f%% of L1-roof" % (t[1], t[2], t[3], t[4], t[5], 100 * t[7], 100 * t[8]))
# ---- accuracy
rr = list(csv.DictReader(open(f"{D}/accuracy_{RS}.csv"))); gg = collections.defaultdict(list)
for x in rr: gg[(x["dtype"], int(x["N"]), x["build"])].append(float(x["rel_err_over_eps"]))
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, dt in zip(axs, ("f32", "f64")):
    for b, col, ls in (("scalar", "#8c8c8c", "-"), ("auto", "#d95f02", "--"), ("native", "#1b9e77", ":"), ("fastmath", "#7570b3", "-")):
        Ns = sorted(set(k[1] for k in gg if k[0] == dt)); 
        ax.plot(Ns, [np.median(gg[(dt, n, b)]) for n in Ns], ls=ls, color=col, marker="o", ms=3, label=b)
    Ns = np.array(sorted(set(k[1] for k in gg if k[0] == dt)), float); ax.plot(Ns, np.sqrt(Ns), "k:", lw=0.8, label="sqrt(N)")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("N"); ax.set_ylabel("|error| / |sum| in units of eps"); ax.set_title(f"dot product {dt}: error vs double-double reference"); ax.legend(fontsize=7)
save(fig, "exp7_reduction_accuracy")
for dt in ("f32", "f64"):
    for n in sorted(set(k[1] for k in gg if k[0] == dt)): out.append(f"accuracy {dt} N={n}: " + " ".join(f"{b}={np.median(gg[(dt, n, b)]):.3g}eps" for b in ("scalar", "scalar_unroll8", "auto", "native", "fastmath")))
# ---- aliasing / restrict
fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.0))
labs = []
for f, lab in (("alias_%s" % RS, "no overlap"), ("alias_%s_overlap1" % RS, "y = x + 1"), ("alias_%s_overlap64" % RS, "y = x + 64")):
    rows = analyze.load([f"{D}/{f}.csv"]); g2, _ = analyze.group(rows)
    for b in sorted(set(k[0] for k in g2)):
        for k in sorted(g2, key=lambda k: k[3]):
            if k[0] != b: continue
            out.append(f"alias {lab} {b} n={k[3]}: {np.median(g2[k]) / k[3] * GHZ:.2f} cycles per element")
rows_ = {lab: analyze.load([f"{D}/{f}.csv"]) for f, lab in (("alias_%s" % RS, "arrays do not overlap"), ("alias_%s_overlap1" % RS, "y = x + 1 element"), ("alias_%s_overlap64" % RS, "y = x + 64 elements"))}
BUILDS = (("auto", "#d95f02", "auto, restrict"), ("auto_norestrict", "#7570b3", "auto, no restrict"), ("scalar_norestrict", "#8c8c8c", "scalar, no restrict"), ("scalar_unroll8", "#1f77b4", "scalar, unroll 8 (restrict)"))
wd = 0.2
for gi, (lab, rr_) in enumerate(rows_.items()):
    g2, _ = analyze.group(rr_)
    for bi, (b, col, nm) in enumerate(BUILDS):
        ks = sorted([k for k in g2 if k[0] == b], key=lambda k: k[3])
        if not ks: continue
        v = np.median(g2[ks[0]]) / ks[0][3] * GHZ; sq = analyze.stats(g2[ks[0]])
        axs[0].bar(gi + (bi - 1.5) * wd, v, wd, color=col, label=nm if gi == 0 else None,
                   yerr=[[v - sq["q1"] / ks[0][3] * GHZ], [sq["q3"] / ks[0][3] * GHZ - v]], capsize=2)
        axs[0].text(gi + (bi - 1.5) * wd, sq["q3"] / ks[0][3] * GHZ * 1.08, "%.2f" % v if v < 10 else "%.1f" % v, ha="center", fontsize=9)
axs[0].set_xticks(range(3)); axs[0].set_xticklabels(list(rows_.keys())); axs[0].set_yscale("log"); axs[0].set_ylabel("cycles per element (32 KiB working set)")
axs[0].set_title("SAXPY f32: restrict and overlap", loc="left"); axs[0].set_ylim(0.1, 40); axs[0].grid(axis="y", alpha=0.3, which="both", lw=0.4)
axs[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
rows = analyze.load([f"{D}/restrict_smalln_{RS}.csv"]); g3, _ = analyze.group(rows)
ns = sorted(set(k[3] for k in g3)); a = [np.median(g3[("auto", "saxpy", "f32", n, 0, 1)]) for n in ns]; b_ = [np.median(g3[("auto_norestrict", "saxpy", "f32", n, 0, 1)]) for n in ns]
axs[1].plot(ns, np.array(b_) / np.array(a), "o-", color="#7570b3", ms=5, lw=1.4); axs[1].axhline(1, color="gray", lw=0.6); axs[1].set_xscale("log", base=2); axs[1].set_xlabel("N (elements, non-overlapping arrays)"); axs[1].set_ylabel("time without restrict / time with restrict")
axs[1].set_title("Cost of the runtime overlap check", loc="left"); axs[1].grid(alpha=0.3, which="both", lw=0.4)
for n_, a_, b__ in zip(ns, a, b_): out.append(f"restrict small n={n_}: auto {a_:.2f} ns, norestrict {b__:.2f} ns, ratio {b__ / a_:.3f}")
fig.tight_layout()
save(fig, "exp7_alias_restrict", relayout=False)
# ---- naive vs fixed (Exp 8)
fig, ax = plt.subplots(figsize=(8.5, 4.6)); nr = list(csv.DictReader(open(f"{D}/naive_{RS}.csv"))); gg = collections.defaultdict(list)
for x in nr: gg[(x["experiment"], x["variant"])].append(float(x["GiB_per_s_useful"]))
exps = ["N1_hoist", "N2_zeropage", "N3_firsttouch"]; INF_H = 8e3
for i, e in enumerate(exps):
    for j, (v, col) in enumerate((("naive", "#d95f02"), ("fixed", "#1f77b4"))):
        vals = np.array(gg[(e, v)]); med = np.median(vals[np.isfinite(vals)]) if np.isfinite(vals).any() else np.nan
        inf = int((~np.isfinite(vals)).sum()); is_inf = inf > len(vals) / 2
        h = INF_H if is_inf else med
        ax.bar(i * 3 + j, h, color=col, hatch="//" if is_inf else None, edgecolor="k" if is_inf else col, label=("naive" if j == 0 else "corrected") if i == 0 else None)
        ax.text(i * 3 + j, h * 1.07, "inf (0 ns timed)" if is_inf else "%.0f" % med, ha="center", fontsize=10)
        out.append(f"naive {e} {v}: median {med:.1f} GiB/s, {inf} of {len(vals)} runs infinite (0 ns measured)")
ax.set_xticks([0.5, 3.5, 6.5]); ax.set_xticklabels(["N1 hoisted loop", "N2 zero-page read", "N3 first touch in timed region"]); ax.set_yscale("log")
ax.set_ylabel("claimed bandwidth (GiB/s of useful data)"); ax.set_title("Naive versus corrected benchmark (hatched bar: 0 ns timed, bandwidth infinite, height arbitrary)", fontsize=10, loc="left")
ax.set_ylim(10, 3e4); ax.grid(axis="y", alpha=0.3, which="both", lw=0.4); ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
save(fig, "exp8_naive_vs_fixed")
open(f"{ROOT}/data/processed/phase5_summary_{RS}.txt", "w").write("\n".join(out) + "\n")
print("\n".join(l for l in out if not l.startswith("roofline") and not l.startswith("alias") and not l.startswith("accuracy")))
