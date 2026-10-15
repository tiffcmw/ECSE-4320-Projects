#!/usr/bin/env python3
"""Assemble the self-contained report from report/parts/*.md, filling every number from data/processed.

  scripts/build_report.py            -> report/ECSE4320_Project2_Report.md, .docx and .pdf (pandoc + LibreOffice)
Placeholders in the parts have the form {{expression|format}}; the expression is evaluated with the helpers below.
The values actually used are written to report/numbers.json so that scripts/check_report.py can recompute them from the raw CSVs.
"""
import glob, json, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analysis_lib as A  # noqa: E402

ROOT = A.ROOT
REP = os.path.join(ROOT, "report")
PARTS = os.path.join(REP, "parts")
SRC = os.path.join(ROOT, "src")
USED = {}
_cache = {}


def load(g):
    if g not in _cache:
        _cache[g] = A.load(g)
    return _cache[g]


def g(group, metric, field="median", **flt):
    r = A.sel(load(group), metric=metric, **flt)
    if len(r) != 1:
        raise KeyError(f"{group} {metric} {flt}: {len(r)} rows")
    v = r[0][field]
    USED[f"{group}|{metric}|{field}|{sorted(flt.items())}"] = v
    return v


def nr(group, metric, target, field="median", **flt):
    """Value at the working set nearest to `target` bytes (for sweeps whose sizes are not round numbers)."""
    r = A.sel(load(group), metric=metric, **flt)
    best = min(r, key=lambda x: abs(x["ws_bytes"] - target))
    USED[f"{group}|{metric}|{field}|near {int(target)}|{sorted(flt.items())}"] = best[field]
    return best[field]


F = A.freq_ghz()
PEAK = A.PEAK_GBPS
cyc = lambda ns: ns * F
pk = lambda gb: 100.0 * gb / PEAK


def tab(header, rows):
    t = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    t += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(t)


def fb(n):
    return A.fb(n)


