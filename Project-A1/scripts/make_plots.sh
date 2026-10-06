#!/bin/bash
# Regenerate processed CSVs and all plots from the newest raw data.
set -euo pipefail
cd "$(dirname "$0")"
python3 summarize_noise.py
python3 plot_mech1.py
python3 plot_mech2.py
python3 plot_interaction.py
python3 - <<'PY'
import analyze
analyze.write_processed("chase_diag", analyze.aggregate(analyze.load("chase_diag"), "ns_per_load", ["design", "stride"]))
PY
python3 plot_ai.py
