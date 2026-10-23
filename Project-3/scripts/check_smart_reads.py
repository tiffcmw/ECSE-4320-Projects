#!/usr/bin/env python3
"""Independent direct-I/O evidence: bytes fio counted as read vs the SSD's own SMART 'Data Units Read' delta per stage.
If a cache served the reads, SMART would be LOWER than fio. fio's JSON excludes ramp-time IO, so SMART/fio should be about
(runtime+ramp)/runtime or a little more. Writes: same idea with Data Units Written (see exp6b/bytes_written.txt)."""
import json, glob, os
P3 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def smart(path, key):
    for l in open(path):
        if key in l: return int(l.split(":")[1].split("[")[0].replace(",", "").strip()) * 512000
def fio_read(pats):
    tot = 0
    for p in pats:
        for f in glob.glob(P3 + "/" + p):
            t = open(f).read(); tot += json.loads(t[t.index("{"):])["jobs"][0]["read"]["io_bytes"]
    return tot
rows = [("exp34 (Exp 3 and 4, 23 s runs: ramp factor 1.15)", "exp34", ["data/raw/exp3/*.json", "data/raw/exp4/*.json"]),
        ("exp5 (65 s runs: ramp factor 1.08)", "exp5", ["data/raw/exp5/*.json"]),
        ("driftseries (12 s runs: ramp factor 1.20)", "driftseries", ["data/raw/driftseries/*.json"]),
        ("exp4b replicate (23 s runs: ramp factor 1.15)", "exp4b", ["data/raw/exp4b/*.json"])]
out = ["| stage | SMART read delta (GB) | fio read bytes after ramp (GB) | SMART / fio |", "|---|---|---|---|"]
for nm, st, pats in rows:
    b = smart(f"{P3}/data/raw/health/{st}_before.txt", "Data Units Read"); a = smart(f"{P3}/data/raw/health/{st}_after.txt", "Data Units Read"); fb = fio_read(pats)
    out.append(f"| {nm} | {(a-b)/1e9:.1f} | {fb/1e9:.1f} | {(a-b)/fb:.2f} |")
open(P3 + "/data/processed/tables/smart_read_check.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))
