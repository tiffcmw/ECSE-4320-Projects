#!/usr/bin/env bash
# Regenerates every plot and processed table from the raw CSVs. Usage: make_plots.sh [SWEEP_SID ALIGN_SID ROOF_SID]
# Defaults are the committed full-run sessions.
set -euo pipefail
cd "$(dirname "$0")/.."
SW=${1:-phase3}; AL=${2:-phase4}; RF=${3:-phase5}
mkdir -p plots data/processed
python3 scripts/plot_sweep.py "$SW"
python3 scripts/plot_align_stride.py "$AL"
python3 scripts/plot_roofline.py "$SW" "$RF"
ls plots/*.png | wc -l
