#!/usr/bin/env python3
"""Raw long-format CSVs -> processed summary tables (median, IQR, min, max, n per configuration).

  scripts/parse.py [--sid ID] [--raw DIR] [--out DIR]
Rows with minor page faults inside the timed region are excluded and counted (column n_faulted).
"""
import argparse, csv, glob, json, os, re
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ["exp", "variant", "ws_bytes", "stride", "size", "threads", "param", "metric"]
NO_FAULT_FILTER = {"bw_gbps", "bw_thread_min", "bw_thread_max", "lat_ns"}   # process-wide counters in loaded windows


def newest_sid(raw):
    metas = sorted(glob.glob(os.path.join(raw, "meta_*_full.json")) or glob.glob(os.path.join(raw, "meta_*_quick.json")),
                   key=os.path.getmtime)
    if not metas:
        raise SystemExit("no meta_*.json found in " + raw)
    return json.load(open(metas[-1]))["session"]


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def summarize(rows):
    g = {}
    for r in rows:
        k = tuple(r[c] for c in KEYS)
        g.setdefault(k, []).append((float(r["value"]), int(r["faults"])))
    out = []; rounds = []
    for k, v in g.items():
        vals = np.array([x for x, f in v])
        flt = np.array([f for x, f in v])
        keep = vals if k[-1] in NO_FAULT_FILTER else vals[flt == 0]
        nf = len(vals) - len(keep)
        if len(keep) == 0:
            keep = vals
        q1, med, q3 = np.percentile(keep, [25, 50, 75])
        out.append(list(k) + [med, q1, q3, keep.min(), keep.max(), len(keep), nf])
        rounds.append(dict(zip(KEYS, k), values=[float(x) for x in keep]))
    out.sort(key=lambda r: (r[0], r[1], float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6]), r[7]))
    return out, rounds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sid", default="")
    ap.add_argument("--raw", default=os.environ.get("P2_RAW", os.path.join(ROOT, "data", "raw")))
    ap.add_argument("--out", default=os.environ.get("P2_PROC", os.path.join(ROOT, "data", "processed")))
    a = ap.parse_args()
    sid = a.sid or newest_sid(a.raw)
    os.makedirs(a.out, exist_ok=True)
    n = 0
    for sx in (sid, sid + "-pmu"):   # the privileged counter run, if present, uses the suffix -pmu
      for path in sorted(glob.glob(os.path.join(a.raw, f"*_{sx}.csv"))):
          if os.path.basename(path).startswith("xctrace"):
              continue
          grp = re.sub(rf"_{re.escape(sx)}\.csv$", "", os.path.basename(path))
          rows = read_csv(path)
          if not rows:
              continue
          out, rounds = summarize(rows)
          json.dump(rounds, open(os.path.join(a.out, f"{grp}.rounds.json"), "w"))
          with open(os.path.join(a.out, f"{grp}.csv"), "w", newline="") as f:
              w = csv.writer(f)
              w.writerow(KEYS + ["median", "q1", "q3", "min", "max", "n", "n_faulted"])
              w.writerows(out)
          n += 1
    json.dump({"sid": sid}, open(os.path.join(a.out, "SESSION.json"), "w"))
    print(f"parsed {n} groups for session {sid} -> {a.out}")


if __name__ == "__main__":
    main()
