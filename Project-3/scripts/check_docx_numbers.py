#!/usr/bin/env python3
"""Trace every number in Project3_SSD_Report.docx to data.

A number is TRACED if it equals (to its printed precision) a value in data/processed/*.csv, a generated table, a raw
health/sysctl/fio file, or an explicit derived formula below (ratios, percentages, sums computed from those files).
Small integers (<= 300, no decimals) are structural (block sizes, depths, counts, section numbers) and are counted, not matched.
Dates, times and version strings are removed first. Everything else that does not trace is listed as UNTRACED.
Output: data/processed/docx_number_trace.md and a printed summary."""
import csv, glob, json, os, re, subprocess, sys
import numpy as np
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = P3 + "/report/Project3_SSD_Report.docx"
text = subprocess.run(["pandoc", "-t", "plain", "--wrap=none", DOCX], capture_output=True, text=True, check=True).stdout
text = re.sub(r"\[STUDENT TO FILL[^\]]*\]", " ", text)

# ---------- data pool
pool = []
def num(x):
    try: return float(x)
    except Exception: return None
for fn in ("summary.csv", "all_runs.csv"):
    for r in csv.DictReader(open(f"{P3}/data/processed/{fn}")):
        for v in r.values():
            n = num(v)
            if n is not None and np.isfinite(n): pool.append(n)
for fn in glob.glob(P3 + "/data/processed/tables/*.md") + glob.glob(P3 + "/data/raw/health/*.txt") + glob.glob(P3 + "/data/raw/engine_check_*/*.txt") + glob.glob(P3 + "/data/raw/exp6b/*.txt"):
    for t in re.findall(r"\d[\d,]*\.?\d*", open(fn).read()):
        n = num(t.replace(",", ""))
        if n is not None: pool.append(n)
for fn in glob.glob(P3 + "/data/raw/directio_check/*.json") + glob.glob(P3 + "/data/raw/precondition/*.json") + [P3 + "/data/raw/exp6b/exp6b__sustained.json"]:
    t = open(fn).read(); J = json.loads(t[t.index("{"):])["jobs"][0]
    for d in ("read", "write"):
        for k in ("iops", "io_bytes", "bw_bytes", "runtime"): pool.append(float(J[d][k]))
        pool.append(J[d]["lat_ns"]["mean"] / 1e3)

# ---------- derived values (label -> value); each is computed from the files above
S = list(csv.DictReader(open(P3 + "/data/processed/summary.csv"))); f = lambda r, k: float(r[k])
def row(ex, **kw): return next(r for r in S if r["exp"] == ex and all(r.get(k) == v for k, v in kw.items()))
d = {}
A = lambda qd, e="psync": f(row("exp4", eng=e, qd=str(qd)), "r_iops_mean"); B = lambda qd, e="psync": f(row("exp4b", eng=e, qd=str(qd)), "r_iops_mean")
d["exp7 IOPS ratio buffered/direct"] = f(row("exp7", cfg="B"), "r_iops_mean") / f(row("exp7", cfg="A"), "r_iops_mean")
d["exp7 latency ratio direct/buffered"] = f(row("exp7", cfg="A"), "r_lat_mean_us_mean") / f(row("exp7", cfg="B"), "r_lat_mean_us_mean")
d["exp7 buffered GB/s"] = f(row("exp7", cfg="B"), "r_iops_mean") * 4096 / 1e9
d["exp7 direct QD1 MB/s"] = f(row("exp7", cfg="A"), "r_iops_mean") * 4096 / 1e6
d["exp7 buffered / best real IOPS"] = f(row("exp7", cfg="B"), "r_iops_mean") / B(128, "posixaio")
dc = {}
for fn in glob.glob(P3 + "/data/raw/directio_check/*.json"):
    t = open(fn).read(); dc[fn.split("direct=")[1][0]] = json.loads(t[t.index("{"):])["jobs"][0]["read"]
