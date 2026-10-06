#!/usr/bin/env bash
# Per-session characterization: environment snapshot, timer overhead, clock estimate. Usage: session_start.sh <session-id>
set -euo pipefail
cd "$(dirname "$0")/.."
SID=${1:-$(date +%Y%m%d_%H%M%S)}
./scripts/capture_env.sh >/dev/null
./bin/bench timer | tee data/raw/timer_${SID}.txt
caffeinate -dimsu ./bin/bench freq --out data/raw/freq_${SID}.csv --session "$SID" --reps 100
python3 -I - <<PY
import sys; sys.path.insert(0, "scripts")
import analyze
g, h = analyze.freq_ghz(["data/raw/freq_${SID}.csv"])
print("session ${SID}: effective clock %.3f GHz (IQR half-width %.3f)" % (g, h))
PY
