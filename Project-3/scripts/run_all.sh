#!/bin/bash
# One command, end to end. Needs: AC power, lid open, machine otherwise idle. Total about 3 hours and about 4 TB of SSD writes
# (32 GiB fill + ~1.5 TB Exp 2 writes + 2.2 TB sustained write + small stages; SMART counters are logged per stage).
# Usage: bash scripts/run_all.sh        (ALLOW_BATTERY is deliberately not honoured by the stage drivers' guard defaults)
set -euo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"; P3="$(dirname "$S")"
PY="$P3/.venv/bin/python"; [ -x "$PY" ] || { python3 -m venv "$P3/.venv" && "$P3/.venv/bin/pip" install -q matplotlib numpy; }
bash "$S/wait_for_ac.sh"
bash "$S/run_engine_check.sh"
bash "$S/run_00_precondition.sh"
bash "$S/run_01_directio_check.sh"            # exits 2 and stops everything if direct=1 looks cache-like
for st in run_02_exp1_exp2 run_03_exp3_exp4 run_04_exp5_tail run_05_exp6_exp7 run_06_drift_series run_07_exp4_replicate; do
  echo "=== $st"; bash "$S/$st.sh"
done
"$PY" -I "$S/parse_fio.py"; "$PY" -I "$S/make_tables.py"; "$PY" -I "$S/analyze_state_split.py"; "$PY" -I "$S/check_smart_reads.py"; "$PY" -I "$S/plots.py"; "$PY" -I "$S/build_report.py"
if command -v node >/dev/null && [ -d "$S/docx/node_modules" ]; then "$PY" -I "$S/export_docx_data.py" && node "$S/docx/make_docx.js" && "$PY" -I "$S/check_docx_numbers.py"; else echo "skipping Word report (needs: cd scripts/docx && npm install docx; pandoc for the number check)"; fi
echo "done. When finished with the test file:  bash scripts/cleanup.sh"
