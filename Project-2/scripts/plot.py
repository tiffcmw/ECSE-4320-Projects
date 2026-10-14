#!/usr/bin/env python3
"""Figures and derived tables from data/processed. Error bars / bands are the IQR over rounds."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import analysis_lib as A
from analysis_lib import load, sel, series, fb, LINE

os.makedirs(A.PLOTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.bbox": "tight"})
C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#999999"]
TABLES = []


def save(fig, name):
    fig.savefig(os.path.join(A.PLOTS, name + ".png"), dpi=150)
    fig.savefig(os.path.join(A.PLOTS, name + ".pdf"))
    plt.close(fig)


def bytes_axis(ax, which="x"):
    f = FuncFormatter(lambda v, _: fb(v).replace(" ", ""))
    axis = ax.xaxis if which == "x" else ax.yaxis
    lo, hi = (ax.get_xlim() if which == "x" else ax.get_ylim())
    ticks = [2.0 ** k for k in range(0, 40, 3) if lo * 0.99 <= 2.0 ** k <= hi * 1.01]
    if which == "x" and ticks:
        ax.set_xticks(ticks); ax.minorticks_off()
    axis.set_major_formatter(f)


def band(ax, x, m, q1, q3, color, label, marker="o", ms=2.5, ls="-"):
    ax.plot(x, m, ls, color=color, marker=marker, ms=ms, lw=1.3, label=label)
    ax.fill_between(x, q1, q3, color=color, alpha=0.2, lw=0)


def table(title, header, rows):
    t = [f"### {title}", "", "| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    t += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    TABLES.append("\n".join(t) + "\n")


FGHZ = A.freq_ghz()


def region_edges(ws, lat):
    """Level boundaries inferred from the latency curve (not from counters)."""
    at = lambda s: lat[np.argmin(np.abs(ws - s))]
    p1, p2, p3 = at(32 * 1024), at(4 * 2**20), lat[-1]
    e1 = next((w for w, l in zip(ws, lat) if l > 1.5 * p1), ws[-1])
    e2 = next((w for w, l in zip(ws, lat) if w > 2**20 and l > 1.5 * p2), ws[-1])
    e3 = next((w for w, l in zip(ws, lat) if w > e2 and l >= 0.9 * p3), ws[-1])
    return e1, e2, e3, p1, p2, p3


# ------------------------------------------------------------------ Exp 1 and 5
def exp1_exp5():
    ch = load("e1_chase"); bw = load("e5_bw")
    if not ch:
        return
    ws, m, q1, q3, n = series(ch, "ws_bytes", metric="ns_per_load")
    e1, e2, e3, p1, p2, p3 = region_edges(ws, m)
    json.dump({"L1_edge": e1, "L2_edge": e2, "DRAM_edge": e3, "p_L1": p1, "p_L2_4MiB": p2, "p_DRAM": p3},
              open(os.path.join(A.PROC, "regions.json"), "w"), indent=1)
    # zero-queue table at canonical sizes
    rows = []
    for lvl, size, note in (("L1", 32 * 1024, "within 128 KiB Super L1D; 64 KiB Performance L1D would miss here only above 64 KiB"),
                            ("L2", 4 * 2**20, "within 8 MiB (Performance) and 16 MiB (Super) L2"),
                            ("L2, near capacity", 12 * 2**20, "fits Super L2 (16 MiB) but not Performance L2 (8 MiB)"),
                            ("SLC region", 64 * 2**20, "beyond L2; SLC size unknown (not exposed), inside the ramp"),
                            ("DRAM", 1 * 2**30, "far beyond any cache; TLB misses included")):
        i = int(np.argmin(np.abs(ws - size)))
        if abs(ws[i] - size) / size > 0.01:
            continue
        rows.append([lvl, fb(ws[i]), f"{m[i]:.2f} ({q1[i]:.2f} to {q3[i]:.2f})", f"{m[i] * FGHZ:.0f}", int(n[i]), note])
    idle = A.idle_latency()
    if idle == idle:
        rows.append(["DRAM (loaded harness, 0 BW threads)", "1 GiB", f"{idle:.1f}", f"{idle * FGHZ:.0f}", "", "cross-check; separate process, probe thread only"])
    table(f"Zero-queue latency (random single-cycle chase, one thread, f = {FGHZ:.2f} GHz estimated)",
          ["Level", "Working set", "ns, median (IQR)", "cycles (est.)", "n", "Notes"], rows)

    fig, ax = plt.subplots(figsize=(7.2, 3.8), layout="constrained")
    band(ax, ws, m, q1, q3, C[0], "random chase, Super core (QoS interactive)")
    for x, lab, ls in ((A.L1D["Super"], "L1D 128 KiB (Super)", "--"), (A.L1D["Performance"], "L1D 64 KiB (Perf.)", ":"),
                       (A.L2["Performance"], "L2 8 MiB (Perf.)", ":"), (A.L2["Super"], "L2 16 MiB (Super)", "--")):
        ax.axvline(x, color="#777", ls=ls, lw=0.9)
        ax.text(x, 1.15 * p3, lab, rotation=90, va="top", ha="right", fontsize=7, color="#555")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.axhspan(0.4, 1.5 * p1, color=C[2], alpha=0.07); ax.axhspan(p2 / 1.5, 1.5 * p2, color=C[4], alpha=0.07)
    ax.axhspan(0.9 * p3, 1.6 * p3, color=C[1], alpha=0.07)
    ax.text(ws[0], 1.5 * p1 * 1.05, "L1 level", fontsize=7, color=C[2]); ax.text(ws[0], 1.5 * p2 * 1.05, "L2 level", fontsize=7, color=C[4])
    ax.text(ws[0], 1.6 * p3 * 1.03, "DRAM level", fontsize=7, color=C[1])
    ax.set_xlabel("working set (bytes, log2 scale)"); ax.set_ylabel("latency per dependent load (ns, log)")
    ax.set_title("Exp 1: zero-queue latency vs working set (shaded bands: plateau levels, not counters)", fontsize=9)
    bytes_axis(ax); ax.legend(loc="upper left", fontsize=7)
    save(fig, "exp1_zero_queue")

    # Exp 5: latency + bandwidth with annotated regions
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True)
    band(a1, ws, m, q1, q3, C[0], "latency (random chase)")
    a1.set_yscale("log"); a1.set_ylabel("latency (ns, log)")
    if bw:
        bws, bm, b1, b3, bn = series(bw, "ws_bytes", metric="gbps_app", variant="r10w0")
        band(a2, bws, bm, b1, b3, C[1], "sequential read, 1 thread (NEON, 128 B per step)")
        a2.set_yscale("log"); a2.set_ylabel("read bandwidth (GB/s, log)")
        a2.axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); a2.text(bws[0], A.PEAK_GBPS * 1.05, "published DRAM peak 460 GB/s", fontsize=7, color="#555")
    for ax in (a1, a2):
        for (lo, hi, name, col) in ((ws[0], e1, "L1", C[2]), (e1, e2, "L2", C[4]), (e2, e3, "SLC / transition", C[3]), (e3, ws[-1], "DRAM", C[1])):
            ax.axvspan(lo, hi, color=col, alpha=0.08, lw=0)
    for lo, hi, name in ((ws[0], e1, "L1"), (e1, e2, "L2"), (e2, e3, "SLC /\ntransition"), (e3, ws[-1], "DRAM")):
        a1.text(np.sqrt(lo * hi), a1.get_ylim()[1] * 0.8, name, ha="center", va="top", fontsize=8)
    a2.set_xscale("log", base=2); a2.set_xlabel("working set (bytes, log2 scale)"); bytes_axis(a2)
    a1.set_title(f"Exp 5: working-set sweep (region edges from curve: L1 {fb(e1)}, L2 {fb(e2)}, DRAM-like from {fb(e3)})", fontsize=9)
    a1.legend(fontsize=7, loc="upper left"); a2.legend(fontsize=7, loc="upper right")
    save(fig, "exp5_working_set")
    table("Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)",
          ["Edge", "Working set", "sysctl capacity (Super)"], [["L1 to L2", fb(e1), "128 KiB L1D"], ["L2 to SLC", fb(e2), "16 MiB L2"], ["into DRAM plateau", fb(e3), "SLC not exposed"]])


# ------------------------------------------------------------------ Exp 2
def exp2():
    st = load("e2_chase_stride"); pat = load("e2_pat")
    if not st and not pat:
        return
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 3.6), layout="constrained")
    ax = axs[0]
    for i, (mode, lab) in enumerate((("rand", "random order"), ("seq", "sequential order"))):
        x, m, q1, q3, n = series(st, "stride", metric="ns_per_load", variant=mode)
        if len(x):
            ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i], capsize=2, label=lab)
    ax.axvline(128, color="#777", ls=":", lw=0.9)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("node stride (B)"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(a) pointer chase, DRAM-sized footprint", fontsize=9); ax.legend(fontsize=7); bytes_axis(ax)
    for ax, mode in ((axs[1], "seq"), (axs[2], "rand")):
        for j, sz in enumerate((16, 32, 64, 128)):
            x, m, q1, q3, n = series(pat, "stride", metric="gbps_useful", variant=mode, size=sz)
            if len(x):
                ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[j], capsize=2, label=f"{sz} B per access")
        ax.axvline(128, color="#777", ls=":", lw=0.9); ax.annotate("128 B line", xy=(128, 0.02), xycoords=("data", "axes fraction"), fontsize=7, color="#555", ha="left")
        ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("stride between accesses (B)")
        ax.set_ylabel("useful bandwidth (GB/s, bytes requested)")
        ax.set_title(f"({'b' if mode == 'seq' else 'c'}) independent loads, {'sequential' if mode == 'seq' else 'random slots'}", fontsize=9)
        ax.legend(fontsize=7); bytes_axis(ax)
    fig.suptitle("Exp 2: pattern and granularity (1 thread, footprint far beyond cache; bars = IQR over rounds)", fontsize=9)
    save(fig, "exp2_pattern_granularity")
    rows = []
    for mode in ("seq", "rand"):
        x, m, q1, q3, n = series(st, "stride", metric="ns_per_load", variant=mode)
        for xi, mi, a, b in zip(x, m, q1, q3):
            rows.append(["chase", mode, int(xi), f"{mi:.1f} ns ({a:.1f} to {b:.1f})", f"{LINE / mi:.1f} GB/s line-rate"])
    table("Pointer-chase latency per node vs stride (DRAM footprint)", ["Test", "Order", "Stride B", "Latency", "Implied line rate"], rows)
    rows = []
    for mode in ("seq", "rand"):
        for sz in (16, 64, 128):
            for s in (64, 128, 256, 1024, 16384):
                x, m, q1, q3, n = series(pat, "stride", metric="gbps_useful", variant=mode, size=sz)
                for xi, mi in zip(x, m):
                    if xi == s:
                        rows.append([mode, sz, s, f"{mi:.2f}"])
    table("Independent-load useful bandwidth (GB/s of bytes requested), selected points", ["Order", "Access B", "Stride B", "GB/s"], rows)


# ------------------------------------------------------------------ Exp 3
KORDER = ["r10w0", "r7w3_st", "r5w5_st", "r0w10_st", "r7w3_nt", "r5w5_nt", "r0w10_nt", "r0w10_zva", "rmw"]
KLAB = {"r10w0": "100% R", "r7w3_st": "70/30 st", "r5w5_st": "50/50 st", "r0w10_st": "100% W st", "r7w3_nt": "70/30 stnp",
        "r5w5_nt": "50/50 stnp", "r0w10_nt": "100% W stnp", "r0w10_zva": "100% W dc zva", "rmw": "50/50 rmw"}


def traffic_factor(k):
    """DRAM bytes per application byte if stores allocate (model; no counters): reads + 2x writes for plain stores."""
    if k.endswith("_st"):
        w = int(k.split("w")[1].split("_")[0]); r = int(k[1:].split("w")[0])
        return (r + 2 * w) / (r + w)
    return 1.0


def exp3():
    bw = load("e3_mix_bw"); ld = load("e3_mix_loaded")
    if not bw and not ld:
        return
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.8), layout="constrained")
    ax = axs[0]
    sizes = sorted({r["ws_bytes"] for r in bw})
    w = 0.8 / max(1, len(sizes))
    for si, s in enumerate(sizes):
        xs, ms, lo, hi = [], [], [], []
        for ki, k in enumerate(KORDER):
            r = sel(bw, variant=k, ws_bytes=s, metric="gbps_app")
            if r:
                xs.append(ki + si * w); ms.append(r[0]["median"]); lo.append(r[0]["median"] - r[0]["q1"]); hi.append(r[0]["q3"] - r[0]["median"])
        ax.bar(xs, ms, w, yerr=[lo, hi], color=C[si], label=fb(s), capsize=1.5)
    ax.set_xticks(np.arange(len(KORDER)) + w * (len(sizes) - 1) / 2); ax.set_xticklabels([KLAB[k] for k in KORDER], rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("application GB/s (1 thread)"); ax.set_title("(a) mix throughput by footprint", fontsize=9); ax.legend(title="footprint", fontsize=7)
    mixes = [k for k in ("r10w0", "r7w3_st", "r5w5_st", "r0w10_st", "r0w10_nt", "r0w10_zva", "rmw") if sel(ld, variant=k)]
    for i, k in enumerate(mixes):
        x, m, q1, q3, n = series(ld, "threads", variant=k, metric="bw_gbps")
        axs[1].errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i % 8], capsize=2, label=KLAB[k])
        x, m, q1, q3, n = series(ld, "threads", variant=k, metric="lat_ns")
        axs[2].errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i % 8], capsize=2, label=KLAB[k])
    axs[1].axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); axs[1].text(0.5, A.PEAK_GBPS * 1.02, "published peak 460 GB/s", fontsize=7, color="#555")
    axs[1].set_xlabel("bandwidth threads"); axs[1].set_ylabel("aggregate application GB/s"); axs[1].set_title("(b) throughput vs threads", fontsize=9); axs[1].legend(fontsize=7)
    axs[2].set_xlabel("bandwidth threads"); axs[2].set_ylabel("probe latency (ns, random chase)"); axs[2].set_title("(c) loaded read latency vs threads", fontsize=9)
    fig.suptitle("Exp 3: read/write mix (single-thread footprints, and multi-thread loaded latency; bars = IQR)", fontsize=9)
    save(fig, "exp3_rw_mix")
    rows = []
    big = max(sizes) if sizes else 0
    for k in KORDER:
        r = sel(bw, variant=k, ws_bytes=big, metric="gbps_app")
        if r:
            t = traffic_factor(k)
            rows.append([KLAB[k], f"{r[0]['median']:.1f} ({r[0]['q1']:.1f} to {r[0]['q3']:.1f})", f"{t:.2f}", f"{r[0]['median'] * t:.1f}"])
    table(f"Single-thread mix at {fb(big)} footprint: application GB/s and write-allocate-corrected DRAM traffic (model, not measured)",
          ["Mix", "application GB/s (IQR)", "traffic factor (model)", "modeled DRAM GB/s"], rows)
    rows = []
    for k in mixes:
        for N in (4, 16):
            b = sel(ld, variant=k, metric="bw_gbps", threads=N); l = sel(ld, variant=k, metric="lat_ns", threads=N)
            l0 = sel(ld, variant=k, metric="lat_ns", threads=0)
            if b and l and l0:
                rows.append([KLAB[k], N, f"{b[0]['median']:.0f}", f"{l[0]['median']:.0f}", f"{l[0]['median'] / l0[0]['median']:.2f}x"])
    table("Loaded latency by mix (probe thread + N bandwidth threads)", ["Mix", "N threads", "app GB/s", "probe ns", "vs idle"], rows)


# ------------------------------------------------------------------ Exp 4
def little_points():
    ld = load("e4_loaded")
    pts = []
    for ex, tag in (("e4_loaded_threads", "threads"), ("e4_loaded_delay", "delay, 16 thr"), ("e4_loaded_delay6", "delay, 6 thr")):
        keys = sorted({(r["threads"], r["param"]) for r in sel(ld, exp=ex, metric="bw_gbps")})
        for t, p in keys:
            b = sel(ld, exp=ex, metric="bw_gbps", threads=t, param=p); l = sel(ld, exp=ex, metric="lat_ns", threads=t, param=p)
            if b and l and t > 0:
                pts.append((tag, int(t), p, b[0]["median"], l[0]["median"], b[0]["q1"], b[0]["q3"], l[0]["q1"], l[0]["q3"]))
    return pts


def exp4():
    mlp = load("e4_mlp"); ld = load("e4_loaded")
    if not mlp and not ld:
        return
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.8), layout="constrained")
    ax = axs[0]
    kx, bm, b1, b3, _ = series(mlp, "param", metric="gbps")
    _, lm, l1, l3, _ = series(mlp, "param", metric="ns_per_step")
    L0 = lm[0] if len(lm) else float("nan")
    if len(kx):
        ax.errorbar(kx, bm, yerr=[bm - b1, b3 - bm], marker="o", ms=3, color=C[0], capsize=2, label="measured throughput")
        ax.plot(kx, kx * LINE / L0, "--", color="#777", lw=1, label=f"ideal K x 128 B / {L0:.0f} ns")
        a2 = ax.twinx(); a2.errorbar(kx, lm, yerr=[lm - l1, l3 - lm], marker="s", ms=3, color=C[1], capsize=2, label="latency per step")
        a2.set_ylabel("ns per chain step", color=C[1]); a2.grid(False)
    ax.set_xscale("log", base=2); ax.set_xlabel("independent chains K (outstanding loads) in one thread"); ax.set_ylabel("GB/s")
    ax.set_title("(a) one core: throughput vs concurrency", fontsize=9); ax.legend(fontsize=7, loc="upper left")
    pts = little_points(); idle = A.idle_latency()
    ax = axs[1]
    for i, tag in enumerate(("threads", "delay, 16 thr", "delay, 6 thr")):
        P = sorted([p for p in pts if p[0] == tag], key=lambda p: p[3])
        if P:
            ax.errorbar([p[3] for p in P], [p[4] for p in P], xerr=[[p[3] - p[5] for p in P], [p[6] - p[3] for p in P]],
                        yerr=[[p[4] - p[7] for p in P], [p[8] - p[4] for p in P]], marker="o", ms=3, color=C[i], capsize=2, label=tag)
    if idle == idle:
        ax.axhline(idle, color="#777", ls=":", lw=0.9); ax.annotate(f"idle {idle:.0f} ns", xy=(0.02, idle), xycoords=("axes fraction", "data"), xytext=(0, 3), textcoords="offset points", fontsize=7, color="#555")
        ax.axhline(1.5 * idle, color="#777", ls="--", lw=0.9); ax.annotate("1.5 x idle", xy=(0.02, 1.5 * idle), xycoords=("axes fraction", "data"), xytext=(0, 3), textcoords="offset points", fontsize=7, color="#555")
    ax.axvline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9)
    ax.set_xlabel("aggregate read bandwidth (GB/s)"); ax.set_ylabel("loaded latency (ns, probe thread)")
    ax.set_title("(b) throughput-latency curve", fontsize=9); ax.legend(fontsize=7)
    allp = sorted(pts, key=lambda p: p[3]); knee_txt = ""
    if allp and idle == idle:
        below = [p for p in allp if p[4] <= 1.5 * idle]
        k15 = max(below, key=lambda p: p[3]) if below else None
        pw = max(allp, key=lambda p: p[3] / p[4]); sat = max(allp, key=lambda p: p[3])
        if k15:
            ax.plot([k15[3]], [k15[4]], "k*", ms=11, zorder=5); ax.annotate("knee (1.5x idle)", (k15[3], k15[4]), xytext=(8, -16), textcoords="offset points", fontsize=7)
        ax.plot([pw[3]], [pw[4]], "D", color="k", ms=5, zorder=5, mfc="none"); ax.annotate("max BW/latency", (pw[3], pw[4]), xytext=(-60, 14), textcoords="offset points", fontsize=7)
        rows = [["highest BW with latency <= 1.5x idle", f"{k15[3]:.0f} GB/s", f"{k15[4]:.0f} ns", f"{k15[3] * k15[4] / LINE:.0f}", k15[0] + f" N={k15[1]}, delay={k15[2]:.0f}"] if k15 else ["(none)", "", "", "", ""],
                ["max BW / latency (power) point", f"{pw[3]:.0f} GB/s", f"{pw[4]:.0f} ns", f"{pw[3] * pw[4] / LINE:.0f}", pw[0] + f" N={pw[1]}, delay={pw[2]:.0f}"],
                ["maximum measured BW", f"{sat[3]:.0f} GB/s ({100 * sat[3] / A.PEAK_GBPS:.0f}% of 460)", f"{sat[4]:.0f} ns", f"{sat[3] * sat[4] / LINE:.0f}", sat[0] + f" N={sat[1]}, delay={sat[2]:.0f}"]]
        table(f"Knee and Little's Law: lines in flight N = BW x latency / 128 B (idle latency {idle:.0f} ns)",
              ["Point", "bandwidth", "loaded latency", "N (lines in flight)", "config"], rows)
    ax = axs[2]
    for i, tag in enumerate(("threads", "delay, 16 thr", "delay, 6 thr")):
        P = sorted([p for p in pts if p[0] == tag], key=lambda p: p[3])
        if P:
            ax.plot([p[3] for p in P], [p[3] * p[4] / LINE for p in P], "o-", ms=3, color=C[i], label=tag)
    if len(kx):
        ax.axhline(bm.max() * L0 / LINE, color="#777", ls=":", lw=0.9)
        ax.annotate(f"one-core plateau: {bm.max() * L0 / LINE:.0f} lines", xy=(0.02, bm.max() * L0 / LINE), xycoords=("axes fraction", "data"), xytext=(0, 3), textcoords="offset points", fontsize=7, color="#555")
    ax.set_xlabel("aggregate read bandwidth (GB/s)"); ax.set_ylabel("N = BW x latency / 128 B (lines in flight)")
    ax.set_title("(c) Little's Law: inferred in-flight lines", fontsize=9); ax.legend(fontsize=7)
    fig.suptitle("Exp 4: intensity sweep (loaded-latency harness: 1 probe chase thread + N sequential-read threads; bars = IQR)", fontsize=9)
    save(fig, "exp4_intensity")
    if len(kx):
        rows = [[int(k), f"{g:.1f}", f"{l:.0f}", f"{g * L0 / LINE:.1f}"] for k, g, l in zip(kx, bm, lm)]
        table(f"Single-core concurrency sweep: N_eff = throughput x L0 / 128 B with L0 = {L0:.0f} ns (K = 1 latency)",
              ["K chains", "GB/s", "ns per step", "N_eff (lines)"], rows)
    if allp:
        rows = [[p[0], p[1], f"{p[2]:.0f}", f"{p[3]:.1f}", f"{p[4]:.0f}", f"{p[3] * p[4] / LINE:.0f}"] for p in allp]
        table("All loaded-latency points (median over rounds)", ["series", "BW threads", "delay iters", "GB/s", "latency ns", "N lines"], rows)


# ------------------------------------------------------------------ Exp 6
def amat_curve():
    ch = load("e1_chase")
    ws, m, *_ = series(ch, "ws_bytes", metric="ns_per_load")
    return ws, m


def exp6():
    k = load("e6_kern")
    if not k:
        return
    mlp = load("e4_mlp")
    _, bm, *_ = series(mlp, "param", metric="gbps"); _, lm, *_ = series(mlp, "param", metric="ns_per_step")
    Ncore = max(1.0, bm.max() * lm[0] / LINE) if len(bm) else 16.0
    ws_c, lat_c = amat_curve()
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.8), layout="constrained")
    mults = sorted({r["stride"] for r in k if r["metric"] == "ns_per_elem" and r["stride"] != 4 * 40503})
    for ai, kern in enumerate(("mul", "saxpy")):
        ax = axs[ai]
        for j, s in enumerate(mults + [4.0 * 40503]):
            x, m, q1, q3, n = series(k, "ws_bytes", metric="ns_per_elem", variant=kern, stride=s)
            if len(x):
                lab = "unit stride (4 B)" if s == 4 else ("scattered (Weyl index)" if s == 4.0 * 40503 else f"stride {int(s)} B")
                band(ax, x, m, q1, q3, C[j % 8] if s != 4.0 * 40503 else "#000000", lab, ls="--" if s == 4.0 * 40503 else "-")
        # AMAT-style prediction for scattered: t_hit + (L(F) - L_L1) / N_core
        x, m, *_ = series(k, "ws_bytes", metric="ns_per_elem", variant=kern, stride=4.0 * 40503)
        if len(x):
            Lf = np.interp(np.log2(x), np.log2(ws_c), lat_c)
            pred = m[0] + np.maximum(Lf - lat_c[0], 0) / Ncore
            ax.plot(x, pred, ":", color="#000", lw=1.3, label=f"AMAT model, scattered (N={Ncore:.0f})")
        ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("kernel footprint (bytes touched)"); ax.set_ylabel("ns per element")
        ax.set_title(f"({'a' if ai == 0 else 'b'}) {'z[i] = x[i]*y[i]' if kern == 'mul' else 'y[i] = a*x[i] + y[i]'} (f32)", fontsize=9)
        bytes_axis(ax)
        if ai == 0:
            ax.legend(fontsize=6, ncol=1)
    ax = axs[2]
    for ai, kern in enumerate(("mul", "saxpy")):
        big = max(r["ws_bytes"] for r in sel(k, variant=kern))
        xs, ms = [], []
        for s in mults + [4.0 * 40503]:
            r = sel(k, variant=kern, ws_bytes=big, stride=s, metric="ns_per_elem")
            base = sel(k, variant=kern, ws_bytes=big, stride=4.0, metric="ns_per_elem")
            if r and base:
                xs.append(s); ms.append(r[0]["median"] / base[0]["median"])
        ax.plot(xs, ms, "o-", ms=3, color=C[ai], label=f"{kern} at {fb(big)}")
    ax.axvline(128, color="#777", ls=":", lw=0.9); ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("element stride (B); right-most point = scattered")
    ax.set_ylabel("slowdown vs unit stride, same footprint"); ax.set_title("(c) DRAM-resident slowdown by pattern", fontsize=9); ax.legend(fontsize=7)
    fig.suptitle("Exp 6: kernel runtime vs footprint and access pattern (miss behavior inferred from timing; no counters)", fontsize=9)
    save(fig, "exp6_kernels")
    rows = []
    for kern in ("mul", "saxpy"):
        for s, lab in ((4.0, "unit"), (64.0, "stride 64 B"), (4.0 * 40503, "scattered")):
            x, m, q1, q3, n = series(k, "ws_bytes", metric="ns_per_elem", variant=kern, stride=s)
            if len(x) >= 2:
                Lf = np.interp(np.log2(x), np.log2(ws_c), lat_c)
                miss_per_elem = 1.0 / 32 if s == 4 else (1.0 if s >= 128 else 0.5 if s == 64 else 1.0)
                pred = m[0] + miss_per_elem * np.maximum(Lf - lat_c[0], 0) / Ncore
                rows.append([kern, lab, f"{m[0]:.3f}", f"{m[-1]:.3f}", f"{m[-1] / m[0]:.1f}x", f"{pred[-1]:.3f}", f"{m[-1] / pred[-1]:.2f}"])
    table(f"Kernel cost: smallest vs largest footprint and AMAT-style prediction (hit time + miss ratio x (L(F) - L_L1) / N, N = {Ncore:.0f} lines from Exp 4)",
          ["Kernel", "Pattern", "ns/elem smallest", "ns/elem largest", "ratio", "AMAT pred. largest ns", "measured/pred."], rows)


# ------------------------------------------------------------------ Exp 7
def exp7():
    t = load("e7_tlb_pages") or load("e7_tlb")
    if not t:
        return
    pa = sel(t, exp="e7_tlb_pages", variant="paged", metric="ns_per_load"); pk = sel(t, exp="e7_tlb_pages", variant="packed", metric="ns_per_load")
    fx = sel(t, exp="e7_tlb_fixedL", metric="ns_per_load")
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.6), layout="constrained")
    ax = axs[0]
    x, m, q1, q3, _ = series(pa, "ws_bytes", metric="ns_per_load"); xpg, _, _, _, _ = series(pa, "param", metric="ns_per_load")
    band(ax, xpg, m, q1, q3, C[1], "one line per distinct 16 KiB page")
    x2, m2, a2, b2, _ = series(pk, "ws_bytes", metric="ns_per_load"); lines = x2 / LINE
    band(ax, lines / 128.0 if False else sorted({r["param"] for r in pa}), m2, a2, b2, C[0], "same number of lines, packed contiguously")
    ax.set_xscale("log", base=2); ax.set_xlabel("distinct pages touched (= lines for the paged layout)"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(a) pages touched, 1 line per page", fontsize=9); ax.legend(fontsize=7)
    ax = axs[1]
    pen = m - m2 if len(m) == len(m2) else None
    if pen is not None:
        ax.plot(xpg, pen, "o-", color=C[2], ms=3); ax.axhline(0, color="#777", lw=0.8)
        for reach, lab in ((256, "256 pg = 4 MiB"), (2048, "2048 pg = 32 MiB"), (16384, "16384 pg = 256 MiB")):
            ax.axvline(reach, color="#777", ls=":", lw=0.8); ax.text(reach, ax.get_ylim()[1] * 0.92, lab, rotation=90, fontsize=6, ha="right", va="top")
    ax.set_xscale("log", base=2); ax.set_xlabel("distinct pages touched"); ax.set_ylabel("paged minus packed latency (ns)")
    ax.set_title("(b) penalty attributed to address translation", fontsize=9)
    ax = axs[2]
    x, m3, q1, q3, _ = series(fx, "param", metric="ns_per_load")
    if len(x):
        band(ax, x, m3, q1, q3, C[3], "32768 lines (4 MiB) over P pages")
    ax.set_xscale("log", base=2); ax.set_xlabel("distinct pages P holding the same 32768 lines"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(c) fixed cache footprint, vary pages", fontsize=9); ax.legend(fontsize=7)
    fig.suptitle("Exp 7: TLB effect via page locality (16 KiB pages; huge-page comparison not possible on macOS)", fontsize=9)
    save(fig, "exp7_tlb")
    if pen is not None:
        rows = [[int(p), f"{a:.2f}", f"{b:.2f}", f"{a - b:+.2f}"] for p, a, b in zip(xpg, m, m2)]
        table("TLB experiment: latency with one line per page vs the same number of lines packed (median ns)", ["pages touched", "paged", "packed", "difference"], rows)
    if len(x):
        table("Fixed 4 MiB of lines spread over P pages (median ns)", ["P pages", "ns"], [[int(p), f"{v:.2f}"] for p, v in zip(x, m3)])


# ------------------------------------------------------------------ Exp 8
def exp8():
    pit = load("e8_pitfalls")
    if not pit:
        return
    e5 = load("e5_bw")
    fig, axs = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    ax = axs[0, 0]
    res = sel(pit, exp="pitfall_resident_bw", metric="bw_gbps")
    x, m, q1, q3, _ = series(res, "ws_bytes", metric="bw_gbps")
    if len(x):
        ax.errorbar(x * 16, m, yerr=[m - q1, q3 - m], marker="o", ms=4, color=C[1], capsize=2, label="16 threads, private buffers")
        ax.axhline(m[-1], color="#777", ls=":", lw=0.9); ax.text(x[0] * 16, m[-1] * 1.04, "DRAM-resident value", fontsize=7, color="#555")
    ax.axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9)
    ax.set_xscale("log", base=2); ax.set_xlabel("total footprint = 16 x per-thread buffer (bytes)"); ax.set_ylabel("aggregate read GB/s"); bytes_axis(ax)
    ax.set_title("(a) pitfall 1: cache-resident buffer reported as 'DRAM bandwidth'", fontsize=8); ax.legend(fontsize=7)
    ax = axs[0, 1]
    ch = load("e1_chase"); sq = sel(pit, exp="pitfall_seqchase", metric="ns_per_load")
    x, m, q1, q3, _ = series(ch, "ws_bytes", metric="ns_per_load"); band(ax, x, m, q1, q3, C[0], "random chase (correct)")
    x, m, q1, q3, _ = series(sq, "ws_bytes", metric="ns_per_load"); band(ax, x, m, q1, q3, C[1], "sequential chase, 128 B next-node (misleading)")
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("working set (bytes)"); ax.set_ylabel("ns per load"); bytes_axis(ax)
    ax.set_title("(b) pitfall 2: prefetchable chase measures streaming, not latency", fontsize=8); ax.legend(fontsize=7)
    ax = axs[1, 0]
    d = {r["variant"]: r for r in sel(pit, exp="pitfall_dce", metric="gbps_claimed")}
    if d:
        vals = [d.get("no_sink", {}).get("median", np.nan), d.get("with_sink", {}).get("median", np.nan)]
        ax.bar(["result unused\n(loop removed)", "result sunk\n(real work)"], vals, color=[C[1], C[2]]); ax.set_yscale("log")
        for i, v in enumerate(vals):
            ax.text(i, v * 1.15, f"{v:.3g}", ha="center", fontsize=8)
        ax.axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); ax.text(-0.4, A.PEAK_GBPS * 1.2, "460 GB/s published peak", fontsize=7, color="#555")
    ax.set_ylabel("claimed read bandwidth (GB/s, log)"); ax.set_title("(c) pitfall 3: dead-code elimination (256 MiB buffer)", fontsize=8)
    ax = axs[1, 1]
    for var, col, lab in (("after_idle", C[1], "first chunks after 3 s idle"), ("steady", C[0], "steady state (immediately after)")):
        rows = sel(pit, exp="pitfall_ramp", variant=var, metric="ghz_est")
        x, m, q1, q3, _ = series(rows, "param", metric="ghz_est")
        if len(x):
            ax.plot(x * 0.5, m, color=col, lw=1.2, label=lab); ax.fill_between(x * 0.5, q1, q3, color=col, alpha=0.2, lw=0)
    ax.set_xlabel("time since start of burst (ms; 0.5 ms chunks)"); ax.set_ylabel("effective GHz estimate (dependent adds)")
    ax.set_title("(d) pitfall 4: clock ramp after idle", fontsize=8); ax.legend(fontsize=7)
    fig.suptitle("Exp 8: benchmark pitfalls, misleading result next to corrected result", fontsize=9)
    save(fig, "exp8_pitfalls")
    rows = []
    if len(res):
        for r in sorted(res, key=lambda r: r["ws_bytes"]):
            rows.append([fb(r["ws_bytes"] * 16), f"{r['median']:.0f} ({r['q1']:.0f} to {r['q3']:.0f})"])
    table("Pitfall 1: aggregate 'bandwidth' by total footprint (16 threads)", ["total footprint", "GB/s"], rows)
    rows = []
    ra = sel(pit, exp="pitfall_ramp", variant="after_idle", metric="ghz_est"); rs = sel(pit, exp="pitfall_ramp", variant="steady", metric="ghz_est")
    if ra and rs:
        a = {r["param"]: r["median"] for r in ra}; s = np.median([r["median"] for r in rs])
        for ms in (0, 5, 10, 20, 50, 100, 150, 200):
            k = float(ms * 2)
            if k in a:
                rows.append([ms, f"{a[k]:.2f}", f"{a[k] / s:.2f}"])
    table(f"Pitfall 4: clock estimate after 3 s idle vs steady ({s:.2f} GHz)" if rows else "Pitfall 4", ["ms since burst start", "GHz estimate", "fraction of steady"], rows)


# ------------------------------------------------------------------ placement
def placement():
    p = load("e0_placement")
    if not p:
        return
    rows = []
    for q in ("interactive", "default", "background"):
        row = [q]
        for s in (48 * 1024, 96 * 1024, 6 * 2**20, 12 * 2**20):
            r = sel(p, variant=q, ws_bytes=s, metric="ns_per_load")
            row.append(f"{r[0]['median']:.2f}" if r else "")
        rows.append(row)
    table("Placement check by cache signature (random chase ns; Super: L1D 128 KiB, L2 16 MiB; Performance: L1D 64 KiB, L2 8 MiB)",
          ["QoS class", "48 KiB", "96 KiB", "6 MiB", "12 MiB"], rows)


def main():
    placement(); exp1_exp5(); exp2(); exp3(); exp4(); exp6(); exp7(); exp8()
    with open(os.path.join(A.PROC, "tables.md"), "w") as f:
        f.write(f"Session {A.session()}; frequency estimate {FGHZ:.2f} GHz.\n\n" + "\n".join(TABLES))
    print("plots ->", A.PLOTS)


if __name__ == "__main__":
    main()
