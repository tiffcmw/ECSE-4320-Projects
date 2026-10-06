#!/usr/bin/env bash
# Phase 4: Exp 3 (alignment, tail) and Exp 4 (stride, gather). QUICK=1 shortens it.
set -euo pipefail
cd "$(dirname "$0")/.."
SID=${SID:-$(date +%Y%m%d_%H%M%S)}
QUICK=${QUICK:-0}
./scripts/run_tests.sh | tail -3
./scripts/session_start.sh "$SID"
if [ "$QUICK" = 1 ]; then REPS=3; PASSES=1; TAILN="1,2,3,4,5,8,15,16,17,31,33,63,64,65,100,255,256,257,1023,1024,1025,4095,4096,4097"; WS_ST="32768,8388608"; WS_AL="32768,8388608"; OFFS="0,4,16,60,64"
else REPS=5; PASSES=3
  TAILN=$(python3 -c "print(','.join(map(str, list(range(1,161))+list(range(250,266))+list(range(1020,1030))+list(range(4090,4112))+list(range(16380,16392)))))")
  WS_ST="32768,524288,8388608,67108864,536870912"; WS_AL="32768,4194304,268435456"; OFFS="0,4,8,12,16,20,28,32,48,60,64,96,124,128,132"
fi
run() { caffeinate -dimsu bin/bench run --session "$SID" --reps $REPS --passes $PASSES "$@"; }
run --out data/raw/tail_${SID}.csv --builds scalar,scalar_unroll8,auto --kernels saxpy --dtypes f32,f64 --n "$TAILN"
run --out data/raw/align_${SID}.csv --builds scalar_unroll8,auto --kernels saxpy --dtypes f32 --ws "$WS_AL" --offset "$OFFS"
run --out data/raw/stride_${SID}.csv --builds scalar_unroll8,auto,auto_forcevec --kernels saxpy_s1,saxpy_s2,saxpy_s4,saxpy_s8,saxpy_s16,saxpy_s32,gather --dtypes f32 --ws "$WS_ST"
echo "align/stride $SID complete"
