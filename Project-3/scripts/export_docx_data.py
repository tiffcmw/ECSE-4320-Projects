#!/usr/bin/env python3
"""Export every table of the Word report from data/processed (summary.csv and generated markdown tables) to
report/docx_data.json, plus figure pixel sizes. scripts/docx/make_docx.js reads this file, so no table number is typed by hand."""
import csv, json, os, struct, glob
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUM = list(csv.DictReader(open(P3 + "/data/processed/summary.csv")))
f = lambda r, k: float(r[k]); kib = lambda b: int(b[:-1]) * (1024 if b.endswith("m") else 1)
def md(name):
    rows = [l.strip().strip("|").split("|") for l in open(f"{P3}/data/processed/tables/{name}.md") if l.strip()]
    return [[c.strip() for c in r] for i, r in enumerate(rows) if i != 1]
D = {n: md(n) for n in ("exp1", "exp3", "exp5", "exp6b", "exp7", "state_split", "smart_read_check", "exp6a")}
# compact block-size table: MB/s and mean latency per pattern
pats = ("randread", "read", "randwrite", "write"); sizes = ["4k", "16k", "32k", "64k", "128k", "256k", "512k", "1m"]
def cell(rw, bs, k, fmt):
    r = next((x for x in SUM if x["exp"] == "exp2" and x["rw"] == rw and x["bs"] == bs), None)
    if r is None: return "-"
    s = "r" if "read" in rw else "w"; return fmt(f(r, f"{s}_{k}_mean"))
rows = [["Block", "MB/s: rand read", "seq read", "rand write", "seq write", "mean µs: rand read", "seq read", "rand write", "seq write"]]
for bs in sizes:
    rows.append([f"{kib(bs)} KiB"] + [cell(rw, bs, "bw_MBs", lambda v: f"{v:,.0f}") for rw in pats] + [cell(rw, bs, "lat_mean_us", lambda v: f"{v:,.0f}") for rw in pats])
D["exp2c"] = rows
# compact QD table
def q(ex, eng, qd, key, fmt):
    r = next((x for x in SUM if x["exp"] == ex and x["eng"] == eng and x["qd"] == str(qd)), None)
    return "-" if r is None else fmt(f(r, key))
rows = [["QD", "A psync IOPS (k)", "A posixaio IOPS (k)", "A posixaio mean µs", "B psync IOPS (k)", "B posixaio IOPS (k)", "B posixaio mean µs", "Little's QD (A posixaio)"]]
for qd in (1, 2, 4, 8, 16, 32, 64, 128, 256):
    k = lambda v: f"{v/1e3:.1f}"; m = lambda v: f"{v:,.0f}"; l = lambda v: f"{v:.1f}"
    rows.append([str(qd), q("exp4", "psync", qd, "r_iops_mean", k), q("exp4", "posixaio", qd, "r_iops_mean", k), q("exp4", "posixaio", qd, "r_lat_mean_us_mean", m),
                 q("exp4b", "psync", qd, "r_iops_mean", k), q("exp4b", "posixaio", qd, "r_iops_mean", k), q("exp4b", "posixaio", qd, "r_lat_mean_us_mean", m), q("exp4", "posixaio", qd, "littles_qd_mean", l)])
D["exp4c"] = rows
# ceilings table (all from summary.csv)
g = lambda ex, **kw: next(r for r in SUM if r["exp"] == ex and all(r.get(k) == v for k, v in kw.items()))
D["ceilings"] = [["Quantity", "Measured", "Reference"],
    ["4 KiB random read IOPS, QD16 to QD256", f"{f(g('exp4',eng='posixaio',qd='256'),'r_iops_mean')/1e3:.0f} k (A) to {f(g('exp4b',eng='posixaio',qd='128'),'r_iops_mean')/1e3:.0f} k (B)", "0.8 to 0.9 GB/s, 6 to 7% of best read bandwidth"],
    ["Best read bandwidth (256 KiB random)", f"{f(g('exp2',rw='randread',bs='256k'),'r_bw_MBs_mean')/1e3:.1f} GB/s", "PCIe 4.0 x4 payload 7.9 GB/s; 5.0 x4 15.8 GB/s (link not readable on macOS)"],
    ["Best write bandwidth (1 MiB sequential)", f"{f(g('exp2',rw='write',bs='1m'),'w_bw_MBs_mean')/1e3:.1f} GB/s short runs; 11.0 GB/s sustained over 2.2 TB", "about 82 to 86% of the read ceiling"],
    ["QD1 4 KiB random read latency", f"{f(g('exp1',rw='randread',bs='4k'),'r_lat_mean_us_mean'):.1f} µs (Exp 1) to {f(g('exp4',eng='psync',qd='1'),'r_lat_mean_us_mean'):.1f} µs (Exp 4)", "flash page read is tens of µs; the rest is controller, encryption, protocol and file system"]]
# figure sizes
D["fig"] = {}
for p in glob.glob(P3 + "/plots/docx/*.png"):
    d = open(p, "rb").read(24); w, h = struct.unpack(">II", d[16:24]); D["fig"][os.path.basename(p)] = [w, h]
json.dump(D, open(P3 + "/report/docx_data.json", "w"), indent=1); print("report/docx_data.json written;", len(D), "entries")
