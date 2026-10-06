"""Summarize E0 (timer + noise) into data/processed/noise_summary.csv."""
import csv
import os

import numpy as np

import analyze

rows = [r for r in analyze.load("noise") if r["throttled"] != "1"]
out = []
for kind in ("timer_granularity", "timer_overhead", "fixed_work_ns_per_iter_median", "fixed_work_summary_iqr_over_median"):
    v = np.array([float(r["value"]) for r in rows if r["kind"] == kind])
    out.append({"metric": kind, "unit": [r["unit"] for r in rows if r["kind"] == kind][0], "min": v.min(), "median": np.median(v), "max": v.max(), "n_invocations": len(v)})
os.makedirs(f"{analyze.ROOT}/data/processed", exist_ok=True)
with open(f"{analyze.ROOT}/data/processed/noise_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
for r in out:
    print(r)
