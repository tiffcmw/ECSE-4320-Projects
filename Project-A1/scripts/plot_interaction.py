"""Phase 4 plots: core tier x working set."""
import numpy as np
from matplotlib.ticker import FuncFormatter

import analyze
import plotlib as pl

LAB = {"S": "S: plain (Super)", "U": "U: clamp utility (Super, control)", "P": "P: clamp background (Performance, low-power policy)"}
COL = {"S": pl.COLORS[0], "U": pl.COLORS[2], "P": pl.COLORS[1]}


def curves(prefix, value, extra=()):
    rows = analyze.aggregate(analyze.load(prefix), value, ["cond", *extra, "bytes"])
    analyze.write_processed(prefix, rows)
    out = {}
    for r in rows:
        if r["n"]:
            out.setdefault((r["cond"],) + tuple(r[e] for e in extra), []).append(r)
    for k in out:
        out[k].sort(key=lambda r: int(r["bytes"]))
    return out


def fmt(ax):
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_formatter(FuncFormatter(pl.fmt_bytes))
    ax.grid(True, which="both", alpha=0.25)


def latency():
    c = curves("inter_latency", "ns_per_load")
    fig = pl.new_ax((12, 4.8))[0]
    fig.clf(); a1, a2 = fig.subplots(1, 2)
    base = {int(r["bytes"]): float(r["median"]) for r in c[("S",)]}
    for cond in ("S", "U", "P"):
        rs = c[(cond,)]
        x = pl.col(rs, "bytes")
        pl.band(a1, x, pl.col(rs, "median"), pl.col(rs, "q1"), pl.col(rs, "q3"), LAB[cond], COL[cond])
        if cond != "S":
            a2.plot(x, [float(r["median"]) / base[int(r["bytes"])] for r in rs], "o-", ms=3.5, color=COL[cond], label=f"{cond} / S")
    a1.set_yscale("log"); a1.set_ylabel("Latency per dependent load (ns)")
    a1.set_title("Latency vs working set by core-tier condition"); a1.legend(fontsize=7)
    a2.axhline(1, color="gray", lw=0.8); a2.set_ylabel("Latency ratio to S (median)"); a2.set_title("Ratio to plain Super (1 = no change)")
    a2.legend(fontsize=8)
    for ax in (a1, a2):
        fmt(ax); ax.set_xlabel("Working set (bytes)")
    ymax = a2.get_ylim()[1]
    for b, t in ((128 * 1024, "Super L1D"), (8 * 2 ** 20, "Perf L2"), (16 * 2 ** 20, "Super L2")):
        a2.axvline(b, color="gray", ls="--", lw=0.8); a2.text(b, ymax, " " + t, rotation=90, va="top", ha="right", fontsize=7, color="gray")
    pl.save(fig, "inter_latency_tier")


def bandwidth():
    c = curves("inter_bw", "gbps", extra=("kernel_cfg",))
    fig = pl.new_ax()[0]; fig.clf(); axs = fig.subplots(1, 2); fig.set_size_inches(12, 4.6)
    for ax, k in zip(axs, ("read_seq", "read_rand")):
        for cond in ("S", "U", "P"):
            rs = c[(cond, k)]
            pl.band(ax, pl.col(rs, "bytes"), pl.col(rs, "median"), pl.col(rs, "q1"), pl.col(rs, "q3"), LAB[cond], COL[cond])
        fmt(ax); ax.set_yscale("log"); ax.set_xlabel("Working set (bytes)"); ax.set_ylabel("Bandwidth (GB/s)")
        ax.set_title({"read_seq": "Sequential read", "read_rand": "Random line reads"}[k]); ax.legend(fontsize=7)
    pl.save(fig, "inter_bandwidth_tier")


def per_thread():
    rows = [r for r in analyze.load("inter_18t") if r["throttled"] != "1"]
    by = {}
    for r in rows:
        by.setdefault(int(r["bytes"]), []).append(1000.0 / float(r["throughput_munits_s"]))  # ns per load, per (rep, thread)
    xs = sorted(by)
    fig, ax = pl.new_ax((8, 4.8))
    for b in xs:
        ax.scatter([b] * len(by[b]), by[b], s=5, color=pl.COLORS[3], alpha=0.25, lw=0)
    ax.plot(xs, [np.median(by[b]) for b in xs], "o-", ms=3.5, color=pl.COLORS[3], label="18 threads: per-thread median")
    S = analyze.aggregate([r for r in analyze.load("inter_latency")], "ns_per_load", ["cond", "bytes"])
    s = sorted([r for r in S if r["cond"] == "S" and r["n"]], key=lambda r: int(r["bytes"]))
    ax.plot([int(r["bytes"]) for r in s], [float(r["median"]) for r in s], "k--", lw=1, label="1 thread, plain (S)")
    fmt(ax); ax.set_yscale("log"); ax.set_xlabel("Working set per thread (bytes)"); ax.set_ylabel("Per-thread latency per dependent load (ns)")
    ax.set_title("18 plain threads: every (rep, thread) value (dots)"); ax.legend(fontsize=8)
    pl.save(fig, "inter_18threads")
    analyze.write_processed("inter_18t", analyze.aggregate([dict(r, ns=str(1000.0 / float(r["throughput_munits_s"]))) for r in rows], "ns", ["bytes"]), name="inter_18t_ns")


if __name__ == "__main__":
    latency(); bandwidth(); per_thread()
