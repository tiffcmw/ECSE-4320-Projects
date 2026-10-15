#!/bin/bash
# Privileged measurements: powermetrics clock cross-check (R9) and PMU counters (R7).
# Usage (needs the administrator password):  sudo scripts/run_privileged.sh
set -u
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
cd "$(dirname "$0")/.."
SID=${SID:-$(date +%Y%m%d-%H%M)}
RAW=data/raw; mkdir -p $RAW/counters
echo "== powermetrics, single-thread L1-resident chase =="
{
  echo "# membench freq (dependent-add estimate, GHz):"; ./bin/membench freq
  echo "# powermetrics during a 15 s single-thread spin (chase over 16 KiB):"
} > $RAW/powermetrics_$SID.txt
powermetrics --samplers cpu_power -i 1000 -n 14 >> $RAW/powermetrics_$SID.txt 2>&1 &
PM=$!
sleep 1; ./bin/membench chase --sizes 16K --reps 400 --target-ms 30 --exp pm_spin > /dev/null
wait $PM
echo "== PMU counters (kperf) =="
python3 scripts/run_exp.py --profile full --sid ${SID}-pmu --only e13_pmu 2>&1 | tee $RAW/counters/pmu_run_$SID.log
chown -R "${SUDO_USER:-root}" $RAW data/processed 2>/dev/null
echo done
