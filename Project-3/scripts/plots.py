#!/usr/bin/env python3
"""Make all figures from data/processed/{summary,all_runs}.csv and data/raw/exp6b logs. Output: plots/*.png and *.pdf.
Error bars are the sample standard deviation over trials (n = 3 unless stated). Latency in microseconds, throughput in MB/s
(1 MB = 10^6 bytes) or IOPS."""
import csv, glob, os, datetime, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(P3, "data/processed"); OUT = os.path.join(P3, "plots"); os.makedirs(OUT, exist_ok=True)
SUM = list(csv.DictReader(open(PROC + "/summary.csv")))
RUNS = list(csv.DictReader(open(PROC + "/all_runs.csv")))
f = lambda r, k: float(r[k])
C = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9", "grey": "#666666"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 10.5, "axes.labelsize": 10.5, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 130, "legend.fontsize": 9})
FOOT = "Apple M5 Max, APPLE SSD AP2048Z, APFS file (32 GiB), direct I/O, macOS 27.0.1, fio 3.43; mean ± sd, n=3"

def save(fig, name, foot=FOOT):
    """plots/NAME.{png,pdf} carry a footer with platform and knobs; plots/docx/NAME.png (for the Word report) has none,
    the caption states it instead."""
    os.makedirs(OUT + "/docx", exist_ok=True)
    t = fig.text(0.01, 0.005, foot, fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    for ext in ("png", "pdf"): fig.savefig(f"{OUT}/{name}.{ext}")
    t.remove(); fig.tight_layout()
    fig.savefig(f"{OUT}/docx/{name}.png")
    plt.close(fig)

def kib(bs): return int(bs[:-1]) * (1024 if bs.endswith("m") else 1)

# ---- Fig 1: baselines (QD1)
def fig_baseline():
    rows = [r for r in SUM if r["exp"] == "exp1"]
    order = [("randread", "4k"), ("randwrite", "4k"), ("read", "128k"), ("write", "128k")]
    lab = ["4K rand read", "4K rand write", "128K seq read", "128K seq write"]
    fig, ax = plt.subplots(1, 2, figsize=(8, 3.2))
    keys = ["p50", "p95", "p99"]; w = 0.2
    for i, k in enumerate(["mean"] + keys):
        v, e = [], []
        for rw, bs in order:
            r = next(x for x in rows if x["rw"] == rw and x["bs"] == bs); s = "r" if "read" in rw else "w"
            v.append(f(r, f"{s}_lat_{k}_us_mean" if k != "mean" else f"{s}_lat_mean_us_mean"))
            e.append(f(r, f"{s}_lat_{k}_us_std" if k != "mean" else f"{s}_lat_mean_us_std"))
        ax[0].bar(np.arange(4) + (i - 1.5) * w, v, w, yerr=e, label=k, color=[C["grey"], C["blue"], C["orange"], C["red"]][i])
    ax[0].set_xticks(range(4)); ax[0].set_xticklabels(lab, rotation=15); ax[0].set_ylabel("latency (µs)"); ax[0].set_yscale("log")
    ax[0].set_title("Exp 1: QD1 latency (fixed: QD1, 1 job)"); ax[0].legend()
    v = [f(next(x for x in rows if x["rw"] == rw and x["bs"] == bs), ("r" if "read" in rw else "w") + "_bw_MBs_mean") for rw, bs in order]
    e = [f(next(x for x in rows if x["rw"] == rw and x["bs"] == bs), ("r" if "read" in rw else "w") + "_bw_MBs_std") for rw, bs in order]
    ax[1].bar(range(4), v, yerr=e, color=C["blue"]); ax[1].set_xticks(range(4)); ax[1].set_xticklabels(lab, rotation=15)
    ax[1].set_ylabel("throughput (MB/s)"); ax[1].set_title("Exp 1: QD1 throughput")
    save(fig, "fig1_baseline_qd1")

# ---- Fig 2: block size sweep
def fig_blocksize():
    rows = [r for r in SUM if r["exp"] == "exp2"]
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
    for rw, col, mk in (("randread", C["blue"], "o"), ("read", C["sky"], "s"), ("randwrite", C["red"], "o"), ("write", C["orange"], "s")):
        rs = sorted([r for r in rows if r["rw"] == rw], key=lambda r: kib(r["bs"])); s = "r" if "read" in rw else "w"
        x = [kib(r["bs"]) for r in rs]
        ax[0].errorbar(x, [f(r, s + "_bw_MBs_mean") for r in rs], [f(r, s + "_bw_MBs_std") for r in rs], label=rw, color=col, marker=mk, capsize=2)
        ax[1].errorbar(x, [f(r, s + "_iops_mean") for r in rs], [f(r, s + "_iops_std") for r in rs], label=rw, color=col, marker=mk, capsize=2)
        ax[2].errorbar(x, [f(r, s + "_lat_mean_us_mean") for r in rs], [f(r, s + "_lat_mean_us_std") for r in rs], label=rw, color=col, marker=mk, capsize=2)
    for a, yl in zip(ax, ("throughput (MB/s)", "IOPS", "mean latency (µs)")):
        a.set_xscale("log", base=2); a.set_xlabel("block size (KiB)"); a.set_ylabel(yl)
    ax[1].set_yscale("log"); ax[2].set_yscale("log"); ax[0].legend()
    fig.suptitle("Exp 2: block-size sweep (fixed: effective QD16 = 16 psync jobs; varied: block size, random vs sequential, read vs write)", fontsize=10)
    save(fig, "fig2_blocksize")

# ---- Fig 3: read/write mix
def fig_rwmix():
    rows = sorted([r for r in SUM if r["exp"] == "exp3"], key=lambda r: -int(r["mixread"]))
    lab = [f"{r['mixread']}/{100-int(r['mixread'])}" for r in rows]; x = np.arange(len(rows)); w = 0.38
    fig, ax = plt.subplots(1, 2, figsize=(8, 3.3))
    for k, col, nm in (("r", C["blue"], "read"), ("w", C["red"], "write")):
        ax[0].bar(x + (-w / 2 if k == "r" else w / 2), [f(r, k + "_iops_mean") / 1e3 for r in rows], w, yerr=[f(r, k + "_iops_std") / 1e3 for r in rows], color=col, label=nm)
        v = [f(r, k + "_lat_mean_us_mean") if f(r, k + "_ios_mean") > 0 else 0 for r in rows]
        e = [f(r, k + "_lat_mean_us_std") if f(r, k + "_ios_mean") > 0 else 0 for r in rows]
        ax[1].bar(x + (-w / 2 if k == "r" else w / 2), v, w, yerr=e, color=col, label=nm)
    for a, yl in zip(ax, ("IOPS (thousands)", "mean latency (µs)")):
        a.set_xticks(x); a.set_xticklabels(lab); a.set_xlabel("read/write mix (%)"); a.set_ylabel(yl)
    ax[0].legend(); ax[0].set_title("Exp 3: throughput by operation"); ax[1].set_title("Exp 3: latency by operation")
    save(fig, "fig3_rwmix", FOOT + "; fixed: 4 KiB random, QD16")

# ---- Fig 4: QD sweep, throughput vs latency, Little's law
def fig_qd():
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.9))
    ser = [("exp4", "psync", "A: psync (early)", C["blue"], "o", "-"), ("exp4", "posixaio", "A: posixaio (early)", C["sky"], "s", "-"),
           ("exp4b", "psync", "B: psync (later replicate)", C["red"], "o", "--"), ("exp4b", "posixaio", "B: posixaio (later replicate)", C["orange"], "s", "--")]
    for ex, eng, lab, col, mk, ls in ser:
        rs = sorted([r for r in SUM if r["exp"] == ex and r["eng"] == eng], key=lambda r: int(r["qd"]))
        lat = [f(r, "r_lat_mean_us_mean") for r in rs]; io = [f(r, "r_iops_mean") / 1e3 for r in rs]
        ax[0].errorbar(lat, io, yerr=[f(r, "r_iops_std") / 1e3 for r in rs], label=lab, color=col, marker=mk, ls=ls, ms=4, capsize=2)
        if eng == "posixaio":
            for r, x, y in zip(rs, lat, io):
                if int(r["qd"]) in (1, 16, 64, 256): ax[0].annotate(f"QD{r['qd']}", (x, y), textcoords="offset points", xytext=(3, -9), fontsize=8, color=col)
        lq = [f(r, "littles_qd_mean") for r in rs]; cq = [int(r["qd"]) for r in rs]
        ax[1].plot(cq, lq, color=col, marker=mk, ls=ls, ms=4, label=lab)
    kn = next(r for r in SUM if r["exp"] == "exp4" and r["eng"] == "psync" and r["qd"] == "16")
    ax[0].axvline(f(kn, "r_lat_mean_us_mean"), color="k", lw=0.6, ls=":")
    for ex in ("exp4", "exp4b"):
        k2 = next(r for r in SUM if r["exp"] == ex and r["eng"] == "psync" and r["qd"] == "16")
        ax[0].scatter([f(k2, "r_lat_mean_us_mean")], [f(k2, "r_iops_mean") / 1e3], s=160, facecolors="none", edgecolors="k", lw=1)
    ax[0].set_xscale("log"); ax[0].set_xlabel("mean latency (µs, log)"); ax[0].set_ylabel("IOPS (thousands)")
    ax[0].set_title("Exp 4: throughput vs latency, 4 KiB random read"); ax[0].legend(loc="center right", fontsize=8)
    ax[1].plot([1, 256], [1, 256], "k:", lw=0.8, label="y = x"); ax[1].set_xscale("log", base=2); ax[1].set_yscale("log", base=2)
    ax[1].set_xlabel("configured queue depth"); ax[1].set_ylabel("IOPS × mean latency (Little's law)"); ax[1].set_title("Little's law check: outstanding = throughput × latency")
    ax[1].legend(loc="upper left")
    save(fig, "fig4_qd_sweep", FOOT + "; A and B are the same sweep run at two times (see REPORT, anomalies)")

