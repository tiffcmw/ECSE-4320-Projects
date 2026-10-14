#!/usr/bin/env python3
"""Supplementary evidence: Instruments CPU Counters (guided 'bottleneck' mode) via xctrace, no sudo.
Exports pipeline-slot fractions (useful, delivery, processing, discarded), NOT cache or TLB miss counts.
Usage: scripts/xctrace_bottleneck.py <session-id>   (needs Xcode.app; sets DEVELOPER_DIR for this process only)"""
import csv, os, subprocess, sys, tempfile, shutil
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "bin", "membench")
ENV = dict(os.environ, DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer")
CONFIGS = [
    ("mul unit stride, 48 KiB (L1)", ["kern", "--elems", "4096", "--mults", "1"]),
    ("mul unit stride, 192 MiB (DRAM)", ["kern", "--elems", "16777216", "--mults", "1"]),
    ("mul scattered, 48 KiB (L1)", ["kern", "--elems", "4096", "--mults", "40503"]),
    ("mul scattered, 192 MiB (DRAM)", ["kern", "--elems", "16777216", "--mults", "40503"]),
    ("random chase, 32 KiB (L1)", ["chase", "--sizes", "32K"]),
    ("random chase, 1 GiB (DRAM)", ["chase", "--sizes", "1G"]),
]


def metrics(trace):
    xml = subprocess.run(["xcrun", "xctrace", "export", "--input", trace, "--xpath",
                          '/trace-toc/run[@number="1"]/data/table[@schema="MetricAggregationForProcess"]'],
                         env=ENV, capture_output=True, text=True).stdout
    root = ET.fromstring(xml)
    ids, acc = {}, {}
    for row in root.iter("row"):
        vals = []
        for el in row:
            if "ref" in el.attrib:
                el = ids[el.attrib["ref"]]
            elif "id" in el.attrib:
                ids[el.attrib["id"]] = el
            vals.append(el)
        dur, dbl, name, precise = float(vals[1].text), float(vals[4].text), vals[5].text, vals[6].text
        if precise == "1" or name == "cycle":
            continue
        a = acc.setdefault(name, [0.0, 0.0]); a[0] += dbl * dur; a[1] += dur
    return {k: v[0] / v[1] for k, v in acc.items() if v[1] > 0}


def main():
    sid = sys.argv[1] if len(sys.argv) > 1 else "manual"
    tmp = tempfile.mkdtemp()
    rows = []
    for label, args in CONFIGS:
        out = os.path.join(tmp, "t.trace")
        cmd = ["xcrun", "xctrace", "record", "--template", "CPU Counters", "--output", out, "--launch", "--", EXE] + args + ["--reps", "40", "--qos", "interactive"]
        p = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
        if not os.path.exists(out):
            print("record failed:", label, p.stderr[-300:]); continue
        m = metrics(out); shutil.rmtree(out)
        rows.append([label] + [round(m.get(k, float("nan")), 3) for k in ("useful", "delivery", "processing", "discarded")])
        print(rows[-1])
    path = os.path.join(ROOT, "data", "raw", f"xctrace_bottleneck_{sid}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["config", "useful", "delivery", "processing", "discarded"]); w.writerows(rows)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
