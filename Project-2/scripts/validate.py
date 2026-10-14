#!/usr/bin/env python3
"""Sanity checks against known expectations. Writes data/processed/validation.md. Flags are reported, never hidden."""
import glob, os, sys
import numpy as np
import analysis_lib as A
from analysis_lib import load, sel, series, fb

OUT = []
NFLAG = 0


def check(name, ok, detail, flag_if_fail=True):
    global NFLAG
    tag = "PASS" if ok else ("FLAG" if flag_if_fail else "NOTE")
    if not ok and flag_if_fail:
        NFLAG += 1
    OUT.append(f"| {tag} | {name} | {detail} |")


def main():
    f = A.freq_ghz()
    ch = load("e1_chase")
    if ch:
        ws, m, q1, q3, n = series(ch, "ws_bytes", metric="ns_per_load")
        runmax = np.maximum.accumulate(m)
        bad = [(fb(w), round(v, 2), round(r, 2)) for w, v, r in zip(ws, m, runmax) if v < 0.95 * r]
        check("latency non-decreasing with working set (5% tolerance)", not bad,
              "no violations" if not bad else f"{len(bad)} points below running max: {bad[:6]}")
        check("L1 latency not below 2.5 cycles", m.min() * f >= 2.5, f"min {m.min():.3f} ns = {m.min() * f:.1f} cycles at {f:.2f} GHz (estimate)")
        check("L1 latency within 2.5 to 6.5 cycles (typical 3 to 5)", 2.5 <= m[0] * f <= 6.5, f"{m[0]:.3f} ns = {m[0] * f:.1f} cycles")
        for name, size in (("L1 plateau 32 KiB", 32 * 1024), ("L2 plateau 4 MiB", 4 * 2**20), ("DRAM plateau 1 GiB", 2**30)):
            i = int(np.argmin(np.abs(ws - size)))
            rel = (q3[i] - q1[i]) / m[i]
            check(f"repeatability {name} (IQR/median <= 5%)", rel <= 0.05, f"IQR/median = {100 * rel:.1f}% over n = {int(n[i])}")
    # bandwidth ceiling
    over = []
    for g in ("e5_bw", "e3_mix_bw", "e3_mix_loaded", "e4_loaded", "e4_mlp", "e2_pat", "e6_kern", "pitfall"):
        pass
    for g, mets in (("e5_bw", ("gbps_app",)), ("e3_mix_bw", ("gbps_app",)), ("e3_mix_loaded", ("bw_gbps",)), ("e4_loaded", ("bw_gbps",)),
                    ("e4_mlp", ("gbps",)), ("e2_pat", ("gbps_useful",)), ("e6_kern", ("gbps_useful",)), ("e8_pitfalls", ("bw_gbps",))):
        for r in load(g):
            if r["metric"] in mets and r["median"] > A.PEAK_GBPS:
                foot = r["ws_bytes"] * (max(r["threads"], 1) if g in ("e3_mix_loaded", "e4_loaded", "e8_pitfalls") else 1)
                over.append((g, r["variant"], r["exp"], fb(foot), round(r["median"], 0), foot))
    hard = [o for o in over if o[5] >= 256 * 2**20]
    soft = [o for o in over if o[5] < 256 * 2**20]
    check("no DRAM-resident (>= 256 MiB total) bandwidth above 460 GB/s published peak", not hard,
          "none" if not hard else f"{len(hard)} rows: {hard[:5]}")
    OUT.append(f"| NOTE | cache-resident bandwidth above 460 GB/s (expected, not DRAM) | {len(soft)} rows, e.g. {soft[:3]} |")
    # placement
    p = load("e0_placement")
    if p:
        def v(q, s):
            r = sel(p, variant=q, ws_bytes=s, metric="ns_per_load"); return r[0]["median"] if r else float("nan")
        dram = float(m[int(np.argmin(np.abs(ws - 2**30)))]) if ch else 100.0
        super_ok = v("interactive", 96 * 1024) < 1.5 * v("interactive", 48 * 1024) and v("interactive", 12 * 2**20) < 0.4 * dram
        check("QoS interactive thread shows Super-core cache signature (96 KiB in L1, 12 MiB in L2)", super_ok,
              f"96 KiB {v('interactive', 96 * 1024):.2f} ns vs 48 KiB {v('interactive', 48 * 1024):.2f} ns; 12 MiB {v('interactive', 12 * 2**20):.1f} ns")
        check("background QoS shows a different (Performance) signature", v("background", 96 * 1024) > 3 * v("background", 48 * 1024),
              f"96 KiB {v('background', 96 * 1024):.1f} ns vs 48 KiB {v('background', 48 * 1024):.2f} ns", flag_if_fail=False)
    # Little's law on the single-core MLP sweep: N_eff cannot exceed K
    mlp = load("e4_mlp")
    if mlp:
        kx, bm, *_ = series(mlp, "param", metric="gbps"); _, lm, *_ = series(mlp, "param", metric="ns_per_step")
        neff = bm * lm[0] / A.LINE
        check("single-core N_eff = throughput x L0 / 128 B does not exceed K (+15%)", bool(np.all(neff <= 1.15 * kx)),
              "max N_eff/K = %.2f" % float(np.max(neff / kx)))
    # DRAM latency cross-check
    idle = A.idle_latency()
    if ch and idle == idle:
        ws, m, *_ = series(ch, "ws_bytes", metric="ns_per_load")
        d = m[int(np.argmin(np.abs(ws - 2**30)))]
        check("DRAM latency: chase sweep (1 GiB) vs loaded-harness idle probe within 15%", abs(idle - d) / d <= 0.15, f"{d:.1f} ns vs {idle:.1f} ns")
    # thermal
    mt = A.meta()
    if mt:
        bad = [(g["group"], t["round"]) for g in mt.get("groups_done", []) for t in g["thermal_by_round"] if not t["no_warning"]]
        check("no thermal or performance warning recorded at any round start", not bad, "none" if not bad else f"{bad[:5]}")
        check("thermal state clean at end", mt.get("thermal_end", {}).get("no_warning", False), mt.get("thermal_end", {}).get("text", "")[:80].replace("\n", " "))
        try:
            a, b = float(mt["effective_freq_ghz_estimate"]), float(mt["effective_freq_ghz_estimate_end"])
            check("frequency estimate stable start vs end (within 5%)", abs(a - b) / a <= 0.05, f"{a:.2f} vs {b:.2f} GHz")
        except Exception:
            pass
    # faults
    nf = 0
    for path in glob.glob(os.path.join(A.PROC, "*.csv")):
        for r in load(os.path.basename(path)[:-4]):
            nf += int(r["n_faulted"])
    OUT.append(f"| NOTE | rows excluded for page faults in the timed region | {nf} |")
    # selftest
    st = os.path.join(A.PROC, "selftest.log")
    if os.path.exists(st):
        t = open(st).read()
        check("correctness self-test (chase cycles, kernels vs scalar reference, store variants)", "SELFTEST PASSED" in t, t.strip().splitlines()[-1] if t.strip() else "")
    hdr = ["# Validation", "", f"Frequency used for cycle conversion: {f:.2f} GHz (estimate). Flags: {NFLAG}.", "",
           "| Result | Check | Detail |", "|---|---|---|"]
    open(os.path.join(A.PROC, "validation.md"), "w").write("\n".join(hdr + OUT) + "\n")
    print("\n".join(hdr + OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
