"""Plot helpers: consistent style, IQR bands, PNG + PDF output."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLOTS = os.path.join(ROOT, "plots")
COLORS = ["#1f77b4", "#d95f02", "#1b9e77", "#7570b3", "#e7298a", "#666666"]

# Cache boundaries from sysctl (docs/ENVIRONMENT.md). SLC size is not exposed.
BOUNDS = [(128 * 1024, "Super L1D 128 KB"), (64 * 1024, "Perf L1D 64 KB"),
          (8 * 2 ** 20, "Perf L2 8 MB"), (16 * 2 ** 20, "Super L2 16 MB")]


def fmt_bytes(x, _=None):
    for unit, d in (("GB", 2 ** 30), ("MB", 2 ** 20), ("KB", 2 ** 10)):
        if x >= d:
            return f"{x / d:g} {unit}"
    return f"{x:g} B"


def new_ax(figsize=(8, 4.8)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True, which="both", alpha=0.25)
    return fig, ax


def band(ax, x, med, q1, q3, label, color, mn=None, marker="o"):
    ax.plot(x, med, marker=marker, ms=3.5, lw=1.4, color=color, label=label)
    ax.fill_between(x, q1, q3, color=color, alpha=0.25, lw=0)
    if mn is not None:
        ax.plot(x, mn, ls=":", lw=0.9, color=color, alpha=0.8)


def mark_bounds(ax, which=(0, 1, 2, 3)):
    ymax = ax.get_ylim()[1]
    for i in which:
        x, lab = BOUNDS[i]
        ax.axvline(x, color="gray", ls="--", lw=0.8, alpha=0.7)
        ax.text(x, ymax, " " + lab, rotation=90, va="top", ha="right", fontsize=7, color="gray")


def save(fig, name):
    os.makedirs(PLOTS, exist_ok=True)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(PLOTS, f"{name}.{ext}"), dpi=160)
    plt.close(fig)
    print("saved", name)


def col(rows, key, cast=float):
    return np.array([cast(r[key]) if r[key] != "" else np.nan for r in rows])
