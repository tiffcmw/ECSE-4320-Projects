#!/usr/bin/env python3
"""Exp 6 roofline and Exp 7/8 plots. Usage: plot_roofline.py <SWEEP_SID> <ROOF_SID>
Reads sweep_<SWEEP_SID>_*.csv, triad_/triadmp_/fmapeak_/alias_/restrict_smalln_/accuracy_/naive_ files of <ROOF_SID>."""
import sys, os, glob, csv, collections
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import analyze
SW = sys.argv[1] if len(sys.argv) > 1 else "phase3"; RS = sys.argv[2] if len(sys.argv) > 2 else "phase5"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = f"{ROOT}/data/raw"
GHZ, GERR = analyze.freq_ghz([f"{D}/freq_{RS}.csv"])
def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{ROOT}/plots/{name}.png", dpi=150); fig.savefig(f"{ROOT}/plots/{name}.pdf"); plt.close(fig)
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
dram = max(v for (b, dt, ws), v in bw.items() if b == "auto" and ws >= 256 * 2**20)
dram_f = [v for (b, dt, ws), v in bw.items() if b == "auto" and ws >= 256 * 2**20]
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
fig, axs = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
mk = {"saxpy": "o", "mul": "s", "dot": "^", "stencil": "D"}
regimes = [("L1 (32 KiB)", 32 * 1024, "#1b9e77"), ("L2 (4 MiB)", 4 * 2**20, "#7570b3"), ("DRAM (1 GiB)", 2**30, "#d95f02")]
tab = []
for ax, dt in zip(axs, ("f32", "f64")):
    pk = peak["4s"][0] if dt == "f32" else peak["2d"][0]
    x = np.logspace(-2.2, 1.2, 200)
    ax.plot(x, np.minimum(pk, x * dram * 2**30 / 1e9), "k-", lw=1.6, label=f"single-thread roof: DRAM {dram:.0f} GiB/s (triad), peak {pk:.0f} GFLOP/s (fmla sweep)")
    kk = [k for k in g if k[0] == "auto" and k[1] == "saxpy" and k[2] == dt]
    kk = min(kk, key=lambda k: abs(np.log(k[3] * 2 * analyze.SIZEOF[dt] / 2**30))); sx = analyze.derive("saxpy", dt, kk[3], analyze.stats(g[kk])["median"])["gibs"]
    ax.plot(x, np.minimum(pk, x * sx * 2**30 / 1e9), color="gray", ls="-.", lw=1.0, label=f"best observed DRAM-size rate (SAXPY plateau) {sx:.0f} GiB/s")
    l1 = max(v for (b, d_, ws), v in bw.items() if ws <= 64 * 1024 and d_ == dt)
    ax.plot(x, np.minimum(pk, x * l1 * 2**30 / 1e9), "k--", lw=0.9, label=f"L1 triad bandwidth {l1:.0f} GiB/s")
    for kernel in ("saxpy", "mul", "dot", "stencil"):
        for build, fill in (("auto", True), ("fastmath", False)):
            if kernel != "dot" and build == "fastmath": continue
            for lab, ws, col in regimes:
                m, lo, hi = pt(build, kernel, dt, ws); a = AI[(kernel, dt)]
                roof = min(pk, a * dram * 2**30 / 1e9)
                ax.errorbar(a, m, yerr=[[m - lo], [hi - m]], marker=mk[kernel], color=col, mfc=col if fill else "none", ms=7, capsize=2, lw=1)
                tab.append((dt, kernel, build, lab, a, m, roof, m / roof, m / min(pk, a * l1 * 2**30 / 1e9)))
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("arithmetic intensity (FLOP per byte of compulsory traffic)"); ax.set_title(f"Roofline, {dt} (single thread, Apple M5 Max, clock {GHZ:.2f} GHz)")
    ax.set_ylim(1, 600)
    for kernel, m_ in mk.items(): ax.plot([], [], m_, color="gray", label=f"{kernel}" + (" (hollow: -ffast-math)" if kernel == "dot" else ""))
    for lab, ws, col in regimes: ax.plot([], [], "o", color=col, label=lab)
    ax.legend(fontsize=6.5, loc="upper left")
axs[0].set_ylabel("GFLOP/s")
save(fig, "exp6_roofline")
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
fig, axs = plt.subplots(1, 2, figsize=(13, 4.3))
labs = []
for f, lab in (("alias_%s" % RS, "no overlap"), ("alias_%s_overlap1" % RS, "y = x + 1"), ("alias_%s_overlap64" % RS, "y = x + 64")):
    rows = analyze.load([f"{D}/{f}.csv"]); g2, _ = analyze.group(rows)
    for b in sorted(set(k[0] for k in g2)):
        for k in sorted(g2, key=lambda k: k[3]):
            if k[0] != b: continue
            out.append(f"alias {lab} {b} n={k[3]}: {np.median(g2[k]) / k[3] * GHZ:.2f} cycles per element")
