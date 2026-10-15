#!/usr/bin/env python3
"""Numeric consistency check (R17). Recomputes the report's derived numbers from the RAW per-round CSV files (not from the processed
tables used by build_report.py) and fails on mismatches. Also checks a list of numbers typed literally into the report text.

  scripts/check_report.py     exit code 0 = all pass
"""
import csv, glob, json, os, re, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
SID = json.load(open(os.path.join(PROC, "SESSION.json")))["sid"]
NUM = json.load(open(os.path.join(ROOT, "report", "numbers.json")))
MD = open(os.path.join(ROOT, "report", "ECSE4320_Project2_Report.md")).read()
NOFILTER = {"bw_gbps", "bw_thread_min", "bw_thread_max", "lat_ns", "bw_writer_gbps"}
_cache = {}
fails, passes = [], 0


def rows(group):
    if group not in _cache:
        out = []
        for sid in (SID, SID + "-pmu"):
            p = os.path.join(RAW, f"{group}_{sid}.csv")
            if os.path.exists(p):
                out += list(csv.DictReader(open(p)))
        _cache[group] = out
    return _cache[group]


def med(group, metric, **kw):
    """Median over all rounds of the raw rows matching kw (rows with page faults dropped unless the metric is process-wide)."""
    vals = []
    for r in rows(group):
        if r["metric"] != metric:
            continue
        ok = all((r[k] == v) if isinstance(v, str) else abs(float(r[k]) - float(v)) < 1e-6 for k, v in kw.items())
        if ok and (metric in NOFILTER or int(r["faults"]) == 0):
            vals.append(float(r["value"]))
    if not vals:
        raise KeyError(f"{group} {metric} {kw}")
    return float(np.median(vals))


def meta():
    m = json.load(open(glob.glob(os.path.join(RAW, f"meta_{SID}_full.json"))[0]))
    return (float(m["effective_freq_ghz_estimate"]) + float(m["effective_freq_ghz_estimate_end"])) / 2


F = meta()
PEAK = 460.0


def check(name, got, want, tol=0.005):
    global passes
    ok = abs(got - want) <= tol * max(abs(want), 1e-9) + 1e-9
    if ok:
        passes += 1
    else:
        fails.append(f"{name}: report {got:.6g} vs raw {want:.6g}")


def txt(expr):
    k = "text:" + expr
    if k not in NUM:
        raise KeyError("expression not in report: " + expr)
    return NUM[k]


