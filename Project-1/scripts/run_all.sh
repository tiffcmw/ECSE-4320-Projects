#!/usr/bin/env bash
# Reproduces the study.
#   scripts/run_all.sh                 build, test, regenerate vectorization reports and ALL plots from the committed raw data (about 1 minute)
#   COLLECT=quick scripts/run_all.sh   additionally re-measure a reduced version of every experiment into new raw CSVs (about 10 minutes) and plot those
#   COLLECT=full  scripts/run_all.sh   re-measure everything at full resolution (about 40 minutes)
# Controls for measuring: AC power, Low Power Mode off, no heavy background apps (see docs/METHODOLOGY.md).
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/run_tests.sh
python3 scripts/vecreport.py
case "${COLLECT:-none}" in
  none) ./scripts/make_plots.sh ;;
  quick|full)
    SID=${SID:-rerun_$(date +%Y%m%d_%H%M%S)}
    Q=0; [ "$COLLECT" = quick ] && Q=1
    export SID QUICK=$Q
    ./scripts/exp_sweep.sh
    ./scripts/exp_align_stride.sh
    ./scripts/exp_roofline.sh
    ./scripts/exp_extra.sh
    clang -O3 -ffast-math -std=c11 src/naive/naive_bench.c -o bin/naive_bench
    caffeinate -dimsu ./bin/naive_bench > data/raw/naive_${SID}.csv
    ./scripts/make_plots.sh "$SID" "$SID" "$SID" "$SID" ;;
  *) echo "COLLECT must be none, quick or full"; exit 2 ;;
esac
echo "run_all done"
