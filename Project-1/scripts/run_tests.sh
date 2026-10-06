#!/usr/bin/env bash
# Builds and runs correctness tests. Run before every benchmark run.
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build.sh >/dev/null
./bin/test_kernels
