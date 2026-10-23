#!/usr/bin/env python3
"""Write markdown tables (data/processed/tables/*.md) from summary.csv. REPORT.md pulls them in via build_report.py."""
import csv, os, glob, collections, json
import numpy as np
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUM = list(csv.DictReader(open(P3 + "/data/processed/summary.csv")))
OUT = P3 + "/data/processed/tables"; os.makedirs(OUT, exist_ok=True)
f = lambda r, k: float(r[k])
def ms(r, k, d=1): return f"{f(r,k+'_mean'):.{d}f} ({f(r,k+'_std'):.{d}f})"
def write(name, hdr, rows):
    with open(f"{OUT}/{name}.md", "w") as fh:
        fh.write("| " + " | ".join(hdr) + " |\n|" + "|".join("---" for _ in hdr) + "|\n")
        for r in rows: fh.write("| " + " | ".join(str(c) for c in r) + " |\n")
kib = lambda bs: int(bs[:-1]) * (1024 if bs.endswith("m") else 1)
# exp1
rows = []
for rw, bs, nm in (("randread", "4k", "4 KiB random read"), ("randwrite", "4k", "4 KiB random write"), ("read", "128k", "128 KiB sequential read"), ("write", "128k", "128 KiB sequential write")):
    r = next(x for x in SUM if x["exp"] == "exp1" and x["rw"] == rw and x["bs"] == bs); s = "r" if "read" in rw else "w"
    rows.append([nm, f"{f(r,s+'_iops_mean'):,.0f}", f"{f(r,s+'_bw_MBs_mean'):,.0f}"] + [ms(r, f"{s}_lat_{k}_us") for k in ("mean_us".replace("_us", ""), "p50", "p95", "p99")] if False else
                [nm, f"{f(r,s+'_iops_mean'):,.0f}", f"{f(r,s+'_bw_MBs_mean'):,.0f}", ms(r, s + "_lat_mean_us"), ms(r, s + "_lat_p50_us"), ms(r, s + "_lat_p95_us"), ms(r, s + "_lat_p99_us")])
write("exp1", ["workload (QD1, 1 job)", "IOPS", "MB/s", "mean µs", "p50 µs", "p95 µs", "p99 µs"], rows)
# exp2
rows = []
for rw in ("randread", "read", "randwrite", "write"):
    for r in sorted([x for x in SUM if x["exp"] == "exp2" and x["rw"] == rw], key=lambda x: kib(x["bs"])):
        s = "r" if "read" in rw else "w"
        rows.append([rw, f"{kib(r['bs'])} KiB", ms(r, s + "_bw_MBs", 0), f"{f(r,s+'_iops_mean'):,.0f}", ms(r, s + "_lat_mean_us", 0), ms(r, s + "_lat_p99_us", 0), f"{f(r,'littles_qd_mean'):.1f}"])
write("exp2", ["pattern", "block", "MB/s (sd)", "IOPS", "mean µs (sd)", "p99 µs (sd)", "Little's QD (cfg 16)"], rows)
# exp3
rows = []
for r in sorted([x for x in SUM if x["exp"] == "exp3"], key=lambda x: -int(x["mixread"])):
    m = int(r["mixread"]); rows.append([f"{m}/{100-m}", f"{f(r,'r_iops_mean'):,.0f}", f"{f(r,'w_iops_mean'):,.0f}", f"{f(r,'tot_iops_mean'):,.0f} ({f(r,'tot_iops_std'):,.0f})", f"{f(r,'tot_bw_MBs_mean'):,.0f}",
        "-" if m == 0 else f"{f(r,'r_lat_mean_us_mean'):.0f} / {f(r,'r_lat_p99_us_mean'):.0f}", "-" if m == 100 else f"{f(r,'w_lat_mean_us_mean'):.0f} / {f(r,'w_lat_p99_us_mean'):.0f}"])
write("exp3", ["read/write %", "read IOPS", "write IOPS", "total IOPS (sd)", "total MB/s", "read mean / p99 µs", "write mean / p99 µs"], rows)
# exp4 (A early, B replicate)
rows = []
for ex, tag in (("exp4", "A"), ("exp4b", "B")):
    for eng in ("psync", "posixaio"):
        for r in sorted([x for x in SUM if x["exp"] == ex and x["eng"] == eng], key=lambda x: int(x["qd"])):
            rows.append([tag, eng, r["qd"], f"{f(r,'r_iops_mean'):,.0f} ({f(r,'r_iops_std'):,.0f})", f"{f(r,'r_lat_mean_us_mean'):.1f}", f"{f(r,'r_lat_p99_us_mean'):.0f}", f"{f(r,'littles_qd_mean'):.1f}", r["qd_flag"] or "ok"])
