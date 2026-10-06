#!/usr/bin/env bash
# Phase 5: Exp 6 (bandwidth ceilings, FMA peak) and Exp 7 (negative cases: aliasing, restrict overhead, reduction numerics).
set -euo pipefail
cd "$(dirname "$0")/.."
SID=${SID:-$(date +%Y%m%d_%H%M%S)}
QUICK=${QUICK:-0}
./scripts/run_tests.sh | tail -3
./scripts/session_start.sh "$SID"
if [ "$QUICK" = 1 ]; then REPS=3; PASSES=1; TRIADWS="33554432,268435456"; KS="1 2"; FREPS=5; ACC_SKIP=1
else REPS=5; PASSES=3; TRIADWS="32768,4194304,268435456,536870912,1073741824,2147483648"; KS="1 2 4 6 12"; FREPS=15; ACC_SKIP=0; fi
run() { caffeinate -dimsu bin/bench run --session "$SID" --reps $REPS --passes $PASSES "$@"; }
caffeinate -dimsu bin/bench fmapeak --out data/raw/fmapeak_${SID}.csv --session "$SID" --reps $FREPS
run --out data/raw/triad_${SID}.csv --builds scalar_unroll8,auto --kernels triad --dtypes f32,f64 --ws "$TRIADWS"
# aggregate bandwidth: k concurrent single-thread processes (separate address spaces), 512 MiB triad each (QUICK: 256 MiB)
AGG=536870912; [ "$QUICK" = 1 ] && AGG=268435456
for k in $KS; do
  for i in $(seq 1 $k); do
    caffeinate -dimsu bin/bench run --session "$SID" --reps 5 --passes 2 --out data/raw/triadmp_${SID}_k${k}_p${i}.csv --builds auto --kernels triad --dtypes f32 --ws $AGG &
  done; wait
done
# negative case: aliasing (no restrict) and restrict overhead
run --out data/raw/alias_${SID}.csv --builds auto,auto_norestrict,scalar_norestrict,scalar_unroll8 --kernels saxpy --dtypes f32 --ws 32768,4194304,268435456 --alias 0
run --out data/raw/alias_${SID}_overlap1.csv --builds auto_norestrict,scalar_norestrict --kernels saxpy --dtypes f32 --ws 32768,4194304,268435456 --alias 1
run --out data/raw/alias_${SID}_overlap64.csv --builds auto_norestrict,scalar_norestrict --kernels saxpy --dtypes f32 --ws 32768,4194304,268435456 --alias 64
run --out data/raw/restrict_smalln_${SID}.csv --builds auto,auto_norestrict --kernels saxpy --dtypes f32 --n 4,8,16,32,64,128,256,512,1024,4096
bin/accuracy data/raw/accuracy_${SID}.csv
echo "roofline/negative $SID complete"
