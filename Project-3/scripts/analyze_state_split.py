#!/usr/bin/env python3
"""Analysis only (no new measurements): do the two IOPS levels of the 4 KiB random read / 16 psync job workload
(about 189 k vs about 222 k) line up with run order, time since heavy writes, power source, thermal state or display state?
Inputs: data/processed/all_runs.csv, data/raw/health/*.txt, data/raw/health/pmset_events_2026-10-22.txt (pmset log extract).
Output: data/processed/tables/state_split.md"""
import csv, os, re, glob, datetime as dt
import numpy as np
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = list(csv.DictReader(open(P3 + "/data/processed/all_runs.csv")))
T = lambda s: dt.datetime.fromtimestamp(float(s))
# --- target runs (identical workload) and their state
def sel(r):
    if r["ioengine"] != "psync" or r["cfg_qd"] != "16" or float(r["w_iops"]) > 0: return False
    e = r["exp"]
    return ((e == "exp2" and r.get("rw") == "randread" and r.get("bs") == "4k") or e in ("exp3", "exp4", "exp4b", "drift", "driftseries")
            or (e == "exp5" and r.get("role") == "knee") or (e == "exp6a" and r.get("range") == "32g" and r.get("rw") == "randread")
            or (e == "exp7" and r.get("cfg") == "C")) and (e != "exp3" or r.get("mixread") == "100") and (e not in ("exp4", "exp4b") or r.get("qd") == "16")
tgt = sorted([r for r in RUNS if sel(r)], key=lambda r: float(r["timestamp"]))
iops = np.array([float(r["r_iops"]) for r in tgt]); high = (iops > 205e3).astype(float)
end = np.array([float(r["timestamp"]) for r in tgt])
dur = np.array([(float(r["runtime_ms"]) / 16 if r["runtime_ms"] else 0) / 1000 for r in tgt])   # runtime_ms is summed over 16 jobs
# --- heavy-write runs: any run that wrote data
W = sorted([(float(r["timestamp"]), float(r["w_bytes"])) for r in RUNS if float(r["w_bytes"]) > 0] +
           [(float(r["timestamp"]) + 0, 2.199e12) for r in [] ])
# Exp 6b is not in all_runs.csv: add it from its json (end time = file mtime of the json is unreliable, use JSON timestamp)
import json
t = open(P3 + "/data/raw/exp6b/exp6b__sustained.json").read(); J = json.loads(t[t.index("{"):]); W.append((J["timestamp"], J["jobs"][0]["write"]["io_bytes"])); W.sort()
Wt = np.array([w[0] for w in W]); Wb = np.array([w[1] for w in W])
def since_write(ts, minbytes):   # minutes since the end of the most recent write run of at least minbytes, relative to this run's start
    ok = Wt[(Wb >= minbytes) & (Wt < ts)]
    return (ts - ok.max()) / 60 if len(ok) else float("nan")
start = end - dur - 3
since10g = np.array([since_write(s, 10e9) for s in start])
gb_prior30 = np.array([Wb[(Wt < s) & (Wt > s - 1800)].sum() / 1e9 for s in start])
# --- pmset events: power source, display, sleep
ev = []
for l in open(P3 + "/data/raw/health/pmset_events_2026-10-22.txt"):
    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", l)
    if m: ev.append((dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp(), l))
def state_at(ts, key_on, key_off, default=None):
    cur = default
    for t, l in ev:
        if t > ts: break
        if key_on in l: cur = True
        elif key_off in l: cur = False
    return cur
def power(ts):
    cur = None
    for t, l in ev:
        if t > ts: break
        m = re.search(r"Using (AC|Batt)\(Charge: ?(\d+)", l)
        if m: cur = (m.group(1), int(m.group(2)))
    return cur
disp = [state_at(s, "Display is turned on", "Display is turned off") for s in start]
pw = [power(s) for s in start]
sleeps_in_run = [sum(1 for t, l in ev if s <= t <= e and ("Sleep" in l and "Entering" in l)) for s, e in zip(start, end)]
# --- thermal: SMART temperature before/after the stage that contains each run (no per-run reading exists)
def temps(stage):
    out = []
    for ph in ("before", "after"):
        p = f"{P3}/data/raw/health/{stage}_{ph}.txt"
        if os.path.exists(p):
            m = re.search(r"Temperature:\s+(\d+) Celsius", open(p).read()); out.append(int(m.group(1)) if m else None)
    return out
