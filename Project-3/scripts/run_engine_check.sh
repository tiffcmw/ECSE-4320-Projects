#!/bin/bash
# Quick engine/queue-depth check on a 1 GiB file. Also documents unsupported engines.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight nofile
CHECKFILE="$SCRATCH/engine_check.bin"; guard_path "$CHECKFILE"
OUT="$RAW/engine_check"; mkdir -p "$OUT"
for e in libaio io_uring posixaio psync; do
  fio --enghelp 2>&1 | grep -qw "$e" && echo "engine $e: available" || echo "engine $e: NOT available on this platform"
done | tee "$OUT/engines.txt"
fio --version >> "$OUT/engines.txt"
# write 1 GiB of incompressible data so reads hit allocated blocks
if [ ! -f "$CHECKFILE" ] || [ "$(stat -f %z "$CHECKFILE")" != 1073741824 ]; then
  fio --name=fill --filename="$CHECKFILE" --size=1g --rw=write --bs=1m --direct=1 --ioengine=psync \
      --refill_buffers=1 --buffer_compress_percentage=0 --output="$OUT/fill.log" >/dev/null
fi
sysctl kern.aiomax kern.aioprocmax kern.aiothreads > "$OUT/aio_sysctl.txt"
export CHECKFILE
run_chk() { # engine iodepth numjobs
  run_fio "$FIO_DIR/engine_check.fio" "$OUT/chk__eng=$1__iodepth=$2__numjobs=$3.json" ENGINE="$1" IODEPTH="$2" NUMJOBS="$3" CHECKFILE="$CHECKFILE"
}
for qd in 1 4 16 32 64; do run_chk posixaio $qd 1; done
for nj in 1 4 16 64; do run_chk psync 1 $nj; done
python3 -I - "$OUT" <<'PY'
import json,glob,sys,os
for f in sorted(glob.glob(sys.argv[1]+"/chk__*.json")):
    t=open(f).read(); j=json.loads(t[t.index("{"):])["jobs"][0]; r=j["read"]
    lv=j.get("iodepth_level",{}); 
    print(f"{os.path.basename(f):48s} iops={r['iops']:9.0f} mean_lat_us={r['lat_ns']['mean']/1e3:7.1f} littleQD={r['iops']*r['lat_ns']['mean']/1e9:6.2f}  fio_iodepth_level={ {k:v for k,v in lv.items() if v>0} }")
PY