# ---- Fig 5: tail latency
def fig_tail():
    rows = [r for r in SUM if r["exp"] == "exp5"]; keys = ["p50", "p90", "p95", "p99", "p99.9", "p99.99"]
    fig, ax = plt.subplots(figsize=(6.5, 3.5)); w = 0.38
    for i, (role, col) in enumerate((("mid", C["blue"]), ("knee", C["red"]))):
        r = next(x for x in rows if x["role"] == role)
        v = [f(r, f"r_lat_{k}_us_mean") for k in keys]; e = [f(r, f"r_lat_{k}_us_std") for k in keys]
        ax.bar(np.arange(6) + (i - 0.5) * w, v, w, yerr=e, color=col, capsize=2,
               label=f"QD{r['qd']} ({'mid' if role=='mid' else 'near knee'}), {f(r,'r_ios_mean')/1e6:.1f} M IOs/run")
        for j, y in enumerate(v): ax.text(j + (i - 0.5) * w, y * 1.05, f"{y:.0f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(6)); ax.set_xticklabels(keys); ax.set_yscale("log"); ax.set_ylabel("latency (µs, log)"); ax.set_xlabel("percentile")
    ax.set_title("Exp 5: tail latency, 4 KiB random read, 60 s runs"); ax.legend()
    save(fig, "fig5_tail_latency", FOOT)

# ---- Fig 6: working set + sustained write
def per_second_series():
    sec = collections.defaultdict(lambda: collections.defaultdict(list))
    for lf in glob.glob(P3 + "/data/raw/exp6b/exp6b_bw.*.log"):
        for line in open(lf):
            p = line.split(","); sec[int(p[0]) // 1000][lf].append(float(p[1]) / 1e6)   # KiB/s -> GB/s (approx, 1 KiB = 1024 B)
    xs = sorted(sec); return xs, [sum(np.mean(v) for v in sec[s].values()) * 1.024 for s in xs]

def fig_state():
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.5), gridspec_kw={"width_ratios": [1, 1.4, 1.2]})
    rows = [r for r in SUM if r["exp"] == "exp6a"]
    for i, (rw, s, col) in enumerate((("randread", "r", C["blue"]), ("randwrite", "w", C["red"]))):
        for j, rg in enumerate(("1g", "32g")):
            r = next(x for x in rows if x["rw"] == rw and x["range"] == rg)
            ax[0].bar(i * 3 + j, f(r, s + "_iops_mean") / 1e3, yerr=f(r, s + "_iops_std") / 1e3, color=col, alpha=1 if j else 0.55, capsize=2)
            ax[0].text(i * 3 + j, f(r, s + "_iops_mean") / 1e3 + 4, rg.upper().replace("G", " GiB"), ha="center", fontsize=8)
    ax[0].set_xticks([0.5, 3.5]); ax[0].set_xticklabels(["4K rand read", "4K rand write"]); ax[0].set_ylabel("IOPS (thousands)")
    ax[0].set_title("Exp 6a: address range 1 vs 32 GiB (QD16)")
    xs, gb = per_second_series()
    ax[1].plot(xs, gb, color=C["blue"], lw=1); ax[1].set_ylim(0, max(gb) * 1.25); ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("write throughput (GB/s)")
    tl = [l.split() for l in open(P3 + "/data/raw/exp6b/temperature.log") if len(l.split()) == 2]
    if tl:
        t0 = int(tl[0][0]); a2 = ax[1].twinx(); a2.plot([int(a) - t0 for a, b in tl], [int(b) for a, b in tl], color=C["red"], lw=1)
        a2.set_ylabel("SMART temperature (°C)", color=C["red"]); a2.set_ylim(20, 90); a2.grid(False)
    ax[1].set_title("Exp 6b: 1 MiB sequential write, 2.2 TB, 1 s windows")
    cum = np.cumsum(gb) / 1e3
    ax[2].plot(cum, gb, color=C["blue"], lw=1); ax[2].set_ylim(0, max(gb) * 1.25); ax[2].set_xlabel("cumulative data written (TB)"); ax[2].set_ylabel("write throughput (GB/s)")
    ax[2].set_title("same data vs bytes written")
    save(fig, "fig6_working_set_and_sustained_write", FOOT.replace("n=3", "6a n=3, 6b single run (user-capped)"))