write("exp4", ["run", "engine", "configured QD", "IOPS (sd)", "mean µs", "p99 µs", "Little's QD", "check"], rows)
# exp5
rows = []
for role in ("mid", "knee"):
    r = next(x for x in SUM if x["exp"] == "exp5" and x["role"] == role)
    rows.append([f"QD{r['qd']} ({role})", f"{f(r,'r_ios_mean')/1e6:.1f} M", f"{f(r,'r_ios_mean')*0.001:,.0f}"] + [ms(r, f"r_lat_{k}_us", 1) for k in ("p50", "p90", "p95", "p99", "p99.9", "p99.99")] + [f"{f(r,'r_lat_max_us_max'):,.0f}", f"{f(r,'r_lat_p99.9_us_mean')/f(r,'r_lat_p50_us_mean'):.2f}"])
write("exp5", ["QD", "IOs/run", "samples above p99.9", "p50 µs", "p90 µs", "p95 µs", "p99 µs", "p99.9 µs", "p99.99 µs", "max µs", "p99.9 / p50"], rows)
# exp6a
rows = []
for rw in ("randread", "randwrite"):
    for rg in ("1g", "32g"):
        r = next(x for x in SUM if x["exp"] == "exp6a" and x["rw"] == rw and x["range"] == rg); s = "r" if rw == "randread" else "w"
        rows.append([rw, rg.replace("g", " GiB"), f"{f(r,s+'_iops_mean'):,.0f} ({f(r,s+'_iops_std'):,.0f})", ms(r, s + "_lat_mean_us", 0), ms(r, s + "_lat_p99_us", 0)])
write("exp6a", ["pattern", "address range", "IOPS (sd)", "mean µs (sd)", "p99 µs (sd)"], rows)
# exp7
rows = []; nm = {"A": "A: direct=1, QD1 (correct)", "B": "B: direct=0 buffered, QD1 (flawed: page cache)", "C": "C: direct=1, QD16 (correct)", "D": "D: psync with iodepth=64 (flawed: depth ignored)"}
for r in sorted([x for x in SUM if x["exp"] == "exp7"], key=lambda x: x["cfg"]):
    rows.append([nm[r["cfg"]], f"{f(r,'r_iops_mean'):,.0f} ({f(r,'r_iops_std'):,.0f})", ms(r, "r_lat_mean_us", 2), ms(r, "r_lat_p99_us", 2), f"{f(r,'cfg_qd_mean'):.0f}", f"{f(r,'littles_qd_mean'):.2f}"])
write("exp7", ["setup", "IOPS (sd)", "mean µs (sd)", "p99 µs (sd)", "configured QD", "effective QD (Little)"], rows)
# 6b stats
sec = collections.defaultdict(lambda: collections.defaultdict(list))
for lf in glob.glob(P3 + "/data/raw/exp6b/exp6b_bw.*.log"):
    for line in open(lf):
        p = line.split(","); sec[int(p[0]) // 1000][lf].append(float(p[1]) * 1024 / 1e9)
xs = sorted(sec); gb = np.array([sum(np.mean(v) for v in sec[s].values()) for s in xs])
t = open(P3 + "/data/raw/exp6b/exp6b__sustained.json").read(); w = json.loads(t[t.index("{"):])["jobs"][0]["write"]
temps = [int(l.split()[1]) for l in open(P3 + "/data/raw/exp6b/temperature.log") if len(l.split()) == 2]
smart = open(P3 + "/data/raw/exp6b/bytes_written.txt").read().split(":")[-1].strip()
rows = [["fio bytes written (io_bytes)", f"{w['io_bytes']/1e12:.3f} TB"], ["SMART host bytes written delta", f"{int(smart)/1e12:.3f} TB"], ["duration (1 s log windows)", f"{len(xs)} s"],
        ["mean throughput, first 10 s", f"{gb[:10].mean():.2f} GB/s"], ["mean throughput, 10 to 60 s", f"{gb[10:60].mean():.2f} GB/s"], ["mean throughput, last 30 s", f"{gb[-30:].mean():.2f} GB/s"],
        ["slowest 1 s window", f"{gb.min():.2f} GB/s"], ["p99.9 / max single-write latency", f"{w['lat_ns']['percentile']['99.900000']/1e3:,.0f} µs / {w['lat_ns']['max']/1e6:.1f} ms"],
        ["SMART temperature start → end", f"{temps[0]} → {temps[-1]} °C (max {max(temps)})"]]
write("exp6b", ["metric", "value"], rows)
print("tables written:", sorted(os.listdir(OUT)))
