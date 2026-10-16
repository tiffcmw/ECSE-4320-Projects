#!/usr/bin/env python3
"""Parse raw fio JSON (data/raw/**) into data/processed/all_runs.csv and summary.csv.

File names encode knobs: <exp>__key=value__...__t<trial>[__p<proc>].json
Runs split over several fio processes (suffix __p<k>, used for QD > 16) are merged:
IOPS and bandwidth are summed (exact), mean latency is IO-weighted (exact), percentiles are
IO-weighted averages of the per-process percentiles (an approximation; column `merged_procs` > 1 marks them).
Units: latency in microseconds, bandwidth in MB/s (1 MB = 10^6 bytes), IOPS in IO/s.
"""
import csv, glob, json, os, re, sys
from collections import defaultdict
import numpy as np

P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(P3, os.environ.get("RAW_SUBDIR", "data/raw"))
OUT = os.path.join(P3, "data", "processed")
PCTS = ["50", "90", "95", "99", "99.9", "99.99"]

def load(path):
    t = open(path).read()
    return json.loads(t[t.index("{"):])

def side(j, d):
    s = j[d]
    p = {round(float(k), 3): v for k, v in s.get("lat_ns", {}).get("percentile", {}).items()}
    out = {"iops": s["iops"], "bw_MBs": s["bw_bytes"] / 1e6, "ios": s["total_ios"], "bytes": s["io_bytes"],
           "lat_mean_us": s["lat_ns"]["mean"] / 1e3 if s["total_ios"] else float("nan"),
           "lat_std_us": s["lat_ns"]["stddev"] / 1e3 if s["total_ios"] else float("nan"),
           "lat_min_us": s["lat_ns"]["min"] / 1e3, "lat_max_us": s["lat_ns"]["max"] / 1e3}
    for q in PCTS:
        out["lat_p" + q + "_us"] = p.get(round(float(q), 3), float("nan")) / 1e3
    return out

def parse_name(fn):
    base = os.path.basename(fn)[:-5]
    parts = base.split("__")
    d = {"exp": parts[0]}; proc = None; trial = 1
    for p in parts[1:]:
        if re.fullmatch(r"t\d+", p): trial = int(p[1:])
        elif re.fullmatch(r"p\d+", p): proc = int(p[1:])
        elif "=" in p: k, v = p.split("=", 1); d[k] = v
    return d, trial, proc

def main():
    files = [f for f in glob.glob(RAW + "/*/*.json") if "/health/" not in f and "/precondition/" not in f
             and os.path.basename(f) != "exp6b__sustained.json"]
    groups = defaultdict(list)
    for f in sorted(files):
        knobs, trial, proc = parse_name(f)
        groups[(tuple(sorted(knobs.items())), trial)].append(f)
    rows = []
    for (knobs, trial), fl in groups.items():
        row = dict(knobs); row["trial"] = trial; row["merged_procs"] = len(fl)
        sides = {"r": [], "w": []}; cfg_qd = 0; engine = None; runtime = []
        for f in fl:
            J = load(f); j = J["jobs"][0]; o = {**J.get("global options", {}), **j.get("job options", {})}
            cfg_qd += int(o.get("numjobs", 1)) * int(o.get("iodepth", 1)); engine = o.get("ioengine", "?")
            runtime.append(j["read"]["runtime"] or j["write"]["runtime"])
            for k, d in (("r", "read"), ("w", "write")): sides[k].append(side(j, d))
            row["fio_version"] = J.get("fio version", "")
            row["direct"] = o.get("direct", "")
        row["ioengine"] = engine; row["cfg_qd"] = cfg_qd; row["runtime_ms"] = int(np.mean(runtime))
        littles = 0.0
        for k in ("r", "w"):
            S = sides[k]; tot = sum(s["ios"] for s in S)
            for m in ("iops", "bw_MBs", "ios", "bytes"): row[f"{k}_{m}"] = sum(s[m] for s in S)
            for m in S[0]:
                if m in ("iops", "bw_MBs", "ios", "bytes"): continue
                w = np.array([s["ios"] for s in S], float)
                vals = np.array([s[m] for s in S], float)
                if tot == 0: row[f"{k}_{m}"] = float("nan")
                elif m == "lat_min_us": row[f"{k}_{m}"] = vals.min()
                elif m == "lat_max_us": row[f"{k}_{m}"] = vals.max()
                else: row[f"{k}_{m}"] = float(np.sum(w * vals) / w.sum())
            if tot: littles += row[f"{k}_iops"] * row[f"{k}_lat_mean_us"] / 1e6
        row["littles_qd"] = littles                          # outstanding = throughput x latency
        row["qd_error_pct"] = 100 * (littles - cfg_qd) / cfg_qd
        row["qd_flag"] = "MISMATCH" if abs(row["qd_error_pct"]) > 10 else ""
        row["tot_iops"] = row["r_iops"] + row["w_iops"]
        row["tot_bw_MBs"] = row["r_bw_MBs"] + row["w_bw_MBs"]
        rows.append(row)
    if not rows: sys.exit("no raw json found in " + RAW)
    cols = []
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    rows.sort(key=lambda r: [str(r.get(c, "")) for c in cols[:12]])
    os.makedirs(OUT, exist_ok=True)
    with open(OUT + "/all_runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(rows)
    # summary over trials
    num = [c for c in cols if isinstance(rows[0].get(c), (int, float)) and c not in ("trial",)]
    knobcols = [c for c in cols if c not in num and c not in ("trial", "qd_flag", "fio_version", "ioengine", "direct") or c in ("ioengine",)]
    g = defaultdict(list)
    for r in rows: g[tuple(r.get(c, "") for c in knobcols)].append(r)
    with open(OUT + "/summary.csv", "w", newline="") as fh:
        hdr = knobcols + ["n_trials"] + [f"{c}_{s}" for c in num for s in ("mean", "std", "min", "max")] + ["qd_flag"]
        w = csv.writer(fh); w.writerow(hdr)
        for key, rs in g.items():
            line = list(key) + [len(rs)]
            for c in num:
                v = np.array([r.get(c, float("nan")) for r in rs], float)
                line += [v.mean(), v.std(ddof=1) if len(v) > 1 else 0.0, v.min(), v.max()]
            line.append(";".join(sorted({r["qd_flag"] for r in rs if r["qd_flag"]})))
            w.writerow(line)
    print(f"parsed {len(rows)} runs -> {OUT}/all_runs.csv, {len(g)} points -> summary.csv")

if __name__ == "__main__":
    main()
