"""AI-resilience diagnostic plot: naive sequential chase vs stride, with random reference."""
import csv

import plotlib as pl
from matplotlib.ticker import FuncFormatter

rows = [r for r in csv.DictReader(open(f"{pl.ROOT}/data/processed/chase_diag.csv")) if r["n"] != "0"]
seq = sorted([r for r in rows if r["design"] == "seq"], key=lambda r: int(r["stride"]))
rnd = [r for r in rows if r["design"] == "random"][0]
fig, ax = pl.new_ax((7.5, 4.6))
pl.band(ax, pl.col(seq, "stride"), pl.col(seq, "median"), pl.col(seq, "q1"), pl.col(seq, "q3"), "sequential (stride-linked) chase, 1 GB", pl.COLORS[3])
ax.axhline(float(rnd["median"]), color=pl.COLORS[1], lw=1.6, label=f"random single-cycle chase, 1 GB ({float(rnd['median']):.0f} ns)")
ax.set_xscale("log", base=2); ax.set_yscale("log")
ax.xaxis.set_major_formatter(FuncFormatter(pl.fmt_bytes))
ax.set_xlabel("Node spacing / stride (bytes)"); ax.set_ylabel("Latency per dependent load (ns)")
ax.set_title("Naive chase is prefetcher-fed at every constant stride")
ax.legend(fontsize=8, loc="center right")
pl.save(fig, "ai_resilience_stride_diag")