rows_ = {lab: analyze.load([f"{D}/{f}.csv"]) for f, lab in (("alias_%s" % RS, "no overlap"), ("alias_%s_overlap1" % RS, "y = x + 1"), ("alias_%s_overlap64" % RS, "y = x + 64"))}
bars = []; names = []
for lab, rr_ in rows_.items():
    g2, _ = analyze.group(rr_)
    for b, col in (("auto", "#d95f02"), ("auto_norestrict", "#7570b3"), ("scalar_norestrict", "#8c8c8c"), ("scalar_unroll8", "#1f77b4")):
        ks = sorted([k for k in g2 if k[0] == b], key=lambda k: k[3])
        if not ks: continue
        axs[0].bar(len(names), np.median(g2[ks[0]]) / ks[0][3] * GHZ, color=col); names.append(f"{lab}\n{b}")
axs[0].set_xticks(range(len(names))); axs[0].set_xticklabels(names, fontsize=5.5, rotation=90); axs[0].set_yscale("log"); axs[0].set_ylabel("cycles per element (L1, 32 KiB)"); axs[0].set_title("SAXPY f32: restrict and overlap (L1 working set)")
rows = analyze.load([f"{D}/restrict_smalln_{RS}.csv"]); g3, _ = analyze.group(rows)
ns = sorted(set(k[3] for k in g3)); a = [np.median(g3[("auto", "saxpy", "f32", n, 0, 1)]) for n in ns]; b_ = [np.median(g3[("auto_norestrict", "saxpy", "f32", n, 0, 1)]) for n in ns]
axs[1].plot(ns, np.array(b_) / np.array(a), "o-", color="#7570b3"); axs[1].axhline(1, color="gray", lw=0.6); axs[1].set_xscale("log", base=2); axs[1].set_xlabel("N (non-overlapping arrays)"); axs[1].set_ylabel("time(no restrict) / time(restrict)"); axs[1].set_title("Cost of the runtime overlap check")
for n_, a_, b__ in zip(ns, a, b_): out.append(f"restrict small n={n_}: auto {a_:.2f} ns, norestrict {b__:.2f} ns, ratio {b__ / a_:.3f}")
save(fig, "exp7_alias_restrict")
# ---- naive vs fixed (Exp 8)
fig, ax = plt.subplots(figsize=(8, 4.2)); nr = list(csv.DictReader(open(f"{D}/naive_{RS}.csv"))); gg = collections.defaultdict(list)
for x in nr: gg[(x["experiment"], x["variant"])].append(float(x["GiB_per_s_useful"]))
exps = ["N1_hoist", "N2_zeropage", "N3_firsttouch"]
for i, e in enumerate(exps):
    for j, (v, col) in enumerate((("naive", "#d95f02"), ("fixed", "#1f77b4"))):
        vals = np.array(gg[(e, v)]); med = np.median(vals[np.isfinite(vals)]) if np.isfinite(vals).any() else np.nan
        inf = int((~np.isfinite(vals)).sum())
        ax.bar(i * 3 + j, med if np.isfinite(med) else 1e4, color=col, label=v if i == 0 else None); ax.text(i * 3 + j, (med if np.isfinite(med) else 1e4) * 1.05, ("inf in %d/%d" % (inf, len(vals))) if inf > len(vals) / 2 else "%.0f" % med, ha="center", fontsize=8)
        out.append(f"naive {e} {v}: median {med:.1f} GiB/s, {inf} of {len(vals)} runs infinite (0 ns measured)")
ax.set_xticks([0.5, 3.5, 6.5]); ax.set_xticklabels(["N1 hoisted loop", "N2 zero-page read", "N3 first touch"]); ax.set_yscale("log"); ax.set_ylabel("claimed GiB/s (useful data)"); ax.legend(); ax.set_title("Exp 8: naive vs corrected benchmark"); ax.set_ylim(10, 2e4)
save(fig, "exp8_naive_vs_fixed")
open(f"{ROOT}/data/processed/phase5_summary_{RS}.txt", "w").write("\n".join(out) + "\n")
print("\n".join(l for l in out if not l.startswith("roofline") and not l.startswith("alias") and not l.startswith("accuracy")))
