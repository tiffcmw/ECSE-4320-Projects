#!/usr/bin/env bash
# Experiments added for final submission: pointer-chase latency (A), memory-traffic accounting (B), dot-product decomposition (C),
# relative misalignment (D), stride-jump probes (E). Same methodology as the earlier runs: QoS user-interactive, 15 samples per point
# (3 passes x 5 reps, configuration order reshuffled each pass), thermal level before and after each sample, tests run first.
# Usage: SID=name [QUICK=1] scripts/exp_extra.sh      Output: data/raw/{chase,ceiling,dotdec,misalign,stridejump}_<SID>.csv
set -euo pipefail
cd "$(dirname "$0")/.."
SID=${SID:-$(date +%Y%m%d_%H%M%S)}
QUICK=${QUICK:-0}
./scripts/run_tests.sh | tail -4
./scripts/session_start.sh "$SID"
if [ "$QUICK" = 1 ]; then REPS=3; PASSES=1; CSTEP=2; DSTEP=4; DMAX=30
else REPS=5; PASSES=3; CSTEP=1; DSTEP=1; DMAX=38; fi
run() { caffeinate -dimsu bin/bench run --session "$SID" --reps $REPS --passes $PASSES "$@"; }
# A: pointer chase, 4 KiB to 2 GiB, 4 sizes per octave (2 in QUICK)
CHASE_WS=$(python3 -c "print(','.join(str(int(4096*2**(k/4))) for k in range(0,77,$CSTEP)))")
caffeinate -dimsu bin/bench chase --session "$SID" --reps $REPS --passes $PASSES --out data/raw/chase_${SID}.csv --ws "$CHASE_WS"
# A2: page-granular chase (one node per 16 KiB page, node spacing 16 KiB + 128 B): separates TLB reach from cache capacity.
# Working set = nodes x 16512 B; 16 to 16384 nodes (pages), 4 sizes per octave (2 in QUICK).
PAGE_WS=$(python3 -c "print(','.join(str(int(2**(4+k/4))*16512) for k in range(0,41,$CSTEP)))")
caffeinate -dimsu bin/bench chase --session "$SID" --reps $REPS --passes $PASSES --node-bytes 16512 --out data/raw/chasepage_${SID}.csv --ws "$PAGE_WS"
# B: traffic accounting. read, incr, copy, scale, add, saxpy_oop only exist for f32 and the builds scalar_unroll8 and auto.
CEIL_WS="32768,4194304,67108864,268435456,1073741824"; [ "$QUICK" = 1 ] && CEIL_WS="32768,268435456"
run --out data/raw/ceiling_${SID}.csv --builds scalar_unroll8,auto --kernels read,incr,copy,scale,add,triad,saxpy,saxpy_oop --dtypes f32 --ws "$CEIL_WS"
# C: dot product with 1, 4, 8, 16 scalar accumulators (-fno-vectorize), the NEON build of the same code, and the earlier dot variants, f32 and f64
DOT_WS=$(python3 -c "print(','.join(str(int(4096*2**(k/2))) for k in range(0,$DMAX+1,$DSTEP)))")
run --out data/raw/dotdec_${SID}.csv --builds scalar,auto --kernels dot_a1,dot_a4,dot_a8,dot_a16 --dtypes f32,f64 --ws "$DOT_WS" --append
run --out data/raw/dotdec_${SID}.csv --builds scalar,scalar_unroll8,auto,fastmath --kernels dot --dtypes f32,f64 --ws "$DOT_WS" --append
# D: relative misalignment, x and y start offsets independently (bytes), SAXPY f32
OFFS=(0 4 8 16 32 64); PAIRS=""
for ox in "${OFFS[@]}"; do for oy in "${OFFS[@]}"; do PAIRS="$PAIRS${PAIRS:+,}$ox:$oy"; done; done
if [ "$QUICK" = 1 ]; then PAIRS="0:0,4:0,0:4,4:4,4:8,16:16"; fi
run --out data/raw/misalign_${SID}.csv --builds scalar_unroll8,auto --kernels saxpy --dtypes f32 --ws 32768,268435456 --offsets-xy "$PAIRS"
# E: stride-jump probes. Strides 16, 24, 32, 48 at three footprints, then stride 32 and 16 at footprint-aligned and unaligned element counts.
E_WS="8388608,67108864,536870912"; [ "$QUICK" = 1 ] && E_WS="8388608,536870912"
run --out data/raw/stridejump_${SID}.csv --builds auto,scalar_unroll8 --kernels saxpy_s1,saxpy_s16,saxpy_s24,saxpy_s32,saxpy_s48 --dtypes f32 --ws "$E_WS" --append
run --out data/raw/stridejump_${SID}.csv --builds auto --kernels saxpy_s16,saxpy_s32 --dtypes f32 --n 2097152,2097153,2097216 --append
echo "extra experiments $SID complete"
