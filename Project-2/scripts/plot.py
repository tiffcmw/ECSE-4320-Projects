#!/usr/bin/env python3
"""Figures and derived tables from data/processed. Lines are medians; bands and error bars span min to max over rounds; dots are individual rounds."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import analysis_lib as A
from analysis_lib import load, sel, series, fb, LINE

os.makedirs(A.PLOTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.bbox": "tight"})
C = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000", "#999999"]
TABLES = []


def _nosuptitle(fig, *a, **k):
    """Figure titles are carried by the report captions."""
    return None


def panels(n):
    """2x2 grid (n = 3 leaves the fourth cell empty) sized for a portrait page; returns the n used axes."""
    fig, ax = plt.subplots(2, 2, figsize=(7.6, 6.6), layout="constrained")
    ax = ax.flatten()
    for a in ax[n:]:
        a.set_axis_off()
    return fig, ax[:n]


def save(fig, name):
    fig.savefig(os.path.join(A.PLOTS, name + ".png"), dpi=220)
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


def dots(ax, group, xkey, color, **kw):
    """Every round as a small point (all rounds are shown, not only a summary)."""
    x, y = A.rounds(group, xkey, **kw)
    if len(x):
        ax.plot(x, y, ".", color=color, ms=2.2, alpha=0.35, zorder=1, lw=0)


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
                            ("L2, 2 MiB (128 pages)", 2 * 2**20, "smaller footprint than 4 MiB, so less translation cost"),
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
          ["Level", "Working set", "ns, median (min to max)", "cycles (est.)", "n rounds", "Notes"], rows)

    fig, ax = plt.subplots(figsize=(7.2, 4.2), layout="constrained")
    band(ax, ws, m, q1, q3, C[0], f"random chase, Super core (median, band = min to max, dots = rounds, n = {int(n.min())} to {int(n.max())})")
    dots(ax, "e1_chase", "ws_bytes", C[0], metric="ns_per_load")
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
    ax.set_title("Exp 1: zero-queue latency vs working set (shaded bands: plateau levels inferred from timing)", fontsize=8)
    bytes_axis(ax); ax.legend(loc="lower right", fontsize=7)
    save(fig, "exp1_zero_queue")

    # Exp 5: latency + bandwidth with annotated regions
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True)
    band(a1, ws, m, q1, q3, C[0], "latency (random chase)")
    a1.set_yscale("log"); a1.set_ylabel("latency (ns, log)")
    if bw:
        bws, bm, b1, b3, bn = series(bw, "ws_bytes", metric="gbps_app", variant="r10w0")
        band(a2, bws, bm, b1, b3, C[1], "sequential read, 1 thread (NEON, 128 B per step)")
        a2.set_yscale("log"); a2.set_ylabel("read bandwidth (GB/s, log)")
        a2.axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); a2.text(bws[0], A.PEAK_GBPS * 1.05, "DRAM peak 460 GB/s (Apple spec)", fontsize=7, color="#555")
    for ax in (a1, a2):
        for (lo, hi, name, col) in ((ws[0], e1, "L1", C[2]), (e1, e2, "L2", C[4]), (e2, e3, "SLC / transition", C[3]), (e3, ws[-1], "DRAM", C[1])):
            ax.axvspan(lo, hi, color=col, alpha=0.08, lw=0)
    for lo, hi, name in ((ws[0], e1, "L1"), (e1, e2, "L2"), (e2, e3, "SLC /\ntransition"), (e3, ws[-1], "DRAM")):
        a1.text(np.sqrt(lo * hi), a1.get_ylim()[1] * 0.8, name, ha="center", va="top", fontsize=8)
    a2.set_xscale("log", base=2); a2.set_xlabel("working set (bytes, log2 scale)"); bytes_axis(a2)
    a1.set_title(f"Exp 5: working-set sweep (region edges from curve: L1 {fb(e1)}, L2 {fb(e2)}, DRAM-like from {fb(e3)})", fontsize=8)
    a1.legend(fontsize=7, loc="upper left"); a2.legend(fontsize=7, loc="upper right")
    save(fig, "exp5_working_set")
    table("Region edges inferred from the latency curve (first working set exceeding 1.5x the plateau; DRAM edge = within 10% of the largest-size value)",
          ["Edge", "Working set", "sysctl capacity (Super)"], [["L1 to L2", fb(e1), "128 KiB L1D"], ["L2 to SLC", fb(e2), "16 MiB L2"], ["into DRAM plateau", fb(e3), "SLC not exposed"]])


# ------------------------------------------------------------------ Exp 2
def exp2():
    st = load("e2_chase_stride"); pat = load("e2_pat")
    if not st and not pat:
        return
    fig, axs = panels(3)
    ax = axs[0]
    for i, (mode, lab) in enumerate((("rand", "random order"), ("seq", "sequential order"))):
        x, m, q1, q3, n = series(st, "stride", metric="ns_per_load", variant=mode)
        if len(x):
            ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i], capsize=2, label=lab)
    ax.axvline(128, color="#777", ls=":", lw=0.9)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("node stride (B)"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(a) pointer chase, DRAM-sized footprint", fontsize=8); ax.legend(fontsize=7); bytes_axis(ax)
    for ax, mode in ((axs[1], "seq"), (axs[2], "rand")):
        for j, sz in enumerate((16, 32, 64, 128)):
            x, m, q1, q3, n = series(pat, "stride", metric="gbps_useful", variant=mode, size=sz)
            if len(x):
                ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[j], capsize=2, label=f"{sz} B per access")
        ax.axvline(128, color="#777", ls=":", lw=0.9); ax.annotate("128 B line", xy=(128, 0.02), xycoords=("data", "axes fraction"), fontsize=7, color="#555", ha="left")
        ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("stride between accesses (B)")
        ax.set_ylabel("useful bandwidth (GB/s, bytes requested)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if v in (2, 3, 5, 20, 30, 50) else ""))
        ax.set_title(f"({'b' if mode == 'seq' else 'c'}) independent loads, {'sequential' if mode == 'seq' else 'random slots'}", fontsize=8)
        ax.legend(fontsize=7); bytes_axis(ax)
    _nosuptitle(fig, "Exp 2: pattern and granularity (1 thread, footprint far beyond cache; bars = min to max over rounds)", fontsize=8)
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
KORDER = ["r10w0", "r7w3_st_r", "r5w5_st_r", "r0w10_st_r", "r7w3_nt_r", "r5w5_nt_r", "r0w10_nt_r", "rmw"]
KLAB = {"r10w0": "100% R", "r7w3_st_r": "70/30 st", "r5w5_st_r": "50/50 st", "r0w10_st_r": "100% W st", "r7w3_nt_r": "70/30 stnp",
        "r5w5_nt_r": "50/50 stnp", "r0w10_nt_r": "100% W stnp", "rmw": "50/50 rmw",
        "r7w3_st": "70/30 st (uniform)", "r5w5_st": "50/50 st (uniform)", "r0w10_st": "100% W st (uniform)", "r7w3_nt": "70/30 stnp (uniform)",
        "r5w5_nt": "50/50 stnp (uniform)", "r0w10_nt": "100% W stnp (uniform)", "r0w10_zva": "100% W dc zva",
        "r0w10_st_z": "100% W st (zero)", "r0w10_nt_z": "100% W stnp (zero)"}


def traffic_factor(k):
    """DRAM bytes per application byte if stores allocate (MODEL, not measured): reads + 2x writes for plain stores."""
    if k.endswith("_st_r") or k.endswith("_st"):
        w = int(k.split("w")[1].split("_")[0]); r = int(k[1:].split("w")[0])
        return (r + 2 * w) / (r + w)
    return 1.0


def exp3():
    bw = load("e3_mix_bw"); ld = load("e3_mix_loaded")
    if not bw and not ld:
        return
    fig, axs = panels(4)
    ax = axs[0]
    sizes = sorted({r["ws_bytes"] for r in bw})
    w = 0.8 / max(1, len(sizes))
    for si, s_ in enumerate(sizes):
        xs, ms, lo, hi = [], [], [], []
        for ki, k in enumerate(KORDER):
            r = sel(bw, variant=k, ws_bytes=s_, metric="gbps_app")
            if r:
                xs.append(ki + si * w); ms.append(r[0]["median"]); lo.append(r[0]["median"] - r[0]["min"]); hi.append(r[0]["max"] - r[0]["median"])
        ax.bar(xs, ms, w, yerr=[lo, hi], color=C[si], label=fb(s_), capsize=1.5)
    big = max(sizes) if sizes else 0
    mx, mxs = [], []
    for ki, k in enumerate(KORDER):   # modeled DRAM traffic if plain stores allocate: hatched, open bars, NOT measured
        r = sel(bw, variant=k, ws_bytes=big, metric="gbps_app")
        if r and traffic_factor(k) > 1:
            mx.append(ki + (len(sizes) - 1) * w); mxs.append(r[0]["median"] * traffic_factor(k))
    if mx:
        ax.bar(mx, mxs, w, fill=False, hatch="//", edgecolor="#333", lw=0.8, label=f"modeled DRAM traffic at {fb(big)} (write-allocate model, not measured)")
    ax.set_xticks(np.arange(len(KORDER)) + w * (len(sizes) - 1) / 2); ax.set_xticklabels([KLAB[k] for k in KORDER], rotation=40, ha="right", fontsize=7)
    ax.set_ylabel("application GB/s (1 thread, random store data)"); ax.set_title("(a) measured throughput by footprint", fontsize=8); ax.set_ylim(0, ax.get_ylim()[1] * 1.3); ax.legend(title="footprint", fontsize=6, loc="upper right", ncol=1)
    ax = axs[1]   # content test, 100% write, 1 GiB
    cases = [("r0w10_st_r", "st\nrandom"), ("r0w10_st", "st\nuniform"), ("r0w10_st_z", "st\nzero"), ("r0w10_nt_r", "stnp\nrandom"),
             ("r0w10_nt", "stnp\nuniform"), ("r0w10_nt_z", "stnp\nzero"), ("r0w10_zva", "dc zva")]
    xs = np.arange(len(cases)); vals = []; lo = []; hi = []
    for k, _ in cases:
        r = sel(bw, variant=k, ws_bytes=big, metric="gbps_app")
        vals.append(r[0]["median"] if r else np.nan); lo.append(r[0]["median"] - r[0]["min"] if r else 0); hi.append(r[0]["max"] - r[0]["median"] if r else 0)
    ax.bar(xs, vals, 0.7, yerr=[lo, hi], color=[C[0], C[0], C[0], C[1], C[1], C[1], C[3]], capsize=1.5)
    ax.set_xticks(xs); ax.set_xticklabels([c[1] for c in cases], fontsize=7); ax.set_ylabel("application GB/s (1 thread, 100% write, 1 GiB)")
    ax.set_title("(b) store data content changes write throughput", fontsize=8)
    mixes = [k for k in ("r10w0", "r7w3_st_r", "r5w5_st_r", "r0w10_st_r", "r0w10_nt_r", "rmw") if sel(ld, variant=k)]
    for i_, k in enumerate(mixes):
        x, m, q1, q3, n = series(ld, "threads", variant=k, metric="bw_gbps")
        axs[2].errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i_ % 8], capsize=2, label=KLAB[k])
        x, m, q1, q3, n = series(ld, "threads", variant=k, metric="lat_ns")
        axs[3].errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[i_ % 8], capsize=2, label=KLAB[k])
    axs[2].axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); axs[2].text(0.5, A.PEAK_GBPS * 1.02, "peak 460 GB/s (Apple spec)", fontsize=7, color="#555")
    axs[2].set_xlabel("bandwidth threads"); axs[2].set_ylabel("aggregate application GB/s"); axs[2].set_title("(c) throughput vs threads", fontsize=8); axs[2].legend(fontsize=6)
    axs[3].set_yscale("log"); axs[3].set_xlabel("bandwidth threads"); axs[3].set_ylabel("probe latency (ns, log; bars = min to max incl. outlier rounds)"); axs[3].set_title("(d) loaded read latency vs threads", fontsize=8); axs[3].legend(fontsize=6)
    _nosuptitle(fig, "Exp 3: read/write mix. Single-thread footprints and store-content test (a, b), multi-thread loaded runs (c, d). Bars/error bars: median and min to max over rounds", fontsize=8)
    save(fig, "exp3_rw_mix")
    rows = []
    for k in KORDER + ["r0w10_st", "r0w10_nt", "r0w10_st_z", "r0w10_nt_z", "r0w10_zva"]:
        r = sel(bw, variant=k, ws_bytes=big, metric="gbps_app")
        if r:
            t = traffic_factor(k)
            rows.append([KLAB[k], f"{r[0]['median']:.1f} ({r[0]['min']:.1f} to {r[0]['max']:.1f})", int(r[0]["n"]), (f"{t:.2f}" if t > 1 else "1.00 (no allocate fetch assumed)"), (f"{r[0]['median'] * t:.1f}" if t > 1 else "")])
    table(f"Single-thread mix at {fb(big)} footprint. Measured: application GB/s. Modeled (not measured): DRAM traffic if plain stores allocate",
          ["Mix", "measured application GB/s (min to max)", "n rounds", "modeled traffic factor", "modeled DRAM GB/s"], rows)
    rows = []
    for k in mixes:
        for N in (4, 16):
            b = sel(ld, variant=k, metric="bw_gbps", threads=N); l = sel(ld, variant=k, metric="lat_ns", threads=N)
            l0 = sel(ld, variant=k, metric="lat_ns", threads=0)
            if b and l and l0:
                rows.append([KLAB[k], N, f"{b[0]['median']:.0f}", f"{l[0]['median']:.0f}", f"{l[0]['median'] / l0[0]['median']:.2f}x", int(b[0]["n"])])
    table("Loaded latency by mix (probe thread + N bandwidth threads)", ["Mix", "N threads", "app GB/s", "probe ns", "vs idle", "n rounds"], rows)


# ------------------------------------------------------------------ Exp 4
def little_points():
    """All throughput-latency points: fine thread sweep (1 to 16 threads, no delay) and the two injection-delay series."""
    ld = load("e4_loaded")
    pts = []
    for ex, tag in (("e4_loaded_threads", "threads"), ("e4_loaded_delay", "delay, 16 thr"), ("e4_loaded_delay6", "delay, 6 thr")):
        keys = sorted({(r["threads"], r["param"]) for r in sel(ld, exp=ex, metric="bw_gbps")})
        for t, p in keys:
            b = sel(ld, exp=ex, metric="bw_gbps", threads=t, param=p); l = sel(ld, exp=ex, metric="lat_ns", threads=t, param=p)
            if b and l and t > 0:
                _, bv = A.rounds("e4_loaded", "threads", exp=ex, metric="bw_gbps", threads=t, param=p)
                _, lv = A.rounds("e4_loaded", "threads", exp=ex, metric="lat_ns", threads=t, param=p)
                pts.append(dict(tag=tag, thr=int(t), delay=p, bw=b[0]["median"], lat=l[0]["median"], bwlo=b[0]["min"], bwhi=b[0]["max"],
                                latlo=l[0]["min"], lathi=l[0]["max"], n=int(b[0]["n"]), bwr=bv, latr=lv))
    return pts


def knees(pts, idle):
    """Knee definitions fixed before analysis (hypotheses, H4f). K1: first load level (fewest bandwidth threads, no injected delay) whose median
    bandwidth reaches 95% of the maximum median bandwidth of the thread sweep. K2: point of maximum bandwidth / latency over the whole curve.
    (A first implementation ordered points by bandwidth instead of by offered load; with a noisy curve that picked 10 threads. The
    definition as written is first crossing along the thread sweep, and that is what is reported.)"""
    th = sorted([p for p in pts if p["tag"] == "threads"], key=lambda p: p["thr"])
    mx = max(p["bw"] for p in th)
    k1 = next(p for p in th if p["bw"] >= 0.95 * mx)
    k2 = max(pts, key=lambda p: p["bw"] / p["lat"])
    sat = max(pts, key=lambda p: p["bw"])
    return {"K1: fewest threads reaching 95% of maximum bandwidth": k1, "K2: maximum bandwidth / latency": k2, "maximum bandwidth": sat}


def exp4():
    mlp = load("e4_mlp"); ld = load("e4_loaded")
    if not mlp and not ld:
        return
    fig, axs = panels(3)
    ax = axs[0]
    kx, bm, b1, b3, bn = series(mlp, "param", metric="gbps")
    _, lm, l1, l3, _ = series(mlp, "param", metric="ns_per_step")
    L0 = lm[0] if len(lm) else float("nan")
    if len(kx):
        ax.errorbar(kx, bm, yerr=[bm - b1, b3 - bm], marker="o", ms=3, color=C[0], capsize=2, label=f"measured throughput (n = {int(bn.min())} rounds)")
        dots(ax, "e4_mlp", "param", C[0], metric="gbps")
        ax.plot(kx, kx * LINE / L0, "--", color="#777", lw=1, label=f"ideal K x 128 B / {L0:.0f} ns")
        a2 = ax.twinx(); a2.errorbar(kx, lm, yerr=[lm - l1, l3 - lm], marker="s", ms=3, color=C[1], capsize=2, label="latency per step")
        a2.set_ylabel("ns per chain step", color=C[1]); a2.grid(False)
    ax.set_xscale("log", base=2); ax.set_xlabel("independent chains K (outstanding loads) in one thread"); ax.set_ylabel("GB/s")
    ax.set_title("(a) one core: throughput vs concurrency", fontsize=8); ax.legend(fontsize=7, loc="upper left")
    pts = little_points(); idle = A.idle_latency()
    ax = axs[1]
    for i, tag in enumerate(("threads", "delay, 16 thr", "delay, 6 thr")):
        P = sorted([p for p in pts if p["tag"] == tag], key=lambda p: p["bw"])
        if P:
            ax.errorbar([p["bw"] for p in P], [p["lat"] for p in P], xerr=[[p["bw"] - p["bwlo"] for p in P], [p["bwhi"] - p["bw"] for p in P]],
                        yerr=[[p["lat"] - p["latlo"] for p in P], [p["lathi"] - p["lat"] for p in P]], marker="o", ms=3, color=C[i], capsize=2, lw=1, label=tag + " (median, bars = min to max)")
            for p in P:
                ax.plot(p["bwr"], p["latr"], ".", color=C[i], ms=2, alpha=0.3, zorder=1)
    if idle == idle:
        ax.axhline(idle, color="#777", ls=":", lw=0.9); ax.annotate(f"idle {idle:.0f} ns", xy=(0.02, idle), xycoords=("axes fraction", "data"), xytext=(0, 3), textcoords="offset points", fontsize=7, color="#555")
    ax.axvline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); ax.text(A.PEAK_GBPS, 0.97, "peak 460", transform=ax.get_xaxis_transform(), fontsize=7, rotation=90, ha="right", va="top", color="#555")
    ax.set_xlabel("aggregate read bandwidth (GB/s)"); ax.set_ylabel("loaded latency (ns, probe thread)")
    top = max(p["lathi"] for p in pts) if pts else 300
    ax.set_yscale("log"); ax.set_ylim(90, max(top * 1.3, 400)); ax.set_xlim(0, A.PEAK_GBPS * 1.02)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if v in (200, 300, 500, 2000, 3000) else ""))
    ax.set_title("(b) throughput-latency curve with knees (dots: every round)", fontsize=8)
    rows = []
    if pts and idle == idle:
        kn = knees(pts, idle); mk = {"K1: fewest threads reaching 95% of maximum bandwidth": ("*", 12), "K2: maximum bandwidth / latency": ("D", 7)}
        for name, p in kn.items():
            if name in mk:
                ax.plot([p["bw"]], [p["lat"]], mk[name][0], color="k", ms=mk[name][1], mfc="none" if mk[name][0] == "D" else "k", zorder=6)
                ax.annotate(name.split(":")[0], (p["bw"], p["lat"]), xytext=(6, -14 if name.startswith("K1") else 8), textcoords="offset points", fontsize=8, weight="bold")
            rows.append([name, f"{p['tag']}, {p['thr']} thr, delay {p['delay']:.0f}", f"{p['bw']:.0f} ({p['bwlo']:.0f} to {p['bwhi']:.0f})", f"{p['lat']:.0f} ({p['latlo']:.0f} to {p['lathi']:.0f})",
                         f"{p['lat'] / idle:.2f}x", f"{p['bw'] * p['lat'] / LINE:.0f}", p["n"]])
        table(f"Knee under two definitions fixed in advance (idle latency {idle:.0f} ns; N = BW x latency / 128 B)",
              ["Definition", "point", "bandwidth GB/s (min to max)", "loaded latency ns (min to max)", "latency vs idle", "N lines in flight", "n rounds"], rows)
        k1, k2 = kn["K1: fewest threads reaching 95% of maximum bandwidth"], kn["K2: maximum bandwidth / latency"]
        KNEE_INFO.update(k1=k1, k2=k2, sat=kn["maximum bandwidth"], idle=idle, worst_ratio=max(p["lat"] for p in pts if p["bw"] >= 0.5 * kn["maximum bandwidth"]["bw"]) / idle)
    ax.legend(fontsize=6, loc="upper left")
    ax = axs[2]
    Ncore = bm.max() * L0 / LINE if len(bm) else float("nan")
    for i, tag in enumerate(("threads", "delay, 16 thr", "delay, 6 thr")):
        P = sorted([p for p in pts if p["tag"] == tag], key=lambda p: p["bw"])
        if P:
            ax.plot([p["bw"] for p in P], [p["bw"] * p["lat"] / LINE for p in P], "o-", ms=3, color=C[i], label=tag)
    if len(kx):
        ax.axhline(Ncore, color="#777", ls=":", lw=0.9)
        ax.annotate(f"one-core plateau: {Ncore:.0f} lines (1 core)", xy=(0.02, Ncore), xycoords=("axes fraction", "data"), xytext=(0, 3), textcoords="offset points", fontsize=7, color="#555")
    ax.set_xlabel("aggregate read bandwidth (GB/s)"); ax.set_ylabel("N = BW x latency / 128 B (lines in flight)")
    ax.set_title("(c) Little's Law: inferred lines in flight, every point", fontsize=8); ax.legend(fontsize=7)
    _nosuptitle(fig, "Exp 4: intensity sweep (1 probe chase thread + N sequential-read threads; 1 to 8 threads in steps of 1 then 10, 12, 14, 16; injection delays at 16 and 6 threads)", fontsize=8.5)
    save(fig, "exp4_intensity")
    if len(kx):
        rows = [[int(k), f"{g:.1f} ({a:.1f} to {b:.1f})", f"{l:.0f}", f"{g * L0 / LINE:.1f}", int(nn)] for k, g, a, b, l, nn in zip(kx, bm, b1, b3, lm, bn)]
        table(f"Single-core concurrency sweep: N_eff = throughput x L0 / 128 B with L0 = {L0:.0f} ns (K = 1 latency)",
              ["K chains", "GB/s (min to max)", "ns per step", "N_eff (lines)", "n rounds"], rows)
        KNEE_INFO["Ncore"] = Ncore; KNEE_INFO["L0"] = L0
    allp = sorted(pts, key=lambda p: p["bw"])
    if allp:
        rows = []
        for p in allp:
            N = p["bw"] * p["lat"] / LINE
            per = f"{N / p['thr']:.1f}" if p["tag"] in ("threads", "delay, 16 thr", "delay, 6 thr") else ""
            rows.append([p["tag"], p["thr"], f"{p['delay']:.0f}", f"{p['bw']:.1f}", f"{p['lat']:.0f}", f"{N:.0f}", per, p["n"]])
        table("All loaded-latency points (median over rounds). N per thread is the Little's Law consistency check: it should stay near the one-core plateau while threads are not saturated",
              ["series", "BW threads", "delay iters", "GB/s", "latency ns", "N lines", "N per thread", "n rounds"], rows)


KNEE_INFO = {}


# ------------------------------------------------------------------ Exp 6
def amat_curve():
    ch = load("e1_chase")
    ws, m, *_ = series(ch, "ws_bytes", metric="ns_per_load")
    return ws, m


K6 = {}


def exp6():
    k = load("e6_kern")
    if not k:
        return
    mlp = load("e4_mlp")
    _, bm, *_ = series(mlp, "param", metric="gbps"); _, lm, *_ = series(mlp, "param", metric="ns_per_step")
    Ncore = max(1.0, bm.max() * lm[0] / LINE) if len(bm) else 16.0
    ws_c, lat_c = amat_curve()
    fig, axs = panels(3)
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
        ax.set_title(f"({'a' if ai == 0 else 'b'}) {'z[i] = x[i]*y[i]' if kern == 'mul' else 'y[i] = a*x[i] + y[i]'} (f32)", fontsize=8)
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
    ax.set_ylabel("slowdown vs unit stride, same footprint"); ax.set_title("(c) DRAM-resident slowdown by pattern", fontsize=8); ax.legend(fontsize=7)
    _nosuptitle(fig, "Exp 6: kernel runtime vs footprint and access pattern (miss behavior inferred from timing; no counters)", fontsize=8)
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
    rows = []
    for kern in ("mul", "saxpy"):
        feet = sorted({r["ws_bytes"] for r in sel(k, variant=kern)})
        for ft in (feet[0], feet[len(feet) // 2], feet[-1]):
            u = sel(k, variant=kern, ws_bytes=ft, stride=4.0, metric="ns_per_elem"); sc = sel(k, variant=kern, ws_bytes=ft, stride=4.0 * 40503, metric="ns_per_elem")
            s64 = sel(k, variant=kern, ws_bytes=ft, stride=64.0, metric="ns_per_elem")
            if u and sc:
                rows.append([kern, fb(ft), f"{u[0]['median']:.3f}", f"{s64[0]['median']:.3f}" if s64 else "", f"{sc[0]['median']:.3f}", f"{sc[0]['median'] / u[0]['median']:.1f}x", int(u[0]["n"])])
                K6[(kern, ft)] = sc[0]["median"] / u[0]["median"]
    table("Scattered vs unit-stride cost at the same footprint (the ratio depends strongly on the footprint)",
          ["kernel", "footprint", "unit ns/elem", "stride 64 B ns/elem", "scattered ns/elem", "scattered / unit", "n rounds"], rows)


# ------------------------------------------------------------------ Exp 7
LAY = [("paged", "original layout (offset = index mod 128)", C[4], "--"), ("paged_rand", "random in-page offsets", C[1], "-"),
       ("paged_const", "constant in-page offset", C[3], "-"), ("packed", "packed contiguous (same lines)", C[0], "-")]
TLB_INFO = {}


def exp7():
    t = load("e7_tlb_pages") or load("e7_tlb")
    if not t:
        return
    P = {}
    for lay, *_ in LAY:
        x, m, q1, q3, n = series(sel(t, exp="e7_tlb_pages", variant=lay, metric="ns_per_load"), "ws_bytes", metric="ns_per_load")
        P[lay] = (x / LINE, m, q1, q3, n)
    fig, axs = panels(4)
    ax = axs[0]
    for lay, lab, col, ls in LAY:
        if len(P[lay][0]):
            x, m, q1, q3, n = P[lay]; band(ax, x, m, q1, q3, col, lab + f" (n={int(n.min())})", ls=ls)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("lines in the cycle (= distinct 16 KiB pages for paged layouts)"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(a) one line per page: four placements", fontsize=8); ax.legend(fontsize=6)
    ax = axs[1]
    xr, mr = P["paged_rand"][0], P["paged_rand"][1]; xp, mp = P["packed"][0], P["packed"][1]
    xc, mc = P["paged_const"][0], P["paged_const"][1]; xo, mo = P["paged"][0], P["paged"][1]
    if len(xr) == len(xp):
        ax.plot(xr, mr - mp, "o-", color=C[1], ms=3, label="translation penalty: random offsets minus packed")
    if len(xr) == len(xc):
        ax.plot(xr, mc - mr, "s-", color=C[3], ms=3, label="set-conflict penalty: constant minus random offsets")
    if len(xr) == len(xo):
        ax.plot(xr, mo - mr, "^--", color=C[4], ms=3, label="original layout minus random offsets")
    ax.axhline(0, color="#777", lw=0.8)
    for reach, lab in ((256, "256 pg"), (2048, "2048 pg"), (16384, "16384 pg")):
        ax.axvline(reach, color="#777", ls=":", lw=0.8); ax.text(reach, 0.03, lab, transform=ax.get_xaxis_transform(), rotation=90, fontsize=6, ha="right", va="bottom")
    ax.set_xscale("log", base=2); ax.set_yscale("symlog", linthresh=1); ax.set_xlabel("distinct pages touched"); ax.set_ylabel("latency difference (ns, symlog)")
    ax.set_title("(b) separating translation from set conflicts", fontsize=8); ax.legend(fontsize=6, loc="upper left", bbox_to_anchor=(0.0, 0.8))
    ax = axs[2]
    for lay, lab, col, ls in LAY[:3]:
        fx = sel(t, exp="e7_tlb_fixedL", variant=lay, metric="ns_per_load")
        x, m3, q1, q3, n = series(fx, "param", metric="ns_per_load")
        if len(x):
            band(ax, x, m3, q1, q3, col, lab, ls=ls)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("distinct pages P holding the same 32768 lines (4 MiB)"); ax.set_ylabel("ns per dependent load")
    ax.set_title("(c) fixed cache footprint, vary pages", fontsize=8); ax.legend(fontsize=6)
    ax = axs[3]
    pm = load("e13_pmu"); got = False
    for ev, col in (("L1D_TLB_MISS_NONSPEC", C[0]), ("L2_TLB_MISS_DATA", C[1]), ("L1D_CACHE_MISS_LD_NONSPEC", C[2])):
        for lay, ls in (("paged_rand", "-"), ("packed", "--")):
            r = sel(pm, exp="e13_pmu_tlb", variant=lay, metric=f"pmu_{ev}_per_op")
            x, m, q1, q3, n = series(r, "ws_bytes", metric=f"pmu_{ev}_per_op")
            if len(x):
                got = True; ax.plot(x / LINE, m, ls, color=col, marker="o", ms=2.5, label=f"{ev} ({lay})")
    if got:
        ax.set_xscale("log", base=2); ax.set_xlabel("lines in the cycle"); ax.set_ylabel("PMU events per load")
        ax.set_title("(d) hardware counters (kperf, root)", fontsize=8); ax.legend(fontsize=5.5)
    else:
        ax.text(0.5, 0.5, "no PMU data in this dataset", ha="center", va="center", transform=ax.transAxes); ax.set_axis_off()
    _nosuptitle(fig, "Exp 7: TLB effect via page locality, 16 KiB pages. Huge-page comparison not possible on macOS. Median, band = min to max over rounds", fontsize=8)
    save(fig, "exp7_tlb")
    if len(xr) == len(xp):
        rows = []
        for i_, pg in enumerate(xr):
            row = [int(pg)]
            for lay in ("paged", "paged_rand", "paged_const", "packed"):
                x_, m_ = P[lay][0], P[lay][1]
                row.append(f"{m_[i_]:.2f}" if i_ < len(m_) and len(x_) == len(xr) else "")
            row.append(f"{mr[i_] - mp[i_]:+.2f}"); row.append(f"{mo[i_] - mp[i_]:+.2f}" if len(xo) == len(xp) else "")
            row.append(int(P["paged_rand"][4][i_]))
            rows.append(row)
        table("Exp 7: median ns per load by layout. 'rand-packed' is the translation penalty after removing set conflicts; 'orig-packed' is the earlier definition",
              ["pages (= lines)", "original", "random offsets", "constant offset", "packed", "rand - packed", "orig - packed", "n rounds"], rows)
        TLB_INFO.update(pages=list(xr), rand=list(mr), packed=list(mp), orig=list(mo), const=list(mc))
    rows = []
    fx = {lay: series(sel(t, exp="e7_tlb_fixedL", variant=lay, metric="ns_per_load"), "param", metric="ns_per_load") for lay, *_ in LAY[:3]}
    if len(fx["paged"][0]):
        for i_, pg in enumerate(fx["paged"][0]):
            rows.append([int(pg)] + [(f"{fx[l][1][i_]:.2f}" if i_ < len(fx[l][1]) else "") for l in ("paged", "paged_rand", "paged_const")])
        table("Fixed 4 MiB of lines spread over P pages (median ns)", ["P pages", "original", "random offsets", "constant offset"], rows)


# ------------------------------------------------------------------ Exp 8
def exp8():
    pit = load("e8_pitfalls")
    if not pit:
        return
    e5 = load("e5_bw")
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 6.8), layout="constrained")
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
        ax.axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9); ax.text(-0.4, A.PEAK_GBPS * 1.2, "460 GB/s peak (Apple spec)", fontsize=7, color="#555")
    ax.set_ylabel("claimed read bandwidth (GB/s, log)"); ax.set_title("(c) pitfall 3: dead-code elimination (256 MiB buffer)", fontsize=8)
    ax = axs[1, 1]
    for var, col, lab in (("after_idle", C[1], "first chunks after 3 s idle"), ("steady", C[0], "steady state (immediately after)")):
        rows = sel(pit, exp="pitfall_ramp", variant=var, metric="ghz_est")
        x, m, q1, q3, _ = series(rows, "param", metric="ghz_est")
        if len(x):
            ax.plot(x * 0.5, m, color=col, lw=1.2, label=lab); ax.fill_between(x * 0.5, q1, q3, color=col, alpha=0.2, lw=0)
    ax.set_xlabel("time since start of burst (ms; 0.5 ms chunks)"); ax.set_ylabel("effective GHz estimate (dependent adds)")
    ax.set_title("(d) pitfall 4: clock ramp after idle", fontsize=8); ax.legend(fontsize=7)
    _nosuptitle(fig, "Exp 8: benchmark pitfalls, misleading result next to corrected result", fontsize=8)
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


# ------------------------------------------------------------------ extra experiments (aliasing, read ceiling, plateau, counters)
ALIAS = {}


def extras():
    # ---- stride aliasing (R3): independent random 16 B loads and element-stride kernels
    al = load("e2_alias"); ks = load("e6_stride")
    if al or ks:
        fig, axs = panels(3)
        ax = axs[0]
        for var, col, lab in (("rand", C[0], "plain stride"), ("randj", C[1], "stride + hashed line offset in block")):
            x, m, q1, q3, n = series(al, "stride", variant=var, metric="gbps_useful")
            if len(x):
                ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=col, capsize=2, label=f"{lab} (n={int(n.min())})")
        for sx in (128, 256, 512, 1024):
            ax.axvline(sx, color="#bbb", lw=0.6, ls=":")
        ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("stride between slots (B); dotted = powers of two"); ax.set_ylabel("useful bandwidth (GB/s, 16 B random loads)")
        ax.set_title("(a) independent random loads, 1 thread", fontsize=8); ax.legend(fontsize=7)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ALIAS["pat"] = {(v, int(sx_)): m_ for v in ("rand", "randj") for sx_, m_ in zip(*series(al, "stride", variant=v, metric="gbps_useful")[:2])}
        for ai, kern in enumerate(("mul", "saxpy")):
            ax = axs[1 + ai]
            feet = sorted({r["ws_bytes"] for r in ks if r["variant"] == kern})
            for fi, ft in enumerate(feet):
                x, m, q1, q3, n = series(ks, "stride", variant=kern, ws_bytes=ft, metric="ns_per_elem")
                ax.errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=C[fi], capsize=2, label=f"{fb(ft)}")
                xj, mj, a_, b_, _ = series(ks, "stride", variant=kern + "_j", ws_bytes=ft, metric="ns_per_elem")
                if len(xj):
                    ax.plot(xj, mj, "x", color=C[fi], ms=7, label=f"{fb(ft)}, hashed offset")
                ALIAS[(kern, ft)] = dict(zip(x.astype(int), m)); ALIAS[(kern + "_j", ft)] = dict(zip(xj.astype(int), mj))
            for sx in (128, 256, 512, 1024):
                ax.axvline(sx, color="#bbb", lw=0.6, ls=":")
            ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xlabel("element stride (B); non-powers of two: 96, 192, 320, 384, 640")
            ax.set_ylabel("ns per element"); ax.set_title(f"({'bc'[ai]}) {'z = x*y' if kern == 'mul' else 'y = a*x + y'} by stride and footprint", fontsize=8); ax.legend(fontsize=6)
        _nosuptitle(fig, "Stride aliasing test: power-of-two vs other strides, and a hashed in-block line offset (x markers)", fontsize=8)
        save(fig, "exp2b_stride_aliasing")
        rows = []
        for sx in sorted({int(r["stride"]) for r in al}):
            a1 = sel(al, variant="rand", stride=sx, metric="gbps_useful"); a2 = sel(al, variant="randj", stride=sx, metric="gbps_useful")
            rows.append([sx, "yes" if sx & (sx - 1) == 0 else "no", f"{a1[0]['median']:.2f} ({a1[0]['min']:.2f} to {a1[0]['max']:.2f})" if a1 else "",
                         f"{a2[0]['median']:.2f}" if a2 else "", int(a1[0]["n"]) if a1 else ""])
        table("Independent random 16 B loads: useful GB/s by stride, with and without hashed line offset in the block", ["stride B", "power of two", "plain GB/s (min to max)", "hashed offset GB/s", "n rounds"], rows)
        rows = []
        for kern in ("mul", "saxpy"):
            feet = sorted({r["ws_bytes"] for r in ks if r["variant"] == kern})
            for ft in feet[-2:]:
                for sx in sorted({int(r["stride"]) for r in ks if r["variant"] == kern and r["ws_bytes"] == ft}):
                    a1 = sel(ks, variant=kern, ws_bytes=ft, stride=sx, metric="ns_per_elem"); a2 = sel(ks, variant=kern + "_j", ws_bytes=ft, stride=sx, metric="ns_per_elem")
                    rows.append([kern, fb(ft), sx, "yes" if sx & (sx - 1) == 0 else "no", f"{a1[0]['median']:.2f}" if a1 else "", f"{a2[0]['median']:.2f}" if a2 else "", int(a1[0]["n"]) if a1 else ""])
        table("Kernels: ns per element by element stride at the two largest footprints, plain and hashed offset", ["kernel", "footprint", "stride B", "power of two", "plain ns", "hashed ns", "n rounds"], rows)

    # ---- read-only ceiling tests (R11)
    e11 = load("e11_ceiling"); base = load("e4_loaded")
    if e11:
        fig, axs = panels(3)
        series_def = [("standard ld1 x4 (e4)", base, "e4_loaded_threads", "r10w0", C[0]), ("ldp q-pairs", e11, "e11_r10w0_ldp", "r10w0_ldp", C[1]),
                      ("ld1 four-register", e11, "e11_r10w0_ld4", "r10w0_ld4", C[2]), ("background QoS only", e11, "e11_bgqos", "r10w0", C[3]),
                      ("random buffer content", e11, "e11_fillrand", "r10w0", C[4])]
        CEIL = {}
        for lab, data, ex, mix, col in series_def:
            r = sel(data, exp=ex, variant=mix, metric="bw_gbps")
            x, m, q1, q3, n = series(r, "threads", metric="bw_gbps")
            if len(x):
                axs[0].errorbar(x, m, yerr=[m - q1, q3 - m], marker="o", ms=3, color=col, capsize=2, label=lab)
                CEIL[lab] = dict(zip(x.astype(int), m))
            r2 = sel(data, exp=ex, variant=mix, metric="bw_gbps"); x2, m2, *_ = series(r2, "threads", metric="bw_gbps")
            if len(x2):
                msk = x2 > 0
                axs[1].plot(x2[msk], m2[msk] / x2[msk], "o-", ms=3, color=col, label=lab)
        axs[0].axhline(A.PEAK_GBPS, color="#777", ls="--", lw=0.9)
        axs[0].set_xlabel("bandwidth threads"); axs[0].set_ylabel("aggregate read GB/s"); axs[0].set_title("(a) aggregate read bandwidth", fontsize=8); axs[0].legend(fontsize=6)
        axs[1].set_xlabel("bandwidth threads"); axs[1].set_ylabel("GB/s per thread"); axs[1].set_title("(b) per-thread rate (mean)", fontsize=8)
        ax = axs[2]; rows = []
        for tag, ex, col in (("none", "e4_loaded_threads", C[0]), ("2 stnp writers", "e11_writer_nt", C[1]), ("2 st writers", "e11_writer_st", C[2])):
            data = base if ex.startswith("e4") else e11
            mix = "r10w0"
            for N in (4, 6):
                rb = sel(data, exp=ex, variant=mix, metric="bw_gbps", threads=N)
                rw = sel(data, exp=ex, variant=mix, metric="bw_writer_gbps", threads=N) if tag != "none" else []
                if rb:
                    rd = rb[0]["median"]; wr = rw[0]["median"] if rw else 0.0
                    rows.append([tag, N, f"{rd:.0f} ({rb[0]['min']:.0f} to {rb[0]['max']:.0f})", f"{wr:.0f}", f"{rd + wr:.0f}", int(rb[0]["n"])])
        xs = np.arange(len(rows))
        if rows:
            ax.bar(xs, [float(r[2].split()[0]) for r in rows], 0.6, color=C[0], label="read threads")
            ax.bar(xs, [float(r[3]) for r in rows], 0.6, bottom=[float(r[2].split()[0]) for r in rows], color=C[1], label="writer threads")
            ax.set_xticks(xs); ax.set_xticklabels([f"{r[0]}\n{r[1]} readers" for r in rows], fontsize=6.5)
        ax.set_ylabel("GB/s (application bytes)"); ax.set_title("(c) read-only plus concurrent writers", fontsize=8); ax.legend(fontsize=7)
        _nosuptitle(fig, "Read-only ceiling tests: load instruction mix, background QoS, buffer content, concurrent writers (median, bars = min to max)", fontsize=8)
        save(fig, "exp4b_read_ceiling")
        table("Read ceiling tests: aggregate read GB/s by thread count", ["variant"] + [f"{n} thr" for n in (1, 2, 4, 6, 8, 12, 16)],
              [[k] + [f"{v.get(n, float('nan')):.0f}" if n in v else "" for n in (1, 2, 4, 6, 8, 12, 16)] for k, v in CEIL.items()])
        table("Read plus concurrent writer threads (stnp or st, random data); writer GB/s is application bytes", ["writers", "read threads", "read GB/s (min to max)", "writer GB/s", "total GB/s", "n rounds"], rows)
        ALIAS["ceil"] = CEIL

    # ---- plateau tests (R12)
    sp = load("e12_plateau")
    if sp:
        fig, axs = panels(3)
        for k_, (var, col) in enumerate((("node64", C[2]), ("node128", C[0]), ("node256", C[1]))):
            x, m, q1, q3, n = series(sel(sp, exp="e12_spacing", variant=var, metric="ns_per_load"), "ws_bytes", metric="ns_per_load")
            if len(x):
                st = int(var[4:])
                band(axs[0], x, m, q1, q3, col, f"{st} B node spacing (n={int(n.min())})"); band(axs[1], x / st, m, q1, q3, col, f"{st} B node spacing")
        axs[0].set_xscale("log", base=2); axs[0].set_yscale("log"); axs[0].set_xlabel("footprint (bytes)"); axs[0].set_ylabel("ns per dependent load")
        axs[0].set_title("(a) latency vs bytes, three node spacings", fontsize=8); axs[0].legend(fontsize=6); bytes_axis(axs[0])
        axs[1].set_xscale("log", base=2); axs[1].set_yscale("log"); axs[1].set_xlabel("nodes in the cycle"); axs[1].set_ylabel("ns per dependent load"); axs[1].set_title("(b) same data vs node count", fontsize=8)
        x, m, q1, q3, n = series(sel(sp, exp="e12_mut", variant="mutating", metric="ns_per_load"), "ws_bytes", metric="ns_per_load")
        xp, mp, *_ = series(sel(sp, exp="e12_spacing", variant="node128", metric="ns_per_load"), "ws_bytes", metric="ns_per_load")
        if len(x) and len(xp):
            band(axs[2], x, m, q1, q3, C[3], f"mutating walk (never repeats; ~5 extra cycles per step) n={int(n.min())}")
            axs[2].plot(xp, mp, "-", color=C[0], marker="o", ms=2.5, label="plain random cycle, 128 B nodes")
            ALIAS["mut"] = dict(x=list(x), m=list(m), xp=list(xp), mp=list(mp))
        axs[2].set_xscale("log", base=2); axs[2].set_yscale("log"); axs[2].set_xlabel("footprint (bytes)"); axs[2].set_ylabel("ns per dependent load")
        axs[2].set_title("(c) repeating cycle vs non-repeating walk", fontsize=8); axs[2].legend(fontsize=6); bytes_axis(axs[2])
        _nosuptitle(fig, "The latency plateau between L1 and L2: does it follow bytes or node count, and does it survive a non-repeating walk? (median, band = min to max)", fontsize=8)
        save(fig, "exp5b_plateau_tests")
        sizes = sorted({r["ws_bytes"] for r in sp if r["exp"] == "e12_mut"})
        rows = []
        for sz in sizes:
            row = [fb(sz)]
            for var in ("node64", "node128", "node256"):
                r = sel(sp, exp="e12_spacing", variant=var, metric="ns_per_load")
                if r:
                    j_ = min(r, key=lambda q: abs(q["ws_bytes"] - sz)); row.append(f"{j_['median']:.2f}" if abs(j_["ws_bytes"] - sz) / sz < 0.03 else "")
            rm = sel(sp, exp="e12_mut", ws_bytes=sz, metric="ns_per_load"); row.append(f"{rm[0]['median']:.2f}" if rm else "")
            rows.append(row)
        table("Plateau tests: median ns per load by footprint", ["footprint", "64 B spacing", "128 B spacing", "256 B spacing", "mutating walk"], rows)

    # ---- counters (R7)
    pm = load("e13_pmu")
    if pm:
        evs = ["FIXED_CYCLES", "FIXED_INSTRUCTIONS", "L1D_CACHE_MISS_LD_NONSPEC", "L1D_TLB_MISS_NONSPEC", "L2_TLB_MISS_DATA", "LD_SRC_LL_CACHE_NONSPEC", "LD_SRC_MEMSYS_NONSPEC"]
        rows = []
        for r in sorted(sel(pm, exp="e13_pmu_chase", metric=lambda v: v.startswith("pmu_") or v == "ns_per_load"), key=lambda r: (r["ws_bytes"], r["metric"])):
            pass
        for sz in sorted({r["ws_bytes"] for r in pm if r["exp"] == "e13_pmu_chase"}):
            row = [fb(sz)]
            r0 = sel(pm, exp="e13_pmu_chase", ws_bytes=sz, metric="ns_per_load"); row.append(f"{r0[0]['median']:.2f}" if r0 else "")
            for ev in evs[2:]:
                r = sel(pm, exp="e13_pmu_chase", ws_bytes=sz, metric=f"pmu_{ev}_per_op"); row.append(f"{r[0]['median']:.3f}" if r else "")
            rows.append(row)
        table("PMU counters, random chase (events per dependent load, median)", ["working set", "ns/load"] + evs[2:], rows)
        rows = []
        for var in ("mul", "saxpy"):
            for st_ in (4, 64, 4 * 40503):
                for ft in sorted({r["ws_bytes"] for r in pm if r["exp"] == "e13_pmu_kern" and r["variant"] == var}):
                    r0 = sel(pm, exp="e13_pmu_kern", variant=var, ws_bytes=ft, stride=st_, metric="ns_per_elem")
                    if not r0 and var:
                        r0 = []
                    row = [var, "unit" if st_ == 4 else ("stride 64 B" if st_ == 64 else "scattered"), fb(ft)]
                    rr = sel(pm, exp="e13_pmu_kern", variant=var, ws_bytes=ft, stride=st_, metric="pmu_L1D_CACHE_MISS_LD_NONSPEC_per_op")
                    if not rr:
                        continue
                    rows.append(row + [f"{rr[0]['median']:.3f}"] + [(lambda q: f"{q[0]['median']:.3f}" if q else "")(sel(pm, exp="e13_pmu_kern", variant=var, ws_bytes=ft, stride=st_, metric=f"pmu_{ev}_per_op")) for ev in evs[3:]]
                                + [(lambda q: f"{q[0]['median']:.3f}" if q else "")(sel(pm, exp="e13_pmu_kern", variant=var, ws_bytes=ft, stride=st_, metric="ns_per_elem"))])
        if rows:
            table("PMU counters, kernels z=x*y and y=a*x+y (events per element; L1D load misses first)", ["kernel", "pattern", "footprint", "L1D ld miss"] + evs[3:] + ["ns/elem"], rows)


def main():
    placement(); exp1_exp5(); exp2(); exp3(); exp4(); exp6(); exp7(); exp8(); extras()
    with open(os.path.join(A.PROC, "tables.md"), "w") as f:
        f.write(f"Session {A.session()}; frequency estimate {FGHZ:.2f} GHz.\n\n" + "\n".join(TABLES))
    print("plots ->", A.PLOTS)


if __name__ == "__main__":
    main()