# ---- Fig 7: misleading setups
def fig_misleading():
    rows = sorted([r for r in SUM if r["exp"] == "exp7"], key=lambda r: r["cfg"])
    lab = {"A": "A\ncorrect", "B": "B\npage cache", "C": "C\nQD16", "D": "D\niodepth=64"}
    col = {"A": C["blue"], "B": C["red"], "C": C["sky"], "D": C["orange"]}
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.5))
    for i, r in enumerate(rows):
        ax[0].bar(i, f(r, "r_iops_mean"), yerr=f(r, "r_iops_std"), color=col[r["cfg"]], capsize=2)
        ax[1].bar(i, f(r, "r_lat_mean_us_mean"), yerr=f(r, "r_lat_mean_us_std"), color=col[r["cfg"]], capsize=2)
        ax[2].bar(i, f(r, "littles_qd_mean"), color=col[r["cfg"]]); ax[2].text(i, f(r, "littles_qd_mean") * 1.1, f"cfg {int(f(r,'cfg_qd_mean'))}", ha="center", fontsize=8)
    for a, yl, ttl in zip(ax, ("IOPS (log)", "mean latency (µs, log)", "effective QD (IOPS × latency, log)"), ("throughput", "latency", "effective vs configured depth")):
        a.set_xticks(range(len(rows))); a.set_xticklabels([lab[r["cfg"]] for r in rows], fontsize=8); a.set_yscale("log"); a.set_ylabel(yl); a.set_title(ttl)
    fig.suptitle("Exp 7: same 4 KiB random read on a 1 GiB range, flawed vs correct setups", fontsize=10)
    save(fig, "fig7_misleading_setups")

