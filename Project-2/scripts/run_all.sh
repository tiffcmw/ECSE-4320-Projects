#!/bin/bash
# One command from raw data to plots.
#   scripts/run_all.sh                  build, self-test, parse + validate + plot from the newest raw data (about 1 min)
#   COLLECT=quick scripts/run_all.sh    first re-measure reduced sweeps into new raw files (about 3 min)
#   COLLECT=full  scripts/run_all.sh    first re-measure everything (about 30 minutes); needs about 6 GB free memory
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build.sh
./scripts/diagnostics.sh
if [ "${COLLECT:-}" = "quick" ] || [ "${COLLECT:-}" = "full" ]; then
  echo "Top CPU users before measuring (close heavy apps, plug in AC power, Low Power Mode off):"
  ps -Ao pcpu,comm -r | head -6 || true
  SID=$(date +%Y%m%d-%H%M%S)
  caffeinate -dimsu python3 scripts/run_exp.py --profile "$COLLECT" --sid "$SID"
fi
python3 scripts/parse.py
(cd scripts && python3 validate.py > /dev/null && python3 plot.py)
if command -v pandoc >/dev/null; then
  python3 scripts/build_report.py && python3 scripts/check_report.py && python3 scripts/make_docx.py > /dev/null 2>&1 || true
fi
echo "validation: data/processed/validation.md   tables: data/processed/tables.md   plots: plots/"
