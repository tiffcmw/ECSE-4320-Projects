"""Mechanism 2 plots from data/raw/qos_*.csv."""
import numpy as np

import analyze
import plotlib as pl

G = ["exp", "kind", "policy", "hog", "qos_req", "threads", "qos_where", "chunks"]
QOS = ["interactive", "initiated", "default", "utility", "background"]


def table(rows, value):
    out = analyze.aggregate(rows, value, G)
    analyze.write_processed("qos", out, name=f"qos_{value}")
    return {tuple(r[c] for c in G): r for r in out if r["n"]}


def label(k):
    exp, kind, policy, hog, qos, thr, where, chunks = k
    return qos if policy == "plain" else policy


def bars(ax, items, value_tab, color, ylabel_log=False):
    xs, med, lo, hi, labs = [], [], [], [], []
    for i, (k, lab) in enumerate(items):
        r = value_tab.get(k)
        if not r:
            continue
        xs.append(i); labs.append(lab)
        med.append(float(r["median"])); lo.append(float(r["median"]) - float(r["q1"])); hi.append(float(r["q3"]) - float(r["median"]))
    ax.bar(xs, med, yerr=[lo, hi], color=color, capsize=3)
    ax.set_xticks(xs); ax.set_xticklabels(labs, rotation=35, ha="right", fontsize=8)
    if ylabel_log:
        ax.set_yscale("log")


def main():
    rows = analyze.load("qos")
    thr = table(rows, "throughput_munits_s")
    cow = table(rows, "cpu_over_wall")
    p99 = table(rows, "p99_chunk_us")

    def key(exp, kind, qos, policy="plain", hog="0", threads="1", where="inside", chunks="200"):
        return (exp, kind, policy, hog, qos, threads, where, chunks)

    # E2a: idle, 1 thread
    fig, axs = pl.new_ax((11, 4.2))[0], None
    fig.clf()
    axs = fig.subplots(1, 2)
    for ax, kind, unit in zip(axs, ("compute", "mem"), ("M multiply-adds / s", "M dependent loads / s")):
        items = [(key("E2a", kind, q), q) for q in QOS] + [(key("E2a", kind, "none", policy=p), p) for p in ("clamp_utility", "clamp_background", "bg_b")]
        bars(ax, items, thr, [pl.COLORS[0]] * 5 + [pl.COLORS[1]] * 3)
        ax.set_ylabel(f"Throughput ({unit})"); ax.set_title(f"{kind}-bound, idle, 1 thread (median, IQR)")
        ax.grid(True, axis="y", alpha=0.25)
    pl.save(fig, "mech2_idle_qos_policy")

    # E2b: N threads
    fig = pl.new_ax()[0]; fig.clf(); axs = fig.subplots(2, 2, figsize=(11, 7)) if False else fig.subplots(2, 2)
    fig.set_size_inches(11, 7)
    for j, kind in enumerate(("compute", "mem")):
        for i, (tab, name, logy) in enumerate(((thr, "Per-thread throughput (M units/s)", False), (p99, "p99 chunk time (us)", True))):
            ax = axs[i][j]
            for ci, q in enumerate(("default", "background")):
                ns, med, lo, hi = [], [], [], []
                for n in (1, 4, 6, 12, 18, 36):
                    k = key("E2b", kind, q, threads=str(n)) if n > 1 else key("E2a", kind, q)
                    r = tab.get(k)
                    if r:
                        ns.append(n); med.append(float(r["median"])); lo.append(float(r["q1"])); hi.append(float(r["q3"]))
                if ns:
                    pl.band(ax, ns, med, lo, hi, f"QoS {q}", pl.COLORS[ci])
            ax.set_xscale("log"); ax.set_xticks([1, 4, 6, 12, 18, 36]); ax.set_xticklabels([1, 4, 6, 12, 18, 36])
            if logy:
                ax.set_yscale("log")
            ax.set_xlabel("Worker threads (18 cores)"); ax.set_ylabel(name); ax.set_title(f"{kind}-bound"); ax.grid(True, alpha=0.25)
            ax.legend(fontsize=8)
    pl.save(fig, "mech2_threads")

    # E2c: contention
    fig = pl.new_ax()[0]; fig.clf(); axs = fig.subplots(1, 3); fig.set_size_inches(14, 4.4)
    for kind, off in (("compute", 0), ("mem", 1)):
        pass
    kinds = ("compute", "mem")
    for ax, (tab, yl, logy) in zip(axs, ((cow, "cpu time / wall time", False), (thr, "Throughput (M units/s)", True), (p99, "p99 chunk time (us)", True))):
        items = []
        for kind in kinds:
            items += [(key("E2c", kind, q, hog="1"), f"{kind[:4]} {q[:5]}") for q in QOS]
            items += [(key("E2c", kind, "none", policy="clamp_background", hog="1", chunks="20"), f"{kind[:4]} clamp-bg"),
                      (key("E2c", kind, "none", policy="bg_b", hog="1", chunks="10"), f"{kind[:4]} -b")]
            items += [(key("E2x", kind, q, hog="1", where="main_after"), f"{kind[:4]} {q[:5]} main_after") for q in ("interactive", "background")]
        bars(ax, items, tab, [pl.COLORS[0] if "clamp" not in l and "-b" not in l else pl.COLORS[1] for _, l in items], logy)
        ax.set_ylabel(yl); ax.grid(True, axis="y", alpha=0.25)
    axs[0].set_title("CPU share under 36-thread hog"); axs[1].set_title("Throughput under hog"); axs[2].set_title("Tail latency under hog")
    pl.save(fig, "mech2_contention")


if __name__ == "__main__":
    main()