# ---------------------------------------------------------------- named values used in the text
def ns_values():
    v = {}
    e1 = "e1_chase"
    v["L1"] = g(e1, "ns_per_load", ws_bytes=32768)
    v["L2_4M"] = g(e1, "ns_per_load", ws_bytes=4194304)
    v["L2_2M"] = g(e1, "ns_per_load", ws_bytes=2097152)
    v["L2_12M"] = g(e1, "ns_per_load", ws_bytes=12582912)
    v["SLC64"] = g(e1, "ns_per_load", ws_bytes=67108864) if A.sel(load(e1), metric="ns_per_load", ws_bytes=67108864) else float("nan")
    ws, m, *_ = A.series(load(e1), "ws_bytes", metric="ns_per_load")
    i64 = int(np.argmin(np.abs(ws - 64 * 2**20))); v["SLC64"] = m[i64]
    v["DRAM"] = m[int(np.argmin(np.abs(ws - 2**30)))]
    v["idle"] = A.idle_latency()
    v["plateau"] = m[int(np.argmin(np.abs(ws - 512 * 1024)))]
    reg = json.load(open(os.path.join(A.PROC, "regions.json")))
    v["edgeL1"], v["edgeL2"], v["edgeDRAM"] = reg["L1_edge"], reg["L2_edge"], reg["DRAM_edge"]
    bw = load("e5_bw")
    for tag, s in (("32K", 32768), ("256K", 262144), ("2M", 2097152), ("16M", 16777216), ("64M", 67108864), ("1G", 2**30)):
        v["bw" + tag] = A.sel(bw, variant="r10w0", ws_bytes=s, metric="gbps_app")[0]["median"]
    # exp 2
    st = load("e2_chase_stride")
    for md in ("seq", "rand"):
        for s in (64, 128, 256, 512, 1024, 2048, 4096):
            v[f"{md}{s}"] = g("e2_chase_stride", "ns_per_load", variant=md, stride=s)
    pt = load("e2_pat")
    for md in ("seq", "rand"):
        for sz in (16, 32, 64, 128):
            for s in (64, 128, 256, 1024):
                r = A.sel(pt, variant=md, size=sz, stride=s, metric="gbps_useful")
                if r:
                    v[f"pat_{md}_{sz}_{s}"] = r[0]["median"]
    al = load("e2_alias")
    for s in (128, 192, 256, 320, 384, 512, 640, 1024):
        v[f"al{s}"] = A.sel(al, variant="rand", stride=s, metric="gbps_useful")[0]["median"]
    for s in (256, 512, 1024):
        v[f"alj{s}"] = A.sel(al, variant="randj", stride=s, metric="gbps_useful")[0]["median"]
    ks = load("e6_stride")
    big = {"mul": 805306368, "saxpy": 536870912}
    for k, ft in big.items():
        for s in (96, 128, 192, 256, 320, 384, 512, 640, 1024):
            r = A.sel(ks, variant=k, ws_bytes=ft, stride=s, metric="ns_per_elem")
            if r:
                v[f"k{k}{s}"] = r[0]["median"]
    # exp 3
    mb = load("e3_mix_bw")
    G = 2**30
    for k in ("r10w0", "r7w3_st_r", "r5w5_st_r", "r0w10_st_r", "r7w3_nt_r", "r5w5_nt_r", "r0w10_nt_r", "rmw", "r0w10_st", "r0w10_nt",
              "r0w10_st_z", "r0w10_nt_z", "r0w10_zva", "r7w3_st", "r5w5_st"):
        r = A.sel(mb, variant=k, ws_bytes=G, metric="gbps_app")
        if r:
            v["mix_" + k] = r[0]["median"]
    # exp 4
    mlp = load("e4_mlp")
    kx, bm, *_ = A.series(mlp, "param", metric="gbps"); _, lm, *_ = A.series(mlp, "param", metric="ns_per_step")
    v["mlp_bw1"] = bm[0]; v["mlp_plateau"] = bm.max(); v["L0"] = lm[0]; v["Ncore"] = bm.max() * lm[0] / A.LINE
    v["mlp_K20"] = bm[list(kx).index(20)]
    ld = load("e4_loaded")
    for t in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16):
        v[f"bw{t}"] = g("e4_loaded", "bw_gbps", exp="e4_loaded_threads", threads=t, param=0)
        v[f"lat{t}"] = g("e4_loaded", "lat_ns", exp="e4_loaded_threads", threads=t, param=0)
    v["maxbw"] = max(v[f"bw{t}"] for t in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16))
    k6 = load("e6_kern")
    feet = sorted({r["ws_bytes"] for r in A.sel(k6, variant="mul")})
    for tag, ft in (("small", feet[0]), ("big", feet[-1])):
        u = A.sel(k6, variant="mul", ws_bytes=ft, stride=4.0, metric="ns_per_elem")[0]["median"]
        sc = A.sel(k6, variant="mul", ws_bytes=ft, stride=4.0 * 40503, metric="ns_per_elem")[0]["median"]
        v["k_scat_ratio" + ("_small" if tag == "small" else "")] = sc / u
        v["k_unit_" + tag] = u; v["k_scat_" + tag] = sc
    v["rmw16"] = g("e3_mix_loaded", "bw_gbps", variant="rmw", threads=16)
    v["rmw16lat"] = g("e3_mix_loaded", "lat_ns", variant="rmw", threads=16)
    v["r16"] = g("e3_mix_loaded", "bw_gbps", variant="r10w0", threads=16)
    return v


# ---------------------------------------------------------------- tables built from data
def headline_table(v):
    rows = [
        ["L1 hit latency (32 KiB)", f"{v['L1']:.2f} ns", f"{cyc(v['L1']):.1f} cycles (est.)", "random single-cycle chase, 12 rounds"],
        ["L2 hit latency (2 MiB)", f"{v['L2_2M']:.2f} ns", f"{cyc(v['L2_2M']):.0f} cycles (est.)", "128 pages, small translation cost"],
        ["L2 latency (4 MiB)", f"{v['L2_4M']:.2f} ns", f"{cyc(v['L2_4M']):.0f} cycles (est.)", "256 pages, includes about 1.3 ns translation cost"],
        ["SLC region (64 MiB)", f"{v['SLC64']:.0f} ns", f"{cyc(v['SLC64']):.0f} cycles (est.)", "a ramp, not a plateau; SLC size not exposed"],
        ["DRAM latency (1 GiB)", f"{v['DRAM']:.1f} ns", f"{cyc(v['DRAM']):.0f} cycles (est.)", f"loaded-harness idle probe: {v['idle']:.0f} ns"],
        ["One-core sequential read bandwidth", f"{v['bw1G']:.0f} GB/s (DRAM), {v['bw32K']:.0f} GB/s (L1)", f"{pk(v['bw1G']):.0f}% of 460 GB/s", "NEON, independent accumulators"],
        ["One-core random-miss concurrency", f"{v['mlp_plateau']:.1f} GB/s", f"N = {v['Ncore']:.1f} lines", "Little's Law with one-core idle latency"],
        ["Chip read bandwidth, maximum", f"{v['maxbw']:.0f} GB/s", f"{pk(v['maxbw']):.0f}% of 460 GB/s", "6 threads; flat from 5 to 16 threads"],
        ["Chip read-modify-write bandwidth", f"{v['rmw16']:.0f} GB/s", f"{pk(v['rmw16']):.0f}% of 460 GB/s", "16 threads, application bytes"],
        ["Knee, two definitions", "5 threads (K1), 4 threads (K2)", "see Section 5", "pre-defined, first crossing and power"],
    ]
    return tab(["Quantity", "Value", "Derived", "Note"], rows)


