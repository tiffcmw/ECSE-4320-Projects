#!/usr/bin/env python3
"""Print the knee QD of Exp 4: smallest effective QD (psync, <=16 per process) whose mean IOPS is >= 90% of the peak
mean IOPS over all psync points (rule fixed in HYPOTHESES.md before data collection). Exits 1 if the knee would be >16."""
import csv, os, sys
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pts = {}
for r in csv.DictReader(open(os.path.join(P3, os.environ.get("PROC_SUBDIR", "data/processed"), "summary.csv"))):
    if r["exp"] == "exp4" and r["eng"] == "psync": pts[int(r["qd"])] = float(r["r_iops_mean"])
if not pts: sys.exit("no exp4 psync data")
peak = max(pts.values()); knee = min(q for q, v in pts.items() if v >= 0.9 * peak)
if knee > 16: sys.exit(f"knee QD {knee} > 16: single-process tail runs not possible")
print(knee)
