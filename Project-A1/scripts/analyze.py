"""Aggregate raw CSVs into processed CSVs: median, IQR, min, max, n per group.

Usage: analyze.py <raw_prefix> <value_col> <group_col> [<group_col> ...]
Uses the newest data/raw/<prefix>_*.csv. Rows flagged throttled=1 are excluded
and counted in `n_throttled`; rows with minor page faults in the timed region are
excluded and counted in `n_faulted`.
"""
import csv
import glob
import os
import sys
from collections import defaultdict

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def latest(prefix):
    files = sorted(glob.glob(os.path.join(ROOT, "data", "raw", f"{prefix}_[0-9]*.csv")))
    if not files:
        raise SystemExit(f"no raw file for {prefix}")
    return files[-1]


def load(prefix):
    with open(latest(prefix)) as f:
        return list(csv.DictReader(f))


def aggregate(rows, value_col, group_cols):
    groups, thr, flt = defaultdict(list), defaultdict(int), defaultdict(int)
    for r in rows:
        key = tuple(r[c] for c in group_cols)
        if r["throttled"] == "1":
            thr[key] += 1
            continue
        if int(r.get("minflt_timed") or 0) > 0:  # page faults inside the timed region
            flt[key] += 1
            continue
        groups[key].append(float(r[value_col]))
    out = []
    for key in sorted(set(groups) | set(thr) | set(flt), key=lambda k: [(float(x) if x.replace('.', '', 1).isdigit() else x) for x in k]):
        v = np.array(groups.get(key, []))
        row = dict(zip(group_cols, key))
        if len(v):
            row.update(median=np.median(v), q1=np.percentile(v, 25), q3=np.percentile(v, 75),
                       min=v.min(), max=v.max(), n=len(v))
        else:
            row.update(median="", q1="", q3="", min="", max="", n=0)
        row["n_throttled"] = thr.get(key, 0)
        row["n_faulted"] = flt.get(key, 0)
        out.append(row)
    return out


def write_processed(prefix, rows, name=None):
    os.makedirs(os.path.join(ROOT, "data", "processed"), exist_ok=True)
    path = os.path.join(ROOT, "data", "processed", f"{name or prefix}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def main():
    prefix, value_col, group_cols = sys.argv[1], sys.argv[2], sys.argv[3:]
    p = write_processed(prefix, aggregate(load(prefix), value_col, group_cols))
    print("wrote", p)


if __name__ == "__main__":
    main()
