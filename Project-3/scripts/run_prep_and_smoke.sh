#!/bin/bash
# Prep chain: wait for AC, precondition, direct-I/O check (stops if cache-like), then SMOKE (3 s) run of each stage.
set -e
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
bash "$S/wait_for_ac.sh"
bash "$S/run_00_precondition.sh"
bash "$S/run_01_directio_check.sh"
for st in run_02_exp1_exp2 run_03_exp3_exp4 run_04_exp5_tail run_05_exp6_exp7; do
  echo "=== SMOKE $st"; SMOKE=1 SETTLE=1 bash "$S/$st.sh"
done
echo "PREP AND SMOKE DONE"
