#!/usr/bin/env bash
# Phase 3: Experiments 1, 2 and 5 (working-set sweeps). QUICK=1 gives a short version for reproducibility checks.
# Output: data/raw/sweep_<SID>_{A,B,C,D}.csv. Usage: SID=name [QUICK=1] scripts/exp_sweep.sh
set -euo pipefail
cd "$(dirname "$0")/.."
SID=${SID:-$(date +%Y%m%d_%H%M%S)}
QUICK=${QUICK:-0}
./scripts/run_tests.sh | tail -3
./scripts/session_start.sh "$SID"
if [ "$QUICK" = 1 ]; then STEP=4; MAXK=30; REPS=3; PASSES=1; else STEP=1; MAXK=38; REPS=5; PASSES=3; fi
sizes() { python3 -c "print(','.join(str(int(4096*2**(k/2))) for k in range($1,$MAXK+1,$2)))"; }
S_ALL=$(sizes 0 $STEP); S_HALF=$(sizes 0 $((STEP*2)))
S_DENSE=$(python3 -c "print(','.join(str(int(2**23*2**(k/4))) for k in range(0,29 if $STEP==1 else 29,$STEP)))")  # 8 MiB to 1 GiB, 2^(1/4) steps
B=bin/bench
run() { caffeinate -dimsu $B run --session "$SID" --reps $REPS --passes $PASSES "$@"; }
run --out data/raw/sweep_${SID}_A.csv --builds scalar,scalar_unroll8,auto,fastmath --kernels saxpy,mul,dot,stencil --dtypes f32,f64 --ws "$S_ALL"
run --out data/raw/sweep_${SID}_B.csv --builds native --kernels saxpy,mul,dot,stencil --dtypes f32 --ws "$S_ALL"
run --out data/raw/sweep_${SID}_C.csv --builds scalar_unroll8,auto,fastmath --kernels saxpy,mul,dot,stencil --dtypes u32 --ws "$S_HALF"
run --out data/raw/sweep_${SID}_D.csv --builds scalar_unroll8,auto --kernels saxpy --dtypes f32 --ws "$S_DENSE"
echo "sweep $SID complete"
