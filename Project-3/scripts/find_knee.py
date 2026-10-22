#!/usr/bin/env python3
"""Knee of Exp 4 (rule fixed in HYPOTHESES.md before data collection): the smallest effective queue depth whose mean IOPS
is >= 90% of the peak mean IOPS. Considers every Exp 4 point whose Little's-law check passed (effective depth within 10%
of configured). Prints: ENGINE NUMJOBS IODEPTH THREAD QD  (the fio configuration that reproduces that point)."""
import csv, os, sys
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [r for r in csv.DictReader(open(os.path.join(P3, os.environ.get("PROC_SUBDIR", "data/processed"), "summary.csv")))
        if r["exp"] == "exp4" and not r["qd_flag"]]
if not rows: sys.exit("no valid exp4 data")
pts = {}  # (eff qd rounded, engine) -> iops
for r in rows: pts[(int(r["qd"]), r["eng"])] = float(r["r_iops_mean"])
peak = max(pts.values())
cands = sorted((q, 0 if e == "psync" else 1, e) for (q, e), v in pts.items() if v >= 0.9 * peak)
q, _, e = cands[0]
cfg = {"psync": (q, 1, 1), "posixaio": (1, q, 1)}[e]
print(e, *cfg, q)