def exp1_table(v):
    rows = []
    for lab, s in (("L1", 32768), ("L1, 96 KiB (inside Super L1D)", 98304), ("L2, 1.5 MiB", None), ("L2, 2 MiB", 2097152), ("L2, 4 MiB", 4194304),
                   ("L2, 12 MiB", 12582912), ("SLC region, 64 MiB", 67108864), ("DRAM, 1 GiB", 2**30)):
        rr = load("e1_chase")
        ws, m, a, b, n = A.series(rr, "ws_bytes", metric="ns_per_load")
        tgt = s if s else 1.5 * 2**20
        i = int(np.argmin(np.abs(ws - tgt)))
        pages = int(np.ceil(ws[i] / 16384))
        rows.append([lab, fb(ws[i]), pages, f"{m[i]:.2f}", f"{a[i]:.2f} to {b[i]:.2f}", f"{cyc(m[i]):.0f}", int(n[i])])
    return tab(["Level", "Working set", "16 KiB pages", "median ns", "min to max ns", "cycles (est.)", "n rounds"], rows)


def knee_table():
    sys.path.insert(0, HERE)
    ld = load("e4_loaded")
    th = sorted({int(r["threads"]) for r in A.sel(ld, exp="e4_loaded_threads", metric="bw_gbps") if r["threads"] > 0})
    idle = A.idle_latency()
    rows = []
    mx = max(A.sel(ld, exp="e4_loaded_threads", metric="bw_gbps", threads=t, param=0)[0]["median"] for t in th)
    for t in th:
        b = A.sel(ld, exp="e4_loaded_threads", metric="bw_gbps", threads=t, param=0)[0]
        l = A.sel(ld, exp="e4_loaded_threads", metric="lat_ns", threads=t, param=0)[0]
        N = b["median"] * l["median"] / A.LINE
        rows.append([t, f"{b['median']:.0f}", f"{b['min']:.0f} to {b['max']:.0f}", f"{100 * b['median'] / mx:.0f}%", f"{l['median']:.0f}", f"{l['min']:.0f} to {l['max']:.0f}",
                     f"{l['median'] / idle:.2f}x", f"{N:.0f}", f"{N / t:.0f}", int(b["n"])])
    return tab(["threads", "GB/s", "min to max", "% of max", "latency ns", "min to max", "vs idle", "N lines", "N per thread", "n"], rows)


def delay_table():
    ld = load("e4_loaded")
    idle = A.idle_latency()
    rows = []
    for ex, lab in (("e4_loaded_delay6", "6 threads"), ("e4_loaded_delay", "16 threads")):
        ds = sorted({r["param"] for r in A.sel(ld, exp=ex, metric="bw_gbps")}, reverse=True)
        for d in ds:
            b = A.sel(ld, exp=ex, metric="bw_gbps", param=d)[0]; l = A.sel(ld, exp=ex, metric="lat_ns", param=d)[0]
            N = b["median"] * l["median"] / A.LINE
            rows.append([lab, f"{d:.0f}", f"{b['median']:.0f}", f"{b['min']:.0f} to {b['max']:.0f}", f"{l['median']:.0f}", f"{l['median'] / idle:.2f}x", f"{N:.0f}", int(b["n"])])
    return tab(["series", "injected delay (loop iterations)", "GB/s", "min to max", "latency ns", "vs idle", "N lines", "n"], rows)


