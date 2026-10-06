#!/bin/bash
# Reproduce everything: build, tests, all experiments, analysis, plots.
#   ./scripts/run_all.sh            full profile (about 70 to 90 minutes)
#   QUICK=1 ./scripts/run_all.sh    reduced sweeps (about 15 to 20 minutes), same code paths
# Preconditions (not enforced): AC power, Low Power Mode off, no heavy apps. Thermal state is recorded per run.
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build.sh
./build/test_harness
./scripts/run_noise.sh
./scripts/run_mech1.sh
./scripts/run_mech2.sh
./scripts/run_interaction.sh
(cd scripts && caffeinate -dimsu python3 exp_chase_diag.py)
./scripts/make_plots.sh
echo "done: raw data in data/raw, processed in data/processed, plots in plots/"
