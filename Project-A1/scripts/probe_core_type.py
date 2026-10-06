"""Placement evidence: record qos_loop under Instruments (CPU Counters template)
and report the share of on-core time spent on Super vs Performance cores, per
QoS class. Needs no sudo; uses Xcode's xctrace via DEVELOPER_DIR (no system change).

Usage: probe_core_type.py [--bg N --bg-qos NAME] [--threads N] [--kind compute|mem] qos [qos ...]
Placement is OBSERVED for these sampled runs (10 ms granularity), not guaranteed.
"""
import argparse
import csv
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer")


def record(args_list, out, wrap=()):
    subprocess.run(["xctrace", "record", "--template", "CPU Counters", "--time-limit", "30s", "--output", out,
                    "--launch", "--"] + list(wrap) + [os.path.join(ROOT, "build", "qos_loop")] + args_list,
                   env=ENV, capture_output=True, text=True, check=True)


def core_share(trace):
    xml = subprocess.run(["xctrace", "export", "--input", trace, "--xpath",
                          '/trace-toc/run[@number="1"]/data/table[@schema="CoreTypeByThread"]'],
                         env=ENV, capture_output=True, text=True, check=True).stdout
    root = ET.fromstring(xml)
    ids = {}
    for el in root.iter():
        if "id" in el.attrib:
            ids[el.attrib["id"]] = el
    def val(el):
        return ids[el.attrib["ref"]] if "ref" in el.attrib else el
    share = defaultdict(float)
    for row in root.iter("row"):
        ct = row.find("core-type")
        du = row.find("duration")
        if ct is None or du is None:
            continue
        share[val(ct).attrib.get("fmt", "?")] += float(val(du).text)
    return share


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--kind", default="compute")
    ap.add_argument("--bg", type=int, default=0)
    ap.add_argument("--bg-qos", default="background")
    ap.add_argument("--reps", type=int, default=15)
    ap.add_argument("--wrap", default="", help="command prefix, e.g. '/usr/sbin/taskpolicy -b'")
    ap.add_argument("qos", nargs="+")
    a = ap.parse_args()
    out_csv = os.path.join(ROOT, "data", "raw", f"coretype_{datetime.now():%Y%m%d_%H%M%S}.csv")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="") as f, tempfile.TemporaryDirectory() as td:
        w = csv.writer(f)
        w.writerow(["wrap", "qos", "kind", "threads", "bg_threads", "bg_qos", "super_ms", "performance_ms", "super_share"])
        for q in a.qos:
            tr = os.path.join(td, f"{q}.trace")
            args = ["--kind", a.kind, "--threads", str(a.threads), "--qos", q, "--reps", str(a.reps)]
            if a.bg:
                args += ["--bg_threads", str(a.bg), "--bg_qos", a.bg_qos]
            record(args, tr, a.wrap.split())
            s = core_share(tr)
            sup, per = s.get("Super", 0) / 1e6, s.get("Performance", 0) / 1e6
            tot = sup + per
            w.writerow([a.wrap or "none", q, a.kind, a.threads, a.bg, a.bg_qos if a.bg else "none", f"{sup:.1f}", f"{per:.1f}",
                        f"{sup / tot:.3f}" if tot else ""])
            print(f"{(a.wrap or "plain"):28s} {q:12s} threads={a.threads} bg={a.bg}: Super {sup:8.1f} ms, Performance {per:8.1f} ms, "
                  f"Super share {sup / tot if tot else float('nan'):.3f}", flush=True)
    print("wrote", out_csv)


if __name__ == "__main__":
    main()
