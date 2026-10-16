#!/bin/bash
# 20 s QD1 4 KiB random read, direct=1 vs direct=0, same file and range. Prints the latency difference.
# Exit status 2 if direct=1 looks cache-like (mean latency < 15 us, or within 3x of the buffered run).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight
OUT="$RAW/directio_check"; mkdir -p "$OUT"
health_log directio before
# drop any cached pages of the file before the buffered run so it starts cold (purge needs sudo; not used).
run_fio "$FIO_DIR/00_directio_check.fio" "$OUT/directio__direct=1.json" DIRECT=1
run_fio "$FIO_DIR/00_directio_check.fio" "$OUT/directio__direct=0.json" DIRECT=0
health_log directio after
python3 -I - "$OUT" <<'PY'
import json,sys
def g(f):
    t=open(f).read(); return json.loads(t[t.index("{"):])["jobs"][0]["read"]
d=g(sys.argv[1]+"/directio__direct=1.json"); b=g(sys.argv[1]+"/directio__direct=0.json")
for n,r in (("direct=1",d),("direct=0",b)):
    p=r["lat_ns"]["percentile"]
    print(f"{n}: IOPS={r['iops']:.0f}  mean={r['lat_ns']['mean']/1e3:.2f} us  p50={p['50.000000']/1e3:.2f}  p99={p['99.000000']/1e3:.2f} us")
ratio=d["lat_ns"]["mean"]/b["lat_ns"]["mean"]
print(f"direct/buffered mean latency ratio = {ratio:.1f}x; buffered IOPS / direct IOPS = {b['iops']/d['iops']:.1f}x")
bad = d["lat_ns"]["mean"] < 15e3 or ratio < 3
print("VERDICT: direct=1 looks CACHE-LIKE, STOP" if bad else "VERDICT: direct=1 bypasses the page cache (latency is flash-like and far above the buffered run)")
sys.exit(2 if bad else 0)
PY