# ---- Fig 8: drift (anomaly)
def fig_drift():
    # every run of the identical workload: 4 KiB random read, 16 psync jobs, whole 32 GiB range, read-only
    def sel(r):
        if r["ioengine"] != "psync" or r["cfg_qd"] != "16" or float(r["w_iops"]) > 0: return False
        e = r["exp"]
        return ((e == "exp2" and r.get("rw") == "randread" and r.get("bs") == "4k") or e in ("exp3", "exp4", "exp4b", "drift", "driftseries")
                or (e == "exp5" and r.get("role") == "knee") or (e == "exp6a" and r.get("range") == "32g" and r.get("rw") == "randread")
                or (e == "exp7" and r.get("cfg") == "C")) and (e not in ("exp3",) or r.get("mixread") == "100") and (e not in ("exp4", "exp4b") or r.get("qd") == "16")
    pts = [(float(r["timestamp"]), float(r["r_iops"]) / 1e3, float(r["sys_cpu_pct"]), r["exp"]) for r in RUNS if sel(r)]
    pts = [p for p in pts if p[1] > 0]; pts.sort()
    cm = {"exp2": C["grey"], "exp3": C["orange"], "exp4": C["blue"], "exp4b": C["red"], "exp5": C["sky"], "exp6a": C["purple"], "exp7": C["grey"], "drift": C["green"], "driftseries": C["green"]}
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    for ex in sorted({p[3] for p in pts}):
        q = [p for p in pts if p[3] == ex]
        ax[0].scatter([datetime.datetime.fromtimestamp(p[0]) for p in q], [p[1] for p in q], s=9, color=cm.get(ex, "k"), label=ex)
        ax[1].scatter([p[2] for p in q], [p[1] for p in q], s=9, color=cm.get(ex, "k"))
    ax[0].set_ylabel("IOPS (thousands)"); ax[0].set_title("4 KiB random read, 16 psync jobs, every run in the campaign")
    ax[0].tick_params(axis="x", labelrotation=30); ax[0].legend(fontsize=8, ncol=2)
    ax[1].set_xlabel("fio system CPU (% of one core, summed)"); ax[1].set_ylabel("IOPS (thousands)"); ax[1].set_title("IOPS vs host kernel CPU")
    save(fig, "fig8_state_drift", "Two performance levels (~189 k and ~222 k IOPS) for an identical workload; cause not established")

