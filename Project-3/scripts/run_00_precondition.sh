#!/bin/bash
# Creates the 32 GiB test file in scratch.noindex and fills it with incompressible data (once).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
preflight nofile
health_log precondition before
B0=$(smart_bytes_written)
if [ -f "$SCRATCH/.precondition_done" ] && [ "$(stat -f %z "$TESTFILE")" = "$SIZE_BYTES" ]; then echo "already preconditioned"; exit 0; fi
# create the file at its final size first so fio does not zero-fill it separately (sparse; every block is
# then written by the fill pass below)
[ -f "$TESTFILE" ] || mkfile -n "${SIZE_GIB}g" "$TESTFILE"
[ "$(stat -f %z "$TESTFILE")" = "$SIZE_BYTES" ] || die "test file size mismatch"
rm -f "$SCRATCH/.precondition_done"
mkdir -p "$RAW/precondition"
env TESTFILE="$TESTFILE" fio --output-format=json --output="$RAW/precondition/precondition.json" "$FIO_DIR/00_precondition.fio"
# verify the fill wrote the full size
python3 -I - "$RAW/precondition/precondition.json" "$SIZE_BYTES" <<'PY' || die "fill incomplete"
import json,sys
t=open(sys.argv[1]).read(); j=json.loads(t[t.index("{"):])["jobs"][0]["write"]
print("fill: %.1f GiB written, %.0f MB/s" % (j["io_bytes"]/2**30, j["bw_bytes"]/1e6))
sys.exit(0 if j["io_bytes"] >= int(sys.argv[2]) else 1)
PY
touch "$SCRATCH/.precondition_done"
health_log precondition after
echo "SMART host bytes written during precondition: $(( $(smart_bytes_written) - B0 ))"
