"""Shared loading and helpers for plot.py and validate.py."""
import csv, json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.environ.get("P2_PROC", os.path.join(ROOT, "data", "processed"))
RAW = os.environ.get("P2_RAW", os.path.join(ROOT, "data", "raw"))
PLOTS = os.environ.get("P2_PLOTS", os.path.join(ROOT, "plots"))
LINE = 128
PEAK_GBPS = 460.0       # published, 32-core-GPU M5 Max (secondary sources)
PEAK_UPPER = 614.0      # 40-core-GPU M5 Max
L1D = {"Super": 128 * 1024, "Performance": 64 * 1024}
L2 = {"Super": 16 * 2**20, "Performance": 8 * 2**20}


def load(name):
    p = os.path.join(PROC, name + ".csv")
    if not os.path.exists(p):
        return []
    rows = []
    for r in csv.DictReader(open(p)):
        for k in ("ws_bytes", "stride", "size", "threads", "param", "median", "q1", "q3", "min", "max", "n", "n_faulted"):
            r[k] = float(r[k])
        rows.append(r)
    return rows


def sel(rows, **kw):
    out = []
    for r in rows:
        ok = True
        for k, v in kw.items():
            if callable(v):
                ok = ok and v(r[k])
            else:
                ok = ok and (r[k] == v if isinstance(v, str) else float(r[k]) == float(v))
        if ok:
            out.append(r)
    return out


def series(rows, xkey, **kw):
    s = sorted(sel(rows, **kw), key=lambda r: r[xkey])
    x = np.array([r[xkey] for r in s]); m = np.array([r["median"] for r in s])
    q1 = np.array([r["q1"] for r in s]); q3 = np.array([r["q3"] for r in s]); n = np.array([r["n"] for r in s])
    return x, m, q1, q3, n


def session():
    p = os.path.join(PROC, "SESSION.json")
    return json.load(open(p))["sid"] if os.path.exists(p) else ""


def meta():
    sid = session()
    for prof in ("full", "quick"):
        p = os.path.join(RAW, f"meta_{sid}_{prof}.json")
        if os.path.exists(p):
            return json.load(open(p))
    return {}


def freq_ghz():
    m = meta()
    vals = []
    for k in ("effective_freq_ghz_estimate", "effective_freq_ghz_estimate_end"):
        try:
            vals.append(float(m[k]))
        except Exception:
            pass
    return float(np.mean(vals)) if vals else 4.4


def fb(n):
    n = float(n)
    for u, s in ((2**30, "GiB"), (2**20, "MiB"), (2**10, "KiB")):
        if n >= u:
            v = n / u
            return f"{v:g} {s}"
    return f"{n:g} B"


def idle_latency():
    """Zero-queue DRAM latency from the loaded harness (0 BW threads), median of rounds."""
    rows = sel(load("e4_loaded"), exp="e4_loaded_threads", metric="lat_ns", threads=0)
    return float(np.median([r["median"] for r in rows])) if rows else float("nan")
