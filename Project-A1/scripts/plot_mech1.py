"""Mechanism 1 plots: latency curves, naive-vs-random (AI-resilience), TLB, bandwidth."""
import analyze
import plotlib as pl
from matplotlib.ticker import FuncFormatter


def series(prefix, value, groups, flt=None):
    rows = analyze.aggregate(analyze.load(prefix), value, groups)
    analyze.write_processed(prefix, rows)
    return [r for r in rows if r["n"] and (flt is None or flt(r))]


def latency_plots():
    rnd = series("chase_random", "ns_per_load", ["bytes"])
    nai = series("chase_naive", "ns_per_load", ["bytes"])
    for name, sets in (("mech1_latency_random", [("random single-cycle chase (corrected)", rnd, 1)]),
                       ("mech1_latency_naive_vs_random", [("naive sequential chase (flawed)", nai, 3),
                                                          ("random single-cycle chase (corrected)", rnd, 1)])):
        fig, ax = pl.new_ax()
        for label, rows, ci in sets:
            x = pl.col(rows, "bytes")
            pl.band(ax, x, pl.col(rows, "median"), pl.col(rows, "q1"), pl.col(rows, "q3"), label, pl.COLORS[ci], pl.col(rows, "min"))
        ax.set_xscale("log", base=2); ax.set_yscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(pl.fmt_bytes))
        ax.set_xlabel("Working set (bytes, one node per 128 B line)")
        ax.set_ylabel("Latency per dependent load (ns)")
        ax.set_title("Pointer-chase latency vs working set (median, IQR band, dotted = min)")
        pl.mark_bounds(ax)
        ax.legend(loc="center left", fontsize=8)
        pl.save(fig, name)


def tlb_plot():
    rows = series("chase_tlb", "ns_per_load", ["bytes", "stride", "n_nodes"])
    fig, ax = pl.new_ax()
    for ci, (stride, lab) in enumerate(((128, "packed (stride 128 B)"), (4224, "4 nodes per 16 KB page"),
                                        (16512, "1 node per 16 KB page"))):
        rs = sorted([r for r in rows if int(r["stride"]) == stride], key=lambda r: int(r["n_nodes"]))
        pl.band(ax, pl.col(rs, "n_nodes"), pl.col(rs, "median"), pl.col(rs, "q1"), pl.col(rs, "q3"), lab, pl.COLORS[ci], pl.col(rs, "min"))
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Number of nodes (= cache lines touched)")
    ax.set_ylabel("Latency per dependent load (ns)")
    ax.set_title("TLB reach: same line count, different page count (16 KB pages)")
    ax.legend(fontsize=8)
    pl.save(fig, "mech1_tlb")


def bw_plot():
    rows = series("bw", "gbps", ["kernel_cfg", "bytes"])
    fig, ax = pl.new_ax()
    kernels = [("read_seq", "sequential read (NEON)"), ("triad", "STREAM-like triad (24 B/elem)"),
               ("stride4", "stride 4 lines (512 B)"), ("stride16", "stride 16 lines (2 KB)"),
               ("stride128", "stride 128 lines (16 KB)"), ("read_rand", "random line reads")]
    for ci, (k, lab) in enumerate(kernels):
        rs = sorted([r for r in rows if r["kernel_cfg"] == k], key=lambda r: int(r["bytes"]))
        if rs:
            pl.band(ax, pl.col(rs, "bytes"), pl.col(rs, "median"), pl.col(rs, "q1"), pl.col(rs, "q3"), lab, pl.COLORS[ci % 6])
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(pl.fmt_bytes))
    ax.set_xlabel("Working set (bytes)")
    ax.set_ylabel("Bandwidth (GB/s, line traffic)")
    ax.set_title("Single-thread bandwidth vs working set and access pattern")
    pl.mark_bounds(ax, (0, 3))
    ax.legend(fontsize=7)
    pl.save(fig, "mech1_bandwidth")


if __name__ == "__main__":
    latency_plots(); tlb_plot(); bw_plot()
