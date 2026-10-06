#!/usr/bin/env python3
"""Shared loading and statistics for benchmark CSVs. Uses only numpy and csv.
Usage: analyze.py summary FILE [FILE...]   prints median, IQR, min per configuration."""
import csv, sys, glob, collections
import numpy as np

FLOPS = {"saxpy": 2.0, "mul": 1.0, "dot": 2.0, "stencil": 5.0}      # per element
BYTES = {"saxpy": 3, "mul": 3, "dot": 2, "stencil": 2}               # useful bytes = this * dtype size
SIZEOF = {"f32": 4, "f64": 8, "u32": 4}
THROTTLE_LEVEL = 1  # thermal pressure level >= 1 (moderate or worse) marks a throttled sample


def load(paths):
    rows = []
    for p in paths:
        with open(p) as f:
            for r in csv.DictReader(f):
                r["n"] = int(r["n"]); r["ws_bytes"] = int(r["ws_bytes"]); r["offset"] = int(r["offset"]); r["stride"] = int(r["stride"])
                r["ns"] = float(r["ns_per_call"]); r["pass"] = int(r["pass"]); r["rep"] = int(r["rep"])
                r["therm"] = max(int(r["therm_before"]), int(r["therm_after"]))
                rows.append(r)
    return rows


def freq_ghz(freq_csv_paths, qos="user-interactive"):
    """Effective clock from the dependent add chain (1 cycle per add). Returns (median GHz, IQR half-width GHz)."""
    v = []
    for p in freq_csv_paths:
        with open(p) as f:
            for r in csv.DictReader(f):
                if r["test"] == "add" and r["qos"] == qos:
                    v.append(1.0 / float(r["ns_per_op"]))
    v = np.array(v)
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    return q2, (q3 - q1) / 2


def stats(x):
    x = np.asarray(x, float)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return {"median": med, "q1": q1, "q3": q3, "min": x.min(), "max": x.max(), "n": len(x)}


def group(rows, keys=("build", "kernel", "dtype", "n", "offset", "stride"), drop_throttled=True):
    g = collections.defaultdict(list)
    thr = collections.Counter()
    for r in rows:
        k = tuple(r[x] for x in keys)
        if drop_throttled and r["therm"] >= THROTTLE_LEVEL:
            thr[k] += 1
            continue
        g[k].append(r["ns"])
    return g, thr


def derive(kernel, dtype, n, ns, ghz=None):
    """ns per call -> dict of ns/elem, GFLOP/s, GiB/s (useful bytes), cycles/elem."""
    ne = n - 2 if kernel == "stencil" else n
    d = {"ns_per_elem": ns / ne,
         "gflops": FLOPS[kernel] * ne / ns,
         "gibs": BYTES[kernel] * SIZEOF[dtype] * n / ns * 1e9 / 2**30}
    if ghz:
        d["cycles_per_elem"] = ns / ne * ghz
    return d


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "summary":
        sys.exit(__doc__)
    files = [f for a in sys.argv[2:] for f in glob.glob(a)]
    rows = load(files)
    g, thr = group(rows)
    print("%-16s %-8s %-4s %10s %10s %10s %9s %9s %8s" % ("build", "kernel", "dt", "n", "median ns", "IQR ns", "GFLOP/s", "GiB/s", "thrown"))
    for k in sorted(g, key=lambda t: (t[1], t[2], t[3], t[0])):
        s = stats(g[k]); d = derive(k[1], k[2], k[3], s["median"])
        print("%-16s %-8s %-4s %10d %10.1f %10.1f %9.2f %9.2f %8d" % (k[0], k[1], k[2], k[3], s["median"], s["q3"] - s["q1"], d["gflops"], d["gibs"], thr.get(k, 0)))