# ---- Fig 9: roofline-style summary
def fig_roofline():
    best = lambda ex, rw, bs, s="r": next(f(r, s + "_bw_MBs_mean") for r in SUM if r["exp"] == ex and r.get("rw") == rw and r.get("bs") == bs)
    items = [("QD1 4K rand read", best("exp1", "randread", "4k"), C["sky"]), ("QD16 4K rand read", best("exp2", "randread", "4k"), C["sky"]),
             ("QD16 4K rand write", best("exp2", "randwrite", "4k", "w"), C["orange"]),
             ("QD16 256K rand read", best("exp2", "randread", "256k"), C["blue"]), ("QD16 1M seq read", best("exp2", "read", "1m"), C["blue"]),
             ("QD16 1M seq write", best("exp2", "write", "1m", "w"), C["red"]), ("sustained 1M seq write (2.2 TB)", 2.199e12 / 199.0 / 1e6, C["red"])]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.barh(range(len(items)), [i[1] / 1e3 for i in items], color=[i[2] for i in items])
    for i, it in enumerate(items): ax.text(it[1] / 1e3 + 0.1, i, f"{it[1]/1e3:.2f} GB/s", va="center", fontsize=8)
    for v, nm in ((3.94, "PCIe 3.0 x4 ≈ 3.9"), (7.88, "PCIe 4.0 x4 ≈ 7.9"), (15.75, "PCIe 5.0 x4 ≈ 15.8")):
        ax.axvline(v, color="k", ls="--", lw=0.7); ax.text(v - 0.1, -0.75, nm, fontsize=8, ha="right", va="center")
    ax.set_yticks(range(len(items))); ax.set_yticklabels([i[0] for i in items]); ax.set_ylim(len(items) - 0.5, -1.1); ax.set_xlabel("throughput (GB/s, 10^9 B/s)")
    ax.set_xlim(0, 17.5); ax.set_title("Measured throughput vs PCIe x4 payload ceilings\n(link generation not readable on macOS)", fontsize=10)
    save(fig, "fig9_roofline_summary", FOOT.replace("; mean ± sd, n=3", ""))

if __name__ == "__main__":
    for fn in (fig_baseline, fig_blocksize, fig_rwmix, fig_qd, fig_tail, fig_state, fig_misleading, fig_drift, fig_roofline):
        fn(); print("ok", fn.__name__)