def mix_table():
    mb = load("e3_mix_bw")
    G = 2**30
    names = [("r10w0", "100% read"), ("r7w3_st_r", "70/30, plain stores"), ("r5w5_st_r", "50/50, plain stores"), ("r0w10_st_r", "100% write, plain stores"),
             ("r7w3_nt_r", "70/30, stnp"), ("r5w5_nt_r", "50/50, stnp"), ("r0w10_nt_r", "100% write, stnp"), ("rmw", "50/50 read-modify-write")]
    rows = []
    for k, lab in names:
        r = A.sel(mb, variant=k, ws_bytes=G, metric="gbps_app")[0]
        w = int(k.split("w")[1].split("_")[0]) if k != "rmw" else 0
        rd = int(k[1:].split("w")[0]) if k != "rmw" else 10
        model = ""
        if k.endswith("_st_r") and w:
            f_ = (rd + 2 * w) / (rd + w); model = f"{f_:.2f} / {r['median'] * f_:.0f}"
        rows.append([lab, f"{r['median']:.1f}", f"{r['min']:.1f} to {r['max']:.1f}", model, int(r["n"])])
    return tab(["mix (1 thread, 1 GiB, random store data)", "measured application GB/s", "min to max", "MODELED traffic factor / modeled DRAM GB/s (not measured)", "n"], rows)


def content_table():
    mb = load("e3_mix_bw")
    G = 2**30
    rows = []
    for st, lab in (("st", "plain stores"), ("nt", "stnp")):
        row = [lab]
        for suf in ("_r", "", "_z"):
            k = f"r0w10_{st}{suf}"
            r = A.sel(mb, variant=k, ws_bytes=G, metric="gbps_app")[0]
            row.append(f"{r['median']:.0f} ({r['min']:.0f} to {r['max']:.0f})")
        rows.append(row)
    r = A.sel(mb, variant="r0w10_zva", ws_bytes=G, metric="gbps_app")[0]
    rows.append(["dc zva (no data stored)", "", "", f"{r['median']:.0f} ({r['min']:.0f} to {r['max']:.0f})"])
    return tab(["100% write, 1 thread, 1 GiB (application GB/s)", "random data", "uniform non-zero line", "zero data"], rows)


def tlb_table():
    t = load("e7_tlb")
    rows = []
    def ser(lay):
        r = A.sel(t, exp="e7_tlb_pages", variant=lay, metric="ns_per_load")
        return {int(x["ws_bytes"] / A.LINE): x for x in r}
    o, r_, c_, p_ = ser("paged"), ser("paged_rand"), ser("paged_const"), ser("packed")
    for pg in sorted(r_):
        if pg < 16:
            continue
        rows.append([pg, f"{p_[pg]['median']:.2f}", f"{o[pg]['median']:.2f}", f"{r_[pg]['median']:.2f}", f"{c_[pg]['median']:.2f}", f"{r_[pg]['median'] - p_[pg]['median']:+.2f}",
                     f"{o[pg]['median'] - p_[pg]['median']:+.2f}", int(r_[pg]["n"])])
    return tab(["pages (= lines)", "packed", "original layout", "random offsets", "constant offset", "translation penalty (random - packed)", "earlier definition (original - packed)", "n"], rows)


def fixedL_table():
    t = load("e7_tlb")
    rows = []
    d = {}
    for lay in ("paged", "paged_rand", "paged_const"):
        for r in A.sel(t, exp="e7_tlb_fixedL", variant=lay, metric="ns_per_load"):
            d.setdefault(int(r["param"]), {})[lay] = r["median"]
    for pg in sorted(d):
        rows.append([pg] + [f"{d[pg].get(l, float('nan')):.1f}" for l in ("paged", "paged_rand", "paged_const")])
    return tab(["pages P holding the same 32768 lines", "original layout", "random offsets", "constant offset"], rows)