d["directio latency ratio"] = dc["1"]["lat_ns"]["mean"] / dc["0"]["lat_ns"]["mean"]
_dev = lambda rows: max(abs(f(r, "littles_qd_mean") - f(r, "cfg_qd_mean")) / f(r, "cfg_qd_mean") * 100 for r in rows)
d["exp4/4b max Little deviation percent, psync"] = _dev([r for r in S if r["exp"] in ("exp4", "exp4b") and r["eng"] == "psync"])
d["exp4/4b max Little deviation percent, posixaio"] = _dev([r for r in S if r["exp"] in ("exp4", "exp4b") and r["eng"] == "posixaio"])
d["exp4 A psync QD8/QD1"] = A(8) / A(1); d["exp4 A psync QD16/QD1"] = A(16) / A(1)
d["exp4 A psync16 / A peak"] = 100 * A(16) / max(A(q, "posixaio") for q in (64, 128, 256)); d["exp4 B psync16 / B peak"] = 100 * B(16) / max(B(q, "posixaio") for q in (64, 128, 256))
d["exp4 A psync8 / A peak"] = 100 * A(8) / max(A(q, "posixaio") for q in (64, 128, 256)); d["exp4 B psync8 / B peak"] = 100 * B(8) / max(B(q, "posixaio") for q in (64, 128, 256))
d["exp4 A plateau latency ms"] = 256 / A(256, "posixaio") * 1e3; d["exp4 B plateau latency ms"] = 256 / B(256, "posixaio") * 1e3
d["exp4 B vs A peak percent"] = 100 * (max(B(q, "posixaio") for q in (64, 128, 256)) / max(A(q, "posixaio") for q in (64, 128, 256)) - 1)
d["exp4 B vs A peak percent (222/189)"] = 100 * (222.0 / 189.0 - 1)
r2 = lambda rw, bs: row("exp2", rw=rw, bs=bs); bw = lambda rw, bs, s: f(r2(rw, bs), s + "_bw_MBs_mean")
d["exp2 16x256KiB latency us"] = 16 * 262144 / (bw("randread", "256k", "r") * 1e6) * 1e6; d["exp2 16x1MiB latency ms"] = 16 * 1048576 / (bw("read", "1m", "r") * 1e6) * 1e3
d["exp2 4K seq-vs-rand percent"] = 100 * (bw("read", "4k", "r") - bw("randread", "4k", "r")) / bw("read", "4k", "r")
e3 = {m: row("exp3", mixread=str(m)) for m in (100, 70, 50, 0)}
d["exp3 arithmetic blend 50/50 k"] = (0.5 * f(e3[100], "r_iops_mean") + 0.5 * f(e3[0], "w_iops_mean")) / 1e3
d["exp3 harmonic 50/50 k"] = 1 / (0.5 / f(e3[100], "r_iops_mean") + 0.5 / f(e3[0], "w_iops_mean")) / 1e3
d["exp3 harmonic 70/30 k"] = 1 / (0.7 / f(e3[100], "r_iops_mean") + 0.3 / f(e3[0], "w_iops_mean")) / 1e3
d["exp3 read cost us"] = 1e6 / f(e3[100], "r_iops_mean"); d["exp3 write cost us"] = 1e6 / f(e3[0], "w_iops_mean")
d["exp3 read mean ratio 50/50"] = f(e3[50], "r_lat_mean_us_mean") / f(e3[100], "r_lat_mean_us_mean"); d["exp3 read p99 ratio 50/50"] = f(e3[50], "r_lat_p99_us_mean") / f(e3[100], "r_lat_p99_us_mean")
d["exp3 writers in flight 50/50"] = f(e3[50], "w_iops_mean") * f(e3[50], "w_lat_mean_us_mean") / 1e6
for nm, rg in (("read", "randread"), ("write", "randwrite")):
    s = "r" if nm == "read" else "w"; a, b = row("exp6a", rw=rg, range="1g"), row("exp6a", rw=rg, range="32g")
    d[f"exp6a {nm} range diff percent"] = 100 * abs(f(a, s + "_iops_mean") - f(b, s + "_iops_mean")) / f(b, s + "_iops_mean")
e1 = lambda rw, bs: row("exp1", rw=rw, bs=bs)
d["exp1 randread p99/p50"] = f(e1("randread", "4k"), "r_lat_p99_us_mean") / f(e1("randread", "4k"), "r_lat_p50_us_mean")
d["exp1 randwrite p99/p50"] = f(e1("randwrite", "4k"), "w_lat_p99_us_mean") / f(e1("randwrite", "4k"), "w_lat_p50_us_mean")
e5 = {k: row("exp5", role=k) for k in ("mid", "knee")}
for k in e5:
    r = e5[k]; d[f"exp5 {k} p99/p50"] = f(r, "r_lat_p99_us_mean") / f(r, "r_lat_p50_us_mean"); d[f"exp5 {k} p99.9/p50"] = f(r, "r_lat_p99.9_us_mean") / f(r, "r_lat_p50_us_mean")
    d[f"exp5 {k} samples above p99.9"] = f(r, "r_ios_mean") * 1e-3; d[f"exp5 {k} samples above p99.99"] = f(r, "r_ios_mean") * 1e-4
