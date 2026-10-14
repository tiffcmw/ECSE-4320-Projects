#!/bin/bash
# Self-test, huge-page probe, and disassembly evidence for the dead-code-elimination pitfall.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw data/processed
./bin/membench selftest 2> data/processed/selftest.log || true
tail -1 data/processed/selftest.log
./bin/membench hugetest > data/raw/hugetest.txt 2>&1 || true
cat data/raw/hugetest.txt
# Disassembly of the two loops: the unused-result loop must reduce to a bare return.
# read_nosink has no symbol at all (the optimizer deleted the empty function), so the evidence is the caller run_dce.
{ echo "# otool -tV: nm shows read_nosink present? $(nm bin/membench | grep -c _read_nosink) (0 = function removed)";
  otool -tV bin/membench | awk '/^_read_sink:/{p=1} /^_run_dce:/{p=1} p{print} /^_[a-z_0-9]+:$/ && !/^_read_sink:/ && !/^_run_dce:/{p=0}'; } > data/raw/dce_asm.txt
echo "dce disassembly lines: $(wc -l < data/raw/dce_asm.txt)"