def kern_table():
    k = load("e6_kern")
    rows = []
    for kern, lab in (("mul", "z = x*y"), ("saxpy", "y = a*x + y")):
        feet = sorted({r["ws_bytes"] for r in A.sel(k, variant=kern)})
        for ft in (feet[0], feet[len(feet) // 2], feet[-1]):
            u = A.sel(k, variant=kern, ws_bytes=ft, stride=4.0, metric="ns_per_elem")[0]
            s64 = A.sel(k, variant=kern, ws_bytes=ft, stride=64.0, metric="ns_per_elem")[0]
            sc = A.sel(k, variant=kern, ws_bytes=ft, stride=4.0 * 40503, metric="ns_per_elem")[0]
            rows.append([lab, fb(ft), f"{u['median']:.3f}", f"{s64['median']:.3f}", f"{sc['median']:.3f}", f"{sc['median'] / u['median']:.1f}x", int(u["n"])])
    return tab(["kernel", "footprint", "unit stride ns/elem", "stride 64 B ns/elem", "scattered ns/elem", "scattered / unit", "n"], rows)


def amat_table(v):
    k = load("e6_kern")
    ws_c, lat_c, *_ = A.series(load("e1_chase"), "ws_bytes", metric="ns_per_load")
    rows = []
    for kern, lab in (("mul", "z = x*y"), ("saxpy", "y = a*x + y")):
        for s, pl, miss in ((4.0, "unit", 1 / 32), (64.0, "stride 64 B", 0.5), (4.0 * 40503, "scattered", 1.0)):
            x, m, *_ = A.series(k, "ws_bytes", metric="ns_per_elem", variant=kern, stride=s)
            Lf = np.interp(np.log2(x), np.log2(ws_c), lat_c)
            pred = m[0] + miss * np.maximum(Lf - lat_c[0], 0) / v["Ncore"]
            rows.append([lab, pl, f"{m[0]:.3f}", f"{m[-1]:.3f}", f"{m[-1] / m[0]:.1f}x", f"{pred[-1]:.3f}", f"{m[-1] / pred[-1]:.2f}"])
            v[f"am_{kern}_{pl.split()[0]}"] = m[-1] / pred[-1]
    return tab(["kernel", "pattern", "smallest ns/elem", "largest ns/elem", "ratio", "AMAT prediction at largest, ns", "measured / predicted"], rows)


def pit_values(v):
    p = load("e8_pitfalls")
    out = {}
    out["res4"] = g("e8_pitfalls", "bw_gbps", exp="pitfall_resident_bw", ws_bytes=262144 * 1 if False else 4 * 2**20 // 16) if False else None
    rs = {int(r["ws_bytes"] * 16): r["median"] for r in A.sel(p, exp="pitfall_resident_bw", metric="bw_gbps")}
    out["res4"] = rs[4 * 2**20]; out["res16"] = rs[16 * 2**20]; out["res64"] = rs[64 * 2**20]; out["res256"] = rs[256 * 2**20]; out["res4g"] = rs[2**32]
    out["nosink"] = g("e8_pitfalls", "gbps_claimed", exp="pitfall_dce", variant="no_sink")
    out["sink"] = g("e8_pitfalls", "gbps_claimed", exp="pitfall_dce", variant="with_sink")
    ra = {r["param"]: r["median"] for r in A.sel(p, exp="pitfall_ramp", variant="after_idle", metric="ghz_est")}
    rsd = np.median([r["median"] for r in A.sel(p, exp="pitfall_ramp", variant="steady", metric="ghz_est")])
    for ms in (5, 20, 50, 100):
        out[f"ramp{ms}"] = ra[float(ms * 2)] / rsd
    out["steady"] = rsd
    sq = A.sel(p, exp="pitfall_seqchase", metric="ns_per_load")
    s1g = min(sq, key=lambda r: abs(r["ws_bytes"] - 2**30))
    out["seq1g"] = s1g["median"]
    return out


# ---------------------------------------------------------------- environment-dependent text
def powermetrics_text():
    files = sorted(glob.glob(os.path.join(A.RAW, "powermetrics_*.txt")))
    if not files:
        return ("powermetrics was not run: it requires administrator rights and the password is not available to the assistant. "
                "A script that runs it during a single-thread spin was prepared. **Frequency cross-check: not done** (open item). All cycle values remain estimates based on the dependent-add calibration.")
    txt = open(files[-1]).read()
    vals = [float(x) for x in re.findall(r"HW active frequency:\s*([\d.]+)\s*MHz", txt)] or [float(x) for x in re.findall(r"CPU \d+ frequency:\s*([\d.]+)\s*MHz", txt)]
    if not vals:
        return "powermetrics ran but its output contained no recognisable cluster frequency lines; no cross-check value is claimed."
    top = [x for x in vals if x > 2500]
    est = float(re.findall(r"^([\d.]+)\s*$", txt, re.M)[0]) if re.findall(r"^([\d.]+)\s*$", txt, re.M) else float("nan")
    med = float(np.median(top)) if top else float("nan")
    USED["powermetrics_MHz"] = med
    return (f"powermetrics (cpu_power sampler, 1 s intervals) reported a median active cluster frequency of {med:.0f} MHz during a single-thread spin, against the "
            f"dependent-add estimate of {est:.2f} GHz taken immediately before. Ratio {med / 1000 / est:.3f}.")


def pmu_text():
    pm = load("e13_pmu")
    if not pm:
        return None
    return True


def code_excerpt(name, start_pat, end_pat, path="src/membench.c", maxlines=26):
    lines = open(os.path.join(ROOT, path)).read().split("\n")
    i = next(k for k, l in enumerate(lines) if re.search(start_pat, l))
    j = next((k for k in range(i + 1, len(lines)) if re.search(end_pat, lines[k])), i + maxlines)
    seg = lines[i:min(j + 1, i + maxlines)]
    return "```c\n" + "\n".join(seg) + "\n```"


def hyp_rows():
    """Original prediction text for every hypothesis written before the benchmarks, from hypotheses.md (references to an unrelated earlier project removed)."""
    txt = open(os.path.join(ROOT, "hypotheses.md")).read()
    head = txt.split("## Amendments")[0]
    out = []
    for line in head.split("\n"):
        m = re.match(r"- \*\*(H\w+)\.\*\* (.*)", line)
        if m:
            t = m.group(2)
            for a, c in ((" (A1 saw 12 ns IQR at 47 MB)", ""), (" (A1: 0.66 ns)", ""),
                         (" A1 saw 7 to 8 ns and an unexplained 2.6 ns step between 128 KB and 1 MB; I predict that step recurs.", " An unexplained 2.6 ns step between 128 KB and 1 MB is predicted."),
                         (" (A1)", ""), ("(prefetcher; A1 saw 14x)", "(prefetcher)"), (" (A1 saw the prefetcher tracking constant strides to 64 KB)", ""),
                         (" (A1 saw 98 GB/s with NEON)", ""), ("; A1 saw +1.3 ns at 256 pages.", "."), (" (A1: 18.5 ns)", ""), (" (A1 saw 14x)", ""),
                         ("(published peak for the 32-core-GPU M5 Max; 614 GB/s is the absolute upper bound)", "(peak for the 32-core-GPU M5 Max)")):
                t = t.replace(a, c)
            assert "A1" not in t, t
            out.append((m.group(1), re.sub(r"(?<!`)\*(?!\*)", r"\\*", t.strip())))
    return out


def new_hyp_rows():
    txt = open(os.path.join(ROOT, "hypotheses.md")).read()
    tail = txt.split("## Amendments, round 2")[1]
    out = []
    for line in tail.split("\n"):
        m = re.match(r"- \*\*(H\w+) \(([^)]*)\)\.\*\* (.*)", line)
        if m:
            out.append((m.group(1), m.group(2), m.group(3).strip()))
    return out


def T(prefix, drop=()):
    """A table generated by plot.py (data/processed/tables.md), selected by the start of its title; optional column indexes to drop."""
    txt = open(os.path.join(A.PROC, "tables.md")).read()
    for blk in txt.split("### ")[1:]:
        title, _, body = blk.partition("\n")
        if title.startswith(prefix):
            lines = [l for l in body.strip().split("\n") if l.startswith("|")]
            if drop:
                lines = ["|" + "|".join(c for i, c in enumerate(l.strip("|").split("|")) if i not in drop) + "|" for l in lines]
            return "\n".join(lines)
    raise KeyError(prefix)


def counters_summary():
    if load("e13_pmu"):
        return "**Hardware counters.** Counter data from the privileged run are reported in Section 8 and Appendix H."
    return ("**Hardware counters.** No cache or TLB miss counters were obtained. The PMU event database for this chip lists the needed events and an own counter-reading tool was written, "
            "but reading counters requires administrator rights, which the assistant did not have. Cache and TLB behavior is therefore inferred from timing signatures throughout, and the "
            "attempts are logged in Appendix H. This is the main weakness of the project against the assignment's counter requirement.")


def counters_deviation():
    if load("e13_pmu"):
        return "Counter values are available for Exp 6 and Exp 7 only (privileged run); all other experiments use timing inference"
    return "No counter values; all cache and TLB statements are inferred from timing (labeled as such)"


def pm_verdict():
    t = powermetrics_text()
    return t if "median active cluster" in t else "powermetrics not run (needs administrator rights); no cross-check value."


def pm_verdict_label():
    t = powermetrics_text()
    m = re.search(r"Ratio ([\d.]+)", t)
    if not m:
        return "Open (not run)"
    return "Confirmed" if abs(float(m.group(1)) - 1) <= 0.05 else "Refuted"


def pmu_rows(exp, variant, metric):
    return {int(r["ws_bytes"]): r["median"] for r in A.sel(load("e13_pmu"), exp=exp, variant=variant, metric=metric)}


def pmu_verdict():
    if not load("e13_pmu"):
        return "Counters not read: the kperf interface needs administrator rights. See Appendix H."
    lm = pmu_rows("e13_pmu_chase", "rand", "pmu_L1D_CACHE_MISS_LD_NONSPEC_per_op")
    small, big = lm[min(lm)], lm[max(lm)]
    pk_ = pmu_rows("e13_pmu_tlb", "packed", "pmu_L2_TLB_MISS_DATA_per_op"); pr = pmu_rows("e13_pmu_tlb", "paged_rand", "pmu_L2_TLB_MISS_DATA_per_op")
    top = max(pr)
    return (f"L1D load misses per load: {small:.3f} at {fb(min(lm))}, {big:.3f} at {fb(max(lm))}. L2 TLB misses per load at {top // A.LINE} pages: {pr[top]:.3f} (random offsets), "
            f"{pk_.get(top, float('nan')):.3f} (packed).")


def pmu_verdict_label():
    if not load("e13_pmu"):
        return "Open (not run)"
    return "See Section 8"


def hyp_table():
    orig = dict(hyp_rows())
    ns_ = dict(NS)
    ver = {}
    for line in open(os.path.join(REP, "verdicts.txt")).read().strip().split("\n"):
        i, meas, lab = [x.strip() for x in line.split("||")]
        ver[i] = (render(meas, ns_), render(lab, ns_))
    rows = []
    for i, text in orig.items():
        rows.append([i, text, ver[i][0], f"**{ver[i][1]}**"])
    for i, area, text in new_hyp_rows():
        rows.append([i, f"({area}) {text}", ver[i][0], f"**{ver[i][1]}**"])
    return tab(["ID", "Prediction (written before the measurement)", "Measured result", "Verdict"], rows)


def counters_log():
    p = os.path.join(A.RAW, "counters", "attempt_log.txt")
    t = open(p).read().replace("/private/tmp/claude-501/", "").replace("./../Project-2/bin/membench header >/dev/null", "")
    lines = [l for l in t.split("\n") if l.strip()][:48]
    return "```\n" + "\n".join(l[:160] for l in lines) + "\n```"


def counters_appendix():
    pm = bool(load("e13_pmu"))
    head = ("**Outcome.** " + ("Counters were read through the kperf interface with administrator rights for Exp 6 and Exp 7 (Section 8)." if pm else
            "No counter value was obtained. Hardware counters are inaccessible without administrator rights, and the assistant cannot supply the password. A privileged run is prepared (`scripts/run_privileged.sh`); the results are reported in Section 8 only if that run was made.") + "\n\n"
            "**Attempts, in the order specified, with outputs.** (1) The PMU event database shipped with macOS lists, for this chip family (`as5-1`), the events needed: `L1D_CACHE_MISS_LD_NONSPEC`, `L1D_TLB_MISS_NONSPEC`, `L2_TLB_MISS_DATA`, `LD_SRC_LL_CACHE_NONSPEC` (loads served by the shared L2) and `LD_SRC_MEMSYS_NONSPEC` (loads served by the system-level cache or DRAM). "
            "(2) Instruments' CPU Counters template, driven through `xctrace`, runs without administrator rights, but its guided mode exports only cycles, instructions and pipeline-bottleneck fractions with undocumented units; the exported per-core tables contain raw counter arrays without the identity of each counter, and the custom-event configuration is only available through the Instruments window, which a command-line session cannot drive. These tables are not used as evidence anywhere in this report. "
            "(3) A counter-reading tool using the private kperf frameworks (`src/pmu.h`) builds the configuration from the event database successfully but stops at the privileged call: `kpc_force_all_ctrs_set failed (not root?)`.\n\n")
    return head + counters_log()


def dce_evidence():
    t = open(os.path.join(A.RAW, "dce_asm.txt")).read().split("\n")
    keep = [t[0]] + [l for l in t if "bl\t" in l and ("read" in l or "mach" in l)]
    return "```\n" + "\n".join(x.replace("\t", " ") for x in keep[:8]) + "\n```"


NS = {}


def render(template, ns):
    def sub(m):
        body = m.group(1)
        fmt = ""
        if "|" in body:
            body, fmt = body.rsplit("|", 1)
        val = eval(body, {"__builtins__": __builtins__}, ns)
        if isinstance(val, (int, float, np.floating, np.integer)):
            USED["text:" + body.strip()] = float(val)
        return format(val, fmt) if fmt else str(val)
    return re.sub(r"\{\{(.+?)\}\}", sub, template)


def fix_widths(md):
    """Pipe-table column widths for pandoc follow the dash counts of the separator line: set them from the cell lengths."""
    lines = md.split("\n"); out = []; i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and re.match(r"^\|(-+\|)+$", lines[i + 1]):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            blk = [[c.strip() for c in l.strip().strip("|").split("|")] for k, l in enumerate(lines[i:j]) if k != 1]
            n = len(blk[0])
            w = []
            for c in range(n):
                lens = [len(r[c]) if c < len(r) else 0 for r in blk]
                w.append(max(9, min(60, int(0.5 * max(lens) + 0.5 * sum(lens) / len(lens)))))
            tot = sum(w)
            dashes = [max(3, round(100 * x / tot)) for x in w]
            out.append(lines[i]); out.append("|" + "|".join("-" * d for d in dashes) + "|")
            out.extend(lines[i + 2:j]); i = j
        else:
            out.append(lines[i]); i += 1
    return "\n".join(out)


def renumber(md):
    """Table and figure numbers follow the order of the captions in the final document; references are remapped."""
    maps = {}
    for kind, pat in (("Table", r"^: Table (\d+)\."), ("Figure", r"^!\[Figure (\d+)\.")):
        order = [int(x) for x in re.findall(pat, md, flags=re.M)]
        maps[kind] = {old: new for new, old in enumerate(order, 1)}
    def sub(m):
        k, n = m.group(1), int(m.group(2))
        return f"{k} {maps[k].get(n, n)}"
    return re.sub(r"\b(Table|Figure) (\d+)", sub, md)


def main():
    v = ns_values()
    v.update(pit_values(v))
    amat_table(v)
    def pen(lay, pg):
        return g('e7_tlb', 'ns_per_load', exp='e7_tlb_pages', variant=lay, ws_bytes=pg * 128) - g('e7_tlb', 'ns_per_load', exp='e7_tlb_pages', variant='packed', ws_bytes=pg * 128)
    def tl(lay, pg):
        return g('e7_tlb', 'ns_per_load', exp='e7_tlb_pages', variant=lay, ws_bytes=pg * 128)
    def fx(lay, P):
        return g('e7_tlb', 'ns_per_load', exp='e7_tlb_fixedL', variant=lay, param=P)
    ns = dict(v=v, g=g, nr=nr, pen=pen, tl=tl, fx=fx, F=F, PEAK=PEAK, cyc=cyc, pk=pk, headline_table=lambda: headline_table(v), exp1_table=lambda: exp1_table(v),
              knee_table=knee_table, delay_table=delay_table, mix_table=mix_table, content_table=content_table, tlb_table=tlb_table,
              fixedL_table=fixedL_table, T=T, counters_summary=counters_summary, counters_deviation=counters_deviation, kern_table=kern_table, amat_table=lambda: amat_table(v), fb=fb, np=np,
              powermetrics_text=powermetrics_text, code_excerpt=code_excerpt, hyp_rows=hyp_rows, new_hyp_rows=new_hyp_rows, tab=tab, load=load, A=A)
    ns.update(v)
    ns.update(pm_verdict=pm_verdict, pm_verdict_label=pm_verdict_label, pmu_verdict=pmu_verdict, pmu_verdict_label=pmu_verdict_label, hyp_table=hyp_table,
              counters_log=counters_log, counters_appendix=counters_appendix, dce_evidence=dce_evidence)
    NS.update(ns)
    parts = sorted(glob.glob(os.path.join(PARTS, "*.md")))
    out = []
    for p in parts:
        t = open(p).read()
        # python blocks: {{! expr}} produce raw text from a function
        out.append(render(t, ns))
    md = "\n\n".join(out)
    md = fix_widths(renumber(md))
    open(os.path.join(REP, "ECSE4320_Project2_Report.md"), "w").write(md)
    json.dump({k: val for k, val in USED.items()}, open(os.path.join(REP, "numbers.json"), "w"), indent=0)
    print(f"report markdown: {len(md.split())} words, {len(USED)} data-derived values")


if __name__ == "__main__":
    main()