def main():
    # ---- values recomputed from raw rows
    L1 = med("e1_chase", "ns_per_load", ws_bytes=32768)
    L2_4M = med("e1_chase", "ns_per_load", ws_bytes=4194304)
    L2_2M = med("e1_chase", "ns_per_load", ws_bytes=2097152)
    DRAM = med("e1_chase", "ns_per_load", ws_bytes=2**30)
    check("L1 ns", txt("v['L1']"), L1)
    check("L2 4 MiB ns", txt("v['L2_4M']"), L2_4M)
    check("L2 2 MiB ns", txt("v['L2_2M']"), L2_2M)
    check("DRAM ns", txt("v['DRAM']"), DRAM)
    check("L1 cycles", txt("cyc(v['L1'])"), L1 * F)
    check("L2 cycles", txt("cyc(v['L2_2M'])"), L2_2M * F)
    check("DRAM cycles", txt("cyc(v['DRAM'])"), DRAM * F)
    seq = med("e2_chase_stride", "ns_per_load", variant="seq", stride=128); rnd = med("e2_chase_stride", "ns_per_load", variant="rand", stride=128)
    check("seq/rand chase ratio", txt("v['rand128']/v['seq128']"), rnd / seq)
    # bandwidth and Little's Law
    bw = {t: med("e4_loaded", "bw_gbps", exp="e4_loaded_threads", threads=t, param=0) for t in (1, 4, 5, 6, 16)}
    lat = {t: med("e4_loaded", "lat_ns", exp="e4_loaded_threads", threads=t, param=0) for t in (1, 4, 5, 6, 16)}
    check("max bw", txt("v['maxbw']"), max(med("e4_loaded", "bw_gbps", exp="e4_loaded_threads", threads=t, param=0) for t in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16)))
    check("max bw percent of 460", txt("pk(v['maxbw'])"), 100 * max(bw.values()) / PEAK)
    check("N lines at 5 threads (Little)", txt("v['bw5']*v['lat5']/128"), bw[5] * lat[5] / 128)
    check("N lines at 16 threads", txt("v['bw16']*v['lat16']/128"), bw[16] * lat[16] / 128)
    check("N per thread at 16", txt("v['bw16']*v['lat16']/128/16"), bw[16] * lat[16] / 128 / 16)
    idle = med("e4_loaded", "lat_ns", exp="e4_loaded_threads", threads=0, param=0)
    check("idle latency", txt("v['idle']"), idle)
    check("latency at 4 threads vs idle", txt("v['lat4']/v['idle']"), lat[4] / idle)
    # single-core MLP
    ks = [1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64]
    gb = [med("e4_mlp", "gbps", param=k) for k in ks]; ns = [med("e4_mlp", "ns_per_step", param=k) for k in ks]
    check("one-core plateau GB/s", txt("v['mlp_plateau']"), max(gb))
    check("one-core N_eff", txt("v['Ncore']"), max(gb) * ns[0] / 128)
    check("N_eff <= K (K=20)", min(1.0, 1.0), 1.0) if max(g_ * ns[0] / 128 / k for g_, k in zip(gb, ks)) <= 1.15 else fails.append("N_eff exceeds K by more than 15%")
    # Exp 3
    G = 2**30
    st_r = med("e3_mix_bw", "gbps_app", variant="r0w10_st_r", ws_bytes=G); st_z = med("e3_mix_bw", "gbps_app", variant="r0w10_st_z", ws_bytes=G)
    nt_r = med("e3_mix_bw", "gbps_app", variant="r0w10_nt_r", ws_bytes=G); nt_u = med("e3_mix_bw", "gbps_app", variant="r0w10_nt", ws_bytes=G)
    rd = med("e3_mix_bw", "gbps_app", variant="r10w0", ws_bytes=G)
    check("zero/random plain stores", txt("v['mix_r0w10_st_z']/v['mix_r0w10_st_r']"), st_z / st_r)
    check("stnp uniform/random", txt("v['mix_r0w10_nt']/v['mix_r0w10_nt_r']"), nt_u / nt_r)
    check("write/read ratio", txt("v['mix_r0w10_st_r']/v['mix_r10w0']"), st_r / rd)
    check("stnp vs st (random)", txt("v['mix_r0w10_nt_r']/v['mix_r0w10_st_r']"), nt_r / st_r)
    # Exp 6 ratios
    u = med("e6_kern", "ns_per_elem", variant="mul", ws_bytes=1610612736, stride=4)
    sc = med("e6_kern", "ns_per_elem", variant="mul", ws_bytes=1610612736, stride=4 * 40503)
    check("scattered/unit at 1.5 GiB", txt("v['k_scat_ratio']"), sc / u)
    # Exp 7 penalties (translation penalty = random offsets minus packed)
    for pg in (256, 4096, 65536):
        a = med("e7_tlb", "ns_per_load", exp="e7_tlb_pages", variant="paged_rand", ws_bytes=pg * 128)
        b = med("e7_tlb", "ns_per_load", exp="e7_tlb_pages", variant="packed", ws_bytes=pg * 128)
        o = med("e7_tlb", "ns_per_load", exp="e7_tlb_pages", variant="paged", ws_bytes=pg * 128)
        check(f"TLB penalty random-packed at {pg}", txt(f"pen('paged_rand',{pg})"), a - b)
        check(f"TLB penalty original-packed at {pg}", txt(f"pen('paged',{pg})"), o - b)
    # Exp 8 ratios
    r4 = med("e8_pitfalls", "bw_gbps", exp="pitfall_resident_bw", ws_bytes=4 * 2**20 // 16)
    r256 = med("e8_pitfalls", "bw_gbps", exp="pitfall_resident_bw", ws_bytes=256 * 2**20 // 16)
    check("resident/DRAM bandwidth ratio", txt("v['res4']/v['res256']"), r4 / r256)
    # ---- numbers typed literally into the text (checked against the raw data)
    k1 = med("e4_loaded", "bw_gbps", exp="e4_loaded_threads", threads=5, param=0); k2 = med("e4_loaded", "bw_gbps", exp="e4_loaded_threads", threads=4, param=0)
    check("literal: K1 - K2 bandwidth difference of 13 GB/s", 13.0, k1 - k2, tol=0.1)
    nt_w4 = med("e11_ceiling", "bw_gbps", exp="e11_writer_nt", threads=4) + med("e11_ceiling", "bw_writer_gbps", exp="e11_writer_nt", threads=4)
    nt_w6 = med("e11_ceiling", "bw_gbps", exp="e11_writer_nt", threads=6) + med("e11_ceiling", "bw_writer_gbps", exp="e11_writer_nt", threads=6)
    st_w4 = med("e11_ceiling", "bw_gbps", exp="e11_writer_st", threads=4) + med("e11_ceiling", "bw_writer_gbps", exp="e11_writer_st", threads=4)
    st_w6 = med("e11_ceiling", "bw_gbps", exp="e11_writer_st", threads=6) + med("e11_ceiling", "bw_writer_gbps", exp="e11_writer_st", threads=6)
    for lab, lit, val in (("336", 336, nt_w4), ("355", 355, nt_w6), ("261", 261, st_w4), ("282", 282, st_w6)):
        check(f"literal: writer total {lab} GB/s", lit, val, tol=0.01)
    check("literal: background-QoS 1 thread 33 GB/s", 33, med("e11_ceiling", "bw_gbps", exp="e11_bgqos", threads=1), tol=0.02)
    check("literal: background-QoS 16 threads 46 GB/s", 46, med("e11_ceiling", "bw_gbps", exp="e11_bgqos", threads=16), tol=0.02)
    for lab, e, t in (("292", "e11_r10w0_ldp", 16), ("301", "e11_r10w0_ld4", 8)):
        mix = "r10w0_ldp" if "ldp" in e else "r10w0_ld4"
        got = med("e11_ceiling", "bw_gbps", exp=e, variant=mix, threads=t)
        check(f"literal: {e} at {t} threads {lab} GB/s", float(lab), got, tol=0.01)
    # literal numbers in Sections 1.2 and 1.5: repeatability, clock endpoints, cross-check with the earlier AC collection
    def iqr_rel(ws):
        v = [float(r["value"]) for r in rows("e1_chase") if r["metric"] == "ns_per_load" and abs(float(r["ws_bytes"]) - ws) < 1e-6 and int(r["faults"]) == 0]
        q1, q3 = np.percentile(v, [25, 75]); return 100 * (q3 - q1) / np.median(v)
    check("literal: IQR/median 32 KiB 0.4%", 0.4, iqr_rel(32768), tol=0.15)
    check("literal: IQR/median 4 MiB 0.4%", 0.4, iqr_rel(4194304), tol=0.15)
    check("literal: IQR/median 1 GiB 1.6%", 1.6, iqr_rel(2**30), tol=0.05)
    check("literal: chase sweep DRAM 108.7 ns", 108.7, DRAM, tol=0.002)
    m = json.load(open(glob.glob(os.path.join(RAW, f"meta_{SID}_full.json"))[0]))
    check("literal: clock at start 4.575 GHz", 4.575, float(m["effective_freq_ghz_estimate"]), tol=0.001)
    check("literal: clock at end 4.578 GHz", 4.578, float(m["effective_freq_ghz_estimate_end"]), tol=0.001)
    old = "20261014-0029"
    def old_med(ws):
        v = [float(r["value"]) for r in csv.DictReader(open(os.path.join(RAW, f"e1_chase_{old}.csv"))) if r["metric"] == "ns_per_load" and abs(float(r["ws_bytes"]) - ws) < 1e-6 and int(r["faults"]) == 0]
        return float(np.median(v))
    check("literal: earlier AC collection L1 0.66 ns", 0.66, old_med(32768), tol=0.01)
    check("literal: earlier AC collection DRAM 109.0 ns", 109.0, old_med(2**30), tol=0.003)
    check("literal: battery vs AC DRAM within 1%", 1.0, 1.0 if abs(DRAM / old_med(2**30) - 1) < 0.01 else 0.0)
    # the hard-coded sentence about every self-test check
    st = open(os.path.join(PROC, "selftest.log")).read()
    check("literal: self-test has 32 passed checks", 32, len(re.findall(r"^ok:", st, flags=re.M)))
    check("literal: self-test passed", 1, 1 if "SELFTEST PASSED" in st else 0)
    # percent, ratio, cycle recomputation inside the text is by construction: every derived number is a placeholder (count them)
    n_text = sum(1 for k in NUM if k.startswith("text:"))
    print(f"checked {passes + len(fails)} values; report contains {n_text} data-derived placeholders")
    if "{{" in MD or "nan" in re.findall(r"\bnan\b", MD):
        fails.append("unresolved placeholder or nan in report text")
    for f in fails:
        print("FAIL", f)
    print("PASS" if not fails else f"{len(fails)} FAILURES", f"({passes} checks passed)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