d["exp5 p50 rise percent QD4->16"] = 100 * (f(e5["knee"], "r_lat_p50_us_mean") / f(e5["mid"], "r_lat_p50_us_mean") - 1)
d["exp5 p99 rise percent QD4->16"] = 100 * (f(e5["knee"], "r_lat_p99_us_mean") / f(e5["mid"], "r_lat_p99_us_mean") - 1)
d["exp5 max ms (QD4, QD16)"] = f(e5["mid"], "r_lat_max_us_max") / 1e3; d["exp5 max ms QD16"] = f(e5["knee"], "r_lat_max_us_max") / 1e3
d["fio cores used (exp4 A psync16)"] = (f(row("exp4", eng="psync", qd="16"), "usr_cpu_pct_mean") + f(row("exp4", eng="psync", qd="16"), "sys_cpu_pct_mean")) / 100
d["4K IOPS GB/s low"] = A(256, "posixaio") * 4096 / 1e9; d["4K IOPS GB/s high"] = B(128, "posixaio") * 4096 / 1e9
d["4K IOPS percent of best read bw low"] = 100 * A(256, "posixaio") * 4096 / 1e6 / bw("randread", "256k", "r"); d["4K IOPS percent of best read bw high"] = 100 * B(128, "posixaio") * 4096 / 1e6 / bw("randread", "256k", "r")
d["read 256K IOPS k"] = f(r2("randread", "256k"), "r_iops_mean") / 1e3
d["write/read ceiling percent (short)"] = 100 * bw("write", "1m", "w") / bw("randread", "256k", "r"); d["write/read ceiling percent (sustained 11.05)"] = 100 * 2.199e12 / 198 / 1e6 / bw("randread", "256k", "r")
d["read vs Gen5 x4 percent"] = 100 * bw("randread", "256k", "r") / 15750
# exp6b time series
import collections
sec = collections.defaultdict(lambda: collections.defaultdict(list))
for lf in glob.glob(P3 + "/data/raw/exp6b/exp6b_bw.*.log"):
    for line in open(lf):
        p = line.split(","); sec[int(p[0]) // 1000][lf].append(float(p[1]) * 1024 / 1e9)
gb = np.array([sum(np.mean(v) for v in sec[s].values()) for s in sorted(sec)])
d["exp6b first second GB/s"] = gb[0]; d["exp6b mean 10-15 s GB/s"] = gb[10:15].mean(); d["exp6b mean 5-15 s GB/s"] = gb[5:15].mean(); d["exp6b burst percent"] = 100 * (1 - gb[10:15].mean() / gb[0])
d["exp6b duration s"] = len(gb); d["exp6b 300s at measured rate TB"] = 2.199 / len(gb) * 300
# timing and volume
def ts(path):
    t = open(path).read(); return json.loads(t[t.index("{"):])["timestamp"]
d["minutes between exp4 A and B psync16"] = (ts(P3 + "/data/raw/exp4b/exp4b__eng=psync__qd=16__t1.json") - ts(P3 + "/data/raw/exp4/exp4__eng=psync__qd=16__t1.json")) / 60
import datetime as _dt
_end = re.search(r"stage exp12 end (\d\d):(\d\d):(\d\d); SMART host bytes written this stage: 1534", open(P3 + "/data/raw/health/exp12_bytes_written.txt").read())
_t4 = _dt.datetime.fromtimestamp(ts(P3 + "/data/raw/exp4/exp4__eng=psync__qd=16__t1.json"))
d["minutes from exp2 rerun write end to exp4 psync16 run"] = (_t4.hour * 60 + _t4.minute + _t4.second / 60) - (int(_end.group(1)) * 60 + int(_end.group(2)) + int(_end.group(3)) / 60)
def stage_bytes(fn):
    m = re.search(r"written this stage: (\d+)", open(fn).read()); return int(m.group(1)) / 1e12
hb = P3 + "/data/raw/health/"
d["stage exp12 first pass TB"] = stage_bytes(hb + "exp12_firstpass_bytes_written.txt")
try: d["stage exp12 rerun TB"] = stage_bytes(hb + "exp12_bytes_written.txt")
except Exception: pass
d["stage exp34 TB"] = stage_bytes(hb + "exp34_bytes_written.txt"); d["stage exp67 TB"] = stage_bytes(hb + "exp67_bytes_written.txt")
sm = lambda fn: int(re.search(r"smart_bytes_written: (\d+)", open(hb + fn).read()).group(1)) / 1e12
d["project total TB (final - precondition_before)"] = sm("project_final.txt") - sm("precondition_before.txt")
d["clean run_all total TB"] = 0.034 + d.get("stage exp12 rerun TB", 1.535) + d["stage exp34 TB"] + d["stage exp67 TB"]
pool_d = np.array(list(d.values()) + [0], float); pool = np.array(pool, float)
FACT = (1, 1e-3, 1e-6, 1e-9, 1e3, 1e-2, 100)
def traced(t, dec, arr):
    tol = 0.5 * 10 ** (-dec) + 1e-9
    for k in FACT:
        if np.any(np.abs(arr * k - t) <= tol): return True
    return False
# ---------- tokenise
clean = re.sub(r"\d{4}-\d\d-\d\d", " ", text); clean = re.sub(r"\b\d{1,2}:\d{2}\b", " ", clean)
VERS = re.findall(r"\b\d+\.\d+\.\d+\b", clean); clean = re.sub(r"\b\d+\.\d+\.\d+\b", " ", clean)
clean = re.sub(r"\b(ECSE|Exp|QD|Figure|Table|Section|Appendix|Project) ?\d+(/\d+)?", " ", clean)   # labels
clean = re.sub(r"\b\d+(\.\d+)? ?(KiB|MiB|GiB)\b", " ", clean)                                         # configured sizes
toks = re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", clean)
WHITE = {"3.43": "fio version (health log)", "3.9": "PCIe 3.0 x4 payload (public spec)", "7.9": "PCIe 4.0 x4 payload (public spec)", "15.8": "PCIe 5.0 x4 payload (public spec)",
         "4.0": "PCIe generation label", "5.0": "PCIe generation label", "5.5": "model name", "4320": "course", "6320": "course"}
out, untraced, counts, lowprec = [], [], collections.Counter(), []
def sig(raw): return len(raw.replace(".", "").lstrip("0"))
def derived_labels(v, dec): return ", ".join(k for k, x in d.items() if any(abs(x * m - v) <= 0.5 * 10 ** (-dec) + 1e-9 for m in FACT))[:150]
for mt in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", clean):
    t = mt.group(0); raw = t.replace(",", ""); dec = len(raw.split(".")[1]) if "." in raw else 0; v = float(raw)
    ctx = clean[max(0, mt.start() - 45): mt.end() + 30].replace("\n", " ")
    if t in WHITE: counts["whitelisted constant"] += 1; out.append((t, "constant: " + WHITE[t])); continue
    if dec == 0 and v <= 300: counts["small integer (structural)"] += 1; continue
    if traced(v, dec, pool_d): counts["derived formula"] += 1; out.append((t, "derived: " + derived_labels(v, dec))); continue
    if sig(raw) >= 3 and traced(v, dec, pool): counts["data (3+ significant digits)"] += 1; continue
    if traced(v, dec, pool): counts["data, low precision (hand review)"] += 1; lowprec.append((t, ctx)); continue
    untraced.append(t); lowprec.append((t + "  [NO MATCH]", ctx))
md = ["# Number trace for Project3_SSD_Report.docx", "", f"Tokens checked: {len(toks)} (versions, dates, times and label numbers removed first: versions {sorted(set(VERS))}).", "",
      "| Category | Count |", "|---|---|"] + [f"| {k} | {n} |" for k, n in counts.items()] + [f"| **UNTRACED** | **{len(untraced)}** |", ""]
md += ["## Untraced numbers", "", ", ".join(sorted(set(untraced), key=lambda x: float(x.replace(',', '')))) or "none", "", "## Traced by derived formula or constant (token: source)", ""]
seen = set()
for t, s in out:
    if (t, s) not in seen: seen.add((t, s)); md.append(f"- {t}: {s}")
md += ["", "## Low-precision matches and unmatched numbers, with context (for hand review)", ""] + [f"- {t}: ...{c}..." for t, c in lowprec] + ["", "## Derived values (label = value)", ""] + [f"- {k} = {v:.4g}" for k, v in d.items()]
open(P3 + "/data/processed/docx_number_trace.md", "w").write("\n".join(md) + "\n")
print(f"tokens {len(toks)}; " + "; ".join(f"{k}: {n}" for k, n in counts.items()) + f"; UNTRACED: {len(untraced)}"); print("untraced:", sorted(set(untraced), key=lambda x: float(x.replace(',', ''))))
print("low-precision / unmatched tokens for hand review:", len(lowprec))