stage_of = {"exp2": "exp12", "exp3": "exp34", "exp4": "exp34", "exp5": "exp5", "exp6a": "exp67", "exp7": "exp67", "drift": "exp67", "driftseries": "driftseries", "exp4b": "exp4b"}
def r_pb(x):   # point-biserial correlation (Pearson with the 0/1 state)
    x = np.asarray(x, float); ok = ~np.isnan(x); return float(np.corrcoef(x[ok], high[ok])[0, 1])
order = np.arange(len(tgt))
lines = ["| Candidate factor | Low level (~189 k) | High level (~222 k) | Point-biserial r with level |", "|---|---|---|---|"]
def grp(x, f=lambda v: f"{np.nanmean(v):.1f}"): return f(np.asarray(x)[high == 0]), f(np.asarray(x)[high == 1])
lo, hi = grp(order); lines.append(f"| Run order (index 0 to {len(tgt)-1}) | mean {lo} | mean {hi} | {r_pb(order):+.2f} |")
lo, hi = grp(since10g); lines.append(f"| Minutes since last write run of at least 10 GB | mean {lo} (min {np.nanmin(since10g[high==0]):.1f}) | mean {hi} (min {np.nanmin(since10g[high==1]):.1f}) | {r_pb(since10g):+.2f} |")
lo, hi = grp(gb_prior30); lines.append(f"| GB written in the 30 min before the run | mean {lo} | mean {hi} | {r_pb(gb_prior30):+.2f} |")
acs = lambda m: sum(1 for p, h in zip(pw, high) if h == m and p and p[0] == "AC"); n0 = int((high == 0).sum()); n1 = int((high == 1).sum())
lines.append(f"| Power source at run start (pmset log) | AC in {acs(0)} of {n0} runs | AC in {acs(1)} of {n1} runs | not computable (no variation)" if acs(0) == n0 and acs(1) == n1 else f"| Power source | AC {acs(0)}/{n0} | AC {acs(1)}/{n1} | see log |")
ch = sorted({p[1] for p in pw if p}); lines[-1] += f" (battery charge held at {ch} %) |"
dn = lambda m: sum(1 for d, h in zip(disp, high) if h == m and d); lines.append(f"| Display on at run start (user activity proxy) | on in {dn(0)} of {n0} | on in {dn(1)} of {n1} | {r_pb([1.0 if d else 0.0 for d in disp]):+.2f} |")
lines.append(f"| Sleep events during the run | {sum(s for s, h in zip(sleeps_in_run, high) if h == 0)} | {sum(s for s, h in zip(sleeps_in_run, high) if h == 1)} | none |")
tv = lambda m: sorted({t for r, h in zip(tgt, high) if h == m for t in temps(stage_of[r["exp"]]) if t is not None})
lines.append(f"| SSD temperature (SMART, stage start and end, C) | {tv(0)} | {tv(1)} | overlap, no per-run reading |")
lo, hi = grp([float(r["sys_cpu_pct"]) for r in tgt]); lines.append(f"| fio system CPU (% of one core, summed) | mean {lo} | mean {hi} | {r_pb([float(r['sys_cpu_pct']) for r in tgt]):+.2f} (consequence, not cause) |")
# --- episode structure
eps = []; prev = None
for r, h, e in zip(tgt, high, end):
    if prev is None or h != prev[0]: eps.append([int(h), r["exp"], T(e).strftime("%H:%M"), T(e).strftime("%H:%M"), 1])
    else: eps[-1][3] = T(e).strftime("%H:%M"); eps[-1][4] += 1
    prev = (h,)
ep = ["", "| Episode | Level | Experiments (first run) | Time span | Runs |", "|---|---|---|---|---|"]
for i, (h, e0, a, b, n) in enumerate(eps): ep.append(f"| {i+1} | {'high' if h else 'low'} | {e0} | {a} to {b} | {n} |")
open(P3 + "/data/processed/tables/state_split.md", "w").write("\n".join(lines + ep) + "\n")
print("\n".join(lines + ep)); print("runs:", len(tgt), "low:", n0, "high:", n1)
